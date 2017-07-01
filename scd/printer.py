from scd import colors
from scd.constants import *


class Printer:
    def __init__(self, verbose_active=False):
        self.verbose_active = verbose_active
        self.prefix = colors.bold(colors.cyan("SCD │ "))
        self.indent = "    "

    def info(self, output, *items, verbose=False, end="\n"):
        if not self.verbose_active and verbose:
            return

        self._print(output, items, colors.no_color, colors.magenta, end)

    def success(self, output, *items, end="\n"):
        def green_bold(s): return colors.green(colors.bold(s))

        self._print(output, items, green_bold, green_bold, end)

    def error(self, output, *items, end="\n"):
        def red_bold(s): return colors.red(colors.bold(s))

        self._print(output, items, colors.red, red_bold, end)

    def _print(self, output, items, str_color, item_color, end):
        if type(output) is str:
            self._print_string(output, items, str_color, item_color, end)
        elif type(output) is list:
            for line in output:
                self._print_string(self.indent + line, [], str_color, item_color, end)

    def _print_string(self, output, items, str_color, item_color, end):
        print(self.prefix, end="")
        i = 0
        for s in output.split("%s"):
            print(str_color(s.replace(HOME, "~")), end="")
            if i < len(items):
                item = str(items[i]).replace(HOME, "~")
                print(item_color(item), end="")
                i += 1
        print(end=end, flush=True)
