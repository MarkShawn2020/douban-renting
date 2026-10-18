# 全网可能最智能的豆瓣小组租房筛选系统

## project structure

```text
.
├── VERSION.txt
├── auto_git_version.sh
├── readme.md
├── requirements.txt
└── src
    ├── config.yaml
    ├── douban
    │   ├── data
    │   │   ├── 2022-03-09-beijingzufang.csv
    │   │   ├── 2022-03-09-beijingzufang_凤凰汇购物中心.csv
    │   │   ├── 2022-03-09-zhufang.csv
    │   │   └── 2022-03-09-zhufang_凤凰汇购物中心.csv
    │   ├── s1_crawl
    │   │   ├── crawl_base.py
    │   │   ├── crawl_via_api.py
    │   │   ├── crawl_via_html.py
    │   │   ├── db.py
    │   │   ├── errors.py
    │   │   ├── readme.md
    │   │   └── settings.py
    │   ├── s2_analysis
    │   │   └── main.py
    │   ├── settings.py
    │   └── utils.py
    ├── gaode
    │   ├── base.py
    │   ├── client.py
    │   └── globals
    │       ├── addr2coords.json
    │       ├── coords2name.json
    │       └── coordspair2duration.json
    ├── main.py
    └── settings.py
```

## init

### environment variables

为安全考虑，以下变量需要需写入环境变量，再经由程序读取。

1. `GAODE_KEY`（或 `GAODE_WEB_SERVICE_API_KEY`）: 高德 Web 服务 key
2. `DOUBAN_COOKIE`（可选）: 豆瓣已登录后的网页 cookie。小组讨论列表目前匿名可访问，但匿名只能翻到第 400 条左右

### python environment

```shell
uv sync
```

## usage sample

### test if project does work

```shell
# `-c` means `city`, for gaode api to recognize your search area
# `-a` means `address`, normally it's your company address, which maybe a building
# `-g` means `groups`, which are joined id list of douban groups by separator `|`
# `-o` means `output_format`, use `-o CSV` for write into csv and for later analysis
# `-n` means `count`, it means how many items you wanna scrape for each group, 5000 is a suitable amount
uv run python src/main.py -c 北京 -a 凤凰汇购物中心 -g "zhufang|beijingzufang" -o CSV -n 50
```

### another way to run via configuring the `src/config.yaml`

```yaml
city: 北京
target_address: 凤凰汇购物中心
groups: zhufang|beijingzufang
count: 5000
max_duration: 30
min_budget: 3000
max_budget: 6000
after_date: null
enable_scrape: true
enable_analysis: true
exclude_only_for_girls: false
include_only_from_personal: false
exclude_unknown_duration: false
exclude_unknown_price: false
```

Then running just via: 

```shell
python src/main.py
```

### scrape but not analyze

```shell
python src/main.py --no-enable_analysis
```

### not scrape but analyze

```shell
python src/main.py --no-enable_scrape
```

## web service

线上地址：https://douban.lovstudio.ai

Web 服务在本机运行，后台每 30 分钟增量抓取 `config.yaml` 中的小组（每组前 4 页），用高德 POI 搜索定位帖子标题；
访客输入工作地点后，按直线距离取最近的一批计算公交通勤并缓存。运行数据（SQLite、高德缓存）在 `var/`。

为保护个人高德 key：每日调用上限 `GAODE_DAILY_BUDGET`（默认 3000），每次查询最多新算 25 条通勤，带地址的查询按 IP 限流。

```shell
# 本地前台运行
zsh deploy/serve.sh   # http://127.0.0.1:8765
```

### deploy (launchd + Cloudflare Tunnel)

- `deploy/ai.lovstudio.douban-renting.plist`：常驻 Web 服务，复制到 `~/Library/LaunchAgents/` 后 `launchctl bootstrap gui/$(id -u) <plist>`
- `deploy/ai.lovstudio.cloudflared.douban.plist` + `deploy/cloudflared.yml`：隧道 `douban-renting` 将 `douban.lovstudio.ai` 回源到 `127.0.0.1:8765`；
  配置放在 `~/.cloudflared/douban-renting.yml`，凭据为同目录下的隧道 JSON
- 更新代码后重启：`launchctl kickstart -k gui/$(id -u)/ai.lovstudio.douban-renting`
- 日志：`~/Library/Logs/douban-renting.log`、`~/Library/Logs/cloudflared-douban.log`
