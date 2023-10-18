import xml.etree.ElementTree as ET
import json
import html
import re
import requests
import urllib.parse

xml_url = 'https://boulangeries.marieblachere.com/wp-content/plugins/superstorefinder-wp/ssf-wp-xml.php'
xml_file = 'ssf-wp-xml.php.xml'

# Download XML file
response = requests.get(xml_url)
if response.status_code == 200:
    open(xml_file, 'wb').write(response.content)
else:
    print(f'Error {response.status_code} when downloading: {xml_file}')
    exit

# Parse the XML file
tree = ET.parse('ssf-wp-xml.php.xml')
root = tree.getroot()

# Create an empty list to store the features
features = []

# Parse address from a string
def parse_address(address):
    properties = None
    # Use regular expressions to extract the components of the address
    # Assume the address format is: number street city, zipcode
    # Use named groups to capture the components
    #pattern = r'(?P<number>\d+)\s+(?P<street>.+?)\s+(?P<city>.+?),\s+(?P<zipcode>\d+)'
    #pattern = r'(?:(?P<number>\d+)\s+)?(?P<street>.+?)\s+(?P<city>.+?),\s+(?P<zipcode>\d+)'
    pattern = r'(?:(?P<number>\d+)\s+)?(?P<street>.+?)\s\s(?P<city>.+?),\s+(?P<zipcode>\d+)'

    match = re.search(pattern, address)
    # If the address matches the pattern, assign the properties from the match groups
    if match:
        properties = {}
        properties['addr:city'] = match.group('city')
        properties['addr:housenumber'] = match.group('number')
        properties['addr:postcode'] = match.group('zipcode')
        properties['addr:street'] = match.group('street')
    # Return the object with properties
    return properties

# Loop through the items inside the store block
for item in root.find('store'):
    # Create a dictionary to store the feature properties
    properties = {}

    # Unescape alt_name
    alt_name = item.find('location').text
    alt_name = html.unescape(alt_name)

    # Parse address
    address = item.find('address').text
    address = html.unescape(address)
    addr = parse_address(address)

    # Assign the properties from the item elements By alphabetic order
    if addr:
        if addr['addr:city']:
            properties['addr:city'] = addr['addr:city'].title().strip()
        if addr['addr:housenumber']:
            properties['addr:housenumber'] = addr['addr:housenumber'].strip()
        if addr['addr:postcode']:
            properties['addr:postcode'] = addr['addr:postcode'].strip()
        if addr['addr:street']:
            properties['addr:street'] = addr['addr:street'].strip().capitalize()

    properties['alt_name'] = alt_name
    properties['brand'] = 'Marie Blachère'
    properties['brand:wikidata'] = 'Q62082410'
    properties['brand:wikipedia'] = 'fr:Marie Blachère'
    properties['fixme'] = 'Check address and delete fixme and fixme:addr.'
    properties['fixme:addr'] = address
    properties['name'] = 'Boulangerie Marie Blachère'
    properties['ref:FR:MarieBlachere:id'] = item.find('storeId').text
    properties['shop'] = 'bakery'
    properties['website'] = item.find('exturl').text.replace(" ", "%20")

    # Create a dictionary to store the feature geometry
    geometry = {}
    # Assign the geometry type and coordinates from the properties
    geometry['type'] = 'Point'
    geometry['coordinates'] = [float(item.find('longitude').text), float(item.find('latitude').text)]

    # Create a dictionary to store the feature
    feature = {}
    # Assign the feature type, properties and geometry
    feature['type'] = 'Feature'
    feature['properties'] = properties
    feature['geometry'] = geometry

    # Append the feature to the list of features
    features.append(feature)

# Create a dictionary to store the geojson object
geojson = {}
# Assign the geojson type and features
geojson['type'] = 'FeatureCollection'
geojson['features'] = features

# Write the geojson object to a file named marie_blachere.geojson
with open('marie_blachere.geojson', 'w', encoding='utf-8') as f:
    json.dump(geojson, f, indent=4, ensure_ascii=False)

# Print a message to indicate the completion of the task
print('The geojson file has been created successfully.')
