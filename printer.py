import colors

PREFIX = colors.BOLD_ + colors.CYAN_ + "SCD | " + colors.CLEAR_


class Printer():
    def __init__(self, isVerbose):
        self.isVerbose = isVerbose

    def verbose(self, txt):
        if self.isVerbose:
            self.info(txt)

    def info(self, txt):
        print(PREFIX + txt)
