# Import the module
import json
import os

# Define the input and output folders
input_folder = "tomerge"

# Initialize an empty list to store the items
items = []
file_count = 0

# Loop through the input files
for file in os.listdir(input_folder):
    # Check if the file is a json file
    if file.endswith(".json"):
        file_count = file_count +1
        # Open the file and load the json data
        with open(os.path.join(input_folder, file), "r") as f:
            data = json.load(f)
        # Check if the data object has a hits property that is an array
        if "hits" in data and isinstance(data["hits"], list):
            # Loop through the hits array and append each item to the list of items
            for item in data["hits"]:
                items.append(item)

# Save the json object as a new file in the output folder with the name gifi.json
with open("gifi.json", "w") as f:
    json.dump(items, f, indent=4)

print(f'Merged {file_count} into gifi.json for a total of {len(items)} shops')