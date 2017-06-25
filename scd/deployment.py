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
        commands = []

        if len(self.programs) != 0:
            self.printer.info("Installing " + ', '.join([MAGENTA(p) for p in self.programs]))
            programs = ' '.join(self.programs)
            install_method = settings.config['install_method']
            commands.append('sudo %s -y -q install %s' % (install_method, programs))

        if len(self.files) != 0:
            self.printer.info("Deploying " + MAGENTA(str(len(self.files))) + " file(s)")
            if len(self.files) < 10:
                for f in self.files:
                    self.printer.info(MAGENTA(f.replace(settings.HOME, '~')))
            self.deploy_zip()
            commands.append('cd ~; unzip -q -o ./%s; rm %s' % (ZIP_NAME, ZIP_NAME))

        return self.execute_commands(commands)

    def execute_commands(self, commands):
        session = self.transport.open_session()
        session.set_combine_stderr(True)
        session.get_pty()

        command = ' && '.join(["(" + c + ")" for c in commands])
        self.printer.verbose("Executing command:")
        self.printer.verbose(command)
        session.exec_command(command)
        stdout = session.makefile('rb', -1)
        self.printer.verbose(MAGENTA("Output"))
        self.printer.divider(verbose=True)
        while True:
            lines = stdout.read().decode('utf-8', errors='replace')
            if len(lines) == 0:
                break

            lines.replace("\r\r", "\n")
            lines.replace("\r\n", "\n")
            for line in lines.split("\n"):
                if len(line) > 0:
                    self.printer.verbose("    " + line.rstrip())

        self.printer.divider(verbose=True)
        stdout.close()
        session.close()
        self.ssh.close()
        return session.recv_exit_status() == 0

    def deploy_zip(self):
        self.create_zip()

        sftp = paramiko.SFTPClient.from_transport(self.ssh.get_transport())
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
