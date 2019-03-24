import socket
from typing import List, Tuple, Callable, TypeVar

import os.path
import paramiko

from scd.constants import *
from scd.data_structs import DeploymentException
from scd.host_status import HostStatus
from scd.printer import Printer
from scd.settings import Settings

T = TypeVar('T')


class Host:
    def __init__(self, printer: Printer, settings: Settings, host_status: HostStatus, url: str):
        self.printer = printer
        self.user = settings.user
        self.password = settings.password
        self.port = settings.port
        self.timeout = settings.timeout
        self.private_key = settings.private_key
        self.host_status = host_status

        self.url = url
        self.name = url  # To display in error message if we're unable to resolve the hostname
        self.name = self._get_host_name(url)
        self.status = self.host_status[self.name]
        self.needs_cleanup = False

    def execute_command(self, commands: List[str], as_sudo=False, exit_on_failure=True, echo_commands=True) -> Tuple[int, List[str]]:
        if not self.password:
            as_sudo = False

        commands = self._get_commands(commands, exit_on_failure, echo_commands)
        home_path = f"/home/{self.user}"
        if as_sudo:
            self._send_pwd(home_path)

        def _execute_command(connection: paramiko.SSHClient) -> Tuple[int, List[str]]:
            session = connection.get_transport().open_session()
            session.get_pty()  # So we can run sudo etc.

            command = self._create_remote_script(commands, home_path, as_sudo)
            self.printer.info("Executing command on server:", verbose=True)
            self.printer.info([l for l in command.lstrip().rstrip().split('\n')], verbose=True)

            session.exec_command(command)
            self.needs_cleanup = False

            stdout = session.makefile("rb", -1)
            output = self._read_output(stdout)

            status: int = session.recv_exit_status()
            session.close()
            return status, output

        return self._with_connection(_execute_command)

    def send_file(self, file_from: str, file_to: str) -> None:
        def _send_file(connection: paramiko.SSHClient) -> None:
            sftp = paramiko.SFTPClient.from_transport(connection.get_transport())
            self.printer.info("Deploying file %s to %s:%s", file_from, self.url, file_to, verbose=True)
            sftp.put(file_from, file_to)
            sftp.close()

        return self._with_connection(_send_file)

    def cleanup(self) -> None :
        def _cleanup_password_file(connection: paramiko.SSHClient) -> None:
            session = connection.get_transport().open_session()
            session.get_pty()  # So we can run sudo etc.
            pwd_path = f"/home/{self.user}/{PWD_NAME}"
            session.exec_command(f"rm {pwd_path}")

        if self.needs_cleanup:
            self._with_connection(_cleanup_password_file)

    def _send_pwd(self, home_path: str) -> None:
        with open(PWD_PATH, 'w') as f:
            f.write(self.password + '\n')
        self.send_file(PWD_PATH, f"{home_path}/{PWD_NAME}")
        self.needs_cleanup = True
        if os.path.isfile(PWD_PATH):
            os.remove(PWD_PATH)

    @staticmethod
    def _create_remote_script(commands: List[str], home_path: str, as_sudo: bool) -> str:
        content = "\n".join(commands)

        if not as_sudo:
            return content

        return fr"""
function finish {{
  rm -- {home_path}/{PWD_NAME} 
}}
trap finish EXIT
read -r -d '' SCRIPT <<- "EOM"
{content}
EOM
cat '{home_path}/{PWD_NAME}' | sudo --prompt='' -S bash -c "$SCRIPT"
"""

    def _get_host_name(self, url: str) -> str:
        name = self.host_status.get_host_name(url)
        if name:
            self.printer.info("Fetched hostname of %s from host mappings: %s.", url, name, verbose=True)
            return name

        exit_code, output = self.execute_command(["hostname"], echo_commands=False)
        if exit_code != 0:
            self.printer.error("Could not get hostname of %s", url)
            raise DeploymentException

        name = output[0]
        self.printer.info("Fetched hostname of %s from host: %s.", url, name, verbose=True)
        self.host_status.add_host_mapping(url, name)
        return name

    @staticmethod
    def _get_commands(commands: List[str], exit_on_failure=True, echo_commands=True) -> List[str]:
        if exit_on_failure and echo_commands:
            c = ["set -ex"]
        elif exit_on_failure:
            c = ["set -e"]
        elif echo_commands:
            c = ["set -x"]
        else:
            c = []

        return c + commands

    def _with_connection(self, do: Callable[[paramiko.SSHClient], T]) -> T:
        connection = self._connect()
        res = do(connection)
        connection.close()
        return res

    def _connect(self) -> paramiko.SSHClient:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        pkey = self._get_private_key()

        try:
            ssh.connect(self.url, username=self.user, password=self.password, port=self.port, timeout=self.timeout, pkey=pkey)
        except paramiko.ssh_exception.AuthenticationException:
            if self.password is None:
                self.printer.error(
                    "Could not authenticate against %s. No password was provided. "
                    "Provide a password using the %s, %s or %s flags.", self.name, "-r", "-f", "-p"
                )
            else:
                self.printer.error("Permission denied.")
            raise DeploymentException
        except socket.timeout:
            self.printer.error("Could not connect to %s, timed out after %s seconds.", self.url, self.timeout)
            raise DeploymentException
        except Exception as e:
            self.printer.error("Could not connect to %s", self.name)
            self.printer.error(f"    {e}")
            raise DeploymentException

        return ssh

    def _get_private_key(self) -> paramiko.PKey:
        if not self.private_key:
            return None

        path = os.path.expanduser(self.private_key)
        try:
            return paramiko.RSAKey.from_private_key_file(path, password=self.password)
        except paramiko.ssh_exception.PasswordRequiredException:
            self.printer.error("Private key %s required a password but none was provided", self.private_key)
            raise DeploymentException
        except paramiko.ssh_exception.SSHException:
            self.printer.error("Could not read private key %s", self.private_key)
            raise DeploymentException

    @staticmethod
    def _read_output(source) -> List[str]:
        output = ""
        while True:
            lines = source.read().decode("utf-8", errors="replace")
            if len(lines) == 0:
                break

            output += lines.replace("\r\r", "\n").replace("\r\n", "\n")
        source.close()
        return [line.strip() for line in output.split("\n") if len(line) > 0]
