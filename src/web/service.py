import logging
import math
import os
import threading
import time
from datetime import datetime

import yaml

from douban.s1_crawl.crawl_base import WriteEngine
from douban.s1_crawl.crawl_via_html import DoubanCrawlerViaHTML
from douban.s2_analysis.rules import parse_price, is_seeking, is_from_personal, is_only_for_girls
from gaode.base import GaodeBase, GaodeError
from settings import SRC_DIR
from web.store import Store, today

DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(os.path.dirname(SRC_DIR), "var")

GROUP_LABELS = {"beijingzufang": "北京租房", "zhufang": "北京无中介租房"}

CRAWL_INTERVAL_SECONDS = int(os.environ.get("CRAWL_INTERVAL_MINUTES", "30")) * 60
# 匿名访问翻到第 400 条左右就会 403 或跳人机验证，再深只会招来风控；靠高频增量累积历史
PAGES_PER_CYCLE = 4
KEEP_DAYS = 30

# 高德 key 是站长个人的，对外服务必须给调用量设上限
GAODE_DAILY_BUDGET = int(os.environ.get("GAODE_DAILY_BUDGET", "3000"))
LOCATE_BUDGET_SHARE = 0.6
MAX_TRANSIT_PER_SEARCH = 25
# 直线距离超过「通勤分钟数 × 该值」的房源不再请求公交规划
KM_PER_MINUTE = 0.35

log = logging.getLogger("douban-renting")


class TargetNotFound(Exception):
    pass


def to_api_time(naive_iso):
    """库里存的是豆瓣页面上的北京时间（无时区），对外补上偏移，避免海外浏览器按本地时区解读"""
    return f"{naive_iso}+08:00" if naive_iso else None


class WebGaode(GaodeBase):

    def is_transit_cached(self, from_coords: str, to_coords: str) -> bool:
        return f"{from_coords}-{to_coords}" in self._coordspair2duration_dict

    def transit_minutes(self, from_coords: str, to_coords: str, city: str):
        minutes = self._calc_transit_duration_between_coords(from_coords, to_coords, city)
        return minutes if minutes is not None and minutes >= 0 else None


def distance_km(a: str, b: str) -> float:
    lng1, lat1 = map(float, a.split(","))
    lng2, lat2 = map(float, b.split(","))
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


