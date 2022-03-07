import os
import pandas as pd

from gaode import get_coords_from_addr, get_transit_duration_between_coords, \
    get_addr_name_from_coords, TARGET_ADDRESS
from globals.utils import dump_dict

DATA_FROM_DOUBAN_DIR = "data_from_douban"
filename = '2022-03-02-zhufang.csv'
filepath = os.path.join(DATA_FROM_DOUBAN_DIR, filename)
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
    df['addr_coords'] = df.post_title.apply(get_coords_from_addr)
finally:
    dump_dict()

# get addr from coords
print("getting addr name from coords")
try:
    df["addr_name"] = df["addr_coords"].apply(get_addr_name_from_coords)
finally:
    dump_dict()

# get duration between coords
print("getting distance from coords")
try:
    df["transit_minutes"] = df["addr_coords"].apply(
        lambda x: get_transit_duration_between_coords(x, get_coords_from_addr(TARGET_ADDRESS)))
finally:
    dump_dict()

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
