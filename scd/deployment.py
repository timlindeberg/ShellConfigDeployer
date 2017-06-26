import os
import sys
import textwrap
import zipfile

import paramiko

from scd import settings
from scd.colors import *

ZIP_NAME = 'scd_conf.zip'


class ConfigDeployer:
    def __init__(self, host, programs, files, change_shell, printer):
        self.programs = programs
        self.files = files
        self.change_shell = change_shell
        self.printer = printer

        self.zip = settings.SCD_FOLDER + '/' + ZIP_NAME

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(host, username=settings.USER, password=settings.PASSWORD, port=settings.PORT)
        except paramiko.ssh_exception.AuthenticationException:
            if settings.PASSWORD is None:
                printer.error(
                    "Could not authenticate against %s. No password was provided. " +
                    "Provide a password using the %s or %s flags.",
                    host, '-p', '-f'
                )
            else:
                printer.error('Permission denied.')
            sys.exit(5)
        except Exception as e:
            printer.error('Could not connect to %s', host)
            printer.error(str(e))
            sys.exit(1)

        self.transport = ssh.get_transport()
        self.ssh = ssh

    def deploy(self):
        commands = ['set -e', 'set -x']

        if len(self.programs) != 0:
            commands += self._install_programs_commands()

        if self.change_shell:
            commands += self._change_shell_commands()

        if len(self.files) != 0:
            commands += self._deploy_files_commands()

        return self._execute_script(commands)

    def _install_programs_commands(self):
        self.printer.info('Installing ' + ', '.join([magenta(p) for p in self.programs]))

        select_package_manager = """
                if [ -f /etc/redhat-release ]; then
                    PACKAGE_MANAGER="yum"
                elif [ -f /etc/arch-release ]; then
                    PACKAGE_MANAGER="pacman"
                elif [ -f /etc/gentoo-release ]; then
                    PACKAGE_MANAGER="emerge"
                elif [ -f /etc/SuSE-release ]; then
                    PACKAGE_MANAGER="zypper"
                elif [ -f /etc/debian_version ]; then
                    PACKAGE_MANAGER="apt-get"
                elif [ "$(uname)" == "Darwin" ]; then
                    PACKAGE_MANAGER="brew"
                else
                    echo "Unsupported distribution."
                    exit 1
                fi
            """

        commands = textwrap.dedent(select_package_manager).strip().split("\n")
        commands += ['sudo sh -c "yes | $PACKAGE_MANAGER install %s"' % ' '.join(self.programs)]
        return commands

    def _change_shell_commands(self):
        self.printer.info('Changing default shell to %s', settings.SHELL)
        return ['sudo chsh -s $(which %s) %s' % (settings.SHELL, settings.USER)]

    def _deploy_files_commands(self):
        self.printer.info('Deploying %s file(s)', len(self.files))
        if len(self.files) < 10:
            self.printer.info([magenta(f) for f in self.files])
        self._deploy_zip()
        return ['cd ~', 'unzip -q -o ./%s' % ZIP_NAME, 'rm %s' % ZIP_NAME]

    def _execute_script(self, commands):
        session = self.transport.open_session()
        session.get_pty()

        script = '\n'.join(commands)

        self.printer.info('Executing script on server:', verbose=True)
        self.printer.info(commands, verbose=True)

        session.exec_command(script)
        stdout = session.makefile('rb', -1)
        lines = self._read_output(stdout)

        status = session.recv_exit_status()
        session.close()
        self.ssh.close()

        self._print_output(status, lines)
        return status == 0

    @staticmethod
    def _read_output(source):
        output = ''
        while True:
            lines = source.read().decode('utf-8', errors='replace')
            if len(lines) == 0:
                break

            output += lines.replace('\r\r', '\n').replace('\r\n', '\n')
        source.close()
        return [line.strip() for line in output.split('\n') if len(line) > 0]

    def _print_output(self, status, lines):
        if status != 0:
            self.printer.error('Remote commands failed with status %s:', status)
            self.printer.error([magenta(l) if l.startswith('+') else red(l) for l in lines])
        else:
            self.printer.info('Output:', verbose=True)
            self.printer.info([magenta(l) if l.startswith('+') else l for l in lines], verbose=True)

    def _deploy_zip(self):
        self._create_zip()

        sftp = paramiko.SFTPClient.from_transport(self.transport)
        self.printer.info('Deploying zip file to server', verbose=True)
        sftp.put(self.zip, '/home/%s/%s' % (settings.USER, ZIP_NAME))
        sftp.close()
        os.remove(self.zip)

    def _create_zip(self):
        self.printer.info('Creating new zip file %s.', self.zip, verbose=True)
        home = os.path.expanduser('~') + '/'
        zip_file = zipfile.ZipFile(self.zip, 'w', zipfile.ZIP_DEFLATED)
        for f in self.files:
            arcname = f if not f.startswith(home) else f[len(home):]
            try:
                zip_file.write(f, arcname=arcname)
            except PermissionError as e:
                self.printer.error("Could not add %s to deployment zip file.", f)
                self.printer.error("    " + str(e))
                sys.exit(1)
        zip_file.close()
