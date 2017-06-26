import json
import os
import time
from datetime import datetime

from scd import settings
from scd.constants import *


class HostStatus:
    SERVER_STATUS_FILE = SCD_FOLDER + '/server_status'
    TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

    @staticmethod
    def initial_status():
        return {
            'last_deployment': '1970-01-01 01:00:00',  # time: 0
            'installed_programs': [],
            'deployed_files': []
        }

    def __init__(self):
        self.status = self.read_server_status()

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
        status = self.status[host]
        time_stamp = self._date_to_time_stamp(status['last_deployment'])
        status['last_deployment'] = time_stamp
        return status

    def update(self, host):
        status = self.status[host] if host in self.status else {}
        status['last_deployment'] = self._time_stamp_to_date(time.time())
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

    def _date_to_time_stamp(self, date):
        return time.mktime(datetime.strptime(date, self.TIME_FORMAT).timetuple())

    def _time_stamp_to_date(self, time_stamp):
        return datetime.fromtimestamp(time_stamp).strftime(self.TIME_FORMAT)
