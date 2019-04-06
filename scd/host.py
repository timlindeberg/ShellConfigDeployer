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
        self.home_path = f"/home/{self.user}"

    def execute_command(self, commands: List[str],  exit_on_failure=True, echo_commands=True) -> Tuple[int, List[str]]:
        as_sudo = self.password and any("sudo" in c for c in commands)
        commands = self._get_commands(commands, as_sudo, exit_on_failure, echo_commands)
        if as_sudo:
            self._send_pwd()

        def _execute_command(connection: paramiko.SSHClient) -> Tuple[int, List[str]]:
            res = self._execute(connection, "\n".join(commands))
            self.needs_cleanup = False
            return res

        return self._with_connection(_execute_command)

    def send_file(self, file_from: str, file_to: str) -> None:
        def _send_file(connection: paramiko.SSHClient) -> None:
            sftp = paramiko.SFTPClient.from_transport(connection.get_transport())
            self.printer.info("Deploying file %s to %s:%s", file_from, self.url, file_to, verbose=True)
            sftp.put(file_from, file_to)
            sftp.close()

        return self._with_connection(_send_file)

    def cleanup(self) -> None:
        if self.needs_cleanup:
            command = f"rm {self.home_path}/{PWD_NAME}"
            self._with_connection(lambda conn: self._execute(conn, command))

    def _execute(self, connection: paramiko.SSHClient, command: str) -> Tuple[int, List[str]]:
        channel = connection.get_transport().open_session()
        channel.get_pty()

        self.printer.info("Executing command on server:", verbose=True)
        self.printer.info(command.split("\n"), verbose=True)

        channel.exec_command(command)
        output = self._read_output(channel)
        status = channel.recv_exit_status()
        channel.close()
        
        return status, output

    def _send_pwd(self) -> None:
        with open(PWD_PATH, 'w') as f:
            f.write(self.password + '\n')
        self.send_file(PWD_PATH, f"{self.home_path}/{PWD_NAME}")
        self.needs_cleanup = True
        if os.path.isfile(PWD_PATH):
            os.remove(PWD_PATH)

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

    def _get_commands(self, commands: List[str], as_sudo: bool, exit_on_failure=True, echo_commands=True) -> List[str]:
        full_command = []
        if exit_on_failure:
            full_command.append("set -e")
        if echo_commands:
            full_command.append("set -x")

        if not as_sudo:
            return full_command + commands

        full_command.extend([
            f"function cleanup {{ rm -- {self.home_path}/{PWD_NAME} }}",
            "trap cleanup EXIT"
        ])
        sudo_replacement = f"cat '{self.home_path}/{PWD_NAME}' | sudo --prompt='' -S"
        return full_command + [c.replace("sudo", sudo_replacement) for c in commands]

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
    def _read_output(channel) -> List[str]:
        output = ""
        with channel.makefile("rb", -1) as stdout:
            while True:
                lines = stdout.read().decode("utf-8", errors="replace")
                if len(lines) == 0:
                    break

                output += lines.replace("\r\r", "\n").replace("\r\n", "\n")
        return [line.strip() for line in output.split("\n") if len(line) > 0]
