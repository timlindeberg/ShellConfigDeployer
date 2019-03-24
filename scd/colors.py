CLEAR = "\033[0m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

no_color = True


def bold(s: str):
    return _color(BOLD, s)


def underline(s: str):
    return _color(UNDERLINE, s)


def black(s: str):
    return _color(BLACK, s)


def red(s: str):
    return _color(RED, s)


def green(s: str):
    return _color(GREEN, s)


def yellow(s: str):
    return _color(YELLOW, s)


def blue(s: str):
    return _color(BLUE, s)


def magenta(s: str):
    return _color(MAGENTA, s)


def cyan(s: str):
    return _color(CYAN, s)


def white(s: str):
    return _color(WHITE, s)


def empty_color(s: str):
    return str(s)


def _color(c: str, s: str):
    return str(s) if no_color else c + str(s) + CLEAR
