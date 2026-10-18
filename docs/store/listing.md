# 豆瓣租房助手：Chrome Web Store 上架材料

对应插件版本 0.2.1。下文的要求均于 2026-10-18 对照 Chrome 官方文档核对，来源见文末；提交时以开发者控制台的实际字段为准。

## 文件清单

| 文件 | 用途 | 规格 |
| --- | --- | --- |
| `output/chrome-douban-renting-v0.2.1.zip` | 上传包（不进 git，按下文「打包」生成） | `manifest.json` 在 zip 根目录 |
| `docs/store/store-icon-128.png` | 商店图标 | 128x128 PNG，图形 96x96，四周 16px 透明留白 |
| `docs/store/screenshots/01-filter-panel.png` | 截图 1：筛选面板与通勤时间 | 1280x800 PNG |
| `docs/store/screenshots/02-list-marks.png` | 截图 2：列表里的看房标记 | 1280x800 PNG |
| `docs/store/screenshots/03-topic-note.png` | 截图 3：帖子页标记栏与备注 | 1280x800 PNG |
| `docs/store/screenshots/04-options-commute.png` | 截图 4：设置页通勤设置 | 1280x800 PNG |
| `docs/store/screenshots/05-options-marks.png` | 截图 5：设置页管理标记 | 1280x800 PNG |
| `docs/store/promo-small-440x280.png` | 小型宣传图（必填） | 440x280 PNG |
| `docs/store/promo-marquee-1400x560.png` | 大型宣传图（选填，用于首页推荐位） | 1400x560 PNG |
| `docs/store/privacy-policy.md` | 隐私政策正文（中英双语） | 需发布成公开网址 |

重新渲染：`python3 docs/store/render.py`。截图来自 `tests/extension/fixtures` 的豆瓣页面夹具，通勤数据来自一次真实的高德调用，结果缓存在被 git 忽略的 `var/store/commute-cache.json`，之后重渲染不再调用高德。帖子页夹具原本是一篇非租房帖，截图时把标题和正文换成了列表夹具里同一条租房帖的内容，插件界面本身未做任何修改。

## 官方要求速查

| 项目 | 官方要求 | 本次材料 |
| --- | --- | --- |
| 商店图标 | 必填；128x128 PNG，正方形图形 96x96，四周各 16px 透明留白 | 已从 `assets/logo.png` 重新生成，插件包里的 `icon128.png` 同步改为留白版 |
| 截图 | 至少 1 张、最多 5 张；1280x800（推荐）或 640x400；直角、无留白满版；商店会缩到 640x400 展示 | 5 张 1280x800，按 1.25 倍渲染，缩小后文字仍可辨认 |
| 小型宣传图 | 必填；440x280；没有小型宣传图的插件排在有图的之后 | 已提供 |
| 大型宣传图 | 选填；1400x560；不提供就不会进首页大图推荐 | 已提供 |
| 宣传视频 | 选填（YouTube 链接） | 未提供 |
| 摘要 | 取自 manifest 的 `description`，纯文本，不超过 132 个字符 | 47 个字符 |
| 名称 | 取自 manifest 的 `name`，不超过 75 个字符 | 6 个字符 |
| 详细说明 | 文档未给字数上限；开头一句说清用途，不能堆砌关键词，不能有匿名用户评价，空说明会被拒 | 见下文 |
| 单一用途 | 必须是窄而易懂的单一用途，在隐私权标签页填写 | 见下文 |
| 权限理由 | 每个权限都要写理由；申请超出用途的权限会被拒 | 见下文 |
| 数据使用 | 勾选收集的数据类型并做三项合规声明；即使只在本机处理或存储也必须披露 | 见下文 |
| 隐私政策 | 处理用户数据就必须提供隐私政策网址，只存本机也不例外 | `privacy-policy.md` |
| 有限使用声明 | 必须在属于插件的网站上（如首页或一次点击可达的页面）声明遵守 Limited Use 要求 | 已写进隐私政策和 README「隐私」一节（官网插件页读取 README） |
| 账号 | 一次性注册费；发布或更新前 Google 账号必须开启两步验证；联系邮箱需验证 | 需你本人完成 |
| 新账号限额 | 新发布者最多同时发布 2 个插件 | 注意与其他插件的上架顺序 |

