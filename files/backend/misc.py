import random


def getid() -> str:
    id = ""
    charlist = list("QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm1234567890")

    for i in range(6):
        id += charlist[random.randint(random.randint(0, len(charlist) - 1), len(charlist))]

    return id
