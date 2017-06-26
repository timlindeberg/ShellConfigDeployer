import fnmatch
import os.path
import signal
import sys

from scd.deployment import ConfigDeployer
from scd.printer import Printer
from scd.settings import VERBOSE, IGNORED_FILES, HOME, HOST_STATUS, HOST, FORCE, PROGRAMS, FILES, SHELL


def main():
    printer = Printer(VERBOSE)

    def modified_files(all_files, host_status):
        modified_files.res = []

        last_deployment = host_status["last_deployment"]

        def modified(file, check_timestamp):
            for ignore in IGNORED_FILES:
                if fnmatch.fnmatch(file, ignore):
                    return
            if os.path.isdir(file):
                for f in os.listdir(file):
                    modified(file + "/" + f, check_timestamp)
                return

            if not check_timestamp or os.path.getctime(file) > last_deployment:
                modified_files.res.append(os.path.abspath(file))

        for f in all_files:
            file = HOME + "/" + f
            if not (os.path.isfile(file) or os.path.isdir(file)):
                printer.error("No such file or directory %s.", file)
                sys.exit(1)
            check_timestamp = f in host_status["deployed_files"]
            if check_timestamp:
                printer.info("Checking timestamp of %s", f, verbose=True)
            else:
                printer.info("Adding new file/folder %s", f, verbose=True)

            modified(file, check_timestamp)

        return modified_files.res

    def signal_handler(signal, frame):
        print()  # since most terminals echo ^C
        printer.error("Received Ctrl+C, exiting...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    host_status = HOST_STATUS.initial_status() if FORCE else HOST_STATUS[HOST]

    programs = set(PROGRAMS + ([SHELL] if SHELL else []))
    programs_to_install = [prog for prog in programs if prog not in host_status["installed_programs"]]
    files_to_deploy = modified_files(FILES, host_status)
    change_shell = SHELL and host_status.get("shell") != SHELL
    printer.info("Found %s files to deploy and %s programs to install.",
                 len(files_to_deploy), len(programs_to_install), verbose=True)

    if not files_to_deploy and not programs_to_install and not change_shell:
        printer.info("No changes to %s. Skipping deployment.", HOST, verbose=True)
        sys.exit(0)

    config_deployer = ConfigDeployer(HOST, programs_to_install, files_to_deploy, change_shell, printer)
    success = config_deployer.deploy()
    if success:
        printer.success("Configuration successfully deployed.")
        HOST_STATUS.update(HOST)
        HOST_STATUS.save()
    else:
        printer.error("%s", "Failed to deploy configuration.")


if __name__ == "__main__":
    main()
