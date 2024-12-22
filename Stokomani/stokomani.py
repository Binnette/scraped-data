import csv
import datetime
import geojson
import itertools
import re
import requests
import urllib3
from bs4 import BeautifulSoup
from geojson2osm import geojson2osm
from multiprocessing import Pool, cpu_count
from tqdm import tqdm

# Disable InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Constants
SSL_VERIFY = False
HISTORY_FILE = 'shop_count_history.csv'
URL_STORES = "https://www.stokomani.fr/Assets/Rbs/Seo/100457/fr_FR/Rbs_Store_Store.1.xml"
GEOJSON_FILE = 'stokomani.geojson'

# Download content from a URL
def download(url):
    response = requests.get(url, allow_redirects=True, verify=SSL_VERIFY)
    if response.status_code == 200:
        return response.content
    else:
        print(f'Error {response.status_code} downloading: {url}')
        return None

def ranges(i):
    for a, b in itertools.groupby(enumerate(i), lambda pair: pair[1] - pair[0]):
        b = list(b)
        yield b[0][1], b[-1][1]

def getTime(time):
    if len(time) < 5 or len(time) > 8:
        return None
    return time[:5]

# Convert opening hours from a structured format to a string
def convert_opening_hours(hours):
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
        if len(k) <= 0:
            continue
        d = dico[k]
        d.sort()
        days = list(ranges(d))
        for t in days:
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

# Convert address to structured format
def convert_address(address):
    words = re.split(r"\n|, ", address)
    re_street = re.compile(r"^(av |avenue |bd |boulevard |chemin |route |rue |esplanade |place )", re.IGNORECASE)
    have_street = any(re_street.match(w) for w in words)

    a = {
        "city": "",
        "country": "",
        "full": " ".join(words),
        "housenumber": "",
        "place": "",
        "postcode": "",
        "street": "",
    }

    for w in words:
        if re.match(r"^Stokomani", w, re.IGNORECASE):
            pass
        elif re.match(r"^France", w, re.IGNORECASE):
            a["country"] = "France"
        elif re.match(r"^[0-9]{4} ", w):
            a["postcode"] = "0" + w[:4]
            a["city"] = w[5:]
        elif re.match(r"^[0-9]{5} ", w):
            a["postcode"] = w[:5]
            a["city"] = w[6:]
        elif re.match(r"^[0-9]", w):
            a["housenumber"] = w.split(" ", 1)[0]
            a["street"] = w.split(" ", 1)[1]
        elif re_street.match(w):
            a["street"] = w
        elif not have_street:
            a["street"] = w
        else:
            a["place"] = w

    if a["city"].isupper():
        a["city"] = a["city"].title()

    return a

# Convert JSON-LD data to GeoJSON feature
def convert_data(data):
    geo = data.get("geo")
    hours = data.get("openingHoursSpecification", [])
    opening_hours = convert_opening_hours(hours)
    address = data.get("address", "")
    addr = convert_address(address)

    return geojson.Feature(
        geometry=geojson.Point((geo.get("longitude"), geo.get("latitude"))),
        properties={
            "brand": "Stokomani",
            "brand:wikidata": "Q22249328",
            "brand:wikipedia": "fr:Stokomani",
            "name": "Stokomani",
            "alt_name": data.get("name", "").title(),
            'addr:housenumber': addr['housenumber'],
            'addr:street': addr['street'],
            'addr:postcode': addr['postcode'],
            'addr:city': addr['city'],
            'addr:place': addr['place'],
            'fixme': f"Please remove this fixme after completing the address given the following string: {addr['full']}",
            "opening_hours": opening_hours,
            "shop": "variety_store",
            "ref:FR:Stokomani:id": data.get("branchCode", ""),
            "website": data.get("url", "")
        }
    )

# Process a single store URL
def process_url(url):
    content = download(url)
    if content:
        soup = BeautifulSoup(content, 'html.parser')
        script = soup.find("main").find("script", {"type": "application/ld+json"})
        if script:
            data = geojson.loads(script.string)
            return convert_data(data)
    return None

def record_history(date, count):
    """Record the date and count of webcams to a CSV file."""
    with open(HISTORY_FILE, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([date, count])

def main():
    print(f"Number of CPU cores available: {cpu_count()}")

    # Download the XML containing URLs to each shop webpage
    xml_content = download(URL_STORES)
    soup = BeautifulSoup(xml_content, 'xml')
    store_urls = [loc.text for loc in soup.find_all("loc")]

    # Use multiprocessing Pool to process URLs in parallel
    with Pool(cpu_count()) as pool:
        features = list(tqdm(pool.imap_unordered(process_url, store_urls), total=len(store_urls), desc="Processing stores"))

    # Filter out None results
    features = [feature for feature in features if feature is not None]

    # Sort by id
    features.sort(key=lambda x: x['properties']['ref:FR:Stokomani:id'])

    geojson_data = geojson.FeatureCollection(features)

    # Write to GeoJSON file
    with open(GEOJSON_FILE, 'w', encoding='utf-8') as f:
        geojson.dump(geojson_data, f, ensure_ascii=False, indent=2)

    print(f'Dump {len(features)} shops in file: {GEOJSON_FILE}')

    osm_xml = geojson2osm(geojson_data)
    with open('stokomani.osm', 'w', encoding='utf-8') as output_file:
        output_file.write(osm_xml)
    print('The OSM file has been created successfully.')

    # Record the date and count of webcams to a CSV file
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    record_history(current_date, len(features))

if __name__ == "__main__":
    main()
