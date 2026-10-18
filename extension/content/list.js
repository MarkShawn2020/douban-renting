(() => {
  const DRH = globalThis.DRH;
  const TOPIC_LINK = 'a[href*="/group/topic/"]';
  const PAGE_DELAY_MS = 1500;
  // 后台按到达顺序排队：一次全发出去，要等所有帖子都定位完才轮到第一条算公交
  const MAX_COMMUTE_IN_FLIGHT = 3;

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  function nextUrlOf(doc, baseUrl) {
    const a = doc.querySelector('.paginator .next a, link[rel="next"]');
    return a ? new URL(a.getAttribute("href"), baseUrl).href : null;
  }

  DRH.enhanceList = async (table) => {
    const pageGroup = document.title.trim();
    const state = {
      rows: [],
      ids: new Set(),
      marks: {},
      seen: {},
      commutes: {},
      commuteError: null,
      commuteGen: 0, // 换了工作地点后，丢弃还在路上的旧结果
      commuteInFlight: 0,
      filters: await DRH.store.getFilters(),
      settings: await DRH.store.getSettings(),
      nextUrl: nextUrlOf(document, location.href),
    };
    const tbody = table.tBodies[0] || table;

    function parseRow(tr) {
      const link = tr.querySelector(TOPIC_LINK);
      const url = link.href.split("?")[0];
      const groupLink = [...tr.querySelectorAll('a[href*="/group/"]')]
        .find((a) => !a.href.includes("/topic/") && !a.href.includes("/people/"));
      const title = (link.getAttribute("title") || link.textContent).trim();
      return {
        tr,
        link,
        id: DRH.topicIdFromUrl(url),
        url,
        title,
        prices: DRH.parsePrices(title),
        group: groupLink?.textContent.trim() || pageGroup,
      };
    }

    function decorate(row) {
      row.tr.classList.add("drh-row");
      const price = document.createElement("span");
      price.className = "drh-price";
      price.textContent = DRH.formatPrices(row.prices);
      const commute = document.createElement("span");
      commute.className = "drh-commute";
      const tools = document.createElement("span");
      tools.className = "drh-tools";
      for (const s of DRH.STATUSES) {
        const b = document.createElement("button");
        b.type = "button";
        b.dataset.status = s.id;
        b.textContent = s.label;
        tools.append(b);
      }
      tools.addEventListener("click", (e) => {
        const b = e.target.closest("button[data-status]");
        if (b) toggleStatus(row, b.dataset.status);
      });
      const line = document.createElement("div");
      line.className = "drh-line";
      line.append(price, commute, tools);
      row.link.closest("td").append(line);
      row.els = { commute, tools };
    }

    function addRows(trs) {
      const added = [];
      for (const tr of trs) {
        if (!tr.querySelector(TOPIC_LINK)) continue;
        const row = parseRow(tr);
        // 翻页期间有新帖顶上来时，后一页会出现重复的帖子
        if (!row.id || state.ids.has(row.id)) continue;
        if (!tr.isConnected) tbody.append(tr);
        state.ids.add(row.id);
        decorate(row);
        state.rows.push(row);
        added.push(row);
      }
      return added;
    }

    async function loadMarks(rows) {
      const ids = rows.map((r) => r.id);
      Object.assign(state.marks, await DRH.store.getMarks(ids));
      Object.assign(state.seen, await DRH.store.getSeen(ids));
    }

    async function toggleStatus(row, status) {
      const prev = state.marks[row.id];
      const next = prev?.status === status ? null : status;
      if (!next && !prev?.note) {
        await DRH.store.setMark(row.id, null);
      } else {
        await DRH.store.setMark(row.id, {
          ...prev, status: next, title: row.title, url: row.url, group: row.group, prices: row.prices,
        });
      }
    }

    const commuteActive = () => !!(state.settings.gaodeKey && state.settings.target);

    function duplicateIds() {
      const seenTitles = new Set();
      const dup = new Set();
      for (const row of state.rows) {
        const key = row.title.replace(/\s+/g, "");
        if (seenTitles.has(key)) dup.add(row.id);
        else seenTitles.add(key);
      }
      return dup;
    }

    function renderCommute(row) {
      const el = row.els.commute;
      const c = state.commutes[row.id];
      el.className = "drh-commute";
      el.title = "";
      if (!commuteActive()) {
        el.textContent = "";
      } else if (!c) {
        el.textContent = row.commutePending ? "通勤计算中…" : "";
      } else if (c.minutes == null) {
        el.textContent = c.place ? "无法估算通勤" : "无法定位";
        el.classList.add("drh-commute-unknown");
        if (c.place) el.title = `定位：${c.place}`;
      } else {
        el.textContent = `公交 ${c.minutes} 分钟`;
        el.title = `定位：${c.place} · 直线 ${c.distanceKm} km`;
        if (state.filters.maxCommute != null && c.minutes <= state.filters.maxCommute) el.classList.add("drh-commute-ok");
      }
    }

    // 合并同一轮里的多次重画；不用 rAF，后台标签页里 rAF 会暂停，通勤计算也会跟着停
    let renderQueued = false;
    function render() {
      if (renderQueued) return;
      renderQueued = true;
      queueMicrotask(() => {
        renderQueued = false;
        const ctx = {
          marks: state.marks,
          seen: state.seen,
          commutes: state.commutes,
          commuteActive: commuteActive(),
          duplicateIds: duplicateIds(),
        };
        let visible = 0;
        for (const row of state.rows) {
          row.reason = DRH.hiddenReason(row, state.filters, ctx);
          const status = state.marks[row.id]?.status;
          row.tr.classList.toggle("drh-hidden", !!row.reason);
          for (const s of DRH.STATUSES) row.tr.classList.toggle(`drh-status-${s.id}`, status === s.id);
          row.tr.classList.toggle("drh-seen", !!state.seen[row.id]);
          for (const b of row.els.tools.children) b.classList.toggle("drh-active", b.dataset.status === status);
          renderCommute(row);
          if (!row.reason) visible++;
        }
        panel.setStats(`显示 ${visible} / ${state.rows.length} 条`);
        scheduleCommutes();
      });
    }

    // 只给通过了其他条件的帖子算通勤，避免浪费高德额度
    function scheduleCommutes() {
      if (!commuteActive() || state.commuteError) return;
      for (const row of state.rows) {
        if (row.reason && !row.reason.startsWith("通勤")) continue;
        if (row.id in state.commutes || row.commutePending) continue;
        if (state.commuteInFlight >= MAX_COMMUTE_IN_FLIGHT) break;
        state.commuteInFlight++;
        row.commutePending = true;
        renderCommute(row);
        const gen = state.commuteGen;
        chrome.runtime.sendMessage({ type: "commute", title: row.title }).then((res) => {
          state.commuteInFlight--;
          row.commutePending = false;
          if (gen !== state.commuteGen) return render();
          if (res?.ok) {
            state.commutes[row.id] = res.data;
          } else if (!state.commuteError) {
            state.commuteError = res?.error || "通勤计算失败";
            panel.setCommute(state.settings, state.commuteError);
          }
          render();
        });
      }
    }

    async function loadMore(pages) {
      panel.setLoading(true);
      try {
        for (let i = 0; i < pages; i++) {
          if (!state.nextUrl) {
            panel.setMessage("已经是最后一页");
            break;
          }
          panel.setMessage(`正在加载第 ${i + 1} / ${pages} 页…`);
          let doc;
          try {
            const res = await fetch(state.nextUrl, { credentials: "include" });
            if (!res.ok) throw new Error(String(res.status));
            doc = new DOMParser().parseFromString(await res.text(), "text/html");
          } catch {
            // 被风控时会跳去 sec.douban.com，跨域跳转在这里表现为请求失败
            panel.setMessage("豆瓣要求人机验证或请求失败：请手动翻一页完成验证后再试", true);
            return;
          }
          const trs = [...(doc.querySelector("table.olt")?.rows || [])];
          if (!trs.some((tr) => tr.querySelector(TOPIC_LINK))) {
            panel.setMessage("没有取到帖子，可能是豆瓣限流或需要登录", true);
            return;
          }
          const added = addRows(trs.map((tr) => document.importNode(tr, true)));
          await loadMarks(added);
          state.nextUrl = nextUrlOf(doc, state.nextUrl);
          render();
          if (i < pages - 1) await sleep(PAGE_DELAY_MS);
        }
        panel.setMessage(`已合并 ${state.rows.length} 条帖子`);
      } finally {
        panel.setLoading(false);
        panel.setHasMore(!!state.nextUrl);
      }
    }

    const panel = DRH.createPanel({
      filters: state.filters,
      onChange(filters) {
        state.filters = filters;
        DRH.store.setFilters(filters);
        render();
      },
      onLoadMore: loadMore,
      onOpenOptions: () => chrome.runtime.sendMessage({ type: "openOptions" }),
    });
    table.before(panel.host);
    panel.setCommute(state.settings, null);
    panel.setHasMore(!!state.nextUrl);

    await loadMarks(addRows([...table.rows]));
    render();

    DRH.store.onChanged(async (changed) => {
      if (changed.settings) {
        state.settings = await DRH.store.getSettings();
        state.commutes = {};
        state.commuteError = null;
        state.commuteGen++;
        panel.setCommute(state.settings, null);
      }
      const ids = [...changed.marks, ...changed.seen].filter((id) => state.ids.has(id));
      if (ids.length) {
        for (const id of ids) {
          delete state.marks[id];
          delete state.seen[id];
        }
        Object.assign(state.marks, await DRH.store.getMarks(ids));
        Object.assign(state.seen, await DRH.store.getSeen(ids));
      }
      if (changed.settings || ids.length) render();
    });
  };
})();
