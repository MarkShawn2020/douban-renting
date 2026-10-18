# 豆瓣租房助手

![豆瓣租房助手](docs/images/cover.png)

在豆瓣租房小组里直接筛选、标记帖子，按到公司的公交通勤时间找房的 Chrome 插件。

## 安装

1. 到 [Releases](https://github.com/MarkShawn2020/douban-renting/releases/latest) 下载 `chrome-douban-renting-v*.zip`，解压
2. Chrome 打开 `chrome://extensions`，开启右上角的「开发者模式」
3. 点击「加载已解压的扩展程序」，选择解压出的文件夹
4. 打开任意豆瓣租房小组的讨论列表（例如「北京租房」），表格上方出现「租房筛选」面板即安装成功

Edge、Arc 等 Chromium 内核浏览器同样适用。

## 功能

- **筛选讨论列表**：包含 / 排除关键词、月租区间（从标题识别）、排除求租帖、只看个人直租 / 转租、排除限女生 / 限男生、隐藏重复帖；适用于小组讨论列表、「我的小组」和组内搜索结果
- **合并多页一起筛**：「加载下一页」「再加载 3 页」把后续页的帖子并入当前列表
- **看房标记**：鼠标移到帖子上即可标记为收藏、已联系、已看房或排除，排除的帖子默认隐藏；打开过的帖子自动记为已读
- **帖子页备注**：详情页右下角的标记栏可以改状态、写备注（房东联系方式、看房时间等）
- **按通勤时间筛选（可选）**：见下文
- **管理标记**：点浏览器工具栏里的插件图标打开设置页，按状态查看全部标记，支持导出 / 导入 JSON

## 按通勤时间筛选

1. 在 [高德开放平台控制台](https://console.amap.com/dev/key/app) 创建应用并添加 Key，服务平台选「Web 服务」
2. 打开插件设置页，填写 Key、城市和工作地点，点「保存并定位」（首次会请求访问高德接口的权限）
3. 回到讨论列表，每条帖子会显示到工作地点的公交时间，在面板里选择「45 分钟内」等即可筛选

帖子位置由标题里的小区名、地铁站名识别，定位结果会显示在通勤时间的悬浮提示里，识别错误时以原帖为准。同一帖子的定位与通勤结果会缓存，不重复消耗额度。

## 隐私

标记、已读记录和高德 Key 只保存在本机浏览器，插件不收集、不上传任何数据。开启通勤功能后，帖子标题、城市、工作地点及其坐标只会发送给高德接口，用于计算通勤时间。完整说明见[隐私政策](https://github.com/MarkShawn2020/douban-renting/blob/main/docs/store/privacy-policy.md)。

本插件对用户数据的使用遵守 Chrome 应用商店用户数据政策（Chrome Web Store User Data Policy），包括其中的有限使用（Limited Use）要求。

## 开发

插件代码在 `extension/`（Manifest V3，无需构建）。端到端测试使用 Playwright 自带的 Chromium 和真实豆瓣页面夹具；环境里有高德 Key 时会额外真实调用高德跑通勤流程：

```shell
python3 -m playwright install chromium
python3 tests/extension/e2e.py [截图目录]
```

打包发布（文件名需以 `chrome` 开头、`.zip` 结尾，官网下载区才能识别）：

```shell
cd extension && zip -r ../chrome-douban-renting-v$(jq -r .version manifest.json).zip . -x '.*'
```

Chrome Web Store 上架素材、文案与提交步骤在 [`docs/store/`](docs/store/listing.md)，`python3 docs/store/render.py` 重新渲染截图和宣传图。

---

## 附：命令行爬取与自建 Web 服务

插件之前，本项目是一套命令行工具：批量爬取豆瓣小组帖子，用高德计算通勤并导出 CSV。代码仍在 `src/`。

### 环境

```shell
uv sync
```

环境变量：

1. `GAODE_KEY`（或 `GAODE_WEB_SERVICE_API_KEY`）：高德 Web 服务 Key
2. `DOUBAN_COOKIE`（可选）：豆瓣登录后的网页 cookie。讨论列表目前匿名可访问，但匿名只能翻到第 400 条左右

### 命令行

```shell
# -c 城市；-a 目标地址（如公司所在大楼）；-g 小组 id，用 | 分隔；-o 输出格式；-n 每组爬取条数
uv run python src/main.py -c 北京 -a 凤凰汇购物中心 -g "zhufang|beijingzufang" -o CSV -n 50
```

不带参数时读取 `src/config.yaml`。`--no-enable_analysis` 只爬取不分析，`--no-enable_scrape` 只分析当天已爬取的数据。

### 自建 Web 服务

曾部署于 douban.lovstudio.ai，2026-10-18 已下线（改为本插件）。如需自行部署：

```shell
zsh deploy/serve.sh   # http://127.0.0.1:8765
```

后台每 30 分钟增量抓取 `config.yaml` 中的小组（每组前 4 页），用高德 POI 搜索定位帖子标题；访客输入工作地点后，按直线距离取最近的一批计算公交通勤。运行数据在 `var/`。为保护个人高德 Key：每日调用上限 `GAODE_DAILY_BUDGET`（默认 3000），每次查询最多新算 25 条通勤，带地址的查询按 IP 限流。`deploy/` 下有 launchd 与 Cloudflare Tunnel 的配置样例。
