# Stokomani 🏷️

**Data last updated on: 2025-12-01**

Data scraped from: [Stokomani](https://www.stokomani.fr)

![History Diagram](shop_count_history.png?img_date=2025-12-01)

## 📅 Use the Latest Data Scraped Each Month

Simply use the latest version of the data:
- [stokomani.geojson](stokomani.geojson) contains GeoJSON features.
- [challenge.geojson](challenge.geojson) can be used to create a challenge on [MapRoulette](https://maproulette.org/).

## 🛠️ Or Run the Scripts for the Latest Data

### 📋 Prerequisites
- Python 3.x
- Python libraries: `pip install -r requirements.txt`
- Node.js
- MapRoulette CLI: `npm install -g @maproulette/mr-cli`

### 🔧 Steps
1. Run the Python script `scrap-webcam.py`.
2. Wait until the files `stokomani.geojson` and `stokomani.osm` are created.
3. Run `mr coop change --out challenge.geojson ./stokomani.osm`.
4. Use `challenge.geojson` to create a challenge on [MapRoulette](https://maproulette.org/).
