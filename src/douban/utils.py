from datetime import datetime


def get_filename(group: str, date: str):
    return f"{date}-{group}.csv"


def get_cur_date():
    return datetime.now().strftime("%Y-%m-%d")
