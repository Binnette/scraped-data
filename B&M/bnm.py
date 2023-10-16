import html
import itertools
import json
import os
import re
from bs4 import BeautifulSoup

def ranges(i):
    for a, b in itertools.groupby(enumerate(i), lambda pair: pair[1] - pair[0]):
        b = list(b)
        yield b[0][1], b[-1][1]

def getPostcode(data):
    return data.split(" ")[0]

def getCity(data):
    b = data.split(" ")
    city = " ".join(b[1:])
    return city.title()

def getHousenumber(s):
    if re.match('^[0-9].*, ', s):
        return s.split(", ")[0]
    if re.match('^[0-9].* ', s):
        return s.split(" ")[0]
    return ""

def getStreet(s):
    if re.match('^[0-9].*, ', s):
        return " ".join(s.split(", ")[1:])
    if re.match('^[0-9].* ', s):
        return " ".join(s.split(" ")[1:])
    return s

def startWithStreet(s):
    if re.match('^allée', s, re.IGNORECASE): return True
    if re.match('^rue', s, re.IGNORECASE): return True
    if re.match('^chemin', s, re.IGNORECASE): return True
    if re.match('^avenue', s, re.IGNORECASE): return True
    if re.match('^boulevard', s, re.IGNORECASE): return True
    return False

def getAddr(data):
    soup = BeautifulSoup(data)
    # Find div with address
    addr_div = soup.select_one("div.col-xs-12")
    # Remove all the <p> tags inside the addr_div
    for p_tag in addr_div.find_all("p"):
        p_tag.decompose()
    # Remove all the <div> tags inside the addr_div
    for div_tag in addr_div.find_all("div"):
        div_tag.decompose()
    # Remove all the <a> tags inside the addr_div
    for a_tag in addr_div.find_all("a"):
        a_tag.decompose()
    # Use findAll(text=True) on the text
    lines = addr_div.findAll(text=True)
    # Remove \t from lines
    for l in range(len(lines)):
        lines[l] = lines[l].replace('\t', ' ').strip()

    if len(lines) == 2:
        return {
            'addr:housenumber': getHousenumber(lines[0]),
            'addr:street': getStreet(lines[0]),
            'addr:place': '',
            'addr:postcode': getPostcode(lines[1]),
            'addr:city': getCity(lines[1]),
            'note': " ".join(lines)
        } 
    if len(lines) == 3:
        if re.match("^[0-9]", lines[0]) or startWithStreet(lines[0]):
            housenumber = getHousenumber(lines[0])
            street = getStreet(lines[0])
            place = lines[1]
        elif re.match("^[0-9]", lines[1]) or startWithStreet(lines[1]):
            housenumber = getHousenumber(lines[1])
            street = getStreet(lines[1])
            place = lines[0]
        else:
            housenumber = getHousenumber(lines[0])
            street = getStreet(lines[0])
            place = lines[1]
        
        return {
            'addr:housenumber': housenumber,
            'addr:street': street,
            'addr:place': place,
            'addr:postcode': getPostcode(lines[2]),
            'addr:city': getCity(lines[2]),
            'note': " ".join(lines)
        }
    print("error addr: %s" % len(lines))


def gethours(day):
    if len(day) <= 0: return ""
    hours = ""
    zero = day.get("0-")
    if zero is not None and len(zero.get("from")) > 0 and len(zero.get("to")) > 0:
        hours += zero.get("from")[:5] + "-" + zero.get("to")[:5]
    one = day.get("1-")
    if one is not None and len(one.get("from")) > 0 and len(one.get("to")) > 0:
        hours += "," + one.get("from")[:5] + "-" + one.get("to")[:5]
    return hours

def formatHours(data):
    if len(data) <= 0: return ""
    dico = {}
    days = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
    for i, d in enumerate(days):
        dat = data.get(d)
        if dat is not None:
            hours = gethours(dat)
            if dico.get(hours) is None:
                dico[hours] = [i]
            else:
                dico[hours].append(i)
                
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

file = open('shops.json', mode='r', encoding='utf-')
data = json.load(file)
file.close()

features = []
for dat in data:
    shop = dat[1]
    oh = formatHours(shop.get('hours'))
    addr = getAddr(shop.get('pop'))
    
    properties = {
        'shop': 'variety_store',
        'name': 'B&M',
        'alt_name': html.unescape(shop.get('id')),
        'brand': 'B&M',
        'brand:wikidata': 'Q4836931',
        'brand:wikipedia': 'en:B&M',
        "opening_hours": oh,
        'addr:housenumber': addr.get('addr:housenumber').strip(),
        'addr:street': addr.get('addr:street').strip(),
        'addr:place': addr.get('addr:place').strip(),
        'addr:postcode': addr.get('addr:postcode').strip(),
        'addr:city': addr.get('addr:city').strip(),
        'note': addr.get('note').strip()
    }

    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [
                shop.get('lon'),
                shop.get('lat')
            ]
        },
        "properties": properties
    }

    features.append(feature)

res = 'bnm.geojson'
if os.path.exists(res):
    os.remove(res)


geojson = {
  "type": "FeatureCollection",
  "features": features
}

with open(res, 'w', encoding='utf-8') as f:
    json.dump(geojson, f, ensure_ascii=False, indent=2)
  
print(f'Dump {len(features)} shops in the file: {res}')