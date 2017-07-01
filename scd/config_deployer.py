import os
import sys
import textwrap
import zipfile

from scd.colors import *
from scd.constants import *


class ConfigDeployer:
    MAX_FILES_TO_PRINT = 10

    def __init__(self, printer, host_communicator):
        self.printer = printer
        self.host_communicator = host_communicator

    def install_programs(self, programs):
        if len(programs) == 0:
            return True

        self.printer.info("Installing " + ", ".join([magenta(p) for p in programs]))

        select_package_manager = """
                if [ -f /etc/redhat-release ]; then
                    PACKAGE_MANAGER="yum"
                    ANSWER_YES="-y"
                elif [ -f /etc/arch-release ]; then
                    PACKAGE_MANAGER="pacman"
                    ANSWER_YES="--noconfirm"
                elif [ -f /etc/gentoo-release ]; then
                    PACKAGE_MANAGER="emerge"
                    ANSWER_YES=""
                elif [ -f /etc/SuSE-release ]; then
                    PACKAGE_MANAGER="zypper"
                    ANSWER_YES="-n"
                elif [ -f /etc/debian_version ]; then
                    PACKAGE_MANAGER="apt-get"
                    ANSWER_YES="-y"
                elif [ "$(uname)" == "Darwin" ]; then
                    PACKAGE_MANAGER="brew"
                    ANSWER_YES=""
                else
                    echo "Unsupported distribution."
                    exit 1
                fi
            """

        lines = textwrap.dedent(select_package_manager).strip().split("\n")
        lines += ["sudo $PACKAGE_MANAGER $ANSWER_YES install " + " ".join(programs)]
        exit_code, output = self.host_communicator.execute_command(lines)
        return self._result(exit_code, output,
                            lambda: self.printer.error("Failed to install programs."))

    def change_shell(self, shell):
        if not shell:
            return True

        self.printer.info("Changing default shell to %s", shell)
        user = self.host_communicator.user
        command = ["sudo usermod -s $(which %s) %s" % (shell, user)]

        exit_code, output = self.host_communicator.execute_command(command)
        return self._result(exit_code, output,
                            lambda: self.printer.error("Failed to change shell to %s for user %s.", shell, user))

    def deploy_files(self, files):
        if len(files) == 0:
            return True

        self.printer.info("Deploying %s file(s)", len(files))
        if len(files) < self.MAX_FILES_TO_PRINT:
            self.printer.info([magenta(f) for f in files])
        self._create_zip(files)
        home = "/home/%s" % self.host_communicator.user
        self.host_communicator.send_file(ZIP_PATH, "%s/%s" % (home, ZIP_NAME))
        os.remove(ZIP_PATH)
        commands = [
            "cd %s" % home,
            "unzip -q -o ./%s" % ZIP_NAME,
            "rm %s" % ZIP_NAME
        ]
        exit_code, output = self.host_communicator.execute_command(commands)

        return self._result(exit_code, output,
                            lambda: self.printer.error("Failed to deploy configuration files to host."))

    def _result(self, exit_code, lines, on_error):
        success = exit_code == 0
        if success:
            self.printer.info("Output:", verbose=True)
            self.printer.info([magenta(l) if l.startswith("+") else l for l in lines], verbose=True)
        else:
            on_error()
            self.printer.error("Exit code %s:", exit_code)
            self.printer.error([magenta(l) if l.startswith("+") else red(l) for l in lines])
        return success

    def _create_zip(self, files):
        self.printer.info("Creating new zip file %s.", ZIP_PATH, verbose=True)
        home = HOME + "/"
        zip_file = zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED)
        for f in files:
            arcname = f if not f.startswith(home) else f[len(home):]
            try:
                zip_file.write(f, arcname=arcname)
            except PermissionError as e:
                self.printer.error("Could not add %s to deployment zip file.", f)
                self.printer.error("    " + str(e))
                sys.exit(1)
        zip_file.close()
