#!/usr/bin/env python
# coding: utf-8

import os
import requests
import logging

from globals.utils import load_dict, dump_dict, \
    ADDR2COORDS_DICT, COORDS2NAME_DICT, COORDSPAIR2DURATION_DICT

logger = logging.getLogger("root")
logger.setLevel(logging.INFO)

KEY = os.environ["GAODE_KEY"]
print("key: " + KEY)
if not KEY:
    raise Exception("should set key for gaode in environment variables")
CITY = "北京"  # specify city, otherwise search the whole country
TARGET_ADDRESS = "源创空间大厦"

s = requests.Session()
s.params["key"] = KEY


# 编码
def get_coords_from_addr(addr: str):
    # logging.info(f"getting addr of <{addr}>")
    if addr not in ADDR2COORDS_DICT:
        res = s.get('https://restapi.amap.com/v3/geocode/geo', params={
            "city": CITY,
            "address": addr,
        })
        logging.info(f"fetching url: {res.url}")

        assert res.status_code == 200
        result = res.json()
        count = int(result.get('count', 0))
        if count == 0:
            logging.error(f"should have result, however: {result}")
            ADDR2COORDS_DICT[addr] = None
        else:
            if count > 1:
                logging.warning("more than 1 result, select the first")
            loc = result["geocodes"][0]["location"]
            ADDR2COORDS_DICT[addr] = loc

    return ADDR2COORDS_DICT[addr]


def get_addr_name_from_coords(coords: str):
    # logging.info(f"getting addr of <{addr}>")
    if not coords:
        return None
    if coords not in COORDS2NAME_DICT:
        logging.debug(f"fetching coords of {coords} from gaode api")
        res = s.get('https://restapi.amap.com/v3/geocode/regeo', params={
            "location": coords,
        })

        assert res.status_code == 200
        result = res.json()
        COORDS2NAME_DICT[coords] = result['regeocode']['formatted_address']
    return COORDS2NAME_DICT[coords]


# 步行
def get_walking_duration(from_loc, to_loc):
    res = s.get('https://restapi.amap.com/v3/direction/walking',
                params={
                    "origin": from_loc,
                    "destination": to_loc,
                    "output": "json",
                })
    result = res.json()
    count = int(result.get("count", 0))
    if count == 0:
        logging.warning("not found any walking solution")
        logging.warning(result)
        return -1
    return int(float(result["route"]["paths"][0]["duration"]) / 60)  # minutes


# 通勤计算
def get_transit_duration_between_coords(from_coords, to_coords):
    if not to_coords:
        raise Exception("to coords must exist")
    if not from_coords:
        return None

    key = from_coords + "-" + to_coords

    if key not in COORDSPAIR2DURATION_DICT:
        res = s.get('https://restapi.amap.com/v3/direction/transit/integrated',
                    params={
                        "origin": from_coords,
                        "destination": to_coords,
                        "strategy": 3,  # 0：最快捷模式, 1：最经济模式, 2：最少换乘模式, 3：最少步行模式, 5：不乘地铁模式
                        "city": CITY
                    })
        result = res.json()
        count = int(result.get("count", 0))
        if count == 0:
            logging.info("not found any transit solution, trying walking ones")
            logging.info(result)
            COORDSPAIR2DURATION_DICT[key] = get_walking_duration(from_coords, to_coords)
        else:
            COORDSPAIR2DURATION_DICT[key] = int(float(result["route"]["transits"][0]["duration"]) / 60)  # minutes
    return COORDSPAIR2DURATION_DICT[key]


# 通勤计算
def get_transit_duration_between_addrs(from_addr, to_addr):
    from_loc = get_coords_from_addr(from_addr)
    to_loc = get_coords_from_addr(to_addr)
    return get_transit_duration_between_coords(from_loc, to_loc)


load_dict()
