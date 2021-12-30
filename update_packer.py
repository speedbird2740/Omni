import os
import zipfile

from cryptography.fernet import Fernet
from main import version


def packupdate(include_setup):
    text = open("main.py", "r", encoding="utf8").read()

    if "bot.run(api_key_dev)" in text:
        input("You have the dev api key enabled. Press enter to continue: ")

    if not os.path.exists("versions/"):
        os.mkdir("versions/")

    if not os.path.exists("temp/omni.temp"):
        open("temp/omni.temp", "w").write("")

    if not os.path.exists(f"versions/{version}"):
        os.mkdir(f"versions/{version}")
        os.mkdir(f"versions/{version}/files")
        os.mkdir(f"versions/{version}/files/backend")

    print("Zipping...")
    with zipfile.ZipFile("temp/omni.temp", "a") as zip:
        zip.write("main.py")
        open(f"versions/{version}/main.py", "wb").write(open("main.py", "rb").read()) # lines like these are for version control

        if include_setup == "yes":
            zip.write("setup.py")

        for file in os.listdir("files/"):
            if file.endswith(".py"):
                zip.write(f"files/{file}")

                open(f"versions/{version}/files/{file}", "wb").write(open(f"files/{file}", "rb").read())
            elif file == "backend":
                for file in os.listdir("files/backend/"):
                    if file.endswith(".py"):
                        zip.write(f"files/backend/{file}")

                        open(f"versions/{version}/files/backend/{file}", "wb").write(open(f"files/backend/{file}", "rb").read())

        zip.close()

    key = open("update.key", "rb").read()
    data = open("temp/omni.temp", "rb").read()

    data = Fernet(key).encrypt(data)

    open("omni_update.pack", "wb").write(data)


if os.path.exists("update.key") and os.path.exists("main.py") and __name__ == "__main__":
    if os.path.exists("omni_update.pack"):
        os.remove("omni_update.pack")

    if os.path.exists("temp/omni.temp"):
        os.remove("temp/omni.temp")

    setuppy = input("Should setup be included? ")

    packupdate(setuppy)
