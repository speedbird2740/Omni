import argparse
import json
import os
import platform
import sys
import traceback

import pkg_resources


def install_pkg(package):
    os.system(f"{sys.executable} -m pip install {package}")


def check_reqs():
    warnings = []
    python_version = platform.python_version_tuple()

    print("Checking Python version...")

    if int(python_version[0]) < 3:
        raise Exception("Python 3.x required")
    if int(python_version[1]) != 7:
        warnings.append("WARNING: some Python packages may not install/work properly without Python 3.7")

    print("Checking operating system...")
    if not platform.system() == "Windows":
        raise Exception("Omni only supports the Windows operating system")

    print("Cloning repository...")

    if not os.path.exists("temp/setup_cli"):
        os.mkdir("temp/setup_cli")

    git.Repo.clone_from("https://github.com/speedbird2740/Omni", "temp/setup_cli/Omni_repo/")

    try:
        update_reqs = json.load(open("updates.json", "r"))
    except Exception:
        traceback.print_exc()
        print("Failed to load update requirements. Get update requirements (updates.json) from the "
              "Omni repository and try again")

        input("Press enter to exit: ")
        sys.exit()

    print("Checking python packages...")

    from temp.setup_cli.Omni_repo.main import version

    pkg_reqs = update_reqs[version]["packages"]
    packages = [dist.project_name for dist in pkg_resources.working_set]

    for pkg in pkg_reqs:
        if pkg not in packages:
            install_pkg(pkg)


if __name__ == "__main__":
    print("Warning: setup utility is a work in progress")
    parser = argparse.ArgumentParser()

    parser.add_argument("-S", "--setup", help="Setup the Omni instance")
    parser.add_argument("-D", "--delete", help="Delete the Omni instance")
    parser.add_argument("-U", "--update", help="Update the Omni instance")

    args = parser.parse_args()

    try:
        import git
    except ImportError:
        input("Git is a required package for this utility. Press enter to install it: ")
        os.system(f"{sys.executable} -m pip install gitpython")
        import git

    if args.setup:
        pass
