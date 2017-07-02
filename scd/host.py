import socket
import sys

import paramiko


class Host:
    def __init__(self, printer, settings):
        self.printer = printer
        self.hostname = settings.hostname
        self.user = settings.user
        self.password = settings.password
        self.port = settings.port
        self.timeout = settings.timeout

    def execute_command(self, command, exit_on_failure=True, echo_commands=True):
        def _execute_command(connection):
            session = connection.get_transport().open_session()
            session.get_pty()  # So we can run sudo etc.

            commands = self._get_commands(command, exit_on_failure, echo_commands)
            self.printer.info("Executing commands on host:", verbose=True)
            self.printer.info(commands, verbose=True)

            session.exec_command("\n".join(commands))
            stdout = session.makefile("rb", -1)
            output = self._read_output(stdout)

            status = session.recv_exit_status()
            session.close()
            return status, output

        return self._with_connection(_execute_command)

    def send_file(self, file_from, file_to):
        def _send_file(connection):
            sftp = paramiko.SFTPClient.from_transport(connection.get_transport())
            self.printer.info("Deploying file %s to %s:%s", file_from, self.hostname, file_to, verbose=True)
            sftp.put(file_from, file_to)
            sftp.close()

        return self._with_connection(_send_file)

    @staticmethod
    def _get_commands(self, commands, exit_on_failure=True, echo_commands=True):
        if exit_on_failure and echo_commands:
            c = ["set -ex"]
        elif exit_on_failure:
            c = ["set -e"]
        elif echo_commands:
            c = ["set -x"]
        else:
            c = []

        if type(commands) == str:
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

        try:
            ssh.connect(self.hostname, username=self.user, password=self.password, port=self.port, timeout=self.timeout)
        except paramiko.ssh_exception.AuthenticationException:
            if self.password is None:
                self.printer.error(
                    "Could not authenticate against %s. No password was provided. " +
                    "Provide a password using the %s, %s or %s flags.", self.hostname, "-r", "-f", "-p"
                )
            else:
                self.printer.error("Permission denied.")
            sys.exit(5)
        except socket.timeout:
            self.printer.error("Could not connect to %s, timed out after %s seconds.", self.hostname, self.timeout)
            sys.exit(1)
        except Exception as e:
            self.printer.error("Could not connect to %s", self.hostname)
            self.printer.error(str(e))
            sys.exit(1)

        return ssh

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
