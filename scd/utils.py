import textwrap
from timeit import default_timer as timer


def trim_multiline_str(string):
    return textwrap.dedent(string).strip()


def get_time(start_time):
    return "%.2f" % (timer() - start_time)

