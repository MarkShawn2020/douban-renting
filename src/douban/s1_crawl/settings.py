import os

CRAWL_DIR = os.path.dirname(__file__)
CRAWL_DATA_DIR = os.path.join(CRAWL_DIR, "data")

API_KEY = '0df993c66c0c636e29ecbb5344252a4a'

_HEADERS_STR = '''Cookie: bid=0uaXoROpOUw; ll="118162"; __gads=ID=590650c4adc344d8-22a561876ad00095:T=1643995647:RT=1643995647:S=ALNI_MZ4DTnIVeMaD4fReHSYutLjTi3L6w; __utmc=30149280; __utmz=30149280.1646043789.3.3.utmcsr=baidu|utmccn=(organic)|utmcmd=organic; dbcl2="27116168:LQk2FPeIZKo"; ck=QvBt; push_noty_num=0; __utmv=30149280.2711; __yadk_uid=Jc2DZONeMdpnF04q69lwwyAfuhQNXuO4; douban-fav-remind=1; ct=y; ap_v=0,6.0; push_doumail_num=0; _pk_ref.100001.8cb4=%5B%22%22%2C%22%22%2C1646207832%2C%22https%3A%2F%2Fwww.baidu.com%2Flink%3Furl%3D8KqvSzmmPZdpTT708dJ0lwNdY9I00Li7z7oTULZFYKoZ6oJPq3pxpC97G2fYBTBt%26wd%3D%26eqid%3Df9d575bd0000eaae00000003621ca285%22%5D; _pk_ses.100001.8cb4=*; __utma=30149280.1494039055.1643995646.1646203963.1646207833.14; __utmt=1; _pk_id.100001.8cb4=6d2dbf9e93b60577.1646043787.12.1646208952.1646204254.; __utmb=30149280.445.5.1646208951990
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.109 Safari/537.36'''

HEADERS_DICT = dict(i.split(": ", 1) for i in _HEADERS_STR.splitlines())

CRAWL_MAX_LIMIT = 100

# 是否启用（网络流传的）api，这个虽然更快且方便，但是首先，其中一个api在爬取topics时最多只能前400+个，另一个最多只能有前200+个
ENABLE_API_CRAWLER = False
