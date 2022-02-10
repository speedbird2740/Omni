import argparse
import platform
import pkg_resources

from subprocess import call

pkg_reqs = []


def check_reqs():
    warnings = []
    python_version = platform.python_version_tuple()

    if int(python_version[0]) < 3:
        raise Exception("Python 3.x required")
    if int(python_version[1]) != 7:
        warnings.append("WARNING: some Python packages may not install/work properly without Python 3.7")

    if not platform.system() == "Windows":
        raise Exception("Omni only supports the Windows operating system")

    packages = [dist.project_name for dist in pkg_resources.working_set]
    # More code in development

    return warnings


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-S", "--setup", help="Setup the Omni instance")
    parser.add_argument("-D", "--delete", help="Delete the Omni instance")
    parser.add_argument("-U", "--update", help="Update the Omni instance")

    args = parser.parse_args()

    if args.setup:
        pass
