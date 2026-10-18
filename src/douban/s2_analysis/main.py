import os

import pandas as pd

from douban.s2_analysis.rules import parse_price, is_seeking, is_from_personal, is_only_for_girls
from douban.settings import DOUBAN_DATA_DIR
from douban.utils import get_filename, get_cur_date
from gaode.client import GaodeClient


def analyze(filename: str, city: str, target_address: str, max_duration: int,
            min_budget: int = 3000,
            max_budget: int = 6000,
            after_date: str = None,
            include_only_from_personal: bool = False,
            exclude_only_for_girls: bool = False,
            exclude_unknown_duration: bool = False,
            exclude_unknown_price: bool = False
            ):
    gaode = GaodeClient(city=city, target_address=target_address)

    filepath = os.path.join(DOUBAN_DATA_DIR, filename)
    print("reading file from: " + filepath)
    df = pd.read_csv(filepath)
    print("shape: ", df.shape)

    # convert response_latest_time format into datetime
    df.response_latest_time = pd.to_datetime(df.response_latest_time)

    df["possible_price"] = df.post_title.apply(parse_price)

    # filter price
    def filter_price(price):
        if pd.isna(price):
            return not exclude_unknown_price

        return min_budget <= price <= max_budget

    df = df[df["possible_price"].apply(filter_price)]

    # filter datetime
    if after_date:
        print(f"include only dates after: {after_date}")
        df = df.query(f"'{after_date}' < response_latest_time")

    print("exclude those are asking for rent")
    df = df[~df.post_title.apply(is_seeking)]

    if include_only_from_personal:
        print("only include those are from personal")
        df = df[df.post_title.apply(is_from_personal)]

    # filter personal
    if exclude_only_for_girls:
        print(f"exclude only-for-girls")
        df = df[~df.post_title.apply(is_only_for_girls)]

    # locate title via poi search
    try:
        print("locating title via poi search")
        df = df.copy()
        pois = df["post_title"].apply(lambda t: gaode.search_poi(t, city) or {})
        df['addr_coords'] = pois.apply(lambda p: p.get("location"))
        df["addr_name"] = pois.apply(lambda p: " ".join(filter(None, [p.get("adname"), p.get("name")])) or None)
    finally:
        gaode.dump_dict()

    # calculate duration between coords
    print("calculate duration between coords")
    try:
        df = df.copy()
        df["transit_minutes"] = df["addr_coords"].apply(
            lambda x: gaode.calc_transit_duration_from_coords(x if isinstance(x, str) else None))
        # 公交与步行都无方案时返回 -1，视为未知
        df.loc[df["transit_minutes"] < 0, "transit_minutes"] = None
    finally:
        gaode.dump_dict()

    # filter duration
    print(f"filter duration below {max_duration} minutes")
    f = f"transit_minutes < {max_duration}"
    if not exclude_unknown_duration:
        f += "| transit_minutes.isnull()"
    df = df.query(f)

    print("shape after filter: ", df.shape)

    # sort
    print('sort')
    df = df.sort_values(by=["transit_minutes"], ascending=True)

    # dump
    filtered_filename = filepath.replace(".csv", f"_{target_address}.csv")
    print(f"dump into new csv file: {filtered_filename}")
    df.to_csv(filtered_filename, encoding="utf-8")


if __name__ == '__main__':
    analyze(get_filename("beijingzufang", get_cur_date()),
            city="北京", target_address="凤凰汇购物中心",
            max_duration=30,
            after_date=None,
            exclude_only_for_girls=False,
            exclude_unknown_duration=True,
            exclude_unknown_price=True
            )
