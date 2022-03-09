import json
import os
import requests
import logging

from settings import GAODE_DIR

GAODE_GLOBAL_DIR = os.path.join(GAODE_DIR, "globals")


class GaodeBase:

    def __init__(self):
        self._key = os.environ["GAODE_KEY"]
        if not self._key:
            raise Exception("should set key for gaode in environment variables")

        self._s = requests.Session()
        self._s.params["key"] = self._key

        self._addr2coords_fp = os.path.join(GAODE_GLOBAL_DIR, "addr2coords.json")
        self._addr2coords_dict = {}

        self._dict_coords2name_fp = os.path.join(GAODE_GLOBAL_DIR, "coords2name.json")
        self._coords2name_dict = {}

        self._dict_coordspair2duration_fp = os.path.join(GAODE_GLOBAL_DIR, "coordspair2duration.json")
        self._coordspair2duration_dict = {}

        self.load_dict()

    # 编码
    def _get_coords_from_addr(self, addr: str, city: str):
        logging.debug(f"getting addr of <{addr}>")
        if addr not in self._addr2coords_dict:
            res = self._s.get('https://restapi.amap.com/v3/geocode/geo', params={
                "city": city,
                "address": addr,
            })
            logging.info(f"address: {addr}, fetching url: {res.url}")

            assert res.status_code == 200
            result = res.json()
            count = int(result.get('count', 0))
            if count == 0:
                logging.warning(f"should have result when getting coords from addr: {addr}, however got: {result}")
                self._addr2coords_dict[addr] = None
            else:
                if count > 1:
                    logging.warning("more than 1 result, select the first")
                loc = result["geocodes"][0]["location"]
                self._addr2coords_dict[addr] = loc

        return self._addr2coords_dict[addr]

    def get_addr_name_from_coords(self, coords: str):
        logging.debug(f"getting addr name from coords of <{coords}>")
        if not coords:
            logging.debug("skip getting addr name from coords since it's empty")
            return None
        if coords not in self._coords2name_dict:
            logging.debug(f"fetching coords of {coords} from gaode api")
            res = self._s.get('https://restapi.amap.com/v3/geocode/regeo', params={
                "location": coords,
            })

            assert res.status_code == 200
            result = res.json()
            self._coords2name_dict[coords] = result['regeocode']['formatted_address']
        return self._coords2name_dict[coords]

    # 步行
    def _calc_walking_duration(self, from_loc, to_loc):
        res = self._s.get('https://restapi.amap.com/v3/direction/walking',
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
    def _calc_transit_duration_between_coords(self, from_coords, to_coords, city):
        if not to_coords:
            raise Exception("to coords must exist")
        if not from_coords:
            return None

        key = from_coords + "-" + to_coords

        if key not in self._coordspair2duration_dict:
            res = self._s.get('https://restapi.amap.com/v3/direction/transit/integrated',
                              params={
                                  "origin": from_coords,
                                  "destination": to_coords,
                                  "strategy": 3,  # 0：最快捷模式, 1：最经济模式, 2：最少换乘模式, 3：最少步行模式, 5：不乘地铁模式
                                  "city": city
                              })
            result = res.json()
            count = int(result.get("count", 0))
            if count == 0:
                logging.info("not found any transit solution, trying walking ones")
                logging.info(result)
                self._coordspair2duration_dict[key] = self._calc_walking_duration(from_coords, to_coords)
            else:
                self._coordspair2duration_dict[key] = int(
                    float(result["route"]["transits"][0]["duration"]) / 60)  # minutes
        return self._coordspair2duration_dict[key]

    # 通勤计算
    def _calc_transit_duration_between_addrs(self, from_addr, to_addr, city):
        from_loc = self._get_coords_from_addr(from_addr, city)
        to_loc = self._get_coords_from_addr(to_addr, city)
        return self._calc_transit_duration_between_coords(from_loc, to_loc, city)

    def load_dict(self):
        if os.path.exists(self._addr2coords_fp):
            self._addr2coords_dict = json.load(open(self._addr2coords_fp))
        if os.path.exists(self._dict_coords2name_fp):
            self._coords2name_dict = json.load(open(self._dict_coords2name_fp))
        if os.path.exists(self._dict_coordspair2duration_fp):
            self._coordspair2duration_dict = json.load(open(self._dict_coordspair2duration_fp))

        print(f"loaded "
              f"{len(self._addr2coords_dict)} addr2coords, "
              f"{len(self._coords2name_dict)} coords2name, "
              f"{len(self._coordspair2duration_dict)} coordspair2duration")

    def dump_dict(self):

        if self._addr2coords_dict:  # avoid override by an empty dict
            json.dump(self._addr2coords_dict, open(self._addr2coords_fp, "w"), ensure_ascii=False, indent=2)
        if self._coords2name_dict:  # avoid override by an empty dict
            json.dump(self._coords2name_dict, open(self._dict_coords2name_fp, "w"), ensure_ascii=False, indent=2)
        if self._coordspair2duration_dict:  # avoid override by an empty dict
            json.dump(self._coordspair2duration_dict, open(self._dict_coordspair2duration_fp, "w"), ensure_ascii=False,
                      indent=2)
