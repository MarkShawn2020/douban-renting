import os
import re
import pandas as pd

from src.gaode.client import GaodeClient

DATA_FROM_WECHAT_DIR = "data_from_wechat"
CITY = "北京"
TARGET_ADDRESS = "源创空间大厦"

gaode = GaodeClient(city=CITY, target_address=TARGET_ADDRESS)

files = [
    {
        "FILENAME": "./北漂租房登记（表一）.xlsx",
        "column_contact": "联系方式",
        "column_budget": "价位",
        "column_area": "       区域"
    },
    {
        "FILENAME": "./北漂租房登记（表二）.xlsx",
        "column_contact": "联系方式",
        "column_budget": "预算",
        "column_area": "居室.1"
    }
]

file = files[0]

# read excel
filepath = os.path.join(DATA_FROM_WECHAT_DIR, file["FILENAME"])
print("reading file from: " + filepath)
df_raw = pd.read_excel(filepath)

# drop specific nan
df = df_raw.dropna(subset=[file["column_contact"], file["column_budget"], file["column_area"]])
columns = list(filter(lambda x: not x.startswith("Unnamed"), df.columns))
df = df[columns]


# filter price
def find_price(s: str) -> int:
    s = re.search(r'\d+', str(s))
    return int(s.group()) if s else 0


df['price_base'] = df[file["column_budget"]].apply(find_price)
df = df.query("2000 <= price_base <= 3000")

# call gaode api and update distances
df2 = df.copy()
df2["work_minutes"] = df2[file["column_area"]].apply(
    lambda x: gaode.calc_transit_duration_from_coords(x))
gaode.dump_dict()  # update globals dict

# drop distance too far
df2 = df2.query("work_minutes < 60").copy()

# rank
df2['score'] = df2['price_base'] * df2['work_minutes']
df3 = df2
df3.sort_values(by=["score"], ascending=True, inplace=True)

# render
df3.style.background_gradient(cmap="Reds")
