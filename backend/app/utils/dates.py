"""
Date and Range Utilities
"""

from datetime import date, datetime, timedelta, timezone
from typing import Tuple


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_today_utc() -> date:
    return datetime.now(timezone.utc).date()


def get_date_range(range_key: str) -> Tuple[date, date]:
    """
    Returns (start_date, end_date) for named ranges: 7d, 14d, 30d, 90d, mtd.
    """
    today = get_today_utc()
    if range_key == "7d":
        return today - timedelta(days=7), today
    elif range_key == "14d":
        return today - timedelta(days=14), today
    elif range_key == "30d":
        return today - timedelta(days=30), today
    elif range_key == "90d":
        return today - timedelta(days=90), today
    elif range_key == "mtd":
        return today.replace(day=1), today
    return today - timedelta(days=30), today

