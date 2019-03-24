import socket

import paramiko
import os.path

from scd.constants import *
from scd.config_deployer import DeploymentException
from scd.host_status import HostStatus


class Host:
    def __init__(self, printer, settings, url):
        self.printer = printer
        self.user = settings.user
        self.password = settings.password
        self.port = settings.port
        self.timeout = settings.timeout
        self.private_key = settings.private_key
        self.url = url

        self.name = url  # To display in error message if we're unable to resolve the hostname
        self.host_statuses = HostStatus()
        self.name = self._get_host_name(self.host_statuses, url)
        self.status = self.host_statuses[self.name]
        self.has_password_file = False

    def execute_command(self, command, as_sudo=False, exit_on_failure=True, echo_commands=True):
        if not self.password:
            as_sudo = False

        commands = self._get_commands(command, exit_on_failure, echo_commands)
        home_path = f"/home/{self.user}"
        if as_sudo:
            self._send_pwd(home_path)

        def _execute_command(connection):
            session = connection.get_transport().open_session()
            session.get_pty()  # So we can run sudo etc.

            command = self._create_remote_script(commands, home_path, as_sudo)
            self.printer.info("Executing command on server:\n%s", command, verbose=True)
            session.exec_command(command)
            self.has_password_file = False

            stdout = session.makefile("rb", -1)
            output = self._read_output(stdout)

            status = session.recv_exit_status()
            session.close()
            return status, output

        return self._with_connection(_execute_command)

    def send_file(self, file_from, file_to):
        def _send_file(connection):
            sftp = paramiko.SFTPClient.from_transport(connection.get_transport())
            self.printer.info("Deploying file %s to %s:%s", file_from, self.url, file_to, verbose=True)
            sftp.put(file_from, file_to)
            sftp.close()

        return self._with_connection(_send_file)

    def cleanup(self):
        def _cleanup_password_file(connection):
            session = connection.get_transport().open_session()
            session.get_pty()  # So we can run sudo etc.
            pwd_path = f"/home/{self.user}/{PWD_NAME}"
            session.exec_command(f"rm {pwd_path}")

        if self.has_password_file:
            self._with_connection(_cleanup_password_file)

    def _send_pwd(self, home_path):
        with open(PWD_PATH, 'w') as f:
            f.write(self.password + '\n')
        self.send_file(PWD_PATH, f"{home_path}/{PWD_NAME}")
        self.has_password_file = True
        if os.path.isfile(PWD_PATH):
            os.remove(PWD_PATH)

    @staticmethod
    def _create_remote_script(commands, home_path, as_sudo):
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

    def _get_host_name(self, host_statues, url):
        name = host_statues.get_host_name(url)
        if name:
            self.printer.info("Fetched hostname of %s from host mappings: %s.", url, name, verbose=True)
            return name

        exit_code, output = self.execute_command("hostname", echo_commands=False)
        if exit_code != 0:
            self.printer.error("Could not get hostname of %s", url)
            raise DeploymentException

        name = output[0]
        self.printer.info("Fetched hostname of %s from host: %s.", url, name, verbose=True)
        host_statues.add_host_mapping(url, name)
        return name

    @staticmethod
    def _get_commands(commands, exit_on_failure=True, echo_commands=True):
        if exit_on_failure and echo_commands:
            c = ["set -ex"]
        elif exit_on_failure:
            c = ["set -e"]
        elif echo_commands:
            c = ["set -x"]
        else:
            c = []

        if type(commands) is str:
            c.append(commands)
        else:
            c += commands
        return c

    def _with_connection(self, do):
        connection = self._connect()
        res = do(connection)
        connection.close()
        return res

    def _connect(self):
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
            self.printer.error("    " + str(e))
            raise DeploymentException

        return ssh

    def _get_private_key(self):
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
    def _read_output(source):
        output = ""
        while True:
            lines = source.read().decode("utf-8", errors="replace")
            if len(lines) == 0:
                break

            output += lines.replace("\r\r", "\n").replace("\r\n", "\n")
        source.close()
        return [line.strip() for line in output.split("\n") if len(line) > 0]
