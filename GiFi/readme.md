# GiFi shops

Data scraped from official website.

## Collect data

1. Open this url: https://magasins.gifi.fr/fr/l/
2. Open DevTools
3. Look for the xhr query
4. In the reponse of this query copy the json object "hits"
5. Paste this to a json text file
6. Press button 'next page' at the end of the page
7. Redo this process from step 3 until there is no more page
8. Merge all 'hits' into a gifi.json file

## Process data

Run the python script 'gifi.py'. It will create the file 'gifi.geojson'.

## Create a MapRoulette challenge

1. Open gifi.geojson with JOSM
2. Save the layer as a new file: gifi.osm
3. Run the following mr-cli command:

    `mr coop change --out challenge.geojson gifi.osm`
4. Upload the file challenge.geojson in a new MapRoulette project
5. End!

# Deprecated

I downloaded all data and store them in a unique json file. Then I used the following jq filters to "convert" it to a geojson.
This geojson can be imported into Maproulette to create a "data import/merge" challenge.

cat gifi.json | jq '.[]| {"type": "Feature","geometry": {"type": "Point", "coordinates": [._geoloc.lng,._geoloc.lat] },"properties":{"name": "GiFi", "alt_name": .name, "shop":"variety_store", "brand":"GiFi", "brand:wikidata":"Q3105439", "brand:wikipedia":"fr:Gifi", "ref:FR:GiFi:id": .id, "addr:housenumber": (.street1|split(", ") | .[0]), "addr:street": (.street1|split(", ") | .[1]), "addr:postcode": .zip_code, "addr:city": .city.name, "addr:country": .country.name, "phone": .international_phone, "website": .external_urls.website, "opening_hours": ("Mo " + (.formatted_opening_hours.monday//[] | join(",")) + "; Tu " + (.formatted_opening_hours.tuesday//[] | join(",")) + "; We " + (.formatted_opening_hours.wednesday//[] | join(",")) + "; Th " + (.formatted_opening_hours.thursday//[] | join(",")) + "; Fr " + (.formatted_opening_hours.friday//[] | join(",")) + "; Sa " + (.formatted_opening_hours.saturday//[] | join(",")) + "; Su " + (.formatted_opening_hours.sunday//[] | join(",")) ), "note": (.formatted_address | join(" ")) }}' | jq -s '{"type": "FeatureCollection", "features": . }' > gifi.geojson

=== About this jq command ===

- (.street1|split(", ") | .[0])
  -  Split the property street1 on the string ", " and grab the first part as the housenumber
- operator // default to the right part if the left part is null
- .formatted_opening_hours.wednesday//[] => wednesday will be replaced by an empty array if the wednesday array is null
- ("Mo " + (.formatted_opening_hours.monday//[] | join(","))
  - create a string by joining all string of array monday with the string ","

1. First jq filter will output a "list" (not a json array) of geojson feature.
2. The second jq statement will "slurp" (option -s) the list. Basically it merges the list in a json array. And this json array, will be integrated in a geojson FeatureCollection.