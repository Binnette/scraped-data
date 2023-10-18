# Import the requests and BeautifulSoup libraries
import requests
from bs4 import BeautifulSoup

# Import the json and geojson libraries
import json
import geojson

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
                "shop": "bakery",
                "name": "Boulangerie Paul",
                "website": marker["url"],
                "addr:city": marker["city"].title(),
                "addr:postcode": postcode,
                "ref:FR:Paul:id": marker["id"],
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
            match = re.search("^(\d+[-\/]?\d?[\w]*),?\s+(.*)", address)
            
            # If there is a match, assign the groups to the corresponding properties
            if match:
                properties["addr:housenumber"] = match.group(1)
                properties["addr:street"] = match.group(2)
            else:
                properties["addr:street"] = address

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
