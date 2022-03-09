import os
from datetime import datetime
from enum import Enum

import requests

from douban.s1_crawl.settings import HEADERS_DICT
from douban.settings import DOUBAN_DATA_DIR


class WriteEngine(str, Enum):
    CSV = "CSV"
    JSON = "JSON"
    STDOUT = "STDOUT"


class DoubanCrawlerBase:

    def __init__(self, write_engine: WriteEngine = WriteEngine.STDOUT):
        self._s = requests.Session()
        self._s.headers = HEADERS_DICT

        print("init douban crawler")

        self.write_engine = write_engine
        print("write_engine: " + self.write_engine.value)

        self.data_dir = DOUBAN_DATA_DIR
        print("write output directory: " + self.data_dir)

    def _get_topics_of_group(self, group: str, start: int = 0, limit: int = 100):
        pass

    def crawl_topics_of_group(self, group: str, days: int = 10):
        pass
