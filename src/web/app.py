import logging
import os
import threading
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles

from web.service import Service, TargetNotFound

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# 带地址的查询会消耗高德额度，按 IP 限流
RATE_LIMIT = 20
RATE_WINDOW_SECONDS = 600

service = Service()


class RateLimiter:

    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window
        self._hits = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] < now - self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                return False
            hits.append(now)
            return True


limiter = RateLimiter(RATE_LIMIT, RATE_WINDOW_SECONDS)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    stop = threading.Event()
    if os.environ.get("DISABLE_CRAWLER") != "1":
        threading.Thread(target=service.run_forever, args=(stop,), daemon=True, name="crawler").start()
    yield
    stop.set()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.get("/api/health")
def health():
    return service.health()


@app.get("/api/search")
def search(
        request: Request,
        address: str = Query("", max_length=60),
        max_minutes: int = Query(45, ge=10, le=120),
        min_price: int = Query(0, ge=0, le=100000),
        max_price: int = Query(100000, ge=0, le=100000),
        days: int = Query(7, ge=1, le=30),
        personal_only: bool = False,
        exclude_girls_only: bool = False,
        exclude_unknown_price: bool = False,
):
    address = address.strip()
    if address:
        client_ip = request.headers.get("cf-connecting-ip") or request.client.host
        if not limiter.allow(client_ip):
            raise HTTPException(429, "查询太频繁，请十分钟后再试")
    try:
        return service.search(address, max_minutes, min_price, max_price, days,
                              personal_only, exclude_girls_only, exclude_unknown_price)
    except TargetNotFound as e:
        raise HTTPException(422, str(e))


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
