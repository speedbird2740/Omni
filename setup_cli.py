import argparse
import json
import os
import platform
import sys
import traceback
from getpass import getpass

import pkg_resources


def install_pkg(package):
    os.system(f'"{sys.executable}" -m pip install {package}')


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

    if os.path.exists("temp/setup_cli"):
        os.remove("temp/setup_cli")

    if not os.path.exists("temp/"):
        os.mkdir("temp/")

    os.mkdir("temp/setup_cli/")

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


def copy_files():
    print("copying files...")
    install_dir = "src"
    repo_dir = "temp/setup_cli/Omni_repo"
    if not os.path.exists(install_dir):
        os.mkdir(install_dir)
    if not os.path.exists(f"{install_dir}/data/"):
        os.mkdir(f"{install_dir}/data/")
    if not os.path.exists(f"{install_dir}/files/"):
        os.mkdir(f"{install_dir}/files/")
    if not os.path.exists(f"{install_dir}/files/backend/"):
        os.mkdir(f"{install_dir}/files/backend/")

    data = open(f"{repo_dir}/main.py", "rb").read()
    open(f"{install_dir}/main.py", "wb").write(data)

    for obj in os.listdir(f"{repo_dir}/files"):
        if os.path.isfile(obj):
            data = open(f"{repo_dir}/files/{obj}", "rb").read()
            open(f"{install_dir}/files/{obj}", "wb").write(data)
        elif obj == "backend":
            for file in os.listdir(f"{repo_dir}/files/backend/"):
                data = open(f"{repo_dir}/files/backend/{file}", "rb").read()
                open(f"{install_dir}/files/backend/{file}", "wb").write(data)


def setup_config():
    print("creating configuration...")
    os.chdir("src/")

    open("data/globalconfig.json", "w").write("0")  # Import will not work without this

    from src.files.backend.config_framework import createconfig

    config = createconfig("other")

    config["discord"] = {}
    config["discord"]["name"] = input("Enter your Discord bot name: ")
    config["discord"]["prefix"] = input("Enter your Discord bot's command prefix: ")
    config["discord"]["owner_id"] = int(input("Enter the Discord bot's owner ID: "))
    config["discord"]["log_channel"] = int(input("Enter the logging channel ID: "))
    config["discord"]["api_key"] = getpass("Enter your Discord API key: ")

    config["webservices"] = {}
    config["webservices"]["img_srv"] = {}
    img_srv_keys = config["webservices"]["img_srv"]

    img_srv = input("Supported image lookup providers\n\n"
                    "Google [1]\n"
                    "Microsoft Bing [2]\n\n"
                    "Choose an image lookup provider: ")

    while img_srv not in ["1", "2"]:
        img_srv = input("Choose a image API provider\n\n"
                        "Google [1]\n"
                        "Microsoft Bing [2]")

    img_srv = int(img_srv)

    if img_srv == 1:
        img_srv_keys["service"] = img_srv
        img_srv_keys["api_key"] = getpass("Enter your Google custom search API key: ")
        img_srv_keys["client_cx"] = getpass("Enter your Google client cx: ")

    elif img_srv == 2:
        img_srv_keys["service"] = img_srv
        img_srv_keys["api_key"] = getpass("Enter your Microsoft Bing API key: ")

    config["webservices"]["nasa_api_key"] = getpass("Enter your NASA API key: ")

    json.dump(config, open("data/globalconfig.json", "w"))
    os.chdir(os.pardir)


if __name__ == "__main__":
    print("Warning: setup utility is a work in progress")
    parser = argparse.ArgumentParser()

    parser.add_argument("--setup", action="store_true", help="Setup the Omni instance")
    parser.add_argument("--delete", action="store_true", help="Delete the Omni instance")
    parser.add_argument("--update", action="store_true", help="Update the Omni instance")

    args = parser.parse_args()

    try:
        import git
    except ImportError:
        input("Git is a required package for this utility. Press enter to install it: ")
        os.system(f'"{sys.executable}" -m pip install gitpython')
        import git

    if args.setup:
        check_reqs()
        copy_files()
        setup_config()