## 商品详情（Store listing 标签页）

**名称**（来自 manifest，控制台里不能改）：豆瓣租房助手

**摘要**（来自 manifest，控制台里不能改）：在豆瓣小组里标记、筛选租房帖：价格、关键词、求租与重复帖过滤，可按工作地点的公交通勤时间筛选。

**详细说明**（纯文本，整段复制）：

```text
在豆瓣租房小组里直接筛选、标记帖子，按到公司的公交通勤时间找房。

在豆瓣小组找房，最费时间的是在几百条帖子里反复翻页、逐条点开，还记不住哪些看过、联系过谁。豆瓣租房助手把筛选和标记直接放进豆瓣的讨论列表。

【筛选讨论列表】
· 包含 / 排除关键词，月租区间（从标题里识别价格）
· 排除求租帖，只看个人直租 / 转租，排除限女生 / 限男生
· 隐藏重复帖、已排除和已读的帖子
· 适用于小组讨论列表、「我的小组」聚合页和组内搜索结果

【合并多页一起筛】
「加载下一页」「再加载 3 页」把后续页的帖子并入当前列表，一次筛完。

【看房标记】
鼠标移到帖子上即可标记为收藏、已联系、已看房或排除；排除的帖子默认隐藏，打开过的帖子自动记为已读。

【帖子页备注】
帖子详情页右下角的标记栏可以改状态、写备注，比如房东联系方式、看房时间。

【按通勤时间筛选（可选）】
在设置页填写你自己的高德 Web 服务 Key、城市和工作地点后，每条帖子会显示到工作地点的公交时间，可以只看「45 分钟内」等。帖子位置由标题里的小区名、地铁站名识别，识别错误时以原帖为准。同一帖子的结果会缓存，不重复消耗额度。

【管理标记】
点浏览器工具栏里的插件图标打开设置页，按状态查看全部标记，支持导出 / 导入 JSON。

【隐私】
标记、已读记录、筛选条件和高德 Key 只保存在本机浏览器，插件没有服务器，不收集、不上传任何数据。只有在你开启通勤功能后，帖子标题、城市、工作地点及其坐标才会发送给高德接口，用于计算通勤时间。

本插件是独立开发的第三方工具，与豆瓣官方无关。
开发者：Lovstudio.AI（手工川）
```

**类别**：推荐「Lifestyle（生活方式）→ Household」，备选「Productivity（效率）→ Tools」。官方文档未列出类别清单，以上名称来自第三方统计站，以控制台下拉框为准。

**语言**：中文（简体）。

**图片资源**：按上表上传商店图标、5 张截图（按编号顺序）、小型宣传图、大型宣传图。宣传图不分语言，截图可按语言分别上传。

**其他字段**

| 字段 | 填写 |
| --- | --- |
| 官方网址 | 选填。下拉框只列出在 Google Search Console 验证过的网站；验证 `lovstudio.ai` 后选择它，商店会显示已验证发布者，否则显示发布者名称 |
| 首页网址 | `https://lovstudio.ai/app/douban-renting` |
| 支持网址 | `https://github.com/MarkShawn2020/douban-renting/issues` |
| 成人内容 | 否 |

## 隐私权（Privacy practices 标签页）

这一页主要给审核员看，建议粘贴英文，中文仅供核对。

**单一用途说明**

```text
Helps users find rental housing in Douban groups: it filters and marks rental posts in Douban group discussion lists, lets users add notes on topic pages, and can optionally filter posts by public-transit commute time to the user's workplace.
```

> 帮助用户在豆瓣小组里找房：在讨论列表中筛选、标记租房帖，在帖子页写备注，并可选地按到工作地点的公交通勤时间筛选。

**权限理由**

`storage`

```text
Stores the user's own data locally with chrome.storage.local: marks and notes on Douban topics, IDs of topics the user has opened (to grey out read posts), filter settings, and the optional commute settings and cached commute results. Nothing is synced or uploaded.
```

