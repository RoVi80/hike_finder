import os
import requests
import zipfile
import io
import geopandas as gpd
import logging
import json
import fiona

# --- Config ---
CKAN_API_URL = "https://opendata.swiss/api/3/action/package_show"
DATASET_ID = "langsamverkehr-wanderland-schweiz"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")
TMP_DIR = os.path.join(OUTPUT_DIR, "tmp")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_latest_zip_url():
    """Fetch the latest .gpkg.zip resource from the CKAN API."""
    response = requests.get(CKAN_API_URL, params={"id": DATASET_ID})
    response.raise_for_status()
    resources = response.json()["result"]["resources"]

    print(json.dumps(resources, indent=2))


    for res in resources:
        format_str = res.get("format", "").lower()
        url = res.get("download_url") or res.get("url")  # <- use download_url if present
        if "zip" in format_str and url and url.endswith(".zip"):
            logger.info(f"Found GPKG ZIP resource: {url}")
            return url

    raise ValueError("No suitable GPKG ZIP resource found.")


def download_and_extract_zip(url):
    """Download and extract ZIP to temp folder."""
    os.makedirs(TMP_DIR, exist_ok=True)
    logger.info("Downloading ZIP...")
    response = requests.get(url)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        z.extractall(TMP_DIR)
    logger.info(f"Extracted to {TMP_DIR}")


def convert_gpkg_to_geojson():
    """Convert layers from downloaded GeoPackage to GeoJSON."""
    for file in os.listdir(TMP_DIR):
        if file.endswith(".gpkg"):
            gpkg_path = os.path.join(TMP_DIR, file)

            layers = fiona.listlayers(gpkg_path)
            logger.info(f"Found layers in GPKG: {layers}")

            for layer in layers:
                gdf = gpd.read_file(gpkg_path, layer=layer)
                if "etappe" in layer.lower():
                    gdf.to_file(os.path.join(OUTPUT_DIR, "Etappe.geojson"), driver="GeoJSON")
                    logger.info("✅ Saved Etappe.geojson")
                elif "route" in layer.lower():
                    gdf.to_file(os.path.join(OUTPUT_DIR, "Route.geojson"), driver="GeoJSON")
                    logger.info("✅ Saved Route.geojson")



def clean_tmp():
    """Delete temporary folder."""
    for f in os.listdir(TMP_DIR):
        os.remove(os.path.join(TMP_DIR, f))
    os.rmdir(TMP_DIR)
    logger.info("🧹 Cleaned up temp files")


def main():
    try:
        logger.info("🔄 Starting sync from opendata.swiss")
        zip_url = fetch_latest_zip_url()
        download_and_extract_zip(zip_url)
        convert_gpkg_to_geojson()
        clean_tmp()
        logger.info("✅ Sync completed successfully.")
    except Exception as e:
        logger.error(f"❌ Sync failed: {e}")


if __name__ == "__main__":
    main()
