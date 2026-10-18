import logging
import re
from typing import Optional


def parse_price(title: str) -> Optional[float]:
    nums = [int(i) for i in re.findall(r"\d+", title) if len(i) == 4]
    if not nums:
        return None
    if len(nums) > 1:
        logging.warning(f"should only one price parsed from title, while there are {len(nums)}: {nums}")
    return sum(nums) / len(nums)


def is_seeking(title: str) -> bool:
    """求租帖，不是房源"""
    return "求" in title


def is_from_personal(title: str) -> bool:
    return "个人" in title or "直租" in title or "转租" in title


def is_only_for_girls(title: str) -> bool:
    return "女生" in title or "限女" in title
