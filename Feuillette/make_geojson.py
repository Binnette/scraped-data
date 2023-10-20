# Import the requests library to get the JSON file from the URL
import json
import re
import requests

# Define the URL of the JSON file
url = "https://www.feuillette.fr/wp-content/themes/Divi-Child/api/boulangeries.php"

# Get the response from the URL and parse it as a JSON object
response = requests.get(url)
data = response.json()

# Convert the top JSON object into an array of shops
shops = list(data.values())

# Initialize an empty list to store the geojson features
features = []

# Loop through each shop in the array
for shop in shops:
    # Extract the relevant information from the shop object
    address = shop["adresse"].strip()

    properties = {
        "addr:postcode": shop["code_postal"],
        "addr:city": shop["ville"],
        "alt_name": shop["title"],
        "brand": "Feuillette",
        "email": shop["email"],
        "fixme": "Check address and opening hours, then delete the fixme, fixme:addr and fixme:oh",
        "fixme:addr": address,
        "fixme:oh": shop["texte"],
        "name": "Boulangerie Feuillette",
        "ref:FR:Feuillette:extranet": shop["id_extranet"],
        "ref:FR:Feuillette:id": f'{shop["post_id"]}',
        "shop": "bakery"
    }
    
    # Use a regular expression to find the house number and street name in the address
    match = re.search(r"^(\d+[-\/]?\d?[\w]*),?\s+(.*)", address)
    
    # If there is a match, assign the groups to the corresponding properties
    if match:
        properties["addr:housenumber"] = match.group(1)
        properties["addr:street"] = match.group(2)
    else:
        properties["addr:street"] = address

    # Convert the date of opening into YYYY-MM-DD format
    o = shop["date_douverture"]
    if len(o) == 10:
        properties["start_date"] = f'{o[-4:]}-{o[3:5]}-{o[0:2]}'

    # Format phone +33
    p = shop["telephone"].replace(" ", "")
    if len(p) > 9:
        properties["phone"] = f"+33 {p[-9]} {p[-8:-6]} {p[-6:-4]} {p[-4:-2]} {p[-2:]}"
    

    # Create a geojson feature for the shop with the OpenStreetMap attributes
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [float(shop["longitude"]), float(shop["lattitude"])]
        },
        "properties": properties
    }

    # Append the feature to the list of features
    features.append(feature)

# Create a geojson object with the list of features
geojson = {
    "type": "FeatureCollection",
    "features": features
}

# Write the geojson feature collection to a file named "feuillette.geojson" with 2 spaces indentation
with open("feuillette.geojson", "w") as f:
    json.dump(geojson, f, indent=2)

print(f'Dump {len(features)} shops in feuillette.geojson')