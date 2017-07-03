import os
import os.path
import sys
from fnmatch import fnmatch


class HostConfiguration:
    def __init__(self, printer, settings, host_status):
        self.settings = settings
        self.host_status = host_status
        self.printer = printer

        self.programs = self._programs_to_install()
        self.files = self._files_to_deploy()
        self.scripts = self._scripts_to_run()
        self.shell = self._shell_to_change()

        printer.info("Found %s files to deploy, %s programs to install and %s scripts to run.",
                     len(self.files), len(self.programs), len(self.scripts), verbose=True)

    def is_empty(self):
        return len(self.files) == 0 and len(self.programs) == 0 and len(self.scripts) == 0 and not self.shell

    def _programs_to_install(self):
        shell = self.settings.shell
        programs = set(self.settings.programs)
        if shell:
            programs.add(shell)
        return [p for p in programs if p not in self.host_status["installed_programs"]]

    def _files_to_deploy(self):
        files = set()

        for from_, to in self.settings.files:
            should_check_timestamp = from_ in self.host_status["deployed_files"]
            from_ = os.path.expanduser(from_)
            to = self._expand_remote_user(to)

            if not (os.path.isfile(from_) or os.path.isdir(from_)):
                self.printer.error("No such file or directory %s.", from_)
                sys.exit(1)

            msg = "Checking timestamp of %s." if should_check_timestamp else "Adding new item %s."
            self.printer.info(msg, from_, verbose=True)
            self._add_files(from_, to, should_check_timestamp, files)

        return files

    def _scripts_to_run(self):
        scripts = self.settings.scripts
        return [s for s in scripts if s not in self.host_status["executed_scripts"]]

    def _shell_to_change(self):
        shell = self.settings.shell
        return shell if self.host_status.get("shell") != shell else None

    def _add_files(self, original_path, to, should_check_timestamp, files):
        def _files(file):
            for ignored in self.settings.ignored_files:
                if fnmatch(file, ignored):
                    return

            if os.path.isdir(file):
                for f in os.listdir(file):
                    _files(file + "/" + f)
                return

            if not should_check_timestamp or os.path.getctime(file) > self.host_status["last_deployment"]:
                path = os.path.abspath(file)
                path_to = path.replace(original_path, to)
                files.add((path, path_to))

        _files(original_path)

    def _expand_remote_user(self, path):
        if not path.startswith("~"):
            return path
        user = self.settings.user
        return f"/home/{user}" + path[1:]
