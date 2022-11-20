# Stokomani shops

Data scraped from official website.

## Download the store page list

1. Download the file at url : https://www.stokomani.fr/Assets/Rbs/Seo/100457/fr_FR/Rbs_Store_Store.1.xml
2. Save it in wk/Rbs_Store_Store.1.xml

## Download and extrack data

1. Run the script stokomani.py
2. It scans the file Rbs_Store_Store.1.xml
3. Then it downloads all the store web page (html) and store them in folder wk
4. Then it extracts all data and store them in the file stokomani.geojson

## Create a MapRoulette challenge

1. Open stokomani.geojson with JOSM
2. Save the layer as a new file: stokomani.osm
3. Run the following mr-cli command:

    `mr coop change --out challenge.geojson stokomani.osm`
4. Upload the file challenge.geojson in a new MapRoulette project
5. End!