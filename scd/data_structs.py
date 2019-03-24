from typing import List, Optional


class ScriptData:
    def __init__(self, script: str, as_sudo: bool):
        self.script = script
        self.as_sudo = as_sudo


class FileData:
    def __init__(self, from_path: str, to_path: str):
        self.from_path = from_path
        self.to_path = to_path


class StatusData:

    def __init__(self, last_deployment: str, installed_programs: List[str], deployed_files: List[str], executed_scripts: List[str], shell: Optional[str]):
        self.last_deployment = last_deployment
        self.installed_programs = installed_programs
        self.deployed_files = deployed_files
        self.executed_scripts = executed_scripts
        self.shell = shell

    def init(self, dict) -> None:
        self.__dict__.update(dict)


def empty_status() -> StatusData:
    return StatusData("1970-01-01 01:00:00", [], [], [], None)


class DeploymentException(Exception):
    pass
