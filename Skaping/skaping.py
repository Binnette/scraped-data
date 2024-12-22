import csv
import datetime
import json
import re
import requests
from bs4 import BeautifulSoup
from geojson2osm import geojson2osm

# Constants
SSL_VERIFY = False
HISTORY_FILE = 'webcam_count_history.csv'

def fetch_html_content(url):
    """Fetch the HTML content from the given URL."""
    response = requests.get(url, verify=SSL_VERIFY)
    response.raise_for_status()  # Raise an error for bad status codes
    return response.text

def parse_html(html_content):
    """Parse the HTML content and extract marker and window information."""
    soup = BeautifulSoup(html_content, 'html.parser')
    scripts = soup.find_all('script')
    features = []

    for script in scripts:
        script_text = script.string
        if script_text:
            index = 1

            while True:
                marker_regex = re.compile(r'markers\[' + str(index) + '\].*?\n.*?LatLng\((.*?), (.*?)\).*?\n.*?\n.*?\n.*?title:"(.*?)"')
                window_regex = re.compile(r'windows\[' + str(index) + '\].*?\n.*?href=\\\\"(.*?)\\\\">.*?')

                marker = marker_regex.findall(script_text)
                window = window_regex.findall(script_text)

                if len(marker) == 0 and len(window) == 0:
                    break

                if len(marker) != 1 or len(window) != 1:
                    raise Exception(f"Mismatch between {len(marker)} marker and {len(window)} for index {index}")

                lat = float(marker[0][0])
                lon = float(marker[0][1])
                title = marker[0][2].strip()
                url = window[0]

                feature = create_geojson_feature(lon, lat, title, url)
                features.append(feature)
                index += 1

    return features

def create_geojson(features):
    """Create a GeoJSON structure from the features."""
    return {
        "type": "FeatureCollection",
        "features": features
    }

def create_geojson_feature(lon, lat, title, url):
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat]
        },
        "properties": {
            "contact:webcam": url,
            "description": title,
            "man_made": "surveillance"
        }
    }

def save_geojson(geojson, filename):
    """Save the GeoJSON structure to a file."""
    with open(filename, 'w', encoding='utf-8') as geojson_file:
        json.dump(geojson, geojson_file, indent=2, ensure_ascii=False)

def record_history(date, count):
    """Record the date and count of webcams to a CSV file."""
    with open(HISTORY_FILE, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([date, count])

def main():
    url = "https://www.skaping.com/camera/map"
    geojson_filename = "skaping.geojson"

    # Fetch the HTML content
    html_content = fetch_html_content(url)

    # Parse the HTML content
    features = parse_html(html_content)

    # Create the GeoJSON structure
    geojson = create_geojson(features)

    # Save the GeoJSON to a file
    save_geojson(geojson, geojson_filename)

    # Print the count of webcams
    print(f"{len(features)} webcams saved to {geojson_filename}")

    osm_xml = geojson2osm(geojson)
    with open('skaping.osm', 'w', encoding='utf-8') as output_file:
        output_file.write(osm_xml)
    print('The OSM file has been created successfully.')

    # Record the date and count of webcams to a CSV file
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    record_history(current_date, len(features))

if __name__ == "__main__":
    main()
