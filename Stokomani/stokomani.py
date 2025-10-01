import csv
import datetime
import geojson
import itertools
import re
import requests
import unicodedata
import urllib3
from geojson2osm import geojson2osm

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Constants
SSL_VERIFY = False
HISTORY_FILE = 'shop_count_history.csv'
URL_JSON = 'https://shops.stkmn.tech/get.php'
GEOJSON_FILE = 'stokomani.geojson'
RE_STREET = re.compile(r'(av |avenue |bd |boulevard |chemin |route |rue |esplanade |place )', re.IGNORECASE)
RE_NUMBER = re.compile(r'^[0-9]', re.IGNORECASE)

def fetch_json_data(url):
    response = requests.get(url, verify=SSL_VERIFY)
    if response.ok:
        return response.json()
    print(f"Error {response.status_code} while downloading: {url}")
    return []

def group_consecutive_indices(indices):
    for _, group in itertools.groupby(enumerate(indices), lambda x: x[1] - x[0]):
        group = list(group)
        yield group[0][1], group[-1][1]

def extract_hour(time_str):
    return time_str[:5] if time_str and len(time_str) >= 4 else None

def format_opening_hours(store):
    days_fr = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
    days_en = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
    time_slots = {}

    for i, day in enumerate(days_fr):
        start = extract_hour(store.get(f'magasin_{day}_am_start'))
        end = extract_hour(store.get(f'magasin_{day}_pm_stop'))
        if start and end:
            slot = f"{start}-{end}"
            time_slots.setdefault(slot, []).append(i)

    formatted = []
    for slot, indices in time_slots.items():
        indices.sort()
        for start_idx, end_idx in group_consecutive_indices(indices):
            if start_idx == end_idx:
                formatted.append(f"{days_en[start_idx]} {slot}")
            else:
                formatted.append(f"{days_en[start_idx]}-{days_en[end_idx]} {slot}")
    return '; '.join(formatted)

def raw_opening_hours(store):
    days_fr = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
    days_en = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
    return '; '.join(
        f"{days_en[i]} {store.get(f'magasin_{day}_am_start')}-{store.get(f'magasin_{day}_pm_stop')}"
        for i, day in enumerate(days_fr)
        if store.get(f'magasin_{day}_am_start') and store.get(f'magasin_{day}_pm_stop')
    )

def parse_address_components(street: str):
    result = {'housenumber': '', 'place': '', 'street': ''}
    if not street:
        return result

    parts = re.split(r'\n|, ', street)
    has_street = any(RE_STREET.match(part) for part in parts)

    for part in parts:
        part = part.strip()
        if RE_NUMBER.match(part):
            tokens = part.split(' ', 1)
            result['housenumber'] = tokens[0]
            result['street'] = tokens[1] if len(tokens) > 1 else ''
        elif RE_STREET.match(part):
            result['street'] = part
        elif not has_street:
            result['street'] = part
        else:
            result['place'] = part
    return result

def normalize_phone_number(phone: str) -> str:
    if not phone or not phone.startswith('0'):
        return phone
    digits = re.sub(r'\D', '', phone)
    if len(digits) != 10:
        return phone
    return f"+33 {digits[1]} {' '.join([digits[i:i+2] for i in range(2, 10, 2)])}"

def slugify_city(name: str) -> str:
    name = name.lower().replace("'", "-").replace("’", "-").replace(" ", "-")
    return unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')

def transform_store_to_feature(store):
    addr_raw = store['address']
    addr = parse_address_components(addr_raw.get('address1', ''))
    opening_hours = format_opening_hours(store)

    city_slug = slugify_city(addr_raw.get('city', ''))
    zip_code = addr_raw.get('zip', '')
    website = f"https://www.stokomani.fr/pages/boutique-stokomani-{city_slug}-{zip_code}"

    try:
        response = requests.head(website, allow_redirects=True, timeout=5)
        if response.status_code != 200:
            print(f"\033[93m⚠️  URL not accessible: {website}\033[0m")
    except Exception as e:
        print(f"\033[93m⚠️  Error checking URL: {website}\n💥 {e}\033[0m")

    phone = normalize_phone_number(addr_raw.get('phone', ''))
    fixme = ', '.join(filter(None, [addr_raw.get('address1'), addr_raw.get('address2')]))

    props = {
        'brand': 'Stokomani',
        'brand:wikidata': 'Q22249328',
        'brand:wikipedia': 'fr:Stokomani',
        'name': 'Stokomani',
        'alt_name': store.get('name', '').title().replace('  ', ' ').strip(),
        'addr:housenumber': addr['housenumber'],
        'addr:street': addr['street'],
        'addr:postcode': zip_code,
        'addr:city': addr_raw.get('city', '').title(),
        'addr:place': addr['place'],
        'fixme': f"Please verify address: {fixme}".replace('  ', ' ').strip(),
        'opening_hours': opening_hours,
        'shop': 'variety_store',
        'ref:FR:Stokomani:id': store.get('id_interne'),
        'phone': phone,
        'website': website
    }

    properties = {k: str(v) for k, v in props.items() if v}
    geometry = geojson.Point((addr_raw['coor_2'], addr_raw['coor_1']))
    return geojson.Feature(geometry=geometry, properties=properties)

def log_shop_count(date_str, count):
    with open(HISTORY_FILE, 'a', newline='') as file:
        csv.writer(file).writerow([date_str, count])

def main():
    print("\033[96m📡 Downloading JSON data...\033[0m")
    stores = fetch_json_data(URL_JSON)
    features = sorted([transform_store_to_feature(s) for s in stores],
                      key=lambda f: f['properties']['ref:FR:Stokomani:id'])

    geojson_data = geojson.FeatureCollection(features)
    with open(GEOJSON_FILE, 'w', encoding='utf-8') as f:
        geojson.dump(geojson_data, f, ensure_ascii=False, indent=2)
    print(f"\033[92m✅ {len(features)} stores exported to: {GEOJSON_FILE}\033[0m")

    with open('stokomani.osm', 'w', encoding='utf-8') as f:
        f.write(geojson2osm(geojson_data))
    print("\033[94m🗺️ OSM file successfully generated!\033[0m")

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    log_shop_count(today, len(features))

if __name__ == '__main__':
    main()