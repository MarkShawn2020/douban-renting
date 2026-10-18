# 豆瓣租房助手隐私政策

生效日期：2026-10-18，适用于 Chrome 插件「豆瓣租房助手」0.2.1 及之后的版本。
开发者：Lovstudio.AI（手工川）。

## 插件会处理哪些数据

- **豆瓣小组页面内容**：插件只在 `https://www.douban.com/group/*` 页面运行，读取讨论列表里的帖子标题、链接和小组名，用来识别月租、筛选和显示标记。
- **你的标记与备注**：你给帖子设置的状态（收藏、已联系、已看房、排除）、备注，以及帖子的标题、链接、小组名、识别出的价格和更新时间。
- **已读记录**：你在豆瓣小组里打开过的帖子 ID 和打开时间，用于把已读帖子显示为灰色。
- **筛选条件**：关键词、价格区间等面板设置。
- **通勤设置（可选）**：你填写的高德 Web 服务 Key、城市、工作地点名称，以及定位得到的工作地点坐标。
- **通勤结果缓存（可选）**：帖子标题对应的定位结果和公交通勤时长，避免重复请求。

## 数据存在哪里

以上数据全部保存在你本机浏览器的 `chrome.storage.local` 中，不使用 Chrome 同步存储，也不会上传到开发者的服务器（插件没有任何开发者服务器）。卸载插件时，浏览器会删除这些数据。

## 会发给谁

- **高德开放平台（仅在你启用通勤功能后）**：只有当你在设置页填写高德 Key 并同意浏览器的权限请求后，插件才会通过 HTTPS 向 `restapi.amap.com` 发送：帖子标题（用于搜索小区或地铁站位置）、城市、工作地点名称、定位得到的坐标，以及你的高德 Key。这些请求只用于计算公交通勤时间，高德对数据的处理适用[高德地图开放平台隐私权政策](https://lbs.amap.com/pages/privacy/)。在设置页点「清除」会删除通勤设置并撤销访问高德接口的权限。
- **豆瓣**：点「加载下一页」时，插件会以你当前的豆瓣登录状态请求同一讨论列表的下一页，与你在浏览器里手动翻页相同，不发送额外数据。

除此之外，插件不向任何地方发送数据。

## 插件不做的事

- 不收集姓名、邮箱、手机号等个人身份信息，不读取豆瓣小组以外的网页。
- 不包含统计、分析、广告或任何第三方追踪代码，不加载和执行远程代码。
- 不出售、出租或转让用户数据，不把数据用于个性化广告、信用评估或借贷，也不用于与上述找房功能无关的目的。

## 你可以怎样管理数据

在插件设置页（点浏览器工具栏里的插件图标）可以：查看、修改和删除每一条标记，导出或导入全部标记（JSON），清空已读记录，清除通勤设置。卸载插件会删除全部数据。

## 有限使用声明

豆瓣租房助手对用户数据的使用遵守 Chrome 应用商店用户数据政策（Chrome Web Store User Data Policy），包括其中的有限使用（Limited Use）要求。

## 政策变更

如果插件处理数据的方式发生变化，会更新本页并在插件的更新说明中注明；涉及新的数据收集时，会在插件界面中显著告知并征得你的同意。

## 联系

问题与反馈：<https://github.com/MarkShawn2020/douban-renting/issues>

---

# Privacy Policy — 豆瓣租房助手 (Douban Renting Helper)

Effective 2026-10-18 for version 0.2.1 and later. Developer: Lovstudio.AI.

**Data the extension handles.** The extension runs only on `https://www.douban.com/group/*`. It reads post titles, links and group names from Douban group discussion lists to filter and annotate them. It stores the marks you set (status, note, post title, link, group, parsed price, update time), the IDs and times of topics you opened (to grey out read posts), your filter settings, and — only if you enable the optional commute feature — your AMap (Gaode) Web Service key, city, workplace name and its coordinates, plus cached geocoding and transit results.

**Storage.** All of this is stored locally in your browser via `chrome.storage.local`. Nothing is synced or uploaded to any developer server; the extension has no server. Uninstalling the extension deletes the data.

**Sharing.** Only after you enable the commute feature on the options page and grant the runtime permission for `restapi.amap.com`, the extension sends post titles (to look up the location), your city, workplace name, resulting coordinates and your own AMap key to the AMap Web Service API over HTTPS, solely to compute public-transit commute times. AMap's handling is governed by the [AMap Open Platform privacy policy](https://lbs.amap.com/pages/privacy/). The "load next page" button requests the next page of the same Douban discussion list with your existing Douban session, the same as paging manually. No data is sent anywhere else.

**What it does not do.** No collection of personally identifiable information, no analytics, ads or third-party trackers, no remote code. User data is never sold or transferred, never used for personalized advertising, creditworthiness or lending, and never used for purposes unrelated to the extension's single purpose.

**Your controls.** On the options page you can view, edit and delete marks, export or import them as JSON, clear read history, and clear the commute settings (which also revokes the AMap host permission).

**Limited Use.** The use of information by this extension adheres to the Chrome Web Store User Data Policy, including the Limited Use requirements.

**Changes and contact.** Changes to data practices will be noted here and in the release notes, and new data collection will be disclosed prominently in the extension with your consent. Contact: <https://github.com/MarkShawn2020/douban-renting/issues>
