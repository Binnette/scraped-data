# B&M shops

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