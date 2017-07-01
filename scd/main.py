import fnmatch
import os.path
import signal
import sys
import traceback

from pygments import highlight, lexers, formatters

from scd.config_deployer import ConfigDeployer
from scd.constants import *
from scd.host_communicator import HostCommunicator
from scd.printer import Printer
from scd.settings import Settings


def _color_exceptions(type, value, tb):
    traceback_text = "".join(traceback.format_exception(type, value, tb))
    lexer = lexers.get_lexer_by_name("pytb", stripall=True)
    formatter = formatters.TerminalFormatter()
    stack_trace = highlight(traceback_text, lexer, formatter).strip().split("\n")

    printer = Printer()
    printer.error("An unknown error occurred:")
    for line in stack_trace:
        printer.info(line)


def _sigint_handler(signal, frame):
    print()  # since most terminals echo ^C
    Printer().error("Received Ctrl+C, exiting...")
    sys.exit(0)


def _modified_files(settings, host_status, printer):
    _modified_files.res = []

    last_deployment = host_status["last_deployment"]

    def modified(file, check_timestamp):
        for ignored in settings.ignored_files:
            if fnmatch.fnmatch(file, ignored):
                return
        if os.path.isdir(file):
            for f in os.listdir(file):
                modified(file + "/" + f, check_timestamp)
            return

        if not check_timestamp or os.path.getctime(file) > last_deployment:
            _modified_files.res.append(os.path.abspath(file))

    for f in settings.files:
        file = HOME + "/" + f
        if not (os.path.isfile(file) or os.path.isdir(file)):
            printer.error("No such file or directory %s.", file)
            sys.exit(1)
        check_timestamp = f in host_status["deployed_files"]
        if check_timestamp:
            printer.info("Checking timestamp of %s", f, verbose=True)
        else:
            printer.info("Adding new item %s", f, verbose=True)

        modified(file, check_timestamp)

    return _modified_files.res


def main():
    sys.excepthook = _color_exceptions
    signal.signal(signal.SIGINT, _sigint_handler)

    settings = Settings()
    printer = Printer(settings.verbose)

    if settings.force:
        host_status = settings.host_status.initial_status()
    else:
        host_status = settings.host_status[settings.host]

    programs = set(settings.programs + ([settings.shell] if settings.shell else []))
    programs_to_install = [prog for prog in programs if prog not in host_status["installed_programs"]]
    files_to_deploy = _modified_files(settings, host_status, printer)
    shell = settings.shell
    if host_status.get("shell") == shell:
        shell = None

    printer.info("Found %s files to deploy and %s programs to install.",
                 len(files_to_deploy), len(programs_to_install), verbose=True)

    deploy_config(printer, settings, programs_to_install, files_to_deploy, shell)


def deploy_config(printer, settings, programs, files, shell):
    def on_error():
        printer.error("%s", "Failed to deploy configuration.")
        sys.exit(1)

    if not files and not programs and not shell:
        printer.info("No changes to %s. Skipping deployment.", settings.host, verbose=True)
        sys.exit(0)

    host_communicator = HostCommunicator(printer, settings)
    config_deployer = ConfigDeployer(printer, host_communicator)
    host_status = settings.host_status
    if config_deployer.install_programs(programs):
        host_status.update(settings, installed_programs=settings.programs)
    else:
        on_error()

    if config_deployer.deploy_files(files):
        host_status.update(settings, deployed_files=settings.files)
    else:
        on_error()

    if config_deployer.change_shell(shell):
        host_status.update(settings, shell=shell)
    else:
        on_error()

    printer.success("Configuration successfully deployed.")


if __name__ == "__main__":
    main()
