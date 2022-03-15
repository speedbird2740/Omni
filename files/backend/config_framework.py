import hashlib
import json
import os
import traceback
from multiprocessing.connection import Client, Listener

ports = [2001]
authkey = b"ANY_SECURE_STRING"
changes = []
HOST_PORT = 2000


def listener(port: int) -> Listener:
    global ports

    assert port not in ports if not port == 2001 else True

    if not port == 2001:
        ports.append(port)

    return Listener(("localhost", port), authkey=authkey)


def client(port: int):
    return Client(("localhost", port), authkey=authkey)


def createconfig(scope) -> dict:
    if scope == "server" and id is not None:
        guilddata = {"config": {}}

        guilddata["config"]["someoneping"] = True
        guilddata["config"]["botenabled"] = True
        guilddata["config"]["greetings"] = True
        guilddata["config"]["filterprofanity"] = True
        guilddata["config"]["deleteprofanity"] = False
        guilddata["config"]["noafkchannels"] = []
        guilddata["config"]["modmailchannel"] = None
        guilddata["config"]["log_channel"] = None
        guilddata["config"]["antiraid"] = {}
        guilddata["config"]["antiraid"]["enabled"] = False
        guilddata["config"]["antiraid"]["mode"] = "active"
        guilddata["config"]["antiraid"]["rate"] = [2, 4]
        guilddata["config"]["antiraid"]["underraid"] = False
        guilddata["config"]["antiraid"]["banprofanenicks"] = False
        guilddata["config"]["antiraid"]["blacklist"] = []
        guilddata["config"]["antiraid"]["count"] = 0
        guilddata["config"]["antiraid"]["action"] = "kick"
        guilddata["config"]["antiraid"]["revokeinvites"] = False
        guilddata["config"]["antiraid"]["raiseverification"] = False

        return guilddata

    elif scope == "other":
        botdata = {}
        botdata["modmailexempt"] = []
        botdata["global"] = {}
        globalconfig = botdata["global"]

        globalconfig["botenabled"] = True
        globalconfig["someoneping"] = True
        globalconfig["greetings"] = True

        botdata["errors"] = []
        botdata["commandscount"] = 0
        botdata["log"] = []
        botdata["blacklist"] = []
        botdata["violations"] = {}
        botdata["ratings"] = {}
        botdata["slapcount"] = {}
        botdata["fightcount"] = {}
        botdata["afkmembers"] = {}
        botdata["spacexnotification"] = []
        botdata["pingcooldown"] = []

        return botdata

    raise TypeError("Invalid parameters")


def loadconfig() -> dict:
    data = json.load(open("data/globalconfig.json", "r"))

    for folder in os.listdir("data/"):
        if os.path.isdir(f"data/{folder}"):
            data[folder] = json.load(open(f"data/{folder}/data.json", "r"))

    return data


def saveconfig(changes: dict or str) -> None:
    client = Client(("localhost", HOST_PORT), authkey=authkey)

    client.send(changes)
    client.close()


def processdeltas(deltas, config) -> dict:
    keys = deltas.keys()

    for key in keys:
        token = key.split(".")
        value = deltas[key]

        if token[0] == "guild":
            guildidhash = token[1]

            if token[2] == "config":
                guildconfig = config[guildidhash]["config"]
                setting = token[3]

                if not setting == "antiraid":
                    if type(guildconfig[setting]) == list:
                        action = token[4]

                        if action == "append":
                            guildconfig[setting].append(value)
                        elif action == "remove":
                            guildconfig[setting].remove(value)
                        else:
                            guildconfig[setting] = value
                    else:
                        assert setting in guildconfig

                        guildconfig[setting] = value

                elif setting == "antiraid":
                    raidconfig = guildconfig["antiraid"]
                    setting = token[4]

                    if type(raidconfig[setting]) == dict:
                        action = token[5]

                        if action == "append":
                            name = value[0]
                            value = value[1]
                            raidconfig[setting][name] = value
                        elif action == "remove":
                            name = value[0]

                            del raidconfig[setting][name]
                        elif action == "add":
                            name = value[0]
                            value = value[1]

                            raidconfig[setting][name] += value
                        else:
                            name = value[0]
                            value = value[1]

                            raidconfig[setting][name] = value

                    elif type(raidconfig[setting]) == list and not setting == "rate":
                        action = token[5]

                        if action == "append":
                            raidconfig[setting].append(value)
                        elif action == "remove":
                            raidconfig[setting].remove(value)
                        elif action == "reset":
                            raidconfig[setting] = []
                        else:
                            raidconfig[setting] = value

                    elif type(raidconfig[setting]) == int:
                        action = token[5]

                        if action == "add":
                            raidconfig[setting] += 1
                        elif action == "reset":
                            raidconfig[setting] = 0

                    else:
                        assert setting in raidconfig

                        raidconfig[setting] = value

            elif token[2] == "createconfig":
                config[guildidhash] = createconfig("server")

        elif token[0] == "createconfig":
            newconfig = createconfig("other")

            for key in newconfig.keys():
                config[key] = newconfig[key]

        elif type(config[token[0]]) == dict:
            setting = token[0]
            try:
                action = token[1]
            except:
                action = None

            if action == "append":
                name = value[0]
                value = value[1]

                config[setting][name] = value
            elif action == "remove":
                name = value[0]

                del config[setting][name]
            elif action == "add":
                name = value[0]
                value = value[1]

                config[setting][name] += value
            else:
                name = value[0]
                value = value[1]

                config[setting][name] = value

        elif type(botdata[token[0]]) == list:
            setting = token[0]
            try:
                action = token[1]
            except:
                action = None

            if action == "append":
                config[setting].append(value)
            elif action == "remove":
                config[setting].remove(value)
            elif action == "reset":
                botdata[setting] = []
            else:
                config[setting] = value

        elif type(config[token[0]]) == int:
            setting = token[0]
            action = token[1]

            if action == "add":
                config[setting] += 1
            elif action == "reset":
                config[setting] = 0

    return config


