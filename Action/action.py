import json
import itertools
import re
import requests
from requests.packages import urllib3
from datetime import datetime
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Constants
SSL_VERIFY = False
BASE_URL = 'https://www.action.com'
GRAPHQL_URL = 'https://www.action.com/api/graphql/'

# GraphQL query
GRAPHQL_QUERY = """
{
  "operationName": "StoreSearch",
  "variables": {
    "input": {
      "query": "",
      "page": %d
    }
  },
  "extensions": {
    "persistedQuery": {
      "sha256Hash": "f1c9f4a783fe2110aa19ad2223e632f86c7790ebea33d4839eec4b694bf72eb2",
      "version": 1
    }
  }
}
"""

day_name_mappings = {
    "Maandag": "Mo",
    "Dinsdag": "Tu",
    "Woensdag": "We",
    "Donderdag": "Th",
    "Vrijdag": "Fr",
    "Zaterdag": "Sa",
    "Zondag": "Su"
}

def fetch_graphql_data(page):
    headers = { 'Content-Type': 'application/json' }
    data = json.loads(GRAPHQL_QUERY % page)
    while True:
        try:
            response = requests.post(GRAPHQL_URL, headers=headers, json=data, verify=SSL_VERIFY)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error {e} fetching data for page {page}. Retrying in 61 seconds...")
            time.sleep(61)  # Wait for 61 seconds before retrying

def read_prop(obj, prop_path):
    parts = prop_path.split('.')
    value = obj
    for part in parts:
        value = value.get(part, {})
    return value

def parse_opening_hours(obj):
    data = read_prop(obj, 'openingDays')
    if len(data) <= 0: return ""

    dico = {}
    for d in data:
        day = d.get('dayName')
        opening_hours = d.get('openingHour')
        if opening_hours:
            hours = opening_hours[0].get('openFrom') + "-" + opening_hours[0].get('openUntil')
            if hours in dico:
                dico[hours].append(day)
            else:
                dico[hours] = [day]

    int_to_day = day_name_mappings

    slots = []

    for k in dico:
        days = dico[k]
        days = [int_to_day[day] for day in days]  # Convert to short form
        slots.append(f"{','.join(days)} {k}")

    sanitized = "; ".join(slots)
    sanitized = re.sub("^Mo-Su ", "", sanitized)
    return sanitized

def process_shop(shop):
    info = shop

    start = read_prop(info, 'meta.initialOpeningDate')

    # Skip shops that don't have start_date
    if len(start) <= 0: return None

    if 'T' in start:
        start = start.split('T')[0]

    date = datetime.strptime(start, '%Y-%m-%d')
    today = datetime.now()

    # Skip shops that are not opened yet
    if date > today: return None

    house_number = read_prop(info, 'address.houseNumber') or ''
    house_number_addition = read_prop(info, 'address.houseNumberExtra') or ''
    oh = parse_opening_hours(info)

    properties = {
        'shop': 'variety_store',
        'name': 'Action',
        'brand': 'Action',
        'brand:wikidata': 'Q2634111',
        'brand:wikipedia': 'nl:Action (winkel)',
        'alt_name': info.get('name'),
        'addr:street': info.get('address').get('street'),
        'addr:housenumber': f"{house_number}{house_number_addition}",
        'addr:postcode': info.get('address').get('postalCode'),
        'addr:city': info.get('address').get('city'),
        'addr:country': info.get('address').get('countryCode'),
        'start_date': start,
        'website': BASE_URL + info.get('url'),
        'ref:action:id': info.get('id'),
        'opening_hours': oh
    }
    shop_feature = {
        "type": "Feature",
        "properties": properties,
        "geometry": {
            "coordinates": [
                info.get('geoLocation').get('long'),
                info.get('geoLocation').get('lat')
            ],
            "type": "Point"
        }
    }
    return shop_feature

def main():
    page = 0
    features = []
    while True:
        data = fetch_graphql_data(page)
        shops = data.get('data', {}).get('storeSearchV2', [])
        if not shops:
            break
        for shop in shops:
            shop_feature = process_shop(shop)
            if shop_feature:
                features.append(shop_feature)
        page += 1

    res = 'action.geojson'
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(res, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    print(f'Dumped {len(features)} shops in the file: {res}')

if __name__ == "__main__":
    main()
