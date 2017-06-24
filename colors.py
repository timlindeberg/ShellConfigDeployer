CLEAR_ = '\033[0m'
BOLD_ = '\033[1m'
UNDERLINE_ = '\033[4m'
BLACK_ = '\033[30m'
RED_ = '\033[31m'
GREEN_ = '\033[32m'
YELLOW_ = '\033[33m'
BLUE_ = '\033[34m'
MAGENTA_ = '\033[35m'
CYAN_ = '\033[36m'
WHITE_ = '\033[37m'


def BOLD(s):
    return BOLD_ + str(s) + CLEAR_


def UNDERLINE(s):
    return UNDERLINE_ + str(s) + CLEAR_


def BLACK(s):
    return BLACK_ + str(s) + CLEAR_


def RED(s):
    return RED_ + str(s) + CLEAR_


def GREEN(s):
    return GREEN_ + str(s) + CLEAR_


def YELLOW(s):
    return YELLOW_ + str(s) + CLEAR_


def BLUE(s):
    return BLUE_ + str(s) + CLEAR_


def MAGENTA(s):
    return MAGENTA_ + str(s) + CLEAR_


def CYAN(s):
    return CYAN_ + str(s) + CLEAR_


def WHITE(s):
    return WHITE_ + str(s) + CLEAR_
