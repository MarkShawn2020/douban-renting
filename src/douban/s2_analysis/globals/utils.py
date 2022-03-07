import json
import os


def load_dict():
    global ADDR2COORDS_DICT, COORDS2NAME_DICT, COORDSPAIR2DURATION_DICT
    if os.path.exists(dict_title2coords_fp):
        ADDR2COORDS_DICT = json.load(open(dict_title2coords_fp))
    if os.path.exists(dict_coords2name_fp):
        COORDS2NAME_DICT = json.load(open(dict_coords2name_fp))
    if os.path.exists(dict_coordspair2duration_fp):
        COORDSPAIR2DURATION_DICT = json.load(open(dict_coordspair2duration_fp))
    # print({"ADDR2COORDS_DICT": ADDR2COORDS_DICT, "COORDS2NAME_DICT": COORDS2NAME_DICT, "COORDSPAIR2DURATION_DICT": COORDSPAIR2DURATION_DICT})


def dump_dict():
    global ADDR2COORDS_DICT, COORDS2NAME_DICT, COORDSPAIR2DURATION_DICT
    json.dump(ADDR2COORDS_DICT, open(dict_title2coords_fp, "w"), ensure_ascii=False, indent=2)
    json.dump(COORDS2NAME_DICT, open(dict_coords2name_fp, "w"), ensure_ascii=False, indent=2)
    json.dump(COORDSPAIR2DURATION_DICT, open(dict_coordspair2duration_fp, "w"), ensure_ascii=False, indent=2)


GLOBAL_DIR = os.path.dirname(__file__)
ADDR2COORDS_DICT = COORDS2NAME_DICT = COORDSPAIR2DURATION_DICT = {}

dict_title2coords_fp = os.path.join(GLOBAL_DIR, "ADDR2COORDS_DICT.json")
dict_coords2name_fp = os.path.join(GLOBAL_DIR, "COORDS2NAME_DICT.json")
dict_coordspair2duration_fp = os.path.join(GLOBAL_DIR, "COORDSPAIR2DURATION_DICT.json")

print("globals dict of title to coords path: " + dict_title2coords_fp)
print("globals dict of coords to name path : " + dict_coords2name_fp)
print("globals dict of coords pair to distance path: " + dict_coordspair2duration_fp)
