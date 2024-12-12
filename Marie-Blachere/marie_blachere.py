import csv
import datetime
import html
import json
import re
import requests
from bs4 import BeautifulSoup
from geojson2osm import geojson2osm
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

# Constants
SSL_VERIFY = False
JSON_URL = 'https://boulangeries.marieblachere.com/_next/data/6QhMlpC_aVGtbWYxnjA9t/fr/all.json'
HISTORY_FILE = 'bakery_count_history.csv'

def fetch_json_data(url):
    """Fetch JSON data from the given URL."""
    response = requests.get(url, verify=SSL_VERIFY)
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Error {response.status_code} when fetching data from: {url}')
        exit()

def capitalize_first_letter(input_string):
    """Capitalize the first letter of the input string."""
    if len(input_string) < 2:
        return input_string
    return input_string[0].upper() + input_string[1:]

def parse_street_address(street_address):
    """Parse the street address into house number and street name."""
    properties = {}
    pattern = r'(?P<number>\d+\sà\s\d+)\s(?P<street>.+)'
    match = re.search(pattern, street_address)
    if match:
        properties['addr:housenumber'] = match.group('number')
        properties['addr:street'] = capitalize_first_letter(match.group('street'))
    return properties

def convert_opening_hours(opening_hours_spec):
    """Convert opening hours specification to a formatted string."""
    day_mapping = {
        "http://schema.org/Monday": "Mo",
        "http://schema.org/Tuesday": "Tu",
        "http://schema.org/Wednesday": "We",
        "http://schema.org/Thursday": "Th",
        "http://schema.org/Friday": "Fr",
        "http://schema.org/Saturday": "Sa",
        "http://schema.org/Sunday": "Su"
    }
    formatted_hours = []
    for spec in opening_hours_spec:
        day = day_mapping.get(spec["dayOfWeek"], "")
        opens = spec["opens"]
        closes = spec["closes"]
        formatted_hours.append(f"{day} {opens}-{closes}")
    return "; ".join(formatted_hours)

def format_fr_phone_number(phone_number):
    """Format a French phone number to the international format."""
    digits = re.sub(r'\D', '', phone_number)
    if digits.startswith('0'):
        digits = '+33' + digits[1:]
    if len(digits) == 12:
        return f"+33 {digits[3]} {digits[4:6]} {digits[6:8]} {digits[8:10]} {digits[10:12]}"
    return digits

def extract_json_ld(url):
    """Extract JSON-LD data from the given URL."""
    response = requests.get(url, verify=SSL_VERIFY)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        script_tag = soup.find('script', type='application/ld+json')
        if script_tag:
            return json.loads(script_tag.string)
    return None

def process_bakery(bakery_data):
    """Process a single bakery's data and return a GeoJSON feature."""
    properties = {
        'alt_name': html.unescape(bakery_data['label']),
        'addr:city': bakery_data['City'].capitalize(),
        'addr:postcode': bakery_data['PostalCode']
    }

    bakery_url = f"https://boulangeries.marieblachere.com{bakery_data['url']}"
    json_ld = extract_json_ld(bakery_url)

    if json_ld:
        bakery_info = json_ld[0]
        address_info = bakery_info['address']
        geo_info = bakery_info['geo']

        if bakery_data['City'] != address_info['addressLocality']:
            properties['fixme:addr:city'] = f"Two different city names: {bakery_data['City']} and {address_info['addressLocality']}"
        if bakery_data['PostalCode'] != address_info['postalCode']:
            properties['fixme:addr:postcode'] = f"Two different postal codes: {bakery_data['PostalCode']} and {address_info['postalCode']}"

        properties.update(parse_street_address(address_info['streetAddress']))

        phone = bakery_info.get('telephone', '')
        if address_info['addressCountry'] == 'FR':
            phone = format_fr_phone_number(phone)

        properties.update({
            'brand': 'Marie Blachère',
            'brand:wikidata': 'Q62082410',
            'brand:wikipedia': 'fr:Marie Blachère',
            'fixme': 'Check address and opening_hours and delete all fixmes',
            'fixme:addr': f'{address_info["streetAddress"]} {address_info["postalCode"]} {address_info["addressLocality"]}',
            'name': 'Boulangerie Marie Blachère',
            'ref:FR:MarieBlachere:id': bakery_data['Id'],
            'ref:FR:MarieBlachere:code': bakery_data['Code'],
            'shop': 'bakery',
            'website': bakery_url.replace(" ", "%20"),
            'phone': phone,
            'email': bakery_info.get('email', ''),
            'opening_hours': convert_opening_hours(bakery_info['openingHoursSpecification'])
        })

        geometry = {
            'type': 'Point',
            'coordinates': [geo_info['longitude'], geo_info['latitude']]
        }

        feature = {
            'type': 'Feature',
            'properties': properties,
            'geometry': geometry
        }

        return feature
    return None

def main():
    data = fetch_json_data(JSON_URL)
    bakery_data_list = data['pageProps']['allPois']

    # Use multiprocessing Pool to process bakeries in parallel
    with Pool(cpu_count()) as pool:
        results = list(tqdm(pool.imap_unordered(process_bakery, bakery_data_list), total=len(bakery_data_list), desc="Processing bakeries"))

    features = [feature for feature in results if feature is not None]

    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }

    with open('marie_blachere.geojson', 'w', encoding='utf-8') as file:
        json.dump(geojson, file, indent=4, ensure_ascii=False)

    print('The geojson file has been created successfully.')

    osm_xml = geojson2osm(geojson)

    with open('marie_blachere.osm', 'w', encoding='utf-8') as output_file:
        output_file.write(osm_xml)

    print('The OSM file has been created successfully.')

    # Record the number of bakeries extracted
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    with open(HISTORY_FILE, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([current_date, len(features)])

if __name__ == "__main__":
    main()
