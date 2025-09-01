# Skaping 🎥

**Data last updated on: '2025-09-01''2025-08-01''2025-07-01''2025-06-01'**

Data extracted from: [Skaping](https://www.skaping.com)

![History Diagram](webcam_count_history.png?img_date='2025-09-01''2025-08-01''2025-07-01''2025-06-01')

## 📅 Use the Latest Data Scraped Each Month

Simply use the latest version of the data:
- [skaping.geojson](skaping.geojson) contains GeoJSON features.
- [challenge.geojson](challenge.geojson) can be used to create a challenge on [MapRoulette](https://maproulette.org/).

## 🛠️ Or Run the Scripts for the Latest Data

### 📋 Prerequisites
- Python 3.x
- Python libraries: `pip install -r requirements.txt`
- Node.js
- MapRoulette CLI: `npm install -g @maproulette/mr-cli`

### 🔧 Steps
1. Run the Python script `scrap-webcam.py`.
2. Wait until the files `skaping.geojson` and `skaping.osm` are created.
3. Run `mr coop change --out challenge.geojson ./skaping.osm`.
4. Use `challenge.geojson` to create a challenge on [MapRoulette](https://maproulette.org/).
