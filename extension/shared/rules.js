// 内容脚本、设置页、后台共用；均以经典脚本加载，挂在 globalThis.DRH 上
(() => {
  const DRH = (globalThis.DRH ||= {});

  DRH.STATUSES = [
    { id: "like", label: "收藏" },
    { id: "contacted", label: "已联系" },
    { id: "visited", label: "已看房" },
    { id: "rejected", label: "排除" },
  ];
  DRH.statusLabel = (id) => DRH.STATUSES.find((s) => s.id === id)?.label || "";

  DRH.DEFAULT_FILTERS = {
    enabled: true,
    collapsed: false,
    include: "",
    exclude: "",
    minPrice: null,
    maxPrice: null,
    hideUnknownPrice: false,
    hideSeeking: true,
    personalOnly: false,
    hideGirlsOnly: false,
    hideBoysOnly: false,
    hideDuplicates: true,
    hideRejected: true,
    hideSeen: false,
    onlyMarked: false,
    maxCommute: null,
    hideUnknownCommute: false,
  };

  DRH.DEFAULT_SETTINGS = {
    gaodeKey: "",
    city: "北京",
    target: null, // { query, name, adname, location }
  };

  // 标题里的四位数基本就是月租；一帖多间房时会出现多个价格
  DRH.parsePrices = (title) =>
    (title.match(/\d+/g) || []).filter((n) => n.length === 4).map(Number).filter((n) => n >= 500 && n <= 30000);

  DRH.isSeeking = (title) => /求租|求合租|求整租|求短租|求室友|求房|^\W{0,2}求/.test(title);
  DRH.isFromPersonal = (title) => /个人|直租|转租/.test(title);
  DRH.isOnlyForGirls = (title) => /限女|女生/.test(title);
  DRH.isOnlyForBoys = (title) => /限男|男生/.test(title);

  DRH.topicIdFromUrl = (url) => (url.match(/\/group\/topic\/(\d+)/) || [])[1] || null;

  const words = (s) => (s || "").split(/[\s,，、]+/).filter(Boolean);

  // 返回隐藏原因；null 表示显示。commute 为 undefined 表示尚未计算
  DRH.hiddenReason = (row, f, ctx) => {
    if (!f.enabled) return null;
    const { title } = row;
    const mark = ctx.marks[row.id];
    if (f.onlyMarked && !mark) return "只看已标记";
    if (f.hideRejected && mark?.status === "rejected") return "已排除";
    if (f.hideSeen && ctx.seen[row.id] && !mark) return "已读";
    if (f.hideDuplicates && ctx.duplicateIds.has(row.id)) return "重复帖";
    if (f.hideSeeking && DRH.isSeeking(title)) return "求租";
    if (f.personalOnly && !DRH.isFromPersonal(title)) return "非个人";
    if (f.hideGirlsOnly && DRH.isOnlyForGirls(title)) return "限女生";
    if (f.hideBoysOnly && DRH.isOnlyForBoys(title)) return "限男生";
    const include = words(f.include);
    if (include.length && !include.some((w) => title.includes(w))) return "关键词";
    if (words(f.exclude).some((w) => title.includes(w))) return "排除词";
    if (!row.prices.length) {
      if (f.hideUnknownPrice) return "未标价";
    } else if (f.minPrice != null || f.maxPrice != null) {
      const ok = row.prices.some((p) => (f.minPrice == null || p >= f.minPrice) && (f.maxPrice == null || p <= f.maxPrice));
      if (!ok) return "价格";
    }
    if (ctx.commuteActive && f.maxCommute != null) {
      const c = ctx.commutes[row.id];
      if (c && c.minutes != null && c.minutes > f.maxCommute) return "通勤";
      if (f.hideUnknownCommute && c && c.minutes == null) return "通勤未知";
    }
    return null;
  };

  DRH.formatPrices = (prices) => {
    if (!prices.length) return "";
    const lo = Math.min(...prices);
    const hi = Math.max(...prices);
    return lo === hi ? `¥${lo}` : `¥${lo}–${hi}`;
  };
})();
