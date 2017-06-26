from scd import colors
from scd import constants


class Printer:
    def __init__(self, verbose_active):
        self.verbose_active = verbose_active
        self.prefix = colors.bold(colors.cyan("SCD │ "))
        self.indent = "    "

    def info(self, output, *items, verbose=False):
        if not self.verbose_active and verbose:
            return

        self._print(output, items, colors.no_color, colors.magenta)

    def success(self, output, *items):
        def green_bold(s): return colors.green(colors.bold(s))

        self._print(output, items, green_bold, green_bold)

    def error(self, output, *items):
        def red_bold(s): return colors.red(colors.bold(s))

        self._print(output, items, colors.red, red_bold)

    def _print(self, output, items, str_color, item_color):
        if type(output) is str:
            self._print_string(output, items, str_color, item_color)
        elif type(output) is list:
            for line in output:
                print(self.prefix + self.indent + str_color(line))

    def _print_string(self, output, items, str_color, item_color):
        print(self.prefix, end='')
        i = 0
        for s in output.split("%s"):
            print(str_color(s), end='')
            if i < len(items):
                item = str(items[i]).replace(constants.HOME, '~')
                print(item_color(item), end='')
                i += 1
        print()
