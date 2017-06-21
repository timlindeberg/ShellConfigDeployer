import os
import sys
import zipfile

import paramiko

import configuration
import formatting
from colors import *
from configuration import config

ZIP_NAME = 'scd_conf.zip'


class ConfigDeployer:
    def __init__(self, server, programs, files):
        self.programs = programs
        self.files = files

        self.zip = configuration.SCD_FOLDER + '/' + ZIP_NAME

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(server, username=config['username'], password='vagrant', port=2222)
        except paramiko.ssh_exception.AuthenticationException:
            print(formatting.PREFIX + "Invalid password")
            sys.exit(1)

        self.transport = ssh.get_transport()
        self.ssh = ssh

    def deploy(self):
        commands = []

        if len(self.programs) != 0:
            print(formatting.PREFIX + "Installing " + ', '.join([MAGENTA(p) for p in self.programs]))
            programs = ' '.join(self.programs)
            install_method = config['install_method']
            commands.append('sudo %s -y -q install %s' % (install_method, programs))

        if len(self.files) != 0:
            print(formatting.PREFIX + "Deploying " + MAGENTA(str(len(self.files))) + " file(s)")
            if len(self.files) < 10:
                f = [formatting.PREFIX + '     ' + MAGENTA(f.replace(configuration.HOME, '~')) for f in self.files]
                print('\n'.join(f))
            self.deploy_zip()
            commands.append('cd ~; unzip -q -o ./%s; rm %s' % (ZIP_NAME, ZIP_NAME))

        return self.execute_commands(commands)

    def execute_commands(self, commands):
        session = self.transport.open_session()
        session.set_combine_stderr(True)
        session.get_pty()

        command = ' && '.join(["(" + c + ")" for c in commands])
        session.exec_command(command)
        stdout = session.makefile('r', -1)
        while True:
            line = stdout.readline()
            if len(line) == 0:
                break
            print("%s   %s" % (formatting.PREFIX, line.rstrip()))

        stdout.close()
        session.close()
        self.ssh.close()
        return session.recv_exit_status() == 0

    def deploy_zip(self):
        self.create_zip()

        sftp = paramiko.SFTPClient.from_transport(self.ssh.get_transport())
        sftp.put(self.zip, "/home/%s/%s" % (config['username'], ZIP_NAME))
        sftp.close()
        os.remove(self.zip)

    def create_zip(self):
        home = os.path.expanduser('~') + '/'
        zip_file = zipfile.ZipFile(self.zip, 'w', zipfile.ZIP_DEFLATED)
        for f in self.files:
            arcname = f if not f.startswith(home) else f[len(home):]
            zip_file.write(f, arcname=arcname)
        zip_file.close()

    def close(self):
        self.ssh.close()
