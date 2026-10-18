const DRH = globalThis.DRH;
const $ = (id) => document.getElementById(id);
const AMAP_ORIGIN = "https://restapi.amap.com/*";

const h = (tag, props = {}, children = []) => {
  const node = document.createElement(tag);
  Object.assign(node, props);
  node.append(...children);
  return node;
};

function setStatus(el, text, isError = false) {
  el.textContent = text;
  el.className = isError ? "status error" : "status";
}

// ---------- 通勤设置 ----------

async function loadSettings() {
  const s = await DRH.store.getSettings();
  $("gaodeKey").value = s.gaodeKey;
  $("city").value = s.city;
  $("targetQuery").value = s.target?.query || "";
  if (s.target) setStatus($("settingsStatus"), `当前：${[s.target.adname, s.target.name].filter(Boolean).join(" ")}`);
}

$("toggleKey").addEventListener("click", () => {
  const input = $("gaodeKey");
  input.type = input.type === "password" ? "text" : "password";
  $("toggleKey").textContent = input.type === "password" ? "显示" : "隐藏";
});

$("settings").addEventListener("submit", async (e) => {
  e.preventDefault();
  const status = $("settingsStatus");
  const key = $("gaodeKey").value.trim();
  const city = $("city").value.trim();
  const query = $("targetQuery").value.trim();
  // 访问高德接口的权限按需申请，不用通勤功能的人不必授权
  const granted = await chrome.permissions.request({ origins: [AMAP_ORIGIN] });
  if (!granted) {
    setStatus(status, "需要允许访问高德接口才能计算通勤", true);
    return;
  }
  $("saveSettings").disabled = true;
  setStatus(status, "正在定位工作地点…");
  try {
    const res = await chrome.runtime.sendMessage({ type: "resolvePlace", query, city, key });
    if (!res?.ok) throw new Error(res?.error || "定位失败");
    await DRH.store.setSettings({ gaodeKey: key, city, target: { query, ...res.data } });
    setStatus(status, `已保存，工作地点定位到：${[res.data.adname, res.data.name].filter(Boolean).join(" ")}`);
  } catch (err) {
    setStatus(status, err.message, true);
  } finally {
    $("saveSettings").disabled = false;
  }
});

$("clearSettings").addEventListener("click", async () => {
  await DRH.store.setSettings({ ...DRH.DEFAULT_SETTINGS });
  await chrome.permissions.remove({ origins: [AMAP_ORIGIN] });
  await loadSettings();
  setStatus($("settingsStatus"), "已清除");
});

// ---------- 我的标记 ----------

const TABS = [{ id: "all", label: "全部" }, ...DRH.STATUSES, { id: "note", label: "仅备注" }];
let activeTab = "all";
let marks = [];

function renderTabs() {
  const counts = { all: marks.length, note: marks.filter((m) => !m.status).length };
  for (const s of DRH.STATUSES) counts[s.id] = marks.filter((m) => m.status === s.id).length;
  $("tabs").replaceChildren(...TABS.map((t) => {
    const b = h("button", { type: "button", textContent: `${t.label} ${counts[t.id]}` });
    b.setAttribute("role", "tab");
    b.setAttribute("aria-selected", String(t.id === activeTab));
    b.addEventListener("click", () => {
      activeTab = t.id;
      render();
    });
    return b;
  }));
}

function renderMark({ id, ...m }) {
  const select = h("select", {}, [
    h("option", { value: "", textContent: "无状态" }),
    ...DRH.STATUSES.map((s) => h("option", { value: s.id, textContent: s.label })),
  ]);
  select.value = m.status || "";
  select.addEventListener("change", () => DRH.store.setMark(id, { ...m, status: select.value || null }));

  const note = h("textarea", { value: m.note || "", placeholder: "备注" });
  let timer;
  note.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(() => DRH.store.setMark(id, { ...m, note: note.value.trim() }), 600);
  });

  const remove = h("button", { type: "button", className: "remove", textContent: "删除标记" });
  remove.addEventListener("click", () => DRH.store.setMark(id, null));

  const meta = [h("span", { textContent: m.group || "" })];
  if (m.prices?.length) meta.unshift(h("b", { textContent: DRH.formatPrices(m.prices) }));
  meta.push(h("span", { textContent: `更新于 ${new Date(m.updatedAt).toLocaleString("zh-CN", { hour12: false })}` }), remove);

  return h("li", { className: `mark ${m.status || ""}` }, [
    h("div", { className: "top" }, [
      h("a", { className: "title", href: m.url, target: "_blank", rel: "noopener noreferrer", textContent: m.title || m.url }),
      select,
    ]),
    h("div", { className: "meta" }, meta),
    note,
  ]);
}

function render() {
  renderTabs();
  const q = $("search").value.trim();
  const shown = marks.filter((m) =>
    (activeTab === "all" || (activeTab === "note" ? !m.status : m.status === activeTab)) &&
    (!q || (m.title || "").includes(q) || (m.note || "").includes(q)));
  // 正在输入备注时不重画，避免打断输入
  if (document.activeElement?.tagName === "TEXTAREA") return;
  $("marks").replaceChildren(...shown.map(renderMark));
  setStatus($("marksStatus"), marks.length ? "" : "还没有标记。到豆瓣租房小组的讨论列表里，鼠标移到帖子上就能标记。");
}

async function loadMarks() {
  marks = await DRH.store.allMarks();
  render();
}

$("search").addEventListener("input", render);

$("export").addEventListener("click", () => {
  const blob = new Blob([JSON.stringify({ version: 1, exportedAt: new Date().toISOString(), marks }, null, 2)], { type: "application/json" });
  const a = h("a", { href: URL.createObjectURL(blob), download: `豆瓣租房标记-${new Date().toISOString().slice(0, 10)}.json` });
  a.click();
  URL.revokeObjectURL(a.href);
});

$("import").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  e.target.value = "";
  if (!file) return;
  try {
    const data = JSON.parse(await file.text());
    const items = (Array.isArray(data) ? data : data.marks || []).filter((m) =>
      /^\d+$/.test(String(m.id)) && (m.status == null || DRH.STATUSES.some((s) => s.id === m.status)));
    for (const { id, ...m } of items) {
      await DRH.store.setMark(String(id), {
        status: m.status || null,
        note: typeof m.note === "string" ? m.note : "",
        title: String(m.title || ""),
        url: `https://www.douban.com/group/topic/${id}/`,
        group: String(m.group || ""),
        prices: Array.isArray(m.prices) ? m.prices.filter(Number.isFinite) : [],
      });
    }
    setStatus($("marksStatus"), `已导入 ${items.length} 条标记`);
  } catch {
    setStatus($("marksStatus"), "导入失败：文件不是有效的导出 JSON", true);
  }
});

$("clearSeen").addEventListener("click", async () => {
  await DRH.store.clearSeen();
  setStatus($("marksStatus"), "已清空已读记录");
});

DRH.store.onChanged((changed) => {
  if (changed.marks.length) loadMarks();
});

loadSettings();
loadMarks();
