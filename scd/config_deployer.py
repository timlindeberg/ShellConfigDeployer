import os
import tarfile
from typing import List, Callable

from scd.colors import *
from scd.constants import *
from scd.data_structs import DeploymentException, FileData, ScriptData
from scd.host import Host
from scd.printer import Printer
from scd.utils import *


class ConfigDeployer:
    MAX_FILES_TO_PRINT = 10

    def __init__(self, printer: Printer, host: Host):
        self.printer = printer
        self.host = host

    def install_programs(self, programs: List[str]) -> None:
        if len(programs) == 0:
            return

        start = timer()

        self.printer.info("Installing " + ", ".join([magenta(p) for p in programs]))

        select_package_manager = f"""
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
            $PACKAGE_MANAGER $ANSWER_YES install {" ".join(programs)}
        """

        lines = trim_multiline_str(select_package_manager).split("\n")
        exit_code, output = self.host.execute_command(lines, as_sudo=True)
        elapsed_time = get_time(start)
        self._handle_result(
            exit_code,
            output,
            lambda: self.printer.success("Successfully installed needed programs in %s s.", elapsed_time, verbose=True),
            lambda: self.printer.error("Failed to install programs."))
        if exit_code != 0:
            raise DeploymentException

    def change_shell(self, shell: str) -> None:
        if not shell:
            return

        start = timer()
        self.printer.info("Changing default shell to %s", shell)
        user = self.host.user
        command = [f"usermod -s $(which {shell}) {user}"]

        exit_code, output = self.host.execute_command(command, as_sudo=True)
        elapsed_time = get_time(start)
        self._handle_result(
            exit_code,
            output,
            lambda: self.printer.success("Successfully changed default shell to %s for user %s in %s s.", shell, user, elapsed_time, verbose=True),
            lambda: self.printer.error("Failed to change shell to %s for user %s.", shell, user))
        if exit_code != 0:
            raise DeploymentException

    def deploy_files(self, files: List[FileData]) -> None:
        if len(files) == 0:
            return

        start = timer()
        files_str = "file" if len(files) == 1 else "files"
        self.printer.info(f"Deploying %s {files_str}", len(files))
        if len(files) < self.MAX_FILES_TO_PRINT:
            self.printer.info([magenta(f.from_path) for f in files])
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
        elapsed_time = get_time(start)
        self._handle_result(
            exit_code,
            output,
            lambda: self.printer.success("Successfully deployed %s configuration files to host in %s s.", len(files), elapsed_time, verbose=True),
            lambda: self.printer.error("Failed to deploy configuration files to host."))
        if exit_code != 0:
            raise DeploymentException

    def run_scripts(self, scripts: List[ScriptData]) -> List[str]:
        if len(scripts) == 0:
            return []

        executed_scripts: List[str] = []
        for script_data in scripts:
            if self.run_script(script_data):
                executed_scripts.append(script_data.script)

        return executed_scripts

    def run_script(self, script_data: ScriptData) -> bool:
        start = timer()

        script = script_data.script
        self.printer.info("Executing script %s.", script)
        full_path = os.path.expanduser(script)
        if not os.path.isfile(full_path):
            self.printer.error("Can't execute script %s, no such file.", script)
            return False

        with open(full_path) as script_file:
            script_content = [s for s in script_file.read().split("\n") if s]

        exit_code, output = self.host.execute_command(script_content, exit_on_failure=False, as_sudo=script_data.as_sudo)

        elapsed_time = get_time(start)
        self._handle_result(
            exit_code,
            output,
            lambda: self.printer.success("Successfully executed script %s on host %s in %s s.", script, self.host.name, elapsed_time, verbose=True),
            lambda: self.printer.error("Failed executing script %s on host %s.", script, self.host.name))
        return exit_code == 0

    def _handle_result(self, exit_code: int, lines: List[str], on_success: Callable[[], None], on_error: Callable[[], None]) -> None:
        if exit_code == 0:
            self.printer.info("Output:", verbose=True)
            self.printer.info([magenta(l) if l.startswith("+") else l for l in lines], verbose=True)
            on_success()
        else:
            self.printer.error("Exit code %s:", exit_code)
            self.printer.error([magenta(l) if l.startswith("+") else red(l) for l in lines])
            on_error()

    def _create_tar(self, files: List[FileData]) -> None:
        self.printer.info("Creating new tar file %s.", TAR_PATH, verbose=True)
        if os.path.isfile(TAR_PATH):
            os.remove(TAR_PATH)

        with tarfile.open(TAR_PATH, "w:gz", dereference=True) as tar:
            for file in files:
                try:
                    tar.add(file.from_path, arcname=file.to_path)
                except PermissionError as e:
                    self.printer.error("Could not add %s to deployment tar file.", file.from_path)
                    self.printer.error(f"    {e}")
                    raise DeploymentException
