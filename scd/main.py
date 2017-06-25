import fnmatch
import os.path
import signal
import sys

from scd.deployment import ConfigDeployer
from scd.printer import Printer
from scd.settings import VERBOSE, IGNORED_FILES, HOME, HOST_STATUS, HOST, FORCE, PROGRAMS, FILES


def main():
    printer = Printer(VERBOSE)

    def modified_files(all_files, last_modified):
        modified_files.res = []

        def modified(file):
            for ignore in IGNORED_FILES:
                if fnmatch.fnmatch(file, ignore):
                    return
            if os.path.isdir(file):
                for f in os.listdir(file):
                    modified(file + '/' + f)
                return

            if os.path.getctime(file) > last_modified:
                modified_files.res.append(os.path.abspath(file))

        for f in all_files:
            printer.info("Checking timestamp of %s", f, verbose=True)
            modified(HOME + '/' + f)

        return modified_files.res

    def signal_handler(signal, frame):
        printer.error("Received Ctrl+C, exiting...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    host_status = HOST_STATUS.initial_status() if FORCE else HOST_STATUS[HOST]

    programs_to_install = [prog for prog in PROGRAMS if prog not in host_status['installed_programs']]
    files_to_deploy = modified_files(FILES, host_status['last_modified'])

    printer.info("Found %s files to deploy and %s programs to install.",
                 len(files_to_deploy), len(programs_to_install), verbose=True)
    if len(files_to_deploy) == 0 and len(programs_to_install) == 0:
        printer.info("No changes to %s. Skipping deployment.", HOST, verbose=True)
        sys.exit(0)

    config_deployer = ConfigDeployer(HOST, programs_to_install, files_to_deploy, printer)
    success = config_deployer.deploy()
    if success:
        printer.success("%s", "Configuration successfully deployed.")
        HOST_STATUS.update(HOST)
        HOST_STATUS.save()
    else:
        printer.error("%s", "Failed to deploy configuration.")


if __name__ == '__main__':
    main()
