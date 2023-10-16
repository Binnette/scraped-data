import itertools
import json
import os
import re

def ranges(i):
    for a, b in itertools.groupby(enumerate(i), lambda pair: pair[1] - pair[0]):
        b = list(b)
        yield b[0][1], b[-1][1]

def formatPhone(p):
    if p is None: return ""
    if len(p) != 12: return p
    a = (p[:3], p[3], p[4:6], p[6:8], p[8:10], p[10:])
    return " ".join(a)

def getHousenumber(s):
    if not re.match("^[0-9]", s): return ""
    index = s.find(",")
    if index > 0:
        return s[:index].strip()
    else:
        return s.split(" ")[0]

def getStreet(s):
    if not re.match("^[0-9]", s): return s
    index = s.find(",")
    if index > 0:
        return s[index+1:].strip()
    else:
        return " ".join(s.split(" ")[1:])

def compareStreet(s1, s2):
    s1 = s1.replace(",", "")
    s2 = s2.replace(",", "")
    return s1 == s2

def formatAddr(s1, s2):
    if compareStreet(s1, s2):
        return {
            'housenumber': getHousenumber(s1),
            'street': getStreet(s1),
            'place': ''
        }

    if re.match("^[0-9]", s1):
        return {
            'housenumber': getHousenumber(s1),
            'street': getStreet(s1),
            'place': s2
        }
    
    if re.match("^[0-9]", s2):
        return {
            'housenumber': getHousenumber(s2),
            'street': getStreet(s2),
            'place': s1
        }

    return {
        'housenumber': getHousenumber(s1),
        'street': getStreet(s1),
        'place': s2
    }

def formatHours(data):
    if len(data) <=0: return ""

    for d in data:
        arr = data.get(d)
        for i, a in enumerate(arr):
            hh = a.split('-')
            if re.match("^[0-9]:", hh[0]):
                hh[0] = "0" + hh[0]
            if re.match("^[0-9]:", hh[1]):
                hh[1] = "0" + hh[1]
            arr[i] = "-".join(hh)
        

    arr = [
        ",".join(data.get('monday')),
        ",".join(data.get('tuesday')),
        ",".join(data.get('wednesday')),
        ",".join(data.get('thursday')),
        ",".join(data.get('friday')),
        ",".join(data.get('saturday')),
        ",".join(data.get('sunday'))
    ]

    dico = {}
    for i, d in enumerate(arr):
        if dico.get(d) is None:
            dico[d] = [i]
        else:
            dico[d].append(i)

    intToDay = {
        0: "Mo",
        1: "Tu",
        2: "We",
        3: "Th",
        4: "Fr",
        5: "Sa",
        6: "Su"
    }
    
    slots = []

    for k in dico:
        if len(k) <= 0: continue
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

file = open('gifi.json', mode='r', encoding='utf-8')
jsonData = json.load(file)

features = []
for data in jsonData:
    phone = formatPhone(data.get('international_phone'))
    addr = formatAddr(data.get('street1'), data.get('street2'))
    oh = formatHours(data.get('formatted_opening_hours'))
    properties = {
        "name": "GiFi",
        "alt_name": data.get('name'),
        "shop": "variety_store",
        "brand": "GiFi",
        "brand:wikidata": "Q3105439",
        "brand:wikipedia": "fr:Gifi",
        "ref:FR:GiFi:id": data.get('id'),
        "addr:housenumber": addr.get("housenumber"),
        "addr:street": addr.get("street"),
        "addr:place": addr.get("place"),
        "addr:postcode": data.get('zip_code'),
        "addr:city": data.get('city').get('name'),
        "addr:country": data.get('country').get('code'),
        "phone": phone,
        "website": data.get('external_urls').get('website'),
        "opening_hours": oh,
        "note": ", ".join(data.get('formatted_address'))
        #"external_id": data.get('id')
    }

    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [
                data.get('_geoloc').get('lng'),
                data.get('_geoloc').get('lat')
            ]
        },
        "properties": properties
    }

    features.append(feature)

res = 'gifi.geojson'
if os.path.exists(res):
    os.remove(res)


geojson = {
	"type": "FeatureCollection",
	"features": features
}

with open(res, 'w', encoding='utf-8') as f:
    json.dump(geojson, f, ensure_ascii=False, indent=2)
  
print(f'Dump {len(features)} shops in file: {res}')