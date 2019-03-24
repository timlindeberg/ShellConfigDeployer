import json
import time
from typing import Dict, List, Set, Optional

from scd.constants import *
from scd.data_structs import FileData, StatusData, empty_status
from scd.utils import time_stamp_to_date


class HostStatus:

    def __init__(self):
        self.status: Dict[str, StatusData] = {}
        self.host_mappings: Dict[str, str] = {}
        with open(SERVER_STATUS_FILE) as f:
            try:
                data = json.load(f)
            except json.decoder.JSONDecodeError:
                return
            status = data.get("status")
            if status:
                self.status = self._read_host_status(status)
            self.host_mappings = data.get("host_mappings") or {}

    def __getitem__(self, host: str) -> StatusData:
        if host not in self.status:
            self.status[host] = empty_status()
        return self.status[host]

    def update(self,
               hostname: str,
               installed_programs: Set[str]=None,
               deployed_files: List[FileData]=None,
               shell: Optional[str]=None,
               scripts: List[str]=None) -> None:
        if not (installed_programs or deployed_files or shell or scripts):
            return

        status = self.status[hostname] if hostname in self.status else empty_status()
        status.last_deployment = time_stamp_to_date(time.time())

        programs: Set[str] = set(status.installed_programs)

        if installed_programs:
            programs.update(installed_programs)
        if deployed_files:
            status.deployed_files = [f.from_path for f in deployed_files]
        if shell:
            programs.add(shell)
            status.shell = shell
        if scripts:
            status.executed_scripts = scripts

        status.installed_programs = list(programs)
        self.status[hostname] = status
        self.save()

    def add_host_mapping(self, url: str, name: str) -> None:
        self.host_mappings[url] = name
        self.save()

    def get_host_name(self, url: str) -> Optional[str]:
        return self.host_mappings.get(url)

    def clear(self, url: str) -> bool:
        name = self.get_host_name(url)
        if name and name in self.status:
            del self.status[name]
            return True
        if url in self.status:
            del self.status[url]
            return True
        return False

    def save(self) -> None:
        with open(SERVER_STATUS_FILE, "w") as f:
            f.seek(0)
            f.truncate()
            json.dump(self.as_dict(), f)

    def as_dict(self) -> Dict[str, any]:
        status_data = {}
        for host, status in self.status.items():
            status_data[host] = status.__dict__

        return {
            "host_mappings": self.host_mappings,
            "status": status_data
        }

    def _read_host_status(self, json: Dict[str, any]) -> Dict[str, StatusData]:
        statuses: Dict[str, StatusData] = {}
        for host, data in json.items():
            status = empty_status()
            status.init(data)
            statuses[host] = status
        return statuses

