import os
import re
import time
from datetime import datetime, timedelta
from typing import TypedDict
from pprint import pprint

from src.douban.s1_crawl.crawl_base import DoubanCrawlerBase, WriteEngine
from bs4 import BeautifulSoup

import csv


class Topic(TypedDict):
    response_latest_time: datetime
    post_title: str
    post_url: str
    author_name: str
    author_url: str
    response_count: int


TopicColumns = ["response_latest_time", "post_title", "post_url", "author_name", "author_url", "response_count"]


class DoubanCrawlerViaHTML(DoubanCrawlerBase):

    def _get_topics_of_group(self, group: str, start: int = 0, limit: int = 5):
        """
        :param group:
        :param start:
        :param limit: 基于html爬取的limit参数和基于api不一样，api里是count，html里就是limit，并且会主动加5
        :return:
        """
        url = f'https://www.douban.com/group/{group}/discussion?start={start}&limit={limit}&type=new'
        print(f"FETCHING: {url}")
        res = self._s.get(url)
        soup = BeautifulSoup(res.text, features="html.parser")
        rows = soup.select("#content .article tr")[1:]
        if len(rows) == 0:
            raise Exception("no rows found, maybe banned")
        elif len(rows) == 1:
            raise Exception("no more rows found")

        for row in rows:
            post_title = row.select_one("td:nth-of-type(1) a")["title"]
            post_url = row.select_one("td:nth-of-type(1) a")["href"]
            author_url = row.select_one("td:nth-of-type(2) a")["href"]
            author_name = row.select_one("td:nth-of-type(2) a").text
            response_count = int(row.select_one("td:nth-of-type(3)").text or 0)

            datetime_str = row.select_one("td:nth-of-type(4)").text
            if not re.match("20", datetime_str):  # test if it's year of 20XX
                datetime_str = f"{datetime.now().year}-{datetime_str}"
            response_latest_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")

            yield Topic(post_title=post_title, post_url=post_url, author_url=author_url,
                        author_name=author_name, response_count=response_count,
                        response_latest_time=response_latest_time)

    def crawl_topics_of_group_in_latest_days(self, group: str, days: int = 10):

        if self.write_engine == WriteEngine.CSV:
            self.write_filename += "-" + group + ".csv"
            csv_writer = csv.writer(
                open(os.path.join(self.data_dir, self.write_filename), "w", encoding="utf-8")
            )
            csv_writer.writerow(TopicColumns)

        finished_reason = ""
        start = 0
        limit = 100
        while not finished_reason:
            for item in self._get_topics_of_group(group, start, limit):
                # !IMPORTANT: 豆瓣的排序很奇怪，中途会断掉，所以不能按照这个发帖最后日期回，最后还是打算直接爬天数*1000条
                # if item["response_latest_time"] < datetime.now() - timedelta(days=days):
                #     finished_reason = "finished since target period is all crawled."
                #     break
                # else:
                if self.write_engine == WriteEngine.CSV:
                    csv_writer.writerow(list(item[x] for x in TopicColumns))

                    print(item)
                elif self.write_engine == WriteEngine.STDOUT:
                    print(item)
                else:
                    raise Exception("NOT SUPPORT NOW")
            start += limit
            print("----------------")

            if start > days * 1000:
                finished_reason = "finished collecting specific amount"
            else:
                time.sleep(1)

        print(finished_reason)


if __name__ == '__main__':
    # group = 'beijingzufang'   # 北京租房
    group = 'zhufang'  # 北京无中介租房
    dc = DoubanCrawlerViaHTML(write_engine=WriteEngine.CSV)
    # dc._get_topics_of_group(group)
    dc.crawl_topics_of_group_in_latest_days(group, 10)
