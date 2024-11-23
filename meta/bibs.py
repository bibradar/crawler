import json

# open bezirke.json

with open("bezirke.json", "r") as file:
    bezirke = json.loads(file.read())

bibs = {}

for bezirk in bezirke.values():

    if "bibliothek" in bezirk["name"].lower():
        bibs[bezirk["url"]] = bezirk
        continue

    for room in bezirk["rooms"].values():
        if not "bibliothek" in room["name"].lower():
            continue

        if not bezirk["url"] in bibs:
            bibs[bezirk["url"]] = {
                "name": bezirk["name"],
                "address": bezirk["address"],
                "url": bezirk["url"],
                "rooms": {},
            }

        bibs[bezirk["url"]]["rooms"][room["name"]] = room

with open("bibs.json", "w") as file:
    file.write(json.dumps(bibs, ensure_ascii=False))
