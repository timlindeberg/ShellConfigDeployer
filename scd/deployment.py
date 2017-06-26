import os
import sys
import textwrap
import zipfile

import paramiko

from scd.colors import *
from scd.constants import *


class ConfigDeployer:
    def __init__(self, settings, programs, files, change_shell, printer):
        self.programs = programs
        self.files = files
        self.change_shell = change_shell
        self.printer = printer

        self.user = settings.user
        self.password = settings.password
        self.port = settings.port
        self.shell = settings.shell

        self.ssh = self._connect(settings.host)
        self.transport = self.ssh.get_transport()

    def deploy(self):
        commands = ["set -e", "set -x"]

        if len(self.programs) != 0:
            commands += self._install_programs_commands()

        if self.change_shell:
            commands += self._change_shell_commands()

        if len(self.files) != 0:
            commands += self._deploy_files_commands()

        return self._execute_script(commands)

    def _connect(self, host):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(host, username=self.user, password=self.password, port=self.port)
        except paramiko.ssh_exception.AuthenticationException:
            if self.password is None:
                self.printer.error(
                    "Could not authenticate against %s. No password was provided. " +
                    "Provide a password using the %s or %s flags.", host, "-p", "-f"
                )
            else:
                self.printer.error("Permission denied.")
            sys.exit(5)
        except Exception as e:
            self.printer.error("Could not connect to %s", host)
            self.printer.error(str(e))
            sys.exit(1)

        return ssh

    def _install_programs_commands(self):
        self.printer.info("Installing " + ", ".join([magenta(p) for p in self.programs]))

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

        commands = textwrap.dedent(select_package_manager).strip().split("\n")
        commands += ["sudo $PACKAGE_MANAGER $ANSWER_YES install " + " ".join(self.programs)]
        return commands

    def _change_shell_commands(self):
        self.printer.info("Changing default shell to %s", self.shell)
        return ["sudo usermod -s $(which %s) %s" % (self.shell, self.user)]

    def _deploy_files_commands(self):
        self.printer.info("Deploying %s file(s)", len(self.files))
        if len(self.files) < 10:
            self.printer.info([magenta(f) for f in self.files])
        self._deploy_zip()
        return ["cd ~", "unzip -q -o ./%s" % ZIP_NAME, "rm %s" % ZIP_NAME]

    def _execute_script(self, commands):
        session = self.transport.open_session()
        session.get_pty()

        self.printer.info("Executing script on server:", verbose=True)
        self.printer.info(commands, verbose=True)

        session.exec_command("\n".join(commands))
        stdout = session.makefile("rb", -1)
        lines = self._read_output(stdout)

        status = session.recv_exit_status()
        session.close()
        self.ssh.close()

        self._print_output(status, lines)
        return status == 0

    @staticmethod
    def _read_output(source):
        output = ""
        while True:
            lines = source.read().decode("utf-8", errors="replace")
            if len(lines) == 0:
                break

            output += lines.replace("\r\r", "\n").replace("\r\n", "\n")
        source.close()
        return [line.strip() for line in output.split("\n") if len(line) > 0]

    def _print_output(self, status, lines):
        if status != 0:
            self.printer.error("Remote commands failed with status %s:", status)
            self.printer.error([magenta(l) if l.startswith("+") else red(l) for l in lines])
        else:
            self.printer.info("Output:", verbose=True)
            self.printer.info([magenta(l) if l.startswith("+") else l for l in lines], verbose=True)

    def _deploy_zip(self):
        self._create_zip()

        sftp = paramiko.SFTPClient.from_transport(self.transport)
        self.printer.info("Deploying zip file to server", verbose=True)
        sftp.put(ZIP_PATH, "/home/%s/%s" % (self.user, ZIP_NAME))
        sftp.close()
        os.remove(ZIP_PATH)

    def _create_zip(self):
        self.printer.info("Creating new zip file %s.", ZIP_PATH, verbose=True)
        home = os.path.expanduser("~") + "/"
        zip_file = zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED)
        for f in self.files:
            arcname = f if not f.startswith(home) else f[len(home):]
            try:
                zip_file.write(f, arcname=arcname)
            except PermissionError as e:
                self.printer.error("Could not add %s to deployment zip file.", f)
                self.printer.error("    " + str(e))
                sys.exit(1)
        zip_file.close()
