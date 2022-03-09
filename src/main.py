import os
from argparse import ArgumentParser
from datetime import datetime

import yaml

from douban.s1_crawl.crawl_base import WriteEngine
from douban.s1_crawl.crawl_via_html import DoubanCrawlerViaHTML
from douban.s2_analysis.main import analyze
from douban.utils import get_filename, get_cur_date
from gaode.client import GaodeClient
from settings import DOUBAN_DIR

GROUP_SEPARATOR = "|"

if __name__ == '__main__':

    """
    config
    """
    loader = yaml.load(open(os.path.join(DOUBAN_DIR, "config.yaml")), Loader=yaml.FullLoader)

    """
    args
    """
    parser = ArgumentParser()
    parser.add_argument("--groups", "-g", help=f"待爬取的豆瓣小组，可以有多个，用'{GROUP_SEPARATOR}'号隔开", default=loader["groups"])
    parser.add_argument("--count", "-n", help="待爬取每个豆瓣小组的指定条目数", default=1000)
    parser.add_argument("--output_type", "-o", help="爬取豆瓣小组后的输出格式", default=WriteEngine.CSV)

    parser.add_argument("--city", "-c", help="所在城市", default=loader["city"])
    parser.add_argument("--target_address", "-a", help="目标地址，例如公司地址，具体到大楼即可", default=loader["target_address"])
    parser.add_argument("--max_duration", "-d", help="最大通勤分钟数", default=loader["max_duration"])
    parser.add_argument("--after_date", help="限定筛选指定日期之后", default=None)
    parser.add_argument("--min_budget", default=loader["min_budget"])
    parser.add_argument("--max_budget", default=loader["max_budget"])
    parser.add_argument("--include_only_from_personal", default=loader['include_only_from_personal'])
    parser.add_argument("--exclude_only_for_girls", "-e", help="男生选择此项以排除限女生房源",
                        default=loader["exclude_only_for_girls"])
    parser.add_argument("--exclude_unknown_duration", default=loader['exclude_unknown_duration'])
    parser.add_argument("--exclude_unknown_price", default=loader['exclude_unknown_price'])

    args = parser.parse_args()
    print(args)

    gaode = GaodeClient(city=args.city, target_address=args.target_address)
    if not gaode.target_coordinates:
        raise Exception("目标地址不合法")
    print("target coordinates: " + gaode.target_coordinates)
    gaode.dump_dict()

    """
    crawl
    """
    write_engine = WriteEngine(args.output_type)
    dc = DoubanCrawlerViaHTML(write_engine=write_engine)
    for group in args.groups.split(GROUP_SEPARATOR):
        date = datetime.now().strftime("%Y-%m-%d")
        print(f"crawling group of <{group}>")
        dc.crawl_topics_of_group(group, count=int(args.count))

        """
        analyze
        """
        if write_engine == WriteEngine.CSV:  # the analysis depends on dumped file
            analyze(
                filename=get_filename(group, get_cur_date()),
                city=args.city,
                target_address=args.target_address,
                max_duration=args.max_duration,
                after_date=args.after_date,
                include_only_from_personal=args.include_only_from_personal,
                exclude_only_for_girls=args.exclude_only_for_girls,
                exclude_unknown_price=args.exclude_unknown_price,
                exclude_unknown_duration=args.exclude_unknown_duration,

            )
