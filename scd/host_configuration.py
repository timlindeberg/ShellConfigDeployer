import os
import sys
from fnmatch import fnmatch
from typing import List, Set, Optional

from scd.data_structs import StatusData
from scd.printer import Printer
from scd.settings import Settings, FileData
from scd.utils import date_to_time_stamp


class HostConfiguration:
    def __init__(self, printer: Printer, settings: Settings, status: StatusData):
        self.settings = settings
        self.status = status
        self.printer = printer

        self.programs = self._programs_to_install()
        self.files = self._files_to_deploy()
        self.scripts = self._scripts_to_run()
        self.shell = self._shell_to_change()

        self.printer.info("Found %s files to deploy, %s programs to install and %s scripts to run.", len(self.files), len(self.programs), len(self.scripts), verbose=True)

    def is_empty(self) -> bool:
        return len(self.files) == 0 and len(self.programs) == 0 and len(self.scripts) == 0 and not self.shell

    def _programs_to_install(self) -> List[str]:
        shell = self.settings.shell
        programs = set(self.settings.programs)
        if shell:
            programs.add(shell)
        return [p for p in programs if p not in self.status.installed_programs]

    def _files_to_deploy(self) -> Set[FileData]:
        files: Set[FileData] = set()

        for file in self.settings.files:
            from_path = file.from_path
            to_path = file.to_path
            should_check_timestamp = from_path in self.status.deployed_files
            from_path = os.path.expanduser(from_path)
            to = self._expand_remote_user(to_path)

            if not (os.path.isfile(from_path) or os.path.isdir(from_path)):
                self.printer.error("No such file or directory %s.", from_path)
                sys.exit(1)

            msg = "Checking timestamp of %s." if should_check_timestamp else "Adding new item %s."
            self.printer.info(msg, from_path, verbose=True)
            self._add_files(from_path, to, should_check_timestamp, files)

        return files

    def _scripts_to_run(self) -> List[str]:
        scripts = self.settings.scripts
        return [s for s in scripts if s not in self.status.executed_scripts]

    def _shell_to_change(self) -> Optional[str]:
        shell = self.settings.shell
        return shell if self.status.shell != shell else None

    def _add_files(self, from_path: str, to_path: str, should_check_timestamp: bool, files: Set[FileData]) -> None:
        def _files(file) -> None:
            for ignored in self.settings.ignored_files:
                if fnmatch(file, ignored):
                    return

            if os.path.isdir(file):
                for f in os.listdir(file):
                    _files(f"{file}/{f}")
                return

            timestamp = date_to_time_stamp(self.status.last_deployment)
            if not should_check_timestamp or os.path.getctime(file) > timestamp:
                path = os.path.abspath(file)
                path_to = path.replace(from_path, to_path)
                files.add(FileData(path, path_to))

        _files(from_path)

    def _expand_remote_user(self, path: str) -> str:
        if not path.startswith("~"):
            return path
        return f"/home/{self.settings.user}{path[1:]}"
