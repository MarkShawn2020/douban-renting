// 帖子详情页：右下角悬浮的标记栏，打开即记为已读
(() => {
  const DRH = globalThis.DRH;

  const STYLE = `
    :host { all: initial; position: fixed; right: 20px; bottom: 20px; z-index: 2147483000; }
    .card {
      --background: #F9F9F7; --card: #FFFFFF; --foreground: #181818; --muted-foreground: #737373;
      --primary: #CC785C; --border: #E8E6DC; --danger: #B4483A; --rejected: #87867F;
      font: 13px/1.55 -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      color: var(--foreground); background: var(--background); border: 1px solid var(--border);
      border-radius: 14px; padding: 12px 14px; width: 280px; box-shadow: 0 6px 24px rgba(24, 24, 24, .12);
    }
    .head { display: flex; align-items: center; gap: 8px; }
    .head h2 { font: 600 14px Georgia, "Songti SC", serif; margin: 0; flex: 1; }
    .price { font-weight: 600; }
    button {
      font: inherit; cursor: pointer; border-radius: 8px; padding: 3px 9px;
      border: 1px solid var(--border); background: var(--card); color: var(--foreground);
    }
    button:hover { border-color: var(--primary); color: var(--primary); }
    .statuses { display: flex; gap: 6px; margin-top: 10px; flex-wrap: wrap; }
    .statuses button.active { background: var(--primary); border-color: var(--primary); color: #fff; }
    .statuses button.active[data-status=rejected] { background: var(--rejected); border-color: var(--rejected); }
    textarea {
      box-sizing: border-box; width: 100%; margin-top: 10px; min-height: 64px; resize: vertical;
      font: inherit; color: var(--foreground); background: var(--card);
      border: 1px solid var(--border); border-radius: 8px; padding: 6px 8px;
    }
    textarea:focus { outline: 2px solid var(--primary); outline-offset: -1px; }
    .foot { margin-top: 6px; color: var(--muted-foreground); display: flex; justify-content: space-between; gap: 8px; }
    .foot .error { color: var(--danger); }
    .body[hidden] { display: none; }
    .toggle { padding: 1px 8px; }
  `;

  function topicTitle() {
    const cc = document.querySelector(".tablecc");
    if (cc) return cc.textContent.replace(/^\s*标题：/, "").trim();
    const h1 = document.querySelector("#content h1");
    if (h1) {
      // h1 里还嵌着活动标签等子元素，只取直接文本
      const text = [...h1.childNodes].filter((n) => n.nodeType === Node.TEXT_NODE).map((n) => n.textContent).join("").trim();
      if (text) return text;
    }
    return document.title.trim();
  }

  const h = (tag, props = {}, children = []) => {
    const node = document.createElement(tag);
    Object.assign(node, props);
    node.append(...children);
    return node;
  };

  DRH.enhanceTopic = async (id) => {
    const url = `https://www.douban.com/group/topic/${id}/`;
    const title = topicTitle();
    const group = document.querySelector("#g-side-info .group-item .title a")?.textContent.trim() || "";
    const prices = DRH.parsePrices(title);
    DRH.store.markSeen(id);

    let mark = (await DRH.store.getMarks([id]))[id] || null;
    const { topicCardCollapsed } = await chrome.storage.local.get("topicCardCollapsed");

    const host = h("div", { className: "drh-topic-host" });
    const root = host.attachShadow({ mode: "open" });
    const statuses = h("div", { className: "statuses" }, DRH.STATUSES.map((s) => {
      const b = h("button", { type: "button", textContent: s.label });
      b.dataset.status = s.id;
      return b;
    }));
    const note = h("textarea", { placeholder: "备注：房东联系方式、看房时间、优缺点……" });
    const saved = h("span");
    const commute = h("span");
    const body = h("div", { className: "body" }, [statuses, note, h("div", { className: "foot" }, [commute, saved])]);
    const toggle = h("button", { type: "button", className: "toggle" });

    const sync = () => {
      for (const b of statuses.children) b.classList.toggle("active", b.dataset.status === mark?.status);
      if (document.activeElement !== host) note.value = mark?.note || "";
    };
    const setCollapsed = (collapsed) => {
      body.hidden = collapsed;
      toggle.textContent = collapsed ? "展开" : "收起";
    };

    async function save(patch) {
      const next = { ...mark, ...patch, title, url, group, prices };
      mark = next.status || next.note ? next : null;
      await DRH.store.setMark(id, mark);
      saved.textContent = "已保存";
      setTimeout(() => { saved.textContent = ""; }, 1500);
    }

    statuses.addEventListener("click", (e) => {
      const b = e.target.closest("button[data-status]");
      if (!b) return;
      save({ status: mark?.status === b.dataset.status ? null : b.dataset.status });
      sync();
    });
    let timer;
    note.addEventListener("input", () => {
      clearTimeout(timer);
      timer = setTimeout(() => save({ note: note.value.trim() }), 600);
    });
    toggle.addEventListener("click", () => {
      const collapsed = !body.hidden;
      setCollapsed(collapsed);
      chrome.storage.local.set({ topicCardCollapsed: collapsed });
    });

    root.append(
      h("style", { textContent: STYLE }),
      h("div", { className: "card" }, [
        h("div", { className: "head" }, [
          h("h2", { textContent: "租房标记" }),
          h("span", { className: "price", textContent: DRH.formatPrices(prices) }),
          toggle,
        ]),
        body,
      ]),
    );
    document.body.append(host);
    setCollapsed(!!topicCardCollapsed);
    sync();

    const settings = await DRH.store.getSettings();
    if (settings.gaodeKey && settings.target) {
      commute.textContent = "通勤计算中…";
      const res = await chrome.runtime.sendMessage({ type: "commute", title });
      if (!res?.ok) {
        commute.textContent = res?.error || "通勤计算失败";
        commute.className = "error";
      } else if (res.data.minutes == null) {
        commute.textContent = res.data.place ? `无法估算通勤（定位：${res.data.place}）` : "无法从标题定位";
      } else {
        commute.textContent = `到${settings.target.name}公交 ${res.data.minutes} 分钟`;
        commute.title = `定位：${res.data.place} · 直线 ${res.data.distanceKm} km`;
      }
    }

    DRH.store.onChanged(async (changed) => {
      if (!changed.marks.includes(id)) return;
      mark = (await DRH.store.getMarks([id]))[id] || null;
      sync();
    });
  };
})();
