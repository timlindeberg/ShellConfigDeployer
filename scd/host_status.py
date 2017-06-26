import json
import os
import time

from scd import settings
from scd.constants import *


class HostStatus:
    SERVER_STATUS_FILE = SCD_FOLDER + '/server_status'

    @staticmethod
    def initial_status():
        return {
            'last_deployment': 0,
            'installed_programs': [],
            'deployed_files': []
        }

    def __init__(self):
        self.status = self.read_server_status()
        self.status['last_deployment']

    def read_server_status(self):
        if not os.path.isfile(self.SERVER_STATUS_FILE):
            return {}

        with open(self.SERVER_STATUS_FILE) as f:
            try:
                return json.load(f)
            except ValueError:
                return {}

    def __getitem__(self, host):
        if host not in self.status:
            self.status[host] = self.initial_status()
        return self.status[host]

    def update(self, host):
        status = self.status[host] if host in self.status else {}

        status['last_deployment'] = time.time()
        status['installed_programs'] = settings.PROGRAMS
        status['deployed_files'] = settings.FILES
        if settings.SHELL:
            status['installed_programs'] += [settings.SHELL]
            status['shell'] = settings.SHELL
        self.status[host] = status

    def clear(self, host):
        if self.status.get(host):
            del self.status[host]
            return True
        return False

    def save(self):
        with open(self.SERVER_STATUS_FILE, 'w') as f:
            f.seek(0)
            f.truncate()
            json.dump(self.status, f)
