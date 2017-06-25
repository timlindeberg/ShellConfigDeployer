import shutil

from scd import colors


class Printer:
    def divider(self, verbose=False):
        if verbose and not self.verbose_active:
            return

        if self.divider_string == '':
            columns, rows = shutil.get_terminal_size((55, 20))
            prefix_len = 5
            width = columns - prefix_len
            self.divider_string = width * "─"
        print(colors.BOLD(colors.CYAN("SCD ├" + self.divider_string)))

    def __init__(self, verbose_active):
        self.verbose_active = verbose_active
        self.divider_string = ''
        self.prefix = colors.BOLD(colors.CYAN("SCD │ "))

    def verbose(self, txt):
        if self.verbose_active:
            self.info(txt)

    def info(self, txt):
        print(self.prefix + txt)
