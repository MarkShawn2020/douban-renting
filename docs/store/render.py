"""
渲染 Chrome Web Store 上架素材到 docs/store/：5 张 1280x800 截图、440x280 / 1400x560 宣传图、128 商店图标。

    python3 docs/store/render.py

截图用 tests/extension/fixtures 的豆瓣页面夹具，不访问豆瓣线上页面。
通勤截图要真实调用高德：首次运行需要环境变量 GAODE_WEB_SERVICE_API_KEY（或 GAODE_KEY），
定位与通勤结果缓存到 var/store/commute-cache.json；之后重渲染只读缓存，并拦掉所有高德请求。
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[2]
EXT_DIR = ROOT / "extension"
FIXTURES = ROOT / "tests" / "extension" / "fixtures"
OUT = Path(__file__).resolve().parent
SHOTS = OUT / "screenshots"
CACHE = ROOT / "var" / "store" / "commute-cache.json"
GAODE_KEY = os.environ.get("GAODE_KEY") or os.environ.get("GAODE_WEB_SERVICE_API_KEY")

LIST_URL = "https://www.douban.com/group/beijingzufang/discussion?start=0&type=new"
TOPIC_ID = "502852342"
TOPIC_URL = f"https://www.douban.com/group/topic/{TOPIC_ID}/"

# 商店会把截图缩到 640x400 展示：用 1024x640 的视口按 1.25 倍渲染，字更大，输出正好 1280x800
VIEWPORT = {"width": 1024, "height": 640}
SCALE = 1.25

MARKS = {
    "502853834": ("like", ""),
    TOPIC_ID: ("contacted", "周六下午三点看房，问清取暖费怎么交"),
    "502852221": ("visited", "采光好，离地铁近；次卧偏小"),
    "502846323": ("like", ""),
    "502853012": ("rejected", ""),
}
SEEN = ["502854262", "502853043", "502851966", "502851080"]
FILTERS = {"exclude": "隔断 地下室", "minPrice": 1500, "maxPrice": 6000, "maxCommute": 60}

# 帖子页夹具是一篇非租房帖，截图时换成列表夹具里同一条租房帖的标题，避免商店图出现无关内容和第三方文章
RENTAL_TOPIC = """
(() => {
  if (!location.pathname.startsWith("/group/topic/")) return;
  document.addEventListener("DOMContentLoaded", () => {
    const title = "三元桥 三源里北小街主卧和次卧出租 佳程广场对面 亮马桥周边";
    document.title = title;
    const h1 = document.querySelector("#content h1");
    h1.firstChild.textContent = title;
    document.querySelector("#link-report").innerHTML =
      '<div class="rich-content topic-richtext"><p>三源里北小街，主卧和次卧出租，佳程广场对面，亮马桥周边。</p>' +
      '<p>有意可豆邮联系约看房。</p></div>';
    document.querySelector(".topic-doc .from").innerHTML = '<a href="https://www.douban.com/people/0/">豆友</a>';
    document.querySelector(".create-time").textContent = "2026-10-18 10:32:15";
    document.querySelector("#g-side-info .group-item .title a").textContent = "北京租房";
    document.querySelector("#g-side-info .group-item .pic")?.remove();
    document.querySelector("#g-side-info .ft-members i").textContent = "100万+";
    document.querySelector(".user-face")?.remove();
    for (const h2 of document.querySelectorAll(".aside .mod h2")) h2.closest(".mod").remove();
  });
})();
"""


def prepare_extension(tmp: Path) -> Path:
    # 和 e2e 一样：无法点权限弹窗，把高德的可选权限改成安装即授予
    dst = tmp / "extension"
    shutil.copytree(EXT_DIR, dst)
    manifest = json.loads((dst / "manifest.json").read_text(encoding="utf-8"))
    manifest["host_permissions"] = manifest.pop("optional_host_permissions")
    (dst / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return dst


def fulfill(fixture: str):
    body = (FIXTURES / fixture).read_bytes()
    return lambda route: route.fulfill(status=200, content_type="text/html; charset=utf-8", body=body)


def shot(page, name):
    SHOTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SHOTS / f"{name}.png"))
    print("screenshot", name)


def scroll_to(page, selector, offset=0):
    page.evaluate("([s, o]) => window.scrollTo(0, document.querySelector(s).getBoundingClientRect().top + scrollY - o)",
                  [selector, offset])
    page.wait_for_timeout(200)


def setup_commute(ctx, sw, ext_id):
    """返回 True 表示通勤已就绪；缓存优先，没有缓存才用 Key 真实调用高德。"""
    if CACHE.exists():
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
        ctx.route("https://restapi.amap.com/**", lambda r: r.abort())
        settings = {"gaodeKey": "cached-only", "city": "北京", "target": cache["target"]}
        sw.evaluate("data => chrome.storage.local.set(data)", {**cache["entries"], "settings": settings})
        print(f"commute: {len(cache['entries'])} cached entries, Gaode blocked")
        return True
    if not GAODE_KEY:
        print("commute: skipped (no cache and no GAODE key in env)")
        return False
    opts = ctx.new_page()
    opts.goto(f"chrome-extension://{ext_id}/options/options.html")
    opts.locator("#gaodeKey").fill(GAODE_KEY)
    opts.locator("#city").fill("北京")
    opts.locator("#targetQuery").fill("国贸")
    opts.locator("#saveSettings").click()
    expect(opts.locator("#settingsStatus")).to_contain_text("已保存", timeout=20000)
    opts.close()
    return True


def wait_commutes(page, timeout_s=120):
    for _ in range(timeout_s * 2):
        pending = page.evaluate("""() => {
          const rows = [...document.querySelectorAll('tr.drh-row:not(.drh-hidden)')];
          return rows.filter(r => !r.querySelector('.drh-commute').textContent ||
                                  r.querySelector('.drh-commute').textContent.includes('计算中')).length;
        }""")
        if not pending:
            return
        page.wait_for_timeout(500)
    raise TimeoutError("commute not finished")


def dump_cache(sw):
    data = sw.evaluate("() => chrome.storage.local.get(null)")
    entries = {k: v for k, v in data.items() if k.startswith(("gpoi:", "gtr:"))}
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps({"target": data["settings"]["target"], "entries": entries}, ensure_ascii=False, indent=1),
                     encoding="utf-8")
    print(f"commute: cached {len(entries)} entries to {CACHE.relative_to(ROOT)}")


def render_screenshots(p, tmp: Path):
    ext = prepare_extension(tmp)
    ctx = p.chromium.launch_persistent_context(
        str(tmp / "profile"),
        channel="chromium",
        headless=True,
        viewport=VIEWPORT,
        device_scale_factor=SCALE,
        locale="zh-CN",
        args=[f"--disable-extensions-except={ext}", f"--load-extension={ext}"],
    )
    sw = ctx.service_workers[0] if ctx.service_workers else ctx.wait_for_event("serviceworker")
    ext_id = sw.url.split("/")[2]

    # 豆瓣自身的页面脚本会请求线上接口，被风控时会把页面跳去 sec.douban.com；只保留样式
    ctx.route("**/*", lambda r: r.abort()
              if r.request.resource_type == "script" and r.request.url.startswith("http") else r.fallback())
    ctx.route("https://www.douban.com/group/beijingzufang/discussion*", fulfill("discussion-page1.html"))
    ctx.route("https://www.douban.com/group/topic/**", fulfill("topic.html"))
    ctx.add_init_script(RENTAL_TOPIC)

    cached = CACHE.exists()
    commute = setup_commute(ctx, sw, ext_id)

    page = ctx.new_page()
    page.goto(LIST_URL)
    expect(page.locator(".drh-panel-host")).to_have_count(1)
    group = page.title().strip()
    rows = page.locator("tr.drh-row a[href*='/group/topic/']").evaluate_all(
        "els => els.map(a => [a.href.split('/topic/')[1].split('/')[0], (a.title || a.textContent).trim()])")
    titles = dict(rows)

    if commute and not cached:
        # 先关掉筛选让每条都算一次通勤，结果写进缓存，之后重渲染不再调用高德
        sw.evaluate("f => chrome.storage.local.set({ filters: f })", {"enabled": False})
        page.reload()
        wait_commutes(page)
        dump_cache(sw)

    now = page.evaluate("Date.now()")
    data = {"filters": {**FILTERS, "enabled": True, "maxCommute": FILTERS["maxCommute"] if commute else None}}
    for i, (tid, (status, note)) in enumerate(MARKS.items()):
        data[f"mark:{tid}"] = {"status": status, "note": note, "title": titles[tid], "group": group,
                               "url": f"https://www.douban.com/group/topic/{tid}/", "updatedAt": now - i * 3600_000}
    for tid in SEEN:
        data[f"seen:{tid}"] = now
    sw.evaluate("data => chrome.storage.local.set(data)", data)

    page.reload()
    expect(page.locator(".drh-panel-host")).to_have_count(1)
    if commute:
        wait_commutes(page)
    page.mouse.move(0, 0)
    scroll_to(page, ".drh-panel-host", 100)
    shot(page, "01-filter-panel")

    # 悬停一条帖子露出标记按钮
    scroll_to(page, f"tr.drh-row:has(a[href*='{TOPIC_ID}'])", 210)
    # 悬停在时间格而不是标题链接上：豆瓣的链接悬停样式是整块蓝底
    page.locator("tr.drh-row:not(.drh-hidden)").filter(has=page.locator("a[href*='502849979']")).locator("td.time").hover()
    page.wait_for_timeout(200)
    shot(page, "02-list-marks")

    topic = ctx.new_page()
    topic.goto(TOPIC_URL)
    card = topic.locator(".drh-topic-host")
    expect(card).to_have_count(1)
    expect(card.locator("textarea")).to_have_value(MARKS[TOPIC_ID][1])
    topic.mouse.move(0, 0)
    shot(topic, "03-topic-note")

    opts = ctx.new_page()
    opts.goto(f"chrome-extension://{ext_id}/options/options.html")
    expect(opts.locator(".mark")).to_have_count(len(MARKS))
    opts.wait_for_timeout(300)
    shot(opts, "04-options-commute")
    scroll_to(opts, "#marks", 150)
    shot(opts, "05-options-marks")

    ctx.close()


def render_promos(p):
    browser = p.chromium.launch(channel="chromium", headless=True)
    for name, w, h in [("promo-small-440x280", 440, 280), ("promo-marquee-1400x560", 1400, 560)]:
        page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
        page.goto((OUT / "promo.html").as_uri() + f"?size={w}x{h}")
        page.evaluate("document.fonts.ready")
        page.screenshot(path=str(OUT / f"{name}.png"))
        print("promo", name)
    browser.close()
    shutil.copyfile(EXT_DIR / "icons" / "icon128.png", OUT / "store-icon-128.png")


def main():
    only = sys.argv[1:] or ["screenshots", "promos"]
    tmp = Path(tempfile.mkdtemp(prefix="drh-store-"))
    try:
        with sync_playwright() as p:
            if "screenshots" in only:
                render_screenshots(p, tmp)
            if "promos" in only:
                render_promos(p)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
