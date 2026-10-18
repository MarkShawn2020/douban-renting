// 高德请求只在后台发：内容脚本受豆瓣页面的跨域限制，且需要统一节流
importScripts("shared/rules.js", "shared/storage.js");

const AMAP = "https://restapi.amap.com";
// 个人开发者 key 实测约 3 QPS，超限返回 100xx 而非 HTTP 429
const MIN_INTERVAL_MS = 350;
const QPS_INFOCODES = ["10019", "10020", "10021"];
const QUOTA_INFOCODES = ["10003", "10044", "10045"];

class GaodeError extends Error {}

// 只控制请求发出的间隔，不等上一个返回，网络延迟不会叠加进吞吐
let nextSlot = 0;

async function throttled(fn) {
  const now = Date.now();
  const at = Math.max(now, nextSlot);
  nextSlot = at + MIN_INTERVAL_MS;
  if (at > now) await new Promise((r) => setTimeout(r, at - now));
  return fn();
}

async function amap(path, params, key) {
  const url = `${AMAP}${path}?${new URLSearchParams({ ...params, key })}`;
  for (let attempt = 0; ; attempt++) {
    const data = await throttled(async () => (await fetch(url)).json());
    if (data.status === "1") return data;
    if (QPS_INFOCODES.includes(String(data.infocode)) && attempt < 3) {
      await new Promise((r) => setTimeout(r, 1000 * (attempt + 1)));
      continue;
    }
    if (QUOTA_INFOCODES.includes(String(data.infocode))) throw new GaodeError("高德接口今日额度已用完");
    if (String(data.infocode) === "10001") throw new GaodeError("高德 Key 无效，请到设置页检查");
    throw new GaodeError(`高德接口错误：${data.info}`);
  }
}

async function cached(key, compute) {
  const hit = await chrome.storage.local.get(key);
  if (key in hit) return hit[key];
  const value = await compute();
  await chrome.storage.local.set({ [key]: value });
  return value;
}

// 租房帖标题里多是小区名、地铁站名，POI 关键字搜索的命中率远高于地理编码
function searchPlace(keywords, city, key) {
  keywords = keywords.slice(0, 80);
  return cached(`gpoi:${city}:${keywords}`, async () => {
    const data = await amap("/v3/place/text", { keywords, city, citylimit: "true", offset: 1, page: 1 }, key);
    const poi = (data.pois || [])[0];
    if (!poi || typeof poi.location !== "string" || !poi.location) return null;
    return { location: poi.location, name: poi.name || "", adname: typeof poi.adname === "string" ? poi.adname : "" };
  });
}

function transitMinutes(from, to, city, key) {
  return cached(`gtr:${from}|${to}`, async () => {
    const data = await amap("/v3/direction/transit/integrated", { origin: from, destination: to, city, strategy: 3 }, key);
    const transit = (data.route?.transits || [])[0];
    if (transit) return Math.round(Number(transit.duration) / 60);
    // 距离太近时公交规划无结果，改算步行
    const walk = await amap("/v3/direction/walking", { origin: from, destination: to }, key);
    const path = (walk.route?.paths || [])[0];
    return path ? Math.round(Number(path.duration) / 60) : null;
  });
}

function distanceKm(a, b) {
  const [lng1, lat1] = a.split(",").map(Number);
  const [lng2, lat2] = b.split(",").map(Number);
  const rad = Math.PI / 180;
  const h = Math.sin(((lat2 - lat1) * rad) / 2) ** 2 +
    Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * Math.sin(((lng2 - lng1) * rad) / 2) ** 2;
  return 6371 * 2 * Math.asin(Math.sqrt(h));
}

async function commute(title) {
  const { gaodeKey, city, target } = await DRH.store.getSettings();
  if (!gaodeKey || !target) throw new GaodeError("尚未设置高德 Key 与工作地点");
  const place = await searchPlace(title, city, gaodeKey);
  if (!place) return { minutes: null, place: null, distanceKm: null };
  const placeName = [place.adname, place.name].filter(Boolean).join(" ");
  // 标题写着「通勤国贸」时 POI 会落在目标点本身，真实位置未知
  if (place.location === target.location) return { minutes: null, place: placeName, distanceKm: null };
  return {
    minutes: await transitMinutes(place.location, target.location, city, gaodeKey),
    place: placeName,
    distanceKm: Math.round(distanceKm(place.location, target.location) * 10) / 10,
  };
}

const handlers = {
  commute: ({ title }) => commute(title),
  async resolvePlace({ query, city, key }) {
    const place = await searchPlace(query, city, key);
    if (!place) throw new GaodeError(`在${city}没找到「${query}」，换个更具体的地点名试试`);
    return place;
  },
  openOptions: () => chrome.runtime.openOptionsPage(),
};

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  const handler = handlers[msg?.type];
  if (!handler) return false;
  Promise.resolve(handler(msg))
    .then((data) => sendResponse({ ok: true, data }))
    .catch((e) => sendResponse({ ok: false, error: e instanceof GaodeError ? e.message : `请求失败：${e.message}` }));
  return true;
});

chrome.action.onClicked.addListener(() => chrome.runtime.openOptionsPage());
