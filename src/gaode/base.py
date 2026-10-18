import json
import os
import threading
import time

import requests
import logging

from settings import GAODE_DIR

GAODE_GLOBAL_DIR = os.path.join(GAODE_DIR, "globals")


class GaodeError(Exception):
    """高德返回 status=0（额度、QPS、key 等问题），结果不可缓存"""

    def __init__(self, infocode: str, info: str):
        super().__init__(f"{infocode} {info}")
        self.infocode = infocode
        self.info = info

    @property
    def is_quota_exceeded(self):
        return self.infocode in ("10003", "10044", "10045")


# 个人开发者 key 的并发上限很低（实测约 3 QPS），超限返回 100xx 而非 HTTP 429
QPS_INFOCODES = ("10019", "10020", "10021")
MIN_INTERVAL_SECONDS = 0.35


def _ensure_ok(result: dict) -> dict:
    if result.get("status") != "1":
        raise GaodeError(str(result.get("infocode")), str(result.get("info")))
    return result


class GaodeBase:

    def __init__(self, cache_dir: str = GAODE_GLOBAL_DIR):
        self._key = os.environ.get("GAODE_KEY") or os.environ.get("GAODE_WEB_SERVICE_API_KEY")
        if not self._key:
            raise Exception("should set GAODE_KEY (or GAODE_WEB_SERVICE_API_KEY) in environment variables")

        self._s = requests.Session()
        self._s.params["key"] = self._key
        self._throttle_lock = threading.Lock()
        self._last_request_at = 0.0

        os.makedirs(cache_dir, exist_ok=True)
        self._addr2coords_fp = os.path.join(cache_dir, "addr2coords.json")
        self._addr2coords_dict = {}

        self._dict_coords2name_fp = os.path.join(cache_dir, "coords2name.json")
        self._coords2name_dict = {}

        self._dict_coordspair2duration_fp = os.path.join(cache_dir, "coordspair2duration.json")
        self._coordspair2duration_dict = {}

        self._poi_fp = os.path.join(cache_dir, "poi.json")
        self._poi_dict = {}

        self.load_dict()

    def _get(self, url: str, params: dict):
        for attempt in range(4):
            with self._throttle_lock:
                wait = self._last_request_at + MIN_INTERVAL_SECONDS - time.monotonic()
                if wait > 0:
                    time.sleep(wait)
                self._last_request_at = time.monotonic()
            res = self._s.get(url, params=params, timeout=10)
            if res.status_code == 200 and str(res.json().get("infocode")) in QPS_INFOCODES and attempt < 3:
                time.sleep(1 + attempt)
                continue
            return res

    # 编码
    def _get_coords_from_addr(self, addr: str, city: str):
        logging.debug(f"getting addr of <{addr}>")
        if addr not in self._addr2coords_dict:
            res = self._get('https://restapi.amap.com/v3/geocode/geo', params={
                "city": city,
                "address": addr,
            })
            logging.info(f"address: {addr}, fetching url: {res.url}")

            assert res.status_code == 200
            result = _ensure_ok(res.json())
            count = int(result.get('count', 0))
            if count == 0:
                logging.warning(f"should have result when getting coords from addr: {addr}, however got: {result}")
                self._addr2coords_dict[addr] = None
            else:
                if count > 1:
                    logging.warning("more than 1 result, select the first")
                loc = result["geocodes"][0]["location"]
                self._addr2coords_dict[addr] = loc

        return self._addr2coords_dict[addr]

    def get_addr_name_from_coords(self, coords: str):
        logging.debug(f"getting addr name from coords of <{coords}>")
        if not coords:
            logging.debug("skip getting addr name from coords since it's empty")
            return None
        if coords not in self._coords2name_dict:
            logging.debug(f"fetching coords of {coords} from gaode api")
            res = self._get('https://restapi.amap.com/v3/geocode/regeo', params={
                "location": coords,
            })

            assert res.status_code == 200
            result = _ensure_ok(res.json())
            self._coords2name_dict[coords] = result['regeocode']['formatted_address']
        return self._coords2name_dict[coords]

    # 步行
    def _calc_walking_duration(self, from_loc, to_loc):
        res = self._get('https://restapi.amap.com/v3/direction/walking',
                          params={
                              "origin": from_loc,
                              "destination": to_loc,
                              "output": "json",
                          })
        result = _ensure_ok(res.json())
        count = int(result.get("count", 0))
        if count == 0:
            logging.warning("not found any walking solution")
            logging.warning(result)
            return -1
        return int(float(result["route"]["paths"][0]["duration"]) / 60)  # minutes

    # 通勤计算
    def _calc_transit_duration_between_coords(self, from_coords, to_coords, city):
        if not to_coords:
            raise Exception("to coords must exist")
        if not from_coords:
            return None

        key = from_coords + "-" + to_coords

        if key not in self._coordspair2duration_dict:
            res = self._get('https://restapi.amap.com/v3/direction/transit/integrated',
                              params={
                                  "origin": from_coords,
                                  "destination": to_coords,
                                  "strategy": 3,  # 0：最快捷模式, 1：最经济模式, 2：最少换乘模式, 3：最少步行模式, 5：不乘地铁模式
                                  "city": city
                              })
            result = _ensure_ok(res.json())
            count = int(result.get("count", 0))
            if count == 0:
                logging.info("not found any transit solution, trying walking ones")
                logging.info(result)
                self._coordspair2duration_dict[key] = self._calc_walking_duration(from_coords, to_coords)
            else:
                self._coordspair2duration_dict[key] = int(
                    float(result["route"]["transits"][0]["duration"]) / 60)  # minutes
        return self._coordspair2duration_dict[key]

    # 关键字搜索：租房帖标题里多是小区名、地铁站名，POI 搜索比地理编码命中率高得多
    def search_poi(self, keywords: str, city: str):
        keywords = keywords[:80]
        if keywords not in self._poi_dict:
            res = self._get('https://restapi.amap.com/v3/place/text', params={
                "keywords": keywords,
                "city": city,
                "citylimit": "true",
                "offset": 1,
                "page": 1,
            })
            assert res.status_code == 200
            pois = _ensure_ok(res.json()).get("pois") or []
            if pois and isinstance(pois[0].get("location"), str) and pois[0]["location"]:
                poi = pois[0]
                self._poi_dict[keywords] = {
                    "location": poi["location"],
                    "name": poi.get("name") or "",
                    "adname": poi.get("adname") if isinstance(poi.get("adname"), str) else "",
                }
            else:
                self._poi_dict[keywords] = None
        return self._poi_dict[keywords]

    # 通勤计算
    def _calc_transit_duration_between_addrs(self, from_addr, to_addr, city):
        from_loc = self._get_coords_from_addr(from_addr, city)
        to_loc = self._get_coords_from_addr(to_addr, city)
        return self._calc_transit_duration_between_coords(from_loc, to_loc, city)

    def load_dict(self):
        if os.path.exists(self._addr2coords_fp):
            self._addr2coords_dict = json.load(open(self._addr2coords_fp))
        if os.path.exists(self._dict_coords2name_fp):
            self._coords2name_dict = json.load(open(self._dict_coords2name_fp))
        if os.path.exists(self._dict_coordspair2duration_fp):
            self._coordspair2duration_dict = json.load(open(self._dict_coordspair2duration_fp))
        if os.path.exists(self._poi_fp):
            self._poi_dict = json.load(open(self._poi_fp))

        print(f"loaded "
              f"{len(self._addr2coords_dict)} addr2coords, "
              f"{len(self._coords2name_dict)} coords2name, "
              f"{len(self._coordspair2duration_dict)} coordspair2duration")

    def dump_dict(self):

        if self._addr2coords_dict:  # avoid override by an empty dict
            json.dump(self._addr2coords_dict, open(self._addr2coords_fp, "w"), ensure_ascii=False, indent=2)
        if self._coords2name_dict:  # avoid override by an empty dict
            json.dump(self._coords2name_dict, open(self._dict_coords2name_fp, "w"), ensure_ascii=False, indent=2)
        if self._coordspair2duration_dict:  # avoid override by an empty dict
            json.dump(self._coordspair2duration_dict, open(self._dict_coordspair2duration_fp, "w"), ensure_ascii=False,
                      indent=2)
        if self._poi_dict:
            json.dump(self._poi_dict, open(self._poi_fp, "w"), ensure_ascii=False, indent=2)
