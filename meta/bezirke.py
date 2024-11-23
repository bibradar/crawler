import requests, json
from bs4 import BeautifulSoup

URL = "https://wlan.lrz.de/apstat"

# data = requests.get(URL)
# write data to file
# with open("data.html", "w") as file:
#    file.write(data.text)

# read data from file
with open("data.html", "r") as file:
    data = file.read()

soup = BeautifulSoup(data, "html.parser")

tbody = soup.find_all("tbody")[0]
bezirke = {}

for tr in tbody.find_all("tr"):
    tds = tr.find_all("td")

    if len(tds[0].find_all("a")) == 0:
        continue

    a = tds[0].find_all("a")[0]
    if not a["href"] in bezirke:
        bezirke[a["href"]] = {
            "name": a.text,
            "address": [],
            "url": a["href"],
            "rooms": {},
        }

        for child in tds[0].children:
            if len(child.text) == 0 or child.text == a.text:
                continue

            bezirke[a["href"]]["address"].append(child.text)

    bezirk = bezirke[a["href"]]
    assert bezirk["name"] == a.text
    rooms = bezirk["rooms"]

    if not tds[1].text in rooms:
        rooms[tds[1].text] = {"name": tds[1].text, "aps": []}

    room = rooms[tds[1].text]
    aps = room["aps"]

    ap_a = tds[2].find_all("a")[0]
    aps.append({"name": ap_a.text, "url": ap_a["href"]})


with open("bezirke.json", "w") as file:
    file.write(json.dumps(bezirke, ensure_ascii=False))
