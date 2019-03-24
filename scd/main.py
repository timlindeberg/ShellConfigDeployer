import signal
import sys
import traceback
from typing import List

from pygments import highlight, lexers, formatters

from scd import colors
from scd.config_deployer import ConfigDeployer, DeploymentException
from scd.constants import *
from scd.host import Host
from scd.host_configuration import HostConfiguration
from scd.host_status import HostStatus, empty_status
from scd.printer import Printer
from scd.settings import Settings
from scd.utils import *


class SCD:

    def __init__(self):
        self.settings: Settings = None
        self.host_status: HostStatus = None
        self.printer = Printer()
        self.hosts: List[Host] = []
        sys.excepthook = self.color_exceptions
        signal.signal(signal.SIGINT, self.sigint_handler)

    def run(self):
        self.settings = Settings()
        self.printer = Printer(self.settings.verbose)
        self.host_status = HostStatus()

        for host in self.settings.hosts:
            start = timer()
            self.printer.info("Checking host %s.", host, verbose=True)
            self.printer.info("", verbose=True)
            try:
                if self._deploy_config_to_host(host):
                    time = get_time(start)
                    self.printer.success("Configuration successfully deployed to %s in %s s.", host, time)
            except DeploymentException:
                self.printer.error("Failed deploying configuration to %s.", host)

    def _deploy_config_to_host(self, url: str) -> bool:
        host = Host(self.printer, self.settings, self.host_status, url)
        self.hosts.append(host)

        host_status = empty_status() if self.settings.force else host.status
        configuration = HostConfiguration(self.printer, self.settings, host_status)

        if configuration.is_empty():
            self.printer.info("No changes to %s. Skipping deployment.", host.name, verbose=True)
            return False

        self._deploy_configuration(host, configuration)
        return True

    def _deploy_configuration(self, host: Host, configuration: HostConfiguration) -> None:
        config_deployer = ConfigDeployer(self.printer, host)

        config_deployer.install_programs(configuration.programs)
        self.host_status.update(host.name, installed_programs=self.settings.programs)

        config_deployer.deploy_files(configuration.files)
        self.host_status.update(host.name, deployed_files=self.settings.files)

        config_deployer.change_shell(configuration.shell)
        self.host_status.update(host.name, shell=configuration.shell)

        executed_scripts = config_deployer.run_scripts(configuration.scripts)
        self.host_status.update(host.name, scripts=executed_scripts)
        if len(configuration.scripts) != len(executed_scripts):
            raise DeploymentException

    def color_exceptions(self, type, value, tb):
        stack_trace = "".join(traceback.format_exception(type, value, tb))
        if not colors.no_color:
            lexer = lexers.get_lexer_by_name("pytb", stripall=True)
            formatter = formatters.TerminalFormatter()
            stack_trace = highlight(stack_trace, lexer, formatter)

        self.printer.error("An unknown error occurred:")
        for line in stack_trace.strip().split("\n"):
            self.printer.info(line)

    def sigint_handler(self, _signal, _frame):
        print()  # since most terminals echo ^C
        self.printer.error("Received ^C, exiting...")

        for file in TEMPORARY_FILES:
            if os.path.isfile(file):
                os.remove(file)

        for host in self.hosts:
            host.cleanup()

        sys.exit(0)


if __name__ == "__main__":
    scd = SCD()
    scd.run()
