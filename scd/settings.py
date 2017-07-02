import json
import sys
import textwrap
from getpass import getpass

from pygments import highlight, lexers, formatters

from scd import colors
from scd.argparser import parser
from scd.constants import *
from scd.host_status import HostStatus
from scd.printer import Printer


class Settings:
    DEFAULT_PORT = 22
    DEFAULT_TIMEOUT = 5
    DEFAULT_CONFIG = textwrap.dedent("""
    {
        "user": "",
        "ignored_files": [
            ".git",
            ".DS_Store"
        ],
        "files": [
            ".oh-my-zsh",
            ".zshrc"
        ],
        "programs": [
            "unzip",
            "tree"
        ]
    }
    """).strip()

    def __init__(self):
        args = parser.parse_args()
        colors.no_color = args.no_color

        self.printer = Printer(False)

        self._check_config_file()
        self.host_status = HostStatus()
        config = self._parse_config_file()

        colors.no_color = args.no_color or config.get("use_color") is False

        if args.clear_status:
            self._clear_host_status(args.clear_status)

        if args.print_host_status:
            self._print_host_status()

        if args.print_config:
            self._print_config(config)

        self._parse_settings(args, config)

    def _check_config_file(self):
        if os.path.isfile(SCD_CONFIG):
            return

        self.printer.error("Missing configuration file %s.", SCD_CONFIG)
        self.printer.error("Creating default configuration. Please edit %s with your settings.", SCD_CONFIG)
        if not os.path.exists(SCD_FOLDER):
            os.makedirs(SCD_FOLDER)

        with open(SCD_CONFIG, "w") as f:
            f.write(self.DEFAULT_CONFIG)
            sys.exit(1)

    def _parse_config_file(self):
        with open(SCD_CONFIG) as f:
            try:
                return json.load(f)
            except json.decoder.JSONDecodeError as e:
                self.printer.error("Failed to parse configuration file %s:", SCD_CONFIG)
                self.printer.error("    " + str(e))
                sys.exit(1)

    def _clear_host_status(self, host):
        if self.host_status.clear(host):
            self.host_status.save()
            self.printer.info("Cleared status of host %s.", host)
            sys.exit(0)
        else:
            self.printer.error("Host status file does not contain host %s.", host)
            sys.exit(1)

    def _print_host_status(self):
        self.printer.success("Host Status")
        self.printer.info("")
        self._print_colored_json(self.host_status.status)
        sys.exit(0)

    def _print_config(self, config):
        self.printer.success("Config")
        self.printer.info("")
        self._print_colored_json(config)
        sys.exit(0)

    def _parse_settings(self, args, config):
        self.hostname = args.hostname or config.get("host") or self._error(
            "No host specified. Specify host either in %s under the attribute %s or as a command line argument.",
            SCD_CONFIG, '"host"'
        )

        self.user = args.user or config.get("user") or self._error(
            "No user specified. Specify user either in %s under the attribute %s or using the %s (%s) flag.",
            SCD_CONFIG, '"user"', "--user", "-u"
        )

        self.files = config.get("files") or self._error(
            "Which files to deploy are not specified. Specify which files to deploy in %s under the attribute %s.",
            SCD_CONFIG, '"files"'
        )

        self.programs = config.get("programs") or self._error(
            "Which programs to install are not specified. " +
            "Specify which programs to install in %s under the attribute %s.",
            SCD_CONFIG, '"programs"'
        )

        self.shell = config.get("shell")
        self.ignored_files = config.get("ignored_files") or []
        self.timeout = float(config.get("timeout") or self.DEFAULT_TIMEOUT)
        self.port = int(args.port or config.get("port") or self.DEFAULT_PORT)
        self.verbose = args.verbose
        self.force = args.force

        self.password = self._get_password(args)

    def _get_password(self, args):
        password_file = args.password_file
        if password_file:
            if not os.path.isfile(password_file):
                self._error("The given password file %s does not exist.", password_file)

            return open(password_file).read().strip()

        if args.read_password:
            self.printer.info("Enter password: ", end="")
            return getpass(prompt="")

        if args.password:
            return args.password

        return None

    def _error(self, msg, *items):
        self.printer.error(msg, *items)
        sys.exit(1)

    def _print_colored_json(self, obj):
        formatted_json = json.dumps(obj, sort_keys=True, indent=4)
        if not colors.no_color:
            formatted_json = highlight(formatted_json, lexers.JsonLexer(), formatters.TerminalFormatter()).strip()
        for line in formatted_json.split("\n"):
            self.printer.info(line)
