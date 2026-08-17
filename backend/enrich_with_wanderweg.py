import geopandas as gpd
import os

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, r"wanderland_2056.shp\2025_shape_wanderland")

ETAPPE_PATH = os.path.join(DATA_DIR, "Etappe.geojson")
ROUTE_PATH = os.path.join(DATA_DIR, "Route.geojson")
WANDERWEG_PATH = os.path.join(DATA_DIR, "WanderWeg.shp")

ETAPPE_OUT = os.path.join(DATA_DIR, "Etappe_enriched.gpkg")
ROUTE_OUT = os.path.join(DATA_DIR, "Route_enriched.gpkg")


def enrich_by_spatial_join(base_gdf, base_id_col, wanderwege_gdf):
    base_gdf_orig = base_gdf.copy()
    buffered = base_gdf.copy()
    buffered["geometry"] = buffered.geometry.buffer(1)

    joined = gpd.sjoin(
        wanderwege_gdf[["geometry", "BelagTLM", "WegKat"]],
        buffered[[base_id_col, "geometry"]],
        how="inner",
        predicate="intersects"
    )

    agg = (
        joined.groupby(base_id_col)[["BelagTLM", "WegKat"]]
        .agg(lambda x: sorted(set(filter(None, x))))
        .reset_index()
    )

    enriched = base_gdf_orig.merge(agg, on=base_id_col, how="left")
    return enriched



def main():
    print("📦 Loading data...")
    etappen = gpd.read_file(ETAPPE_PATH)
    routes = gpd.read_file(ROUTE_PATH)
    wanderwege = gpd.read_file(WANDERWEG_PATH)

    # Ensure consistent CRS
    wanderwege = wanderwege.to_crs(etappen.crs)
    routes = routes.to_crs(etappen.crs)

    # Enrich Etappen
    print("🔍 Enriching Etappen...")
    enriched_etappen = enrich_by_spatial_join(etappen, "LVEtappe_I", wanderwege)
    enriched_etappen.to_file(ETAPPE_OUT, driver="GPKG")
    print(f"✅ Saved enriched Etappen to {ETAPPE_OUT}")

    # Enrich Routes
    print("🔍 Enriching Routes...")
    enriched_routes = enrich_by_spatial_join(routes, "LVRoute_ID", wanderwege)
    enriched_routes.to_file(ROUTE_OUT, driver="GPKG")
    print(f"✅ Saved enriched Routes to {ROUTE_OUT}")

    print("🏁 All done.")


if __name__ == "__main__":
    main()
