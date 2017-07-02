import os.path
import sys
from fnmatch import fnmatch

from scd.constants import *


class HostConfiguration:
    def __init__(self, printer, settings, host_status):
        self.files = self._modified_files(settings, host_status, printer)
        programs = set(settings.programs + ([settings.shell] if settings.shell else []))
        self.programs = [prog for prog in programs if prog not in host_status["installed_programs"]]
        self.shell = settings.shell
        if host_status.get("shell") == self.shell:
            self.shell = None

        printer.info("Found %s files to deploy and %s programs to install.",
                     len(self.files), len(self.programs), verbose=True)

    def is_empty(self):
        return len(self.files) == 0 and len(self.programs) == 0 and not self.shell

    @staticmethod
    def _modified_files(settings, host_status, printer):
        HostConfiguration._modified_files.res = []

        last_deployment = host_status["last_deployment"]

        def modified(file, check_timestamp):
            for ignored in settings.ignored_files:
                if fnmatch(file, ignored):
                    return
            if os.path.isdir(file):
                for f in os.listdir(file):
                    modified(file + "/" + f, check_timestamp)
                return

            if not check_timestamp or os.path.getctime(file) > last_deployment:
                modified.res.append(os.path.abspath(file))

        modified.res = []

        for f in settings.files:
            file = HOME + "/" + f
            if not (os.path.isfile(file) or os.path.isdir(file)):
                printer.error("No such file or directory %s.", file)
                sys.exit(1)
            check_timestamp = f in host_status["deployed_files"]
            if check_timestamp:
                printer.info("Checking timestamp of %s", f, verbose=True)
            else:
                printer.info("Adding new item %s", f, verbose=True)

            modified(file, check_timestamp)

        return modified.res
