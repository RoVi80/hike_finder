import geopandas as gpd
import os
from pprint import pprint

# Path to your enriched Etappe GeoPackage
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "wanderland_2056.shp", "2025_shape_wanderland", "Etappe_enriched.gpkg")

# Load the data
gdf = gpd.read_file(DATA_PATH)

# Check a few rows
print("=== Sample rows with 'WegKat' and 'BelagTLM' ===\n")

for i, row in gdf.iterrows():
    print(f"Row {i}")
    print(f"  Type of WegKat: {type(row.get('WegKat'))}")
    print(f"  Value of WegKat: {row.get('WegKat')}")
    print(f"  Type of BelagTLM: {type(row.get('BelagTLM'))}")
    print(f"  Value of BelagTLM: {row.get('BelagTLM')}")
    print("-" * 40)
    
    if i >= 10:
        break  # Only print first 10 rows
