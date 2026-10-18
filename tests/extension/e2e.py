"""
用真实豆瓣页面夹具加载插件跑一遍主流程。

    python3 tests/extension/e2e.py [截图目录]

设置了 GAODE_WEB_SERVICE_API_KEY（或 GAODE_KEY）时会额外跑通勤流程，会真实调用高德接口。
品牌版 Chrome 137+ 已不支持 --load-extension，这里用 Playwright 自带的 Chromium。
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

EXT_DIR = Path(__file__).resolve().parents[2] / "extension"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
SHOTS = Path(sys.argv[1]) if len(sys.argv) > 1 else None
GAODE_KEY = os.environ.get("GAODE_KEY") or os.environ.get("GAODE_WEB_SERVICE_API_KEY")

LIST_URL = "https://www.douban.com/group/beijingzufang/discussion?start=0&type=new"
TOPIC_URL = "https://www.douban.com/group/topic/100110258/"


def prepare_extension(tmp: Path) -> Path:
    # 测试里无法点权限弹窗，把高德的可选权限改成安装即授予
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
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(SHOTS / f"{name}.png"), full_page=False)


def visible_count(page):
    return page.locator("tr.drh-row:not(.drh-hidden)").count()


def main():
    tmp = Path(tempfile.mkdtemp(prefix="drh-e2e-"))
    try:
        ext = prepare_extension(tmp)
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                str(tmp / "profile"),
                channel="chromium",
                headless=True,
                viewport={"width": 1280, "height": 900},
                args=[f"--disable-extensions-except={ext}", f"--load-extension={ext}"],
            )
            sw = ctx.service_workers[0] if ctx.service_workers else ctx.wait_for_event("serviceworker")
            ext_id = sw.url.split("/")[2]

            # 豆瓣自身的页面脚本会请求线上接口，被风控时会把页面跳去 sec.douban.com；测试里只保留样式
            ctx.route("**/*", lambda r: r.abort()
                      if r.request.resource_type == "script" and r.request.url.startswith("http") else r.fallback())
            ctx.route("https://www.douban.com/group/beijingzufang/discussion*", fulfill("discussion-page1.html"))
            ctx.route("https://www.douban.com/group/35417/discussion*", fulfill("discussion-limit100.html"))
            ctx.route("https://www.douban.com/group/topic/**", fulfill("topic.html"))

            # ---- 列表页：面板、行装饰、筛选 ----
            page = ctx.new_page()
            page.goto(LIST_URL)
            panel = page.locator(".drh-panel-host")
            expect(panel).to_have_count(1)
            total = page.locator("tr.drh-row").count()
            assert total >= 20, f"decorated rows: {total}"
            expect(page.locator(".drh-panel-host .stats")).to_contain_text(f"/ {total} 条")
            base_visible = visible_count(page)
            print(f"list: {total} rows, {base_visible} visible with default filters")

            prices = page.locator(".drh-price:not(:empty)").count()
            print(f"list: {prices} rows show a parsed price")

            panel.locator('input[placeholder="任一关键词，空格分隔"]').fill("地铁")
            page.wait_for_timeout(500)
            with_kw = visible_count(page)
            titles = page.locator("tr.drh-row:not(.drh-hidden) a[href*='/group/topic/']").evaluate_all(
                "els => els.map(a => a.title || a.textContent)")
            assert all("地铁" in t for t in titles), titles
            print(f"filter include=地铁: {with_kw} visible")
            panel.locator('input[placeholder="任一关键词，空格分隔"]').fill("")
            page.wait_for_timeout(500)
            assert visible_count(page) == base_visible

            # ---- 标记：收藏、排除 ----
            rows = page.locator("tr.drh-row:not(.drh-hidden)")
            first, second = rows.nth(0), rows.nth(1)
            first_id = first.locator("a[href*='/group/topic/']").first.get_attribute("href").split("/topic/")[1].split("/")[0]
            first.hover()
            first.locator('button[data-status="like"]').click()
            expect(page.locator("tr.drh-status-like")).to_have_count(1)
            second.hover()
            second.locator('button[data-status="rejected"]').click()
            page.wait_for_timeout(300)
            assert visible_count(page) == base_visible - 1, "rejected row should be hidden"
            stored = sw.evaluate("id => chrome.storage.local.get('mark:' + id)", first_id)
            assert stored[f"mark:{first_id}"]["status"] == "like", stored
            print("marks: like + rejected ok, rejected row hidden")
            shot(page, "01-list")

            # ---- 加载下一页并合并 ----
            panel.locator("button", has_text="加载下一页").click()
            expect(page.locator(".drh-panel-host .msg")).to_contain_text("已合并", timeout=15000)
            merged = page.locator("tr.drh-row").count()
            assert merged > total, f"{merged} <= {total}"
            print(f"load more: {total} -> {merged} rows")

            # ---- 帖子页：悬浮标记栏 ----
            topic = ctx.new_page()
            topic.goto(TOPIC_URL)
            card = topic.locator(".drh-topic-host")
            expect(card).to_have_count(1)
            card.locator('button[data-status="contacted"]').click()
            card.locator("textarea").fill("周六下午看房")
            topic.wait_for_timeout(1200)
            stored = sw.evaluate("() => chrome.storage.local.get(['mark:100110258', 'seen:100110258'])")
            mark = stored["mark:100110258"]
            assert mark["status"] == "contacted" and mark["note"] == "周六下午看房", mark
            assert mark["title"].startswith("作为译者的李康"), mark["title"]
            assert mark["group"] == "李康", mark["group"]
            assert "seen:100110258" in stored
            print(f"topic: title={mark['title'][:20]}… group={mark['group']} status+note saved, seen recorded")
            shot(topic, "02-topic")

            # ---- 设置页：标记列表 ----
            opts = ctx.new_page()
            opts.goto(f"chrome-extension://{ext_id}/options/options.html")
            expect(opts.locator(".mark")).to_have_count(3)
            expect(opts.locator("#tabs button").first).to_have_text("全部 3")
            print("options: 3 marks listed")
            shot(opts, "03-options")

            # ---- 通勤（真实调用高德）----
            if GAODE_KEY:
                opts.locator("#gaodeKey").fill(GAODE_KEY)
                opts.locator("#city").fill("北京")
                opts.locator("#targetQuery").fill("国贸")
                opts.locator("#saveSettings").click()
                expect(opts.locator("#settingsStatus")).to_contain_text("已保存", timeout=20000)
                print("options:", opts.locator("#settingsStatus").text_content())

                page.bring_to_front()
                try:
                    expect(page.locator(".drh-commute", has_text="公交").first).to_be_visible(timeout=30000)
                except AssertionError:
                    from collections import Counter
                    print("commute badges:", Counter(page.locator(".drh-commute").evaluate_all("els => els.map(e => e.textContent)")))
                    raise
                panel.locator("select").select_option("45")
                page.wait_for_timeout(15000)
                done = page.locator(".drh-commute", has_text="公交").count()
                over = page.locator(".drh-commute", has_text="公交").evaluate_all(
                    "els => els.filter(e => !e.closest('tr').classList.contains('drh-hidden'))"
                    ".map(e => parseInt(e.textContent.match(/\\d+/)[0])).filter(m => m > 45).length")
                assert over == 0, f"{over} visible rows exceed 45 min"
                print(f"commute: {done} rows computed so far, none visible above 45 min")
                page.evaluate("window.scrollTo(0, 0)")
                shot(page, "04-commute")
            else:
                print("commute: skipped (no GAODE key in env)")

            ctx.close()
        print("ALL PASSED")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
