import os
import textwrap
import tarfile

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

        start = timer()

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
        time = get_time(start)
        self._handle_result(
            exit_code,
            output,
            lambda: self.printer.success("Successfully installed needed programs in %s s.", time, verbose=True),
            lambda: self.printer.error("Failed to install programs."))
        if exit_code != 0:
            raise DeploymentException

    def change_shell(self, shell):
        if not shell:
            return

        start = timer()
        self.printer.info("Changing default shell to %s", shell)
        user = self.host.user
        command = [f"sudo usermod -s $(which {shell}) {user}"]

        exit_code, output = self.host.execute_command(command)
        time = get_time(start)
        self._handle_result(
            exit_code,
            output,
            lambda: self.printer.success("Successfully changed default shell to %s for user %s in %s s.", shell, user, time, verbose=True),
            lambda: self.printer.error("Failed to change shell to %s for user %s.", shell, user))
        if exit_code != 0:
            raise DeploymentException

    def deploy_files(self, files):
        if len(files) == 0:
            return

        start = timer()
        files_str = "file" if len(files) == 1 else "files"
        self.printer.info("Deploying %s " + files_str, len(files))
        if len(files) < self.MAX_FILES_TO_PRINT:
            self.printer.info([magenta(f[0]) for f in files])
        self._create_tar(files)
        home = "/home/%s" % self.host.user
        remote_tar_path = f"{home}/{TAR_NAME}"
        self.host.send_file(TAR_PATH, remote_tar_path)
        os.remove(TAR_PATH)
        commands = [
            f"tar -xzf {remote_tar_path} -C /",
            f"rm {remote_tar_path}"
        ]
        exit_code, output = self.host.execute_command(commands)
        time = get_time(start)
        self._handle_result(
            exit_code,
            output,
            lambda: self.printer.success("Successfully deployed %s configuration files to host in %s s.", len(files), time, verbose=True),
            lambda: self.printer.error("Failed to deploy configuration files to host."))
        if exit_code != 0:
            raise DeploymentException

    def run_scripts(self, scripts):
        if len(scripts) == 0:
            return []

        executed_scripts = []
        for script in scripts:
            start = timer()

            self.printer.info("Executing script %s.", script)
            full_path = os.path.expanduser(script)
            if not os.path.isfile(full_path):
                self.printer.error("Can't execute script %s, no such file.", script)
                continue

            with open(full_path) as script_file:
                script_content = [s for s in script_file.read().split("\n") if s]

            exit_code, output = self.host.execute_command(script_content, exit_on_failure=False)

            time = get_time(start)
            self._handle_result(
                exit_code,
                output,
                lambda: self.printer.success("Successfully executed script %s on host %s in %s s.", script, self.host.name, time, verbose=True),
                lambda: self.printer.error("Failed executing script %s on host %s.", script, self.host.name))
            if exit_code == 0:
                executed_scripts.append(script)
        return executed_scripts

    def _handle_result(self, exit_code, lines, on__success, on_error):
        if exit_code == 0:
            self.printer.info("Output:", verbose=True)
            self.printer.info([magenta(l) if l.startswith("+") else l for l in lines], verbose=True)
            on__success()
        else:
            self.printer.error("Exit code %s:", exit_code)
            self.printer.error([magenta(l) if l.startswith("+") else red(l) for l in lines])
            on_error()

    def _create_tar(self, files):
        self.printer.info("Creating new tar file %s.", TAR_PATH, verbose=True)
        if(os.path.isfile(TAR_PATH)):
            os.remove(TAR_PATH)
        with tarfile.open(TAR_PATH, "w:gz", dereference=True) as tar:
            for from_, to in files:
                try:
                    tar.add(from_, arcname=to)
                except PermissionError as e:
                    self.printer.error("Could not add %s to deployment tar file.", from_)
                    self.printer.error("    " + str(e))
                    raise DeploymentException
