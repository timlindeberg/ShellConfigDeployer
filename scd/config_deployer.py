import os
import textwrap
import zipfile

from scd.colors import *
from scd.constants import *


class DeploymentException(Exception):
    pass


class ConfigDeployer:
    MAX_FILES_TO_PRINT = 10

    def __init__(self, printer, host):
        self.printer = printer
        self.host = host

    def install_programs(self, programs):
        if len(programs) == 0:
            return

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
        exit_code, output = self.host.execute_command(lines)
        self._handle_result(exit_code, output,
                            lambda: self.printer.success("Successfully installed needed programs.", verbose=True),
                            lambda: self.printer.error("Failed to install programs."))

    def change_shell(self, shell):
        if not shell:
            return

        self.printer.info("Changing default shell to %s", shell)
        user = self.host.user
        command = ["sudo usermod -s $(which %s) %s" % (shell, user)]

        exit_code, output = self.host.execute_command(command)
        self._handle_result(exit_code, output,
                            lambda: self.printer.success("Successfully changed default shell to %s for user %s.",
                                                         shell, user, verbose=True),
                            lambda: self.printer.error("Failed to change shell to %s for user %s.", shell, user))

    def deploy_files(self, files):
        if len(files) == 0:
            return

        files_str = "file" if len(files) == 1 else "files"
        self.printer.info("Deploying %s " + files_str, len(files))
        if len(files) < self.MAX_FILES_TO_PRINT:
            self.printer.info([magenta(f[0]) for f in files])
        self._create_zip(files)
        home = "/home/%s" % self.host.user
        self.host.send_file(ZIP_PATH, "%s/%s" % (home, ZIP_NAME))
        os.remove(ZIP_PATH)
        commands = [
            "cd %s" % home,
            "sudo unzip -q -o -d / ./%s" % ZIP_NAME,
            "rm %s" % ZIP_NAME
        ]
        exit_code, output = self.host.execute_command(commands)

        self._handle_result(exit_code, output,
                            lambda: self.printer.success("Successfully deployed configuration files to host.",
                                                         verbose=True),
                            lambda: self.printer.error("Failed to deploy configuration files to host."))

    def _handle_result(self, exit_code, lines, on__success, on_error):
        success = exit_code == 0
        if success:
            self.printer.info("Output:", verbose=True)
            self.printer.info([magenta(l) if l.startswith("+") else l for l in lines], verbose=True)
            on__success()
        else:
            self.printer.error("Exit code %s:", exit_code)
            self.printer.error([magenta(l) if l.startswith("+") else red(l) for l in lines])
            on_error()
            raise DeploymentException

    def _create_zip(self, files):
        self.printer.info("Creating new zip file %s.", ZIP_PATH, verbose=True)
        zip_file = zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED)
        for from_, to in files:
            try:
                zip_file.write(from_, arcname=to)
            except PermissionError as e:
                self.printer.error("Could not add %s to deployment zip file.", from_)
                self.printer.error("    " + str(e))
                raise DeploymentException
        zip_file.close()
