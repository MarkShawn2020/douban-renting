import os
import pandas as pd

from src.gaode.client import GaodeClient

DATA_FROM_DOUBAN_DIR = "data_from_douban"
FILENAME = '2022-03-02-zhufang.csv'
CITY = "北京"
TARGET_ADDRESS = "源创空间大厦"

gaode = GaodeClient(city=CITY, target_address=TARGET_ADDRESS)

filepath = os.path.join(DATA_FROM_DOUBAN_DIR, FILENAME)
print("reading file from: " + filepath)
df = pd.read_csv(filepath)

# convert response_latest_time format into datetime
df.response_latest_time = pd.to_datetime(df.response_latest_time)

# filter datetime
df = df.query("'2022-02-25' < response_latest_time")


# filter personal
df = df[df.post_title.apply(lambda s: "女生" not in s and ("个人" in s or "直租" in s or "转租" in s))]
print("shape: ", df.shape)

# get coords from title
print("getting coords from title")
try:
    df['addr_coords'] = df.post_title.apply(gaode.get_coords_from_addr)
finally:
    gaode.dump_dict()

# get addr from coords
print("getting addr name from coords")
try:
    df["addr_name"] = df["addr_coords"].apply(gaode.get_addr_name_from_coords)
finally:
    gaode.dump_dict()

# get duration between coords
print("getting distance from coords")
try:
    df["transit_minutes"] = df["addr_coords"].apply(
        lambda x: gaode.calc_transit_duration_from_coords(x))
finally:
    gaode.dump_dict()

# filter duration
print("filter duration")
df = df.query("transit_minutes < 60")

# sort
print('sort')
df = df.sort_values(by=["transit_minutes"], ascending=True)

# dump
print("dump")
df.to_csv(filepath.replace(".csv", "_filter.csv"), encoding="utf-8")

df
