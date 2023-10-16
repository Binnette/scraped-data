import itertools
import json
import os
import re
from bs4 import BeautifulSoup

import requests

wkFolder = "wk"
urlStores = "https://www.stokomani.fr/Assets/Rbs/Seo/100457/fr_FR/Rbs_Store_Store.1.xml"
fileStores = os.path.join(wkFolder, "Rbs_Store_Store.1.xml")


def download(url, filename):
    r = requests.get(url, allow_redirects=True, verify=False)
    if r.status_code == 200:
        open(filename, 'wb').write(r.content)
        return True
    else:
        print('Error %s downloading: %s' % (r.status_code, filename))
        return False


def ranges(i):
    for a, b in itertools.groupby(enumerate(i),
                                  lambda pair: pair[1] - pair[0]):
        b = list(b)
        yield b[0][1], b[-1][1]


def getTime(time):
    if len(time) < 5 or len(time) > 8:
        return None

    return time[:5]


def convertOpeningHours(hours):
    oh = {}
    for h in hours:
        d = h.get("dayOfWeek")[:2]
        if d not in oh.keys():
            oh[d] = {}
        opens = getTime(h.get("opens"))
        if opens is not None:
            oh[d]["opens"] = opens
        closes = getTime(h.get("closes"))
        if closes is not None:
            oh[d]["closes"] = closes

    dico = {}
    days = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
    for i, d in enumerate(days):
        if d in oh.keys():
            v = oh[d]
            h = v.get("opens") + "-" + v.get("closes")
            if h not in dico:
                dico[h] = []
            dico[h].append(i)

    intToDay = {0: "Mo", 1: "Tu", 2: "We", 3: "Th", 4: "Fr", 5: "Sa", 6: "Su"}

    slots = []

    for k in dico:
        if len(k) <= 0: continue
        d = dico[k]
        d.sort()
        days = list(ranges(d))
        for t in days:
            first = t[0]
            last = t[1]
            if first != last:
                slots.append({
                    'index':
                    first,
                    'range':
                    intToDay[first] + "-" + intToDay[last] + " " + k
                })
            else:
                slots.append({
                    'index': first,
                    'range': intToDay[first] + " " + k
                })

    slots.sort(key=lambda x: x.get('index'))
    sanitized = "; ".join(o.get('range') for o in slots)
    sanitized = re.sub("^Mo-Su ", "", sanitized)
    return sanitized


def convertAddress(address):
    street = False
    words = re.split("\\n|, ", address)
    a = {
        "housenumber": "",
        "street": "",
        "postcode": "",
        "city": "",
        "country": "",
        "full": " ".join(words)
    }

    for w in words:
        if re.match("^Stokomani", w, re.IGNORECASE):
            pass
        elif re.match("^France", w, re.IGNORECASE):
            a["country"] = "France"
        elif re.match("^[0-9]{4} ", w):
            a["postcode"] = "0" + w[:4]
            a["city"] = w[5:]
        elif re.match("^[0-9]{5} ", w):
            a["postcode"] = w[:5]
            a["city"] = w[6:]
        elif re.match("^[0-9]", w):
            a["housenumber"] = w.split(" ", 1)[0]
            a["street"] = w.split(" ", 1)[1]
            street = True
        elif re.match(
                "^(av |avenue |bd |boulevard |chemin | route |esplanade |place )",
                w, re.IGNORECASE):
            a["street"] = w
            street = True
        elif not street:
            a["street"] = w

    if a["city"].isupper():
        a["city"] = a["city"].title()

    return a


def convertData(data):
    geo = data.get("geo")
    hours = data.get("openingHoursSpecification")
    oh = convertOpeningHours(hours)
    address = data.get("address")
    addr = convertAddress(address)
    fixme = 'Please remove this fixme after completing the address given the following string: '
    name = data.get("name")
    if name.isupper():
        name = name.title()

    feature = {
        "type": "Feature",
        "properties": {
            "brand": "Stokomani",
            "brand:wikidata": "Q22249328",
            "brand:wikipedia": "fr:Stokomani",
            "name": "Stokomani",
            "alt_name": "Stokomani " + name,
            'addr:housenumber': addr.get('housenumber'),
            'addr:street': addr.get('street'),
            'addr:postcode': addr.get('postcode'),
            'addr:city': addr.get('city'),
            'fixme': fixme + addr.get('full'),
            "opening_hours": oh,
            "shop": "variety_store",
            "website": data.get("url")
        },
        "geometry": {
            "coordinates": [geo.get("longitude"),
                            geo.get("latitude")],
            "type": "Point"
        }
    }

    return feature


if not os.path.exists(wkFolder):
    os.makedirs(wkFolder)

# download the xml containing url to each shop webpage (html)
if not os.path.exists(fileStores):
    download(urlStores, fileStores)

storePages = []

with open(fileStores) as f:
    soup = BeautifulSoup(f, 'html.parser')
    locs = soup.find_all("loc")
    for l in locs:
        storePages.append(l.string)

docs = []

for url in storePages:
    docname = url.rsplit("/", 1)[-1]
    docpath = os.path.join(wkFolder, docname)
    docs.append(docpath)
    if not os.path.exists(docpath):
        downloaded = download(url, docpath)

features = []

for doc in docs:
    with open(doc, encoding="utf-8") as f:
        soup = BeautifulSoup(f, 'html.parser')
        main = soup.find("main")
        script = main.find("script", {"type": "application/ld+json"})
        jsonstr = script.string
        data = json.loads(jsonstr)
        feature = convertData(data)
        features.append(feature)

res = 'stokomani.geojson'
if os.path.exists(res):
    os.remove(res)


geojson = {
	"type": "FeatureCollection",
	"features": features
}

with open(res, 'w', encoding='utf-8') as f:
    json.dump(geojson, f, ensure_ascii=False, indent=2)

print(f'Dump {len(features)} shops in file: {res}')