import signal
import sys
import traceback

from pygments import highlight, lexers, formatters

from scd import colors
from scd.config_deployer import ConfigDeployer, DeploymentException
from scd.constants import *
from scd.host import Host
from scd.host_configuration import HostConfiguration
from scd.host_status import HostStatus
from scd.printer import Printer
from scd.settings import Settings


def main():
    sys.excepthook = _color_exceptions
    signal.signal(signal.SIGINT, _sigint_handler)

    settings = Settings()
    printer = Printer(settings.verbose)

    for host in settings.hosts:
        start = timer()
        printer.info("Checking host %s.", host, verbose=True)
        printer.info("", verbose=True)
        try:
            if _deploy_config_to_host(printer, settings, host):
                time = get_time(start)
                printer.success("Configuration successfully deployed to %s in %s s.", host, time)
        except DeploymentException:
            printer.error("Failed deploying configuration to %s.", host)


def _deploy_config_to_host(printer, settings, url):
    host = Host(printer, settings, url)

    host_status = HostStatus.initial_status() if settings.force else host.status
    configuration = HostConfiguration(printer, settings, host_status)

    if configuration.is_empty():
        printer.info("No changes to %s. Skipping deployment.", host.name, verbose=True)
        return False

    _deploy_configuration(printer, settings, host, configuration)
    return True


def _deploy_configuration(printer, settings, host, configuration):
    config_deployer = ConfigDeployer(printer, host)
    host_status = host.host_statuses

    config_deployer.install_programs(configuration.programs)
    host_status.update(host.name, installed_programs=settings.programs)

    config_deployer.deploy_files(configuration.files)
    host_status.update(host.name, deployed_files=settings.files)

    config_deployer.change_shell(configuration.shell)
    host_status.update(host.name, shell=configuration.shell)

    executed_scripts = config_deployer.run_scripts(configuration.scripts)
    host_status.update(host.name, scripts=executed_scripts)
    if len(configuration.scripts) != len(executed_scripts):
        raise DeploymentException


def _color_exceptions(type, value, tb):
    traceback_text = "".join(traceback.format_exception(type, value, tb))
    lexer = lexers.get_lexer_by_name("pytb", stripall=True)
    formatter = formatters.TerminalFormatter()
    stack_trace = traceback_text if colors.no_color else highlight(traceback_text, lexer, formatter)

    printer = Printer()
    printer.error("An unknown error occurred:")
    for line in stack_trace.strip().split("\n"):
        printer.info(line)


def _sigint_handler(signal, frame):
    print()  # since most terminals echo ^C
    Printer().error("Received ^C, exiting...")
    sys.exit(0)


if __name__ == "__main__":
    main()
