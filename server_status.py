import json
import os
import time

import configuration


class ServerStatus:
    HOME = os.path.expanduser('~')
    SERVER_STATUS_FILE = configuration.SCD_FOLDER + '/server_status'

    @staticmethod
    def default_status():
        return {
            'last_modified': 0,
            'installed_programs': []
        }

    def __init__(self):
        self.status = self.read_server_status()

    def read_server_status(self):
        if not os.path.isfile(self.SERVER_STATUS_FILE):
            return {}

        with open(self.SERVER_STATUS_FILE) as f:
            try:
                return json.load(f)
            except:
                return {}

    def __getitem__(self, server):
        if server not in self.status:
            self.status[server] = self.default_status()
        return self.status[server]

    def update(self, server):
        status = self.status[server] if server in self.status else {}

        status['last_modified'] = time.time()
        status['installed_programs'] = configuration.config['programs']
        self.status[server] = status

    def save(self):
        with open(self.SERVER_STATUS_FILE, 'w') as f:
            f.seek(0)
            f.truncate()
            json.dump(self.status, f)
