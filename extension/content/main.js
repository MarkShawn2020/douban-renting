(() => {
  const DRH = globalThis.DRH;
  const topicId = location.pathname.startsWith("/group/topic/") && DRH.topicIdFromUrl(location.pathname);
  if (topicId) {
    DRH.enhanceTopic(topicId);
    return;
  }
  // 小组讨论列表、「我的小组」聚合页、组内搜索结果都用 table.olt
  const table = [...document.querySelectorAll("table.olt")].find((t) => t.querySelector('a[href*="/group/topic/"]'));
  if (table) DRH.enhanceList(table);
})();
