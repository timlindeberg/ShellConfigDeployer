from scd import colors


class Printer:
    def __init__(self, verbose_active):
        self.verbose_active = verbose_active
        self.prefix = colors.BOLD(colors.CYAN("SCD │ "))
        self.indent = "    "

    def verbose(self, output):
        if self.verbose_active:
            self.info(output)

    def info(self, output):
        if type(output) is str:
            print(self.prefix + output)
        elif type(output) is list:
            for line in output:
                self.info(self.indent + line)