主机权限（控制台会把 content script 匹配的 `https://www.douban.com/group/*` 与可选主机权限 `https://restapi.amap.com/*` 列在这里，若分成两栏就分别填对应段落）

```text
https://www.douban.com/group/* (content scripts): the extension only runs on Douban group pages, where it adds the filter panel and mark buttons to discussion lists and a note bar to topic pages. The "load next page" button fetches the next page of the same discussion list from www.douban.com.

https://restapi.amap.com/* (optional host permission): not granted at install. It is requested at runtime only when the user turns on the optional commute feature on the options page and saves their own AMap (Gaode) Web Service key. The background service worker then calls the AMap place search and transit/walking route APIs to compute commute times. Clicking "Clear" on the options page removes this permission.
```

**远程代码**：选择「No, I am not using remote code」。全部脚本随插件打包；对高德接口的请求只返回 JSON 数据，不加载、不执行任何远程代码。

**数据使用**

官方 FAQ 明确：即使数据只在本机处理或存储，也必须披露；2026-08-01 起执行的新版政策还要求所有数据收集都要显著披露。因此建议按插件实际处理的数据如实勾选，和隐私政策保持一致。下表的类别名称以控制台为准。

| 数据类型（控制台英文名） | 勾选 | 依据 |
| --- | --- | --- |
| Personally identifiable information | 否 | 不处理姓名、邮箱、证件号等 |
| Health information | 否 | |
| Financial and payment information | 否 | |
| Authentication information | 是 | 用户填写的高德 Key，只存本机、只发给高德 |
| Personal communications | 否 | |
| Location | 是 | 工作地点名称与坐标、帖子定位坐标；开启通勤功能后发给高德 |
| Web history | 是 | 在本机记录打开过的豆瓣小组帖子 ID 与时间，用于已读标记 |
| User activity | 否 | 不记录点击、滚动、按键等行为 |
| Website content | 是 | 读取豆瓣帖子标题，标记里保存标题；开启通勤功能后把标题发给高德 |

三项合规声明全部勾选：

- I do not sell or transfer user data to third parties, outside of the approved use cases
- I do not use or transfer user data for purposes that are unrelated to my item's single purpose
- I do not use or transfer user data to determine creditworthiness or for lending purposes

**隐私政策网址**：把 `docs/store/privacy-policy.md` 发布成公开网址后填入，任选其一：

1. 本分支合并进 `main` 并推送后，使用 `https://github.com/MarkShawn2020/douban-renting/blob/main/docs/store/privacy-policy.md`（仓库是公开的）。
2. 转成 HTML 后用官网发布脚本发到 `https://lovstudio.ai/p/<slug>`。

隐私政策至少要说明收集什么、怎么用、与谁共享；只存本机的插件也必须提供。`privacy-policy.md` 已覆盖这些内容，并包含有限使用声明和高德隐私政策链接。

## 分发（Distribution）

- 付费：免费
- 可见性：公开；想先小范围试用可选「不公开」（只有拿到链接的人能安装）
- 地区：所有地区

## 测试说明（Test instructions，选填）

```text
1. Open https://www.douban.com/group/beijingzufang/discussion (public, no login needed). A "租房筛选" (rental filter) panel appears above the discussion table; hover a row to see the mark buttons.
2. Open any topic from the list: a mark bar appears at the bottom-right of the page.
3. Click the extension icon to open the options page, which lists all marks.
4. The commute feature is optional and needs the user's own AMap (Gaode) Web Service key; all other features work without it.
```

需要审核员测试通勤功能时，可以在这里额外附一个低额度的测试 Key（不要用主力 Key）。

## manifest 审核检查

