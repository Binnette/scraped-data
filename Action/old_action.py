import json
import itertools
import os
import re
import requests
from requests.packages import urllib3
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import subprocess
from fake_useragent import UserAgent
from tqdm import tqdm
from multiprocessing import Pool, cpu_count, current_process

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Constants
SSL_VERIFY = False
BASE_URL = 'https://www.action.com'

# Set up Selenium WebDriver options
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument(f'user-agent={UserAgent().chrome}')

def find_chromedriver_path():
    if os.name == 'nt':  # Windows
        result = subprocess.run(['where', 'chromedriver.exe'], capture_output=True, text=True)
        if result.returncode == 0:
            paths = result.stdout.splitlines()
            if paths:
                return paths[0]
        raise FileNotFoundError("chromedriver.exe not found in PATH")
    else:  # Linux or macOS
        return '/path/to/chromedriver'  # Update with the path to your chromedriver

chromedriver_path = find_chromedriver_path()
service = Service(chromedriver_path)

def download_with_selenium(driver, url):
    try:
        driver.get(url)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "pre"))
        )
        element = driver.find_element(By.TAG_NAME, "pre")
        json_data = element.text
        return json_data
    except Exception as e:
        print(f"Error {e} downloading data from {url}")
        return None

def download_shop_opening_hours(driver, url):
    try:
        driver.get(url)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//script[@type='application/ld+json']"))
        )
        script_tag = driver.find_element(By.XPATH, "//script[@type='application/ld+json']")
        json_data = script_tag.get_attribute('innerHTML')
        return json_data
    except Exception as e:
        print(f"Error {e} downloading data from {url}")
        return None

def read_prop(obj, prop_name):
    prop = obj.get(prop_name)
    return "" if prop is None else prop

def ranges(i):
    for a, b in itertools.groupby(enumerate(i), lambda pair: pair[1] - pair[0]):
        b = list(b)
        yield b[0][1], b[-1][1]

def parse_opening_hours(obj):
    data = read_prop(obj, 'openingHours')
    if len(data) <= 0: return ""

    dico = {}
    for d in data:
        day = d.get('dayOfWeek')
        week = d.get('opens')
        opening = week.get('opens')
        closing = week.get('closes')
        if opening is not None and closing is not None:
            hours = opening + "-" + closing
            if hours in dico:
                dico[hours].append(day)
            else:
                dico[hours] = [day]

    int_to_day = {
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
        d = dico[k]
        d.sort()
        days = list(ranges(d))
        for t in days:
            first = t[0]
            last = t[1]
            if first != last:
                slots.append({
                    'index': first,
                    'range': int_to_day[first] + "-" + int_to_day[last] + " " + k
                })
            else:
                slots.append({
                    'index': first,
                    'range': int_to_day[first] + " " + k
                })

    slots.sort(key=lambda x: x.get('index'))
    sanitized = "; ".join(o.get('range') for o in slots)
    sanitized = re.sub("^Mo-Su ", "", sanitized)
    return sanitized

def process_shop(shop):
    driver = globals().get(f'driver_{current_process().name}')
    shop_id = shop.get('id')
    url = BASE_URL + '/api/stores/' + shop_id + '/'
    shop_json = download_shop_opening_hours(driver, url)
    if not shop_json:
        print(f"Failed to download data for shop {shop_id}. Skipping.")
        return None

    json_data = json.loads(shop_json)
    info = json_data

    start = read_prop(info, 'initialOpeningDate')

    # Skip shops that don't have start_date
    if len(start) <= 0: return None

    if start.find('T') != -1:
        index = start.index('T')
        start = start[:index]

    date = datetime.strptime(start, '%Y-%m-%d')
    today = datetime.now()

    # Skip shops that are not opened yet
    if date >= today: return None

    house_number = read_prop(info, 'address').get('streetAddress')
    house_number_addition = read_prop(info, 'address').get('addressLocality').get('city')
    oh = parse_opening_hours(info)

    properties = {
        'shop': 'variety_store',
        'name': 'Action',
        'brand': 'Action',
        'brand:wikidata': 'Q2634111',
        'brand:wikipedia': 'nl:Action (winkel)',
        'alt_name': info.get('name'),
        'addr:street': info.get('address').get('streetAddress'),
        'addr:housenumber': f"{house_number}{house_number_addition}",
        'addr:postcode': info.get('address').get('postalCode').get('postalCode'),
        'addr:city': info.get('address').get('addressLocality').get('city'),
        'addr:country': info.get('address').get('addressCountry'),
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
                info.get('geo').get('longitude'),
                info.get('geo').get('latitude')
            ],
            "type": "Point"
        }
    }
    return shop_feature

def worker_init(driver_path):
    global driver
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument(f'user-agent={UserAgent().chrome}')
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    globals()[f'driver_{current_process().name}'] = driver

def worker_exit(driver):
    driver.quit()

def main():
    url = BASE_URL + '/api/stores/coordinates/'
    driver = webdriver.Chrome(service=service, options=chrome_options)
    shops_json = download_with_selenium(driver, url)
    driver.quit()
    if not shops_json:
        print(f"Failed to download {url}. Exiting.")
        return

    shops_data = json.loads(shops_json)
    shops = shops_data.get('data').get('items')

    with Pool(cpu_count(), initializer=worker_init, initargs=(chromedriver_path,)) as pool:
        features = list(tqdm(pool.imap(process_shop, shops), total=len(shops), desc="Processing shops"))

    features = [feature for feature in features if feature is not None]

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
