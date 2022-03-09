import os

API_KEY = '0df993c66c0c636e29ecbb5344252a4a'

HEADERS_DICT = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.109 Safari/537.36",
    "Cookie": os.environ["DOUBAN_COOKIE"]
}

CRAWL_MAX_LIMIT = 100

# 是否启用（网络流传的）api，这个虽然更快且方便，但是首先，其中一个api在爬取topics时最多只能前400+个，另一个最多只能有前200+个
ENABLE_API_CRAWLER = False
