# Action shops

Data scraped from official website.

## Download the list of shops

1. Open the url: https://www.action.com/api/stores/coordinates/
2. Save the content in a file: wk/shops.json

## Process data

Run the python script action.py to create the file 'action.geojson'.

This script will read all shop ids from file 'shops.json' and it will make a web
request for each shop id to download all shop information.

If you encounter some 'download errors', just run the same script again.
It will download only the missings shop details.


## Create a MapRoulette challenge

1. Open action.geojson with JOSM
2. Save the layer as a new file: action.osm
3. Run the following mr-cli command:

    `mr coop change --out challenge.geojson action.osm`
4. Upload the file challenge.geojson in a new MapRoulette project
5. End!
