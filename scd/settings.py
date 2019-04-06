import json
import sys
import textwrap
from getpass import getpass
from typing import List, Set, Dict, Optional

from pygments import highlight, lexers, formatters

from scd import colors
from scd.argparser import parser
from scd.constants import *
from scd.data_structs import FileData
from scd.host_status import HostStatus
from scd.printer import Printer


class Settings:
    DEFAULT_PORT = 22
    DEFAULT_TIMEOUT = 5
    DEFAULT_CONFIG = textwrap.dedent("""
    {
        "user": "",
        "private_key": "",
        "ignored_files": [
            "*/.git/*",
            "*/.gitignore",
            "*/.DS_Store"
        ],
        "files": [
            "~/.oh-my-zsh",
            "~/.zshrc"
        ],
        "programs": [
            "tree"
            "zsh"
        ],
        "scripts": [
            {
                "file": '',
                "as_sudo": false
            }
        ]
    }
    """).strip()

    def __init__(self):
        args = parser.parse_args()

        colors.no_color = args.no_color

        self.printer = Printer(False)

        self._check_config_file()
        config = self._parse_config_file()

        colors.no_color = args.no_color or config.get("use_color") is False

        if args.clear_status:
            self._clear_host_status(args.clear_status)

        if args.print_host_status:
            self._print_host_status(args.print_host_status)

        if args.print_config:
            self._print_config(config)

        self._parse_settings(args, config)

    def _check_config_file(self) -> None:
        if os.path.isfile(SCD_CONFIG):
            return

        self.printer.error("Missing configuration file %s.", SCD_CONFIG)
        self.printer.error("Creating default configuration. Please edit %s with your settings.", SCD_CONFIG)
        if not os.path.exists(SCD_FOLDER):
            os.makedirs(SCD_FOLDER)

        with open(SCD_CONFIG, "w") as f:
            f.write(self.DEFAULT_CONFIG)
            sys.exit(1)

    def _parse_config_file(self) -> Dict[str, any]:
        with open(SCD_CONFIG) as f:
            try:
                return json.load(f)
            except json.decoder.JSONDecodeError as e:
                self.printer.error("Failed to parse configuration file %s:", SCD_CONFIG)
                self.printer.error(f"    {e}")
                sys.exit(1)

    def _clear_host_status(self, host: str) -> None:
        host_status = HostStatus()
        if host_status.clear(host):
            host_status.save()
            self.printer.info("Cleared status of host %s.", host)
            sys.exit(0)
        else:
            self.printer.error("Host status file does not contain host %s.", host)
            sys.exit(1)

    def _print_host_status(self, host_to_print: str) -> None:
        host_status = HostStatus()
        status = host_status.status
        if host_to_print == "all":
            self._print_colored_json(host_status.as_dict())
        elif host_to_print in status:
            self._print_colored_json(status[host_to_print])
        else:
            host_name = host_status.get_host_name(host_to_print)
            if host_name not in host_status.status:
                self.printer.error("No status saved for host %s.", host_to_print)
                sys.exit(1)

            self._print_colored_json(host_status.status[host_name])
        sys.exit(0)

    def _print_config(self, config: Dict[str, any]):
        self._print_colored_json(config)
        sys.exit(0)

    def _parse_settings(self, args: any, config: Dict[str, any]) -> None:
        self.hosts: List[str] = args.hosts or config.get("hosts") or self._error(
            "No host specified. Specify hosts either in %s under the attribute %s or as a command line argument.",
            SCD_CONFIG, '"hosts"'
        )

        self.user: str = args.user or config.get("user") or self._error(
            "No user specified. Specify user either in %s under the attribute %s or using the %s (%s) flag.",
            SCD_CONFIG, '"user"', "--user", "-u"
        )

        self.files = self._parse_files(config)
        self.scripts: List[str] = config.get("scripts") or []
        self.programs: Set[str] = set(config.get("programs") or [])
        self.shell: Optional[str] = config.get("shell")
        self.ignored_files: List[str] = config.get("ignored_files") or []
        self.timeout = float(config.get("timeout") or self.DEFAULT_TIMEOUT)
        self.port = int(args.port or config.get("port") or self.DEFAULT_PORT)
        self.verbose: bool = args.verbose
        self.force: bool = args.force
        self.private_key: str = args.private_key or config.get("private_key") or None
        self.password = self._get_password(config, args)

    def _parse_files(self, config: Dict[str, any]) -> List[FileData]:
        files = config.get("files") or []

        def _parse_file(file: any) -> FileData:
            if type(file) is dict:
                if not (len(file) == 2 and "source_path" in file and "host_path" in file):
                    self.printer.error("Invalid file: %s. Dict items in file should contain two elements, source_path and the host_path.", file)
                    sys.exit(1)

                return FileData(file["source_path"], file["host_path"])
            elif type(file) is list:
                if len(file) != 2:
                    self.printer.error("Invalid file: %s. List items in file should contain two elements, the source path and the host path.", file)
                    sys.exit(1)

                return FileData(file[0], file[1])
            elif type(file) is str:
                return FileData(file, file)
            else:
                self.printer.error("Invalid file: %s. Expected a string, dict or a list.", file)
                sys.exit(1)

        return [_parse_file(file) for file in files]

    def _get_password(self, config: Dict[str, any], args) -> str:
        password_file = args.password_file
        if password_file:
            if not os.path.isfile(password_file):
                self._error("The given password file %s does not exist.", password_file)

            return open(password_file).read().strip()

        if args.read_password:
            self.printer.info("Enter password: ", end="")
            return getpass(prompt="")

        return args.password or config.get("password")

    def _error(self, msg: str, *items) -> None:
        self.printer.error(msg, *items)
        sys.exit(1)

    def _print_colored_json(self, obj) -> None:
        formatted_json = json.dumps(obj, default=lambda o: o.__dict__, sort_keys=True, indent=4)
        if not colors.no_color:
            formatted_json = highlight(formatted_json, lexers.JsonLexer(), formatters.TerminalFormatter()).strip()
        for line in formatted_json.split("\n"):
            self.printer.info(line)
