import json
import os
import time
from datetime import datetime

from scd.constants import *


class HostStatus:
    @staticmethod
    def initial_status():
        return {
            "last_deployment": "1970-01-01 01:00:00",  # time: 0
            "installed_programs": [],
            "deployed_files": [],
            "executed_scripts": []
        }

    def __init__(self):
        self.status = self._read_host_status()

    def __getitem__(self, host):
        if host not in self.status:
            self.status[host] = self.initial_status()
        status = self.status[host]
        time_stamp = self._date_to_time_stamp(status["last_deployment"])
        status["last_deployment"] = time_stamp
        return status

    def update(self, hostname, installed_programs=None, deployed_files=None, shell=None, scripts=None):
        if not (installed_programs or deployed_files or shell or scripts):
            return

        status = self.status[hostname] if hostname in self.status else {}
        status["last_deployment"] = self._time_stamp_to_date(time.time())

        programs = set(status.get("installed_programs") or [])

        if installed_programs:
            programs.update(installed_programs)
        if deployed_files:
            status["deployed_files"] = [f[0] for f in deployed_files]
        if shell:
            programs.add(shell)
            status["shell"] = shell
        if scripts:
            status["executed_scripts"] = scripts

        self.status[hostname] = status
        self.save()

    def clear(self, host):
        if self.status.get(host):
            del self.status[host]
            return True
        return False

    def save(self):
        with open(SERVER_STATUS_FILE, "w") as f:
            f.seek(0)
            f.truncate()
            json.dump(self.status, f)

    @staticmethod
    def _read_host_status():
        if not os.path.isfile(SERVER_STATUS_FILE):
            return {}

        with open(SERVER_STATUS_FILE) as f:
            try:
                return json.load(f)
            except ValueError:
                return {}

    @staticmethod
    def _date_to_time_stamp(date):
        return time.mktime(datetime.strptime(date, TIME_FORMAT).timetuple())

    @staticmethod
    def _time_stamp_to_date(time_stamp):
        return datetime.fromtimestamp(time_stamp).strftime(TIME_FORMAT)
