import textwrap
import time
from datetime import datetime
from timeit import default_timer as timer

from scd.constants import TIME_FORMAT


def trim_multiline_str(string: str) -> str:
    return textwrap.dedent(string).strip()


def get_time(start_time: float) -> str:
    return "%.2f" % (timer() - start_time)


def date_to_time_stamp(date: str) -> float:
    return time.mktime(datetime.strptime(date, TIME_FORMAT).timetuple())


def time_stamp_to_date(time_stamp: float) -> str:
    return datetime.fromtimestamp(time_stamp).strftime(TIME_FORMAT)
