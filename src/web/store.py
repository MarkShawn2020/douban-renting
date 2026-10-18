import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Optional

SCHEMA = """
create table if not exists topics (
    id text primary key,
    grp text not null,
    title text not null,
    url text not null,
    reply_count integer not null default 0,
    last_reply_at text not null,
    first_seen_at text not null,
    price real,
    located integer not null default 0,
    location text,
    poi_name text,
    poi_district text
);
create index if not exists idx_topics_last_reply on topics(last_reply_at);
create table if not exists meta (key text primary key, value text);
create table if not exists gaode_usage (day text primary key, calls integer not null);
"""


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


class Store:

    def __init__(self, path: str):
        self._lock = threading.Lock()
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("pragma journal_mode=wal")
        self._db.executescript(SCHEMA)

    def _exec(self, sql: str, params=()):
        with self._lock, self._db:
            return self._db.execute(sql, params)

    def _query(self, sql: str, params=()):
        with self._lock:
            return self._db.execute(sql, params).fetchall()

    def upsert_topic(self, topic_id: str, group: str, title: str, url: str, reply_count: int,
                     last_reply_at: str, price: Optional[float]):
        self._exec("""
            insert into topics (id, grp, title, url, reply_count, last_reply_at, first_seen_at, price)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(id) do update set
                reply_count = excluded.reply_count,
                last_reply_at = max(topics.last_reply_at, excluded.last_reply_at)
        """, (topic_id, group, title, url, reply_count, last_reply_at, datetime.now().isoformat(timespec="seconds"),
              price))

    def pending_locate(self, limit: int):
        return self._query("""
            select id, title from topics where located = 0 and title not like '%求%'
            order by last_reply_at desc limit ?
        """, (limit,))

    def set_location(self, topic_id: str, poi: Optional[dict]):
        poi = poi or {}
        self._exec("update topics set located = 1, location = ?, poi_name = ?, poi_district = ? where id = ?",
                   (poi.get("location"), poi.get("name"), poi.get("adname"), topic_id))

    def recent_topics(self, days: int):
        since = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
        return self._query("select * from topics where last_reply_at >= ? order by last_reply_at desc", (since,))

    def prune(self, keep_days: int):
        since = (datetime.now() - timedelta(days=keep_days)).isoformat(timespec="seconds")
        self._exec("delete from topics where last_reply_at < ?", (since,))

    def stats(self):
        row = self._query("select count(*), sum(located), sum(location is not null) from topics")[0]
        return {"topics": row[0], "located": row[1] or 0, "with_location": row[2] or 0}

    def get_meta(self, key: str) -> Optional[str]:
        rows = self._query("select value from meta where key = ?", (key,))
        return rows[0][0] if rows else None

    def set_meta(self, key: str, value: str):
        self._exec("insert into meta (key, value) values (?, ?) on conflict(key) do update set value = excluded.value",
                   (key, value))

    def add_gaode_call(self):
        self._exec("""
            insert into gaode_usage (day, calls) values (?, 1)
            on conflict(day) do update set calls = calls + 1
        """, (today(),))

    def gaode_calls_today(self) -> int:
        rows = self._query("select calls from gaode_usage where day = ?", (today(),))
        return rows[0][0] if rows else 0