def host():
    listener = Listener(("localhost", HOST_PORT), authkey=authkey)

    while True:
        try:
            conn = listener.accept()
            data = conn.recv()

            if data == "close":
                for port in ports:
                    client = Client(("localhost", port), authkey=authkey)
                    client.send(data)

                listener.close()
                break

            for key in data.keys():
                token = key.split(".")
                value = data[key]

                if token[0] == "guild":
                    guildidhash = token[1]

                    if guildidhash not in changes:
                        changes.append(guildidhash)

                    if token[2] == "config":
                        guildconfig = botdata[guildidhash]["config"]
                        setting = token[3]

                        if not setting == "antiraid":
                            if type(guildconfig[setting]) == list:
                                action = token[4]

                                if action == "append":
                                    guildconfig[setting].append(value)
                                elif action == "remove":
                                    guildconfig[setting].remove(value)
                                else:
                                    guildconfig[setting] = value
                            else:
                                assert setting in guildconfig

                                guildconfig[setting] = value

                        elif setting == "antiraid":
                            raidconfig = guildconfig["antiraid"]
                            setting = token[4]

                            if type(raidconfig[setting]) == dict:
                                action = token[5]

                                if action == "append":
                                    name = value[0]
                                    config = value[1]

                                    raidconfig[setting][name] = config
                                elif action == "remove":
                                    name = value[0]

                                    del raidconfig[setting][name]
                                elif action == "add":
                                    name = value[0]
                                    value = value[1]

                                    raidconfig[setting][name] += value
                                else:
                                    name = value[0]
                                    value = value[1]

                                    raidconfig[setting][name] = value

                            elif type(raidconfig[setting]) == list and not setting == "rate":
                                action = token[5]

                                if action == "append":
                                    raidconfig[setting].append(value)
                                elif action == "remove":
                                    raidconfig[setting].remove(value)
                                elif action == "reset":
                                    raidconfig[setting] = []
                                else:
                                    raidconfig[setting] = value

                            elif type(raidconfig[setting]) == int:
                                action = token[5]

                                if action == "add":
                                    raidconfig[setting] += 1
                                elif action == "reset":
                                    raidconfig[setting] = 0

                            else:
                                assert setting in raidconfig

                                raidconfig[setting] = value

                    elif token[2] == "createconfig":
                        botdata[guildidhash] = createconfig("server")

                elif token[0] == "createconfig":
                    newconfig = createconfig("other")

                    if "globalconfig" not in changes:
                        changes.append("globalconfig")

                    for key in newconfig.keys():
                        botdata[key] = newconfig[key]

                elif type(botdata[token[0]]) == dict:
                    setting = token[0]
                    try:
                        action = token[1]
                    except:
                        action = None

                    if "globalconfig" not in changes:
                        changes.append("globalconfig")

                    if action == "append":
                        name = value[0]
                        config = value[1]

                        botdata[setting][name] = config
                    elif action == "remove":
                        name = value[0]

                        del botdata[setting][name]
                    elif action == "add":
                        name = value[0]
                        config = value[1]

                        botdata[setting][name] += config
                    else:
                        name = value[0]
                        config = value[1]

                        botdata[setting][name] = config

                elif type(botdata[token[0]]) == list:
                    setting = token[0]
                    try:
                        action = token[1]
                    except:
                        action = None

                    if "globalconfig" not in changes:
                        changes.append("globalconfig")

                    if action == "append":
                        botdata[setting].append(value)
                    elif action == "remove":
                        botdata[setting].remove(value)
                    elif action == "reset":
                        botdata[setting] = []
                    else:
                        botdata[setting] = value

                elif type(botdata[token[0]]) == int:
                    setting = token[0]
                    action = token[1]

                    if "globalconfig" not in changes:
                        changes.append("globalconfig")

                    if action == "add":
                        botdata[setting] += 1
                    elif action == "reset":
                        botdata[setting] = 0

            for port in ports:
                client = Client(("localhost", port), authkey=authkey)
                client.send(data)

            _saveconfig(changes)
            changes.clear()
        except:
            traceback.print_exc()


def gethash(value) -> str:
    if not type(value) == str or not type(value) == bytes:
        value = str(value)

    if not type(value) == bytes:
        value = bytes(value, "utf-8")

    return hashlib.sha256(value).hexdigest()


def _saveconfig(deltas):
    for delta in deltas:
        if delta == "globalconfig":
            data = {}
            keys = createconfig("other").keys()

            for key in keys:
                try:
                    data[key] = botdata[key]
                except KeyError:
                    data[key] = createconfig("other")[key]

            json.dump(data, open("data/globalconfig.json", "w"), indent=5)

        else:
            if not os.path.exists(f"data/{delta}"):
                os.mkdir(f"data/{delta}")

            json.dump(botdata[delta], open(f"data/{delta}/data.json", "w"), indent=5)


# This must not be inside if __name__ == "__main__" statement
while not os.path.exists("data/"):
    os.chdir(os.pardir)

botdata = loadconfig()
