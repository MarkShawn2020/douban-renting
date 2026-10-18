// 每条标记、已读记录各占一个 key，多标签页同时写入也不会互相覆盖
(() => {
  const DRH = (globalThis.DRH ||= {});
  const local = chrome.storage.local;

  const pick = async (prefix, ids) => {
    const res = await local.get(ids.map((id) => prefix + id));
    const out = {};
    for (const id of ids) if (res[prefix + id] !== undefined) out[id] = res[prefix + id];
    return out;
  };

  DRH.store = {
    getMarks: (ids) => pick("mark:", ids),
    getSeen: (ids) => pick("seen:", ids),

    async setMark(id, mark) {
      if (!mark) return local.remove("mark:" + id);
      return local.set({ ["mark:" + id]: { ...mark, updatedAt: Date.now() } });
    },

    markSeen: (id) => local.set({ ["seen:" + id]: Date.now() }),

    async allMarks() {
      const all = await local.get(null);
      return Object.entries(all)
        .filter(([k]) => k.startsWith("mark:"))
        .map(([k, v]) => ({ id: k.slice(5), ...v }))
        .sort((a, b) => b.updatedAt - a.updatedAt);
    },

    async clearSeen() {
      const all = await local.get(null);
      await local.remove(Object.keys(all).filter((k) => k.startsWith("seen:")));
    },

    async getFilters() {
      const { filters } = await local.get("filters");
      return { ...DRH.DEFAULT_FILTERS, ...filters };
    },
    setFilters: (filters) => local.set({ filters }),

    async getSettings() {
      const { settings } = await local.get("settings");
      return { ...DRH.DEFAULT_SETTINGS, ...settings };
    },
    setSettings: (settings) => local.set({ settings }),

    // 监听其他标签页或设置页的改动；回调收到变化的 id 集合
    onChanged(handler) {
      chrome.storage.onChanged.addListener((changes, area) => {
        if (area !== "local") return;
        const keys = Object.keys(changes);
        handler({
          marks: keys.filter((k) => k.startsWith("mark:")).map((k) => k.slice(5)),
          seen: keys.filter((k) => k.startsWith("seen:")).map((k) => k.slice(5)),
          settings: keys.includes("settings"),
          filters: keys.includes("filters"),
        });
      });
    },
  };
})();
