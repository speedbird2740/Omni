import datetime
import json
import time

import requests
from bs4 import BeautifulSoup as bs


def getdata():  # code to get gifs is inaccurate at times
    slapgifs = []
    fightgifs = []
    facts = []

    data = bs(requests.get("https://tenor.com/search/anime-slap-gifs").text, features="html.parser")
    all_gifs = data.select('img')

    for link in all_gifs:
        if "slap" in str(link).lower():
            links = str(link).split('"')
            for link in links:
                if link.endswith(".gif"):
                    slapgifs.append(link)

    data = bs(requests.get("https://tenor.com/search/fight-anime-gifs").text, features="html.parser")
    all_gifs = data.select('img')

    for link in all_gifs:
        if "fight" in str(link).lower():
            links = str(link).split('"')
            for link in links:
                if link.endswith(".gif"):
                    fightgifs.append(link)

    resp = bs(requests.get("https://www.thefactsite.com/100-space-facts/").text, features="html.parser")
    raw_facts = resp.select("h2")

    for fact in raw_facts:
        if "list" in str(fact):
            fact = str(fact).replace("<h2 class=\"list\">", "")
            fact = fact.replace("</h2>", "")
            fact = fact.replace("<em>", " ")
            fact = fact.replace("</em>", " ")
            facts.append(fact)

    nasalinks = json.load(open("data/nasalinks.json", "r"))

    return slapgifs, fightgifs, facts, nasalinks


def spacex_data():
    spacex = {}
    nasa_key = "DEMO_KEY"

    apod = json.loads(requests.get(f"https://api.nasa.gov/planetary/apod?api_key={nasa_key}").text)
    spacex["company"] = json.loads(requests.get("https://api.spacexdata.com/v4/company").text)
    time.sleep(0.5)
    spacex["cores"] = json.loads(requests.get("https://api.spacexdata.com/v4/cores").text)
    time.sleep(0.5)
    spacex["capsules"] = json.loads(requests.get("https://api.spacexdata.com/v4/capsules").text)
    time.sleep(0.5)
    spacex["dragons"] = json.loads(requests.get("https://api.spacexdata.com/v4/dragons").text)
    time.sleep(0.5)
    spacex["history"] = json.loads(requests.get("https://api.spacexdata.com/v4/history").text)
    time.sleep(0.5)
    spacex["starlink"] = json.loads(requests.get("https://api.spacexdata.com/v4/starlink").text)
    time.sleep(0.5)
    spacex["next"] = json.loads(requests.get("https://api.spacexdata.com/v4/launches/next").text)
    spacex["last_updated"] = datetime.datetime.utcnow().strftime(r"%m/%d/%Y %H:%M:%S")

    return apod, spacex