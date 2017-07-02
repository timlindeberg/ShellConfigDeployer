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

remove_color = True


def _color(c, s):
    if remove_color:
        return str(s)
    return c + str(s) + CLEAR


def bold(s):
    return _color(BOLD, s)


def underline(s):
    return _color(UNDERLINE, s)


def black(s):
    return _color(BLACK, s)


def red(s):
    return _color(RED, s)


def green(s):
    return _color(GREEN, s)


def yellow(s):
    return _color(YELLOW, s)


def blue(s):
    return _color(BLUE, s)


def magenta(s):
    return _color(MAGENTA, s)


def cyan(s):
    return _color(CYAN, s)


def white(s):
    return _color(WHITE, s)


def no_color(s):
    return str(s)
