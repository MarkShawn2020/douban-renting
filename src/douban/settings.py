import os

from settings import DOUBAN_DIR

DOUBAN_DATA_DIR = os.path.join(DOUBAN_DIR, "data")
if not os.path.exists(DOUBAN_DATA_DIR):
    os.mkdir(DOUBAN_DATA_DIR)
