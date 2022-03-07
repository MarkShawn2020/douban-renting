from datetime import datetime
from enum import Enum

import requests

from src.douban.s1_crawl.settings import HEADERS_DICT, CRAWL_DATA_DIR


class WriteEngine(str, Enum):
    CSV = "CSV"
    JSON = "JSON"
    STDOUT = "STDOUT"


class DoubanCrawlerBase:

    def __init__(self, write_filename: str = None, write_engine: WriteEngine = WriteEngine.STDOUT):
        self._s = requests.Session()
        self._s.headers = HEADERS_DICT

        print("init douban crawler")

        self.write_engine = write_engine
        print("write_engine: " + self.write_engine.value)

        cur_time = datetime.now().strftime("%Y-%m-%d")
        if not write_filename:
            print(f"filename auto init as: " + cur_time)
            self.write_filename = cur_time
        else:
            self.write_filename = write_filename
        print("write_filename: " + self.write_filename)

        self.data_dir = CRAWL_DATA_DIR
        print("write output directory: " + self.data_dir)

    def _get_topics_of_group(self, group: str, start: int = 0, limit: int = 100):
        pass

    def crawl_topics_of_group_in_latest_days(self, group: str, days: int = 10):
        pass
