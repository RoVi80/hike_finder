import geopandas as gpd
import os

# Adjust path if needed
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, r"wanderland_2056.shp\2025_shape_wanderland")

ETAPPE_OUT = os.path.join(DATA_DIR, "Etappe_enriched.gpkg")
ROUTE_OUT = os.path.join(DATA_DIR, "Route_enriched.gpkg")

# Load and inspect
etappen_enriched = gpd.read_file(ETAPPE_OUT)
routes_enriched = gpd.read_file(ROUTE_OUT)

# Display column names and a few example rows
print("📋 Etappen columns:", etappen_enriched.columns.tolist())
print("🔍 Sample Etappen:")
print(etappen_enriched[["LVEtappe_I", "WegKat", "BelagTLM"]].dropna().head(10))

print("\n📋 Routes columns:", routes_enriched.columns.tolist())
print("🔍 Sample Routes:")
print(routes_enriched[["LVRoute_ID", "WegKat", "BelagTLM"]].dropna().head(10))
