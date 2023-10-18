# Marie-Blachère 🥖

Data extracted from an XML file found here: https://boulangeries.marieblachere.com/

## Extract data

1. Run the python script marie_blachere.py
2. Wait until the file marie_blachere.geojson is created

## Create a MapRoulette challenge

1. Run script geojson_to_osm.py
2. Wait until the file marie_blachere.osm is created
3. Run `mr coop change --out challenge.geojson .\marie_blachere.osm`
4. Upload the file "challenge.geojson" to MapRoulette