| 检查项 | 结论 | 本分支处理 |
| --- | --- | --- |
| `description` 长度 | 47 字符，低于 132 上限 | 不改 |
| `name` 长度 | 6 字符，低于 75 上限 | 不改 |
| `homepage_url` | 原先缺失 | 已补 `https://lovstudio.ai/app/douban-renting` |
| 128 图标 | 原图满版、没有透明留白，商店里会比其他插件显得更大 | `icons/icon128.png` 改为 96x96 图形加 16px 透明留白；16/32/48 是工具栏小图标，保持满版 |
| 权限最小化 | 只有 `storage`；高德是可选主机权限，用户开启通勤时才申请；内容脚本只匹配 `https://www.douban.com/group/*` | 不改 |
| 远程代码 | 无 `eval`、`new Function`，也不加载远程脚本 | 不改 |
| 数据披露 | 设置页原文案只说 Key 会发给高德，没提帖子标题与工作地点也会发出 | 设置页提示改为完整说明发送内容与用途 |
| 版本号 | 打包内容与 GitHub Release v0.2.0 不同了 | `version` 升到 0.2.1，避免同一版本号对应两份不同的包 |
| 名称含「豆瓣」 | 第三方商标用于描述用途，属常见做法 | 详细说明里写明与豆瓣官方无关；若审核以冒充为由驳回，可改名如「租房助手（豆瓣小组）」 |

## 打包与本地验证

```shell
mkdir -p output
git archive --format=zip -o output/chrome-douban-renting-v$(jq -r .version extension/manifest.json).zip HEAD:extension
```

`git archive HEAD:extension` 只打包已提交的文件，`manifest.json` 位于 zip 根目录，不含 tests 和点文件。验证方式：解压到临时目录后，用 Playwright 自带的 Chromium 以 `--load-extension` 加载，确认 service worker 正常启动、manifest 版本为 0.2.1、豆瓣列表夹具上出现筛选面板。

## 需要你亲自完成的步骤

1. **Google 账号开启两步验证**：没有两步验证无法发布或更新插件。
2. **注册开发者账号**：打开 [Chrome Web Store 开发者控制台](https://chrome.google.com/webstore/devconsole)，同意开发者协议并支付一次性注册费。官方文档没写金额，多个 2026 年的第三方指南都写 5 美元，以支付页显示为准。账号邮箱创建后不能更改，建议用常用的工作邮箱。
3. **完善账号信息**：填发布者名称（会显示在「提供方」处，建议 `Lovstudio.AI`），验证联系邮箱。控制台若要求声明交易者（trader）身份，按实际情况填写。
4. **发布隐私政策**：合并本分支并推送，或发布到官网，拿到公开网址。
5. **上传与填写**：「添加新内容」上传 `output/chrome-douban-renting-v0.2.1.zip`，按本文件依次填写商品详情、隐私权、分发、测试说明四个标签页。
6. **提交审核**：点「提交审核」。确认框里可以取消「审核通过后自动发布」，审核通过后 30 天内需手动发布，否则退回草稿。审核时长不固定，可在账号页开启发布通知邮件。
7. **上线后回读**：确认商店页能打开、能安装，再把 README 和官网插件页的安装方式改成商店链接，并补发 GitHub Release v0.2.1。

## 来源

- [Supplying images](https://developer.chrome.com/docs/webstore/images)
- [Complete your listing information](https://developer.chrome.com/docs/webstore/cws-dashboard-listing)
- [Fill out the privacy fields](https://developer.chrome.com/docs/webstore/cws-dashboard-privacy)
- [Program Policies](https://developer.chrome.com/docs/webstore/program-policies/policies)（含两步验证、单一用途、关键词堆砌、Limited Use）
- [User Data FAQ](https://developer.chrome.com/docs/webstore/program-policies/user-data-faq)（本机存储也需披露、需隐私政策）
- [Chrome Web Store policy updates (2026-07-01)](https://developer.chrome.com/blog/cws-policy-updates-2026)（2026-08-01 起执行的 Limited Use 与披露要求）
- [Register your developer account](https://developer.chrome.com/docs/webstore/register)、[Publish in the Chrome Web Store](https://developer.chrome.com/docs/webstore/publish)
- [Manifest: description](https://developer.chrome.com/docs/extensions/reference/manifest/description)、[Manifest: name](https://developer.chrome.com/docs/extensions/reference/manifest/name)
- [高德地图开放平台隐私权政策](https://lbs.amap.com/pages/privacy/)
