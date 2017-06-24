import shutil

from formatting import colors


class Printer:
    def divider(self, verbose=False):
        if verbose and not self.verbose_active:
            return

        if self.divider_string == '':
            columns, rows = shutil.get_terminal_size((56, 20))
            prefix_len = 6
            width = columns - prefix_len
            self.divider_string = colors.BOLD(colors.CYAN(width * "─"))
        self.info(self.divider_string)

    def __init__(self, verbose_active):
        self.verbose_active = verbose_active
        self.divider_string = ''
        self.prefix = colors.BOLD(colors.CYAN("SCD │ "))

    def verbose(self, txt):
        if self.verbose_active:
            self.info(txt)

    def info(self, txt):
        print(self.prefix + txt)
