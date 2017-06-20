import os
import sys
import zipfile

import paramiko

import colors
import formatting
from config import config

ZIP_NAME = 'deploy.zip'


def create_zip(files):
    home = os.path.expanduser('~') + '/'
    zip = zipfile.ZipFile(ZIP_NAME, 'w', zipfile.ZIP_DEFLATED)
    for f in files:
        arcname = f
        if f.startswith(home):
            arcname = f[len(home):]
        zip.write(f, arcname=arcname)
    return zip


def install_programs():


def deploy_to_server(server, files):
    print formatting.PREFIX + "Deploying " + colors.GREEN + str(len(files)) + colors.CLEAR + " files"

    zip = create_zip(files)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(server, username=config['username'], password='vagrant')
    except paramiko.ssh_exception.AuthenticationException:
        print "Invalid password"
        sys.exit(1)

    ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
    ssh.connect(server, username=config['username'], password='vagrant')
    sftp = ssh.open_sftp()
    sftp.put(ZIP_NAME, server)
    sftp.close()

    transport = ssh.get_transport()
    session = transport.open_session()
    ssh.close()

    return True
