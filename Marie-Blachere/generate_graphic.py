# generate_graphic.py
import csv
import matplotlib.pyplot as plt
import pandas as pd

HISTORY_FILE = 'bakery_count_history.csv'
GRAPHIC_FILE = 'bakery_count_history.png'

def generate_graphic():
    # Read the CSV file into a DataFrame
    df = pd.read_csv(HISTORY_FILE, names=['Date', 'Count'])

    # Convert the Date column to datetime
    df['Date'] = pd.to_datetime(df['Date'])

    # Plot the data
    plt.figure(figsize=(10, 6))
    plt.plot(df['Date'], df['Count'], marker='o', linestyle='-')
    plt.title('Number of Bakeries Extracted Over Time')
    plt.xlabel('Date')
    plt.ylabel('Number of Bakeries')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save the plot as an image file
    plt.savefig(GRAPHIC_FILE)
    plt.close()

if __name__ == "__main__":
    generate_graphic()