class Service:

    def __init__(self):
        config = yaml.safe_load(open(os.path.join(SRC_DIR, "config.yaml"), encoding="utf-8"))
        self.city = config["city"]
        self.groups = config["groups"].split("|")

        os.makedirs(DATA_DIR, exist_ok=True)
        self.store = Store(os.path.join(DATA_DIR, "douban.db"))
        self.gaode = WebGaode(cache_dir=os.path.join(DATA_DIR, "gaode"))
        self.gaode._s.hooks["response"].append(lambda *args, **kwargs: self.store.add_gaode_call())
        self.gaode_lock = threading.Lock()
        self.crawler = DoubanCrawlerViaHTML(write_engine=WriteEngine.STDOUT)

    # ---------- 高德额度 ----------

    def _gaode_available(self, kind: str, share: float = 1.0) -> bool:
        if self.store.get_meta(f"gaode_exhausted:{kind}") == today():
            return False
        return self.store.gaode_calls_today() < GAODE_DAILY_BUDGET * share

    def _on_gaode_error(self, kind: str, e: GaodeError):
        log.warning(f"gaode {kind} error: {e}")
        if e.is_quota_exceeded:
            self.store.set_meta(f"gaode_exhausted:{kind}", today())

    # ---------- 后台任务 ----------

    def crawl_group(self, group: str):
        start = 0
        for _ in range(PAGES_PER_CYCLE):
            try:
                topics = list(self.crawler._get_topics_of_group(group, start, 100))
            except Exception as e:
                log.warning(f"crawl {group} stopped at {start}: {e}")
                break
            for t in topics:
                self.store.upsert_topic(
                    topic_id=t["post_url"].rstrip("/").split("/")[-1],
                    group=group,
                    title=t["post_title"],
                    url=t["post_url"],
                    reply_count=t["response_count"],
                    last_reply_at=t["response_latest_time"].isoformat(timespec="seconds"),
                    price=parse_price(t["post_title"]),
                )
            start += len(topics)
            time.sleep(2)
        log.info(f"crawled {start} topics from {group}")

    def locate_pending(self, limit: int = 400):
        located = 0
        try:
            for row in self.store.pending_locate(limit):
                if not self._gaode_available("poi", LOCATE_BUDGET_SHARE):
                    break
                try:
                    with self.gaode_lock:
                        poi = self.gaode.search_poi(row["title"], self.city)
                except GaodeError as e:
                    self._on_gaode_error("poi", e)
                    break
                self.store.set_location(row["id"], poi)
                located += 1
        finally:
            with self.gaode_lock:
                self.gaode.dump_dict()
        log.info(f"located {located} topics")

    def run_forever(self, stop: threading.Event):
        # 重启不应打乱抓取节奏，否则频繁部署会变成高频请求豆瓣
        last = self.store.get_meta("last_crawl_at")
        if last:
            elapsed = (datetime.now() - datetime.fromisoformat(last)).total_seconds()
            stop.wait(max(0.0, CRAWL_INTERVAL_SECONDS - elapsed))
        while not stop.is_set():
            try:
                for group in self.groups:
                    self.crawl_group(group)
                self.locate_pending()
                self.store.prune(KEEP_DAYS)
                self.store.set_meta("last_crawl_at", datetime.now().isoformat(timespec="seconds"))
            except Exception:
                log.exception("crawl cycle failed")
            stop.wait(CRAWL_INTERVAL_SECONDS)

    # ---------- 查询 ----------

    def health(self):
        return {
            "city": self.city,
            "groups": [{"id": g, "label": GROUP_LABELS.get(g, g)} for g in self.groups],
            "last_crawl_at": to_api_time(self.store.get_meta("last_crawl_at")),
            **self.store.stats(),
        }

    def _resolve_target(self, address: str) -> dict:
        if not self._gaode_available("poi"):
            raise TargetNotFound("今日地点查询额度已用完，请明天再试")
        try:
            with self.gaode_lock:
                poi = self.gaode.search_poi(address, self.city)
        except GaodeError as e:
            self._on_gaode_error("poi", e)
            raise TargetNotFound("地点查询暂时不可用，请稍后再试")
        if not poi:
            raise TargetNotFound(f"在{self.city}没找到「{address}」，换个更具体的地点名试试")
        return poi

    def _serialize(self, c: dict) -> dict:
        place = " ".join(filter(None, [c.get("poi_district"), c.get("poi_name")])) or None
        return {
            "title": c["title"],
            "url": c["url"],
            "group": GROUP_LABELS.get(c["grp"], c["grp"]),
            "price": c["price"],
            "last_reply_at": to_api_time(c["last_reply_at"]),
            "reply_count": c["reply_count"],
            "place": place,
            "distance_km": round(c["distance_km"], 1) if c.get("distance_km") is not None else None,
            "minutes": c.get("minutes"),
        }

    def search(self, address: str, max_minutes: int, min_price: int, max_price: int, days: int,
               personal_only: bool, exclude_girls_only: bool, exclude_unknown_price: bool):
        seen_titles = set()
        candidates = []
        for row in self.store.recent_topics(days):
            title = row["title"]
            # 同一房源常被反复顶帖重发，只保留最新一条
            if title in seen_titles or is_seeking(title):
                continue
            seen_titles.add(title)
            if personal_only and not is_from_personal(title):
                continue
            if exclude_girls_only and is_only_for_girls(title):
                continue
            price = row["price"]
            if price is None:
                if exclude_unknown_price:
                    continue
            elif not min_price <= price <= max_price:
                continue
            candidates.append(dict(row))

        stats = {"matched": len(candidates)}
        if not address:
            return {"target": None, "stats": stats, "items": [self._serialize(c) for c in candidates[:100]],
                    "nearby_uncomputed": []}

        target = self._resolve_target(address)
        nearby = []
        for c in candidates:
            # 标题写着「通勤国贸」这类目的地时，POI 会落在目标点本身，真实位置未知
            if c["location"] and c["location"] != target["location"]:
                c["distance_km"] = distance_km(c["location"], target["location"])
                if c["distance_km"] <= max_minutes * KM_PER_MINUTE:
                    nearby.append(c)
        nearby.sort(key=lambda c: c["distance_km"])

        requested = 0
        route_limited = False
        for c in nearby:
            cached = self.gaode.is_transit_cached(c["location"], target["location"])
            if not cached:
                if requested >= MAX_TRANSIT_PER_SEARCH or not self._gaode_available("route"):
                    route_limited = True
                    continue
                requested += 1
            try:
                with self.gaode_lock:
                    c["minutes"] = self.gaode.transit_minutes(c["location"], target["location"], self.city)
            except GaodeError as e:
                self._on_gaode_error("route", e)
                route_limited = True
        if requested:
            with self.gaode_lock:
                self.gaode.dump_dict()

        items = [c for c in nearby if c.get("minutes") is not None and c["minutes"] <= max_minutes]
        items.sort(key=lambda c: (c["minutes"], c["distance_km"]))
        uncomputed = [c for c in nearby if "minutes" not in c]

        stats.update({
            "located": sum(1 for c in candidates if c["location"]),
            "nearby": len(nearby),
            "route_limited": route_limited,
        })
        return {
            "target": {"name": target["name"], "district": target["adname"], "location": target["location"]},
            "stats": stats,
            "items": [self._serialize(c) for c in items],
            "nearby_uncomputed": [self._serialize(c) for c in uncomputed[:30]],
        }
