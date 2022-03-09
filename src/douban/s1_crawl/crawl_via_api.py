from pprint import pprint
from typing import TypedDict, List, Union

from src.douban.s1_crawl.settings import API_KEY, CRAWL_MAX_LIMIT
from src.douban.s1_crawl.crawl_base import DoubanCrawlerBase


class Author(TypedDict):
    name: str
    is_suicide: bool
    avatar: str  # url
    uid: str  # int
    alt: str  # url
    type: str  # UserType
    id: str  # int
    large_avatar: str  # url


class Dimension(TypedDict):
    width: int
    height: int


class Photo(TypedDict):
    size: Dimension
    alt: str  # url
    layout: str
    topic_id: str  # int
    seq_id: str  # int
    author_id: str  # int
    title: str
    id: str  # int
    creation_date: str  # datetime


class DoubanApiTopic(TypedDict):
    is_private: bool
    locked: bool
    liked: bool

    like_count: int
    comment_count: int

    id: str  # int
    created: str  # datetime
    updated: str  # datetime

    title: str
    alt: str  # url
    share_url: str  # url
    screenshot_title: str
    screenshot_url: str  # url
    screenshot_type: str
    content: str

    author: Author
    photos: List[Photo]


class DoubanApiTopicResultSuccess(TypedDict):
    """
    请求成功时的结构体
    """
    count: int  # 0 - 100
    start: int  # default: 0
    total: int
    topics: List[DoubanApiTopic]


class DoubanApiTopicResultFailure(TypedDict):
    """
    当请求失败时，就会返回这个结构体
    """
    msg: str  # "access_error"
    code: int  # 403
    request: str
    localized_message: str


class DoubanCrawlerViaAPI(DoubanCrawlerBase):

    def __init__(self, apikey: str):
        super().__init__()
        self._apikey = apikey
        self._s.params = {"apikey": self._apikey}

    def _get_topics_of_group(self, group: str, start: int = 0, limit: int = 100) \
            -> Union[DoubanApiTopicResultSuccess, DoubanApiTopicResultFailure]:
        url = f'https://api.douban.com/v2/group/{group}/topics?start={start}&count={limit}'
        print(f"requesting url: {url}")
        res = self._s.get(url)
        return res.json()

    def crawl_topics_of_group(self, group: str, days: int = 10, limit: int = 100):
        """
        爬取近N（默认10）天的小组讨论，因为豆瓣帖子是按照更新顺序排列的，此外，超过一定天数的帖子对实际租房没太大意义（研究除外）

        :param group:
        :param days:
        :param limit:
        :return:
        """
        start = 0
        while True:
            result = self._get_topics_of_group(group, start, limit)

            if result.get("code", 0) == 403:
                finished_reason = f"此请求已触及该apikey<{self._apikey}>限制"
                break

            for item in result["topics"]:
                yield DoubanApiTopic(**item)

            start += limit

            if result["start"] + result["count"] >= result["total"]:
                finished_reason = "不容易，所有数据已全部提取完毕"
                break

        print("finished, reason: " + finished_reason)


if __name__ == '__main__':
    group_id = 'beijingzufang'
    dc = DoubanCrawlerViaAPI(API_KEY)
    dc.crawl_topics_of_group(group_id, 1, CRAWL_MAX_LIMIT)
