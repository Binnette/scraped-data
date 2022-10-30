# Action shops

## Download the list of shops

1. Open the url: https://www.action.com/api/stores/coordinates/
2. Save the content in a file: wk/shops.json

## Process data

Run the python script action.py to create the file 'action.geojson'.

This script will read all shop ids from file 'shops.json' and it will make a web
request for each shop id to download all shop information.

If you encounter some 'download errors', just run the same script again.
It will download only the missings shop details.


## Create MapRoulette Challenge

1. Open action.geojson with JOSM
2. Save the layer as action.osm
3. Run MapRoulette command (with mr-cli):

    `mr coop change --out challenge.geojson action.osm`
4. Create a MapRoulette challenge with the file challenge.geojson