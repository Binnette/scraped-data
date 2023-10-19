import requests
import json
import geojson
from bs4 import BeautifulSoup

# Import the re library for regular expressions
import re

# Define the url to scrape
url = "https://www.paul.fr/stores/"

# Get the HTML content from the url
response = requests.get(url)
html = response.text

# Parse the HTML with BeautifulSoup
soup = BeautifulSoup(html, "html.parser")

# Find all the script elements with type "text/x-magento-init"
scripts = soup.find_all("script", {"type": "text/x-magento-init"})

def simple_opening_hours(opening_hours):
    days = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']
    result = []

    for i, hours in enumerate(opening_hours):
        if hours:
            result.append(f"{days[i]} {hours[0]['start_time']}-{hours[0]['end_time']}")

    return ';'.join(result)

def parse_opening_hours(opening_hours):
    if len(opening_hours) == 0:
        return ""
    days = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']
    day_hours = [None]*7
    for i in range(1, 8):
        index = i % 7
        if opening_hours[index]:
            day_hours[i-1] = f"{opening_hours[index][0]['start_time']}-{opening_hours[index][0]['end_time']}"

    groups = []
    cur_group = None
    for i in range(0, 7):
        h = day_hours[i]
        if h == None:
            if cur_group:
                groups.append(cur_group)
                cur_group = None
            continue
        if cur_group == None:
            cur_group = {
                "hours": h,
                "min_day": i,
                "max_day": i
            }
        elif cur_group["hours"] == h:
            cur_group["max_day"] = max(cur_group["max_day"], i)    
        else:
            groups.append(cur_group)
            cur_group = {
                "hours": h,
                "min_day": i,
                "max_day": i
            }
    if cur_group:
        groups.append(cur_group)

    result = []
    if len(groups) == 0:
        return ""
    if len(groups) == 1 and groups[0]["min_day"] == 0 and groups[0]["max_day"] == 6:
        return groups[0]["hours"]

    for group in groups:
        if group["min_day"] == group["max_day"]:
            day = group["min_day"]
            result.append(f'{days[(day+1)%7]} {group["hours"]}')
        else:
            min_day = group["min_day"]
            max_day = group["max_day"]
            result.append(f'{days[(min_day+1)%7]}-{days[(max_day+1)%7]} {group["hours"]}')

    return ';'.join(result)

# Initialize an empty list to store the geojson features
features = []

# Loop through all the script elements
for script in scripts:
    # Get the string content of the script element
    text = script.string
    
    # Check if the text contains the word "markers"
    if "markers" in text:
        # Load the text as a JSON object
        data = json.loads(text)
        
        # Loop through the array of markers
        for marker in data["*"]["Magento_Ui/js/core/app"]["components"]["store-locator-search"]["markers"]:
            # Add missing 0 in front of zipcode
            postcode = ("0" + marker["postCode"])[-5:]

            properties = {
                "addr:city": marker["city"].title(),
                "addr:postcode": postcode,
                "alt_name": marker["name"],
                "brand": "Paul",
                "brand:website": "https://www.paul.fr/",
                "brand:wikidata": "Q3370417",
                "brand:wikipedia": "en:Paul (bakery)",
                "name": "Paul",
                "ref:FR:Paul:id": marker["id"],
                "shop": "bakery",
                "website": marker["url"]
            }

            # Format phone
            p = marker["contact_phone"].replace(" ", "").replace(".", "")
            if len(p) > 8:
                properties["phone"] = f"+33 {p[-9]} {p[-8:-6]} {p[-6:-4]} {p[-4:-2]} {p[-2:]}"
            
            # Format mail
            email = marker["contact_mail"]
            if len(email) > 5:
                properties["email"] = email.strip()

            # Get street. It contains housenumber and street
            address = marker["street"][0]
            
            # Use a regular expression to find the house number and street name in the address
            match = re.search(r"^(\d+[-\/]?\d?[\w]*),?\s+(.*)", address)
            
            # If there is a match, assign the groups to the corresponding properties
            if match:
                properties["addr:housenumber"] = match.group(1)
                properties["addr:street"] = match.group(2)
            else:
                properties["addr:street"] = address

            # Parse Opening Hours
            properties["opening_hours"] = parse_opening_hours(marker["schedule"]["openingHours"])

            properties["fixme"] = "Check address and opening hours, then delete the fixme, fixme:addr and fixme:oh"
            properties["fixme:addr"] = address
            properties["fixme:oh"] = simple_opening_hours(marker["schedule"]["openingHours"])

            # Parse the marker data and convert it to a geojson feature
            feature = geojson.Feature(
                geometry = geojson.Point((float(marker["longitude"]), float(marker["latitude"]))),
                properties = properties
            )

            # Append the feature to the list of features
            features.append(feature)

# Create a geojson feature collection from the list of features
feature_collection = geojson.FeatureCollection(features)

# Write the geojson feature collection to a file named "paul.geojson" with 2 spaces indentation
with open("paul.geojson", "w") as f:
    geojson.dump(feature_collection, f, indent=2)

print(f'Dump {len(features)} shops in paul.geojson')