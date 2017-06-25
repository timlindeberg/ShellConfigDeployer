CLEAR = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
BLACK = '\033[30m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
MAGENTA = '\033[35m'
CYAN = '\033[36m'
WHITE = '\033[37m'


def bold(s):
    return BOLD + str(s) + CLEAR


def underline(s):
    return UNDERLINE + str(s) + CLEAR


def black(s):
    return BLACK + str(s) + CLEAR


def red(s):
    return RED + str(s) + CLEAR


def green(s):
    return GREEN + str(s) + CLEAR


def yellow(s):
    return YELLOW + str(s) + CLEAR


def blue(s):
    return BLUE + str(s) + CLEAR


def magenta(s):
    return MAGENTA + str(s) + CLEAR


def cyan(s):
    return CYAN + str(s) + CLEAR


def white(s):
    return WHITE + str(s) + CLEAR


def no_color(s):
    return str(s)
