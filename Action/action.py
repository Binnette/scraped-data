import json
import itertools
import os
import re
import requests
from requests.packages import urllib3
from datetime import datetime

"""
1. Run this script to create the file action.geojson
2. Open action.geojson with JOSM
3. Save the layer as action.osm
4. Run MapRoulette command: mr coop change --out challenge.geojson action.osm
5. Create a MapRoulette challenge with the file challenge.geojson
"""

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

folder = 'wk/'
fshops = folder + 'shops.json'
baseUrl = 'https://www.action.com'

def download(url, filename):
    r = requests.get(url, allow_redirects=True, verify=False)
    if r.status_code == 200:
        open(filename, 'wb').write(r.content)
    else:
        print('Error %s downloading: %s' % (r.status_code, filename))

def readJsonFile(filename):
    f = open(filename, encoding="utf8")
    jsonData = json.load(f)
    f.close()
    return jsonData

def readProp(obj, propName):
    prop = obj.get(propName)
    return "" if prop is None else prop

def ranges(i):
    for a, b in itertools.groupby(enumerate(i), lambda pair: pair[1] - pair[0]):
        b = list(b)
        yield b[0][1], b[-1][1]

def parseOpeningHours(obj):
    data = readProp(obj, 'openingHours')
    if len(data) <= 0: return ""

    dico = {}
    for d in data:
        day = d.get('day')
        day = 7 if day == 0 else day
        week = d.get('thisWeek')
        opening = week.get('opening')
        closing = week.get('closing')
        if opening is not None and closing is not None:
            hours = opening + "-" + closing
            if hours in dico:
                dico[hours].append(day)
            else:
                dico[hours] = [day]

    intToDay = {
        1: "Mo",
        2: "Tu",
        3: "We",
        4: "Th",
        5: "Fr",
        6: "Sa",
        7: "Su"
    }

    slots = []

    for k in dico:
        d = dico[k]
        d.sort()
        days = list(ranges(d))
        for t in days :
            first = t[0]
            last = t[1]
            if first != last:
                slots.append({
                    'index': first,
                    'range': intToDay[first] + "-" + intToDay[last] + " " + k
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
    

if not os.path.exists(fshops):
    url = baseUrl + '/api/stores/coordinates/'
    download(url, fshops)

jsonData = readJsonFile(fshops)
shops = jsonData.get('data').get('items')

for i in shops:
    id =  i.get('id')
    url = baseUrl + '/api/stores/' + id + '/'
    filename = folder + id + '.json'
    if not os.path.exists(filename):
        print('## Download %s (%s/%s)' % (filename, shops.index(i), len(shops)))
        download(url, filename)

osmShops = []
for i in shops:
    id =  i.get('id')
    filename = folder + id + '.json'
    jsonData = readJsonFile(filename)
    info = jsonData.get('data')

    start = readProp(info, 'initialOpeningDate')

    # skip shops that don't have start_date
    if len(start) <= 0: continue

    if start.find('T') != -1:
        index = start.index('T')
        start = start[:index]
    
    date = datetime.strptime(start, '%Y-%m-%d')
    today = datetime.now()

    # skip shops that are not openned yet
    if date >= today: continue

    housenumber = readProp(info, 'houseNumber')
    addition = readProp(info, 'houseNumberAddition')
    oh = parseOpeningHours(info)

    properties = {
        'shop': 'variety_store',
        'name': 'Action',
        'brand': 'Action',
        'brand:wikidata': 'Q2634111',
        'brand:wikipedia': 'nl:Action (winkel)',
        'alt_name': info.get('store'),
        'addr:street': info.get('street'),
        'addr:housenumber': "{0}{1}".format(housenumber, addition),
        'addr:postcode': info.get('postalCode'),
        'addr:city': info.get('city'),
        'addr:country': info.get('countryCode'),
        'start_date': start,
        'website': baseUrl + info.get('url'),
        'ref:action:id': info.get('id'),
        'opening_hours' : oh
    }
    shop = {
        "type": "Feature",
        "properties": properties,
        "geometry": {
            "coordinates": [
                info.get('longitude'),
                info.get('latitude')
            ],
            "type": "Point"
        }
    }
    osmShops.append(shop)

res = 'action.geojson'
if os.path.exists(res):
    os.remove(res)


geojson = {
  "type": "FeatureCollection",
  "features": osmShops
}

with open(res, 'w', encoding='utf-8') as f:
    json.dump(geojson, f, ensure_ascii=False, indent=2)
  
print('File written: ' + res)