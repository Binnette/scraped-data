# B&M shops

Data scraped from official website.

## Download data

1. Open url: https://www.bmstores.fr/nos-magasins
2. Open devtool and copy paste following code:

```js
function download(content, fileName, contentType) {
    var a = document.createElement("a");
    var file = new Blob([content], {type: contentType});
    a.href = URL.createObjectURL(file);
    a.download = fileName;
    a.click();
}

const jsonData = JSON.stringify(villesordered,  null, 2);
download(jsonData, 'shops.json', 'text/plain');
```

## Extract data

1. Run the python script bnm.py
2. Wait until the file bnm.geojson is created

## Create a MapRoulette challenge

1. Open bnm.geojson with JOSM
2. Save the layer as a new file: bnm.osm
3. Run the following mr-cli command:

    `mr coop change --out challenge.geojson bnm.osm`
4. Upload the file challenge.geojson in a new MapRoulette project
5. End!
