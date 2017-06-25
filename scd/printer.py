from scd import colors


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
        self._print(output, items, colors.green, lambda s: colors.green(colors.bold(s)))

    def error(self, output, *items):
        self._print(output, items, colors.red, lambda s: colors.red(colors.bold(s)))

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
                print(item_color(items[i]), end='')
                i += 1
        print()
