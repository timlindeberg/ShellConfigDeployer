import os
import sys
import zipfile

import paramiko

from scd import settings
from scd.colors import *

ZIP_NAME = 'scd_conf.zip'


class ConfigDeployer:
    def __init__(self, server, programs, files, printer):
        self.programs = programs
        self.files = files
        self.printer = printer

        self.zip = settings.SCD_FOLDER + '/' + ZIP_NAME

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(server, username=settings.config['username'], password=settings.PASSWORD, port=settings.PORT)
        except paramiko.ssh_exception.AuthenticationException:
            if settings.PASSWORD is None:
                printer.info(RED("Could not authenticate against " + BOLD(server) +
                                 RED(". No password was provided. Provide a password using the -p or -f flags.")))
            else:
                printer.info(RED("Permission denied."))

            sys.exit(5)
        except Exception as e:
            printer.info(RED("Could not connect to ") + BOLD(server))
            printer.info(RED(str(e)))
            sys.exit(1)

        self.transport = ssh.get_transport()
        self.ssh = ssh

    def deploy(self):
        commands = ['set -e', 'set -x']

        if len(self.programs) != 0:
            self.printer.info("Installing " + ', '.join([MAGENTA(p) for p in self.programs]))
            programs = ' '.join(self.programs)
            install_method = settings.config['install_method']
            commands += ['sudo %s -y -q install %s' % (install_method, programs)]

        if len(self.files) != 0:
            self.printer.info("Deploying " + MAGENTA(str(len(self.files))) + " file(s)")
            if len(self.files) < 10:
                self.printer.info([MAGENTA(f.replace(settings.HOME, '~')) for f in self.files])
            self.deploy_zip()
            commands += ['cd ~', 'unzip -q -o ./%s' % ZIP_NAME, 'rm %s' % ZIP_NAME]

        return self.execute_commands(commands)

    def execute_commands(self, commands):
        session = self.transport.open_session()
        session.get_pty()

        command = '\n'.join(commands)

        self.printer.verbose(MAGENTA("Executing commands on server:"))
        self.printer.verbose(commands)

        session.exec_command(command)
        stdout = session.makefile('rb', -1)
        lines = self.read_output(stdout)

        status = session.recv_exit_status()
        session.close()
        self.ssh.close()

        self.print_output(status, lines)
        return status == 0

    def print_output(self, status, lines):
        if status != 0:
            self.printer.info(RED("Remote commands failed with status " + BOLD(status) + RED(":")))
            self.printer.info([MAGENTA(l) if l.startswith('+') else RED(l) for l in lines])
        elif settings.VERBOSE:
            self.printer.verbose(MAGENTA("Output:"))
            self.printer.verbose([MAGENTA(l) if l.startswith('+') else l for l in lines])

    @staticmethod
    def read_output(source):
        output = ''
        while True:
            lines = source.read().decode('utf-8', errors='replace')
            if len(lines) == 0:
                break

            output += lines.replace("\r\r", "\n").replace("\r\n", "\n")
        source.close()
        return [line.strip() for line in output.split("\n") if len(line) > 0]

    def deploy_zip(self):
        self.create_zip()

        sftp = paramiko.SFTPClient.from_transport(self.transport)
        self.printer.verbose("Deploying zip file to server")
        sftp.put(self.zip, "/home/%s/%s" % (settings.config['username'], ZIP_NAME))
        sftp.close()
        os.remove(self.zip)

    def create_zip(self):
        self.printer.verbose("Creating new zip file " + MAGENTA(self.zip))
        home = os.path.expanduser('~') + '/'
        zip_file = zipfile.ZipFile(self.zip, 'w', zipfile.ZIP_DEFLATED)
        for f in self.files:
            arcname = f if not f.startswith(home) else f[len(home):]
            zip_file.write(f, arcname=arcname)
        zip_file.close()
