import geopandas as gpd
import logging
from shapely.geometry import LineString
from collections import Counter
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def enrich_with_features(base_gdf, base_id_col, feature_gdf, feature_name_col, buffer_m=500, new_col=""):
    logging.info(f"Buffering {base_id_col} by {buffer_m}m for {new_col}")
    buffered = base_gdf.copy()
    buffered["geometry"] = buffered.geometry.buffer(buffer_m)

    joined = gpd.sjoin(
        feature_gdf[[feature_name_col, "geometry"]],
        buffered[[base_id_col, "geometry"]],
        how="inner",
        predicate="intersects"
    )
    agg = joined.groupby(base_id_col)[feature_name_col].agg(lambda x: sorted(set(filter(None, x)))).reset_index()
    agg.columns = [base_id_col, new_col]

    logging.info(f" → {len(agg)} features matched for {new_col}")
    return base_gdf.merge(agg, on=base_id_col, how="left")

def add_coordinates(gdf):
    logging.info("Adding centroid and WGS84 coordinates...")
    gdf = gdf.copy()
    
    if gdf.crs.to_epsg() != 2056:
        gdf = gdf.to_crs(epsg=2056)

    gdf["centroid"] = gdf.geometry.centroid
    gdf["centroid_x"] = gdf["centroid"].x
    gdf["centroid_y"] = gdf["centroid"].y

    gdf_centroids_wgs = gdf.set_geometry("centroid").to_crs(epsg=4326)
    gdf["lat"] = gdf_centroids_wgs.geometry.y
    gdf["lon"] = gdf_centroids_wgs.geometry.x

    if gdf.geometry.iloc[0].geom_type == "LineString":
        gdf["start_x"] = gdf.geometry.apply(lambda g: g.coords[0][0])
        gdf["start_y"] = gdf.geometry.apply(lambda g: g.coords[0][1])
        gdf["end_x"] = gdf.geometry.apply(lambda g: g.coords[-1][0])
        gdf["end_y"] = gdf.geometry.apply(lambda g: g.coords[-1][1])

    return gdf.drop(columns="centroid")


def add_nearby_named_places(base_gdf, named_gdf, name_col="NAME", radius=1500):
    logging.info(f"Finding all named points within {radius} meters using buffer...")
    base_gdf = base_gdf.copy()
    named_gdf = named_gdf.to_crs(base_gdf.crs)

    named_gdf = named_gdf[named_gdf.geometry.notnull() & named_gdf.geometry.is_valid & ~named_gdf.geometry.is_empty].copy()
    base_gdf = base_gdf[base_gdf.geometry.notnull() & base_gdf.geometry.is_valid & ~base_gdf.geometry.is_empty].copy()

    all_nearby_names = []
    for i, geom in enumerate(base_gdf.geometry):
        try:
            buffer_geom = geom.buffer(radius)
            nearby = named_gdf[named_gdf.geometry.intersects(buffer_geom)]
            names = nearby[name_col].astype(str).str.strip().unique().tolist()
            all_nearby_names.append(names)

            if i % 10 == 0:
                logging.info(f"[{i}] Found {len(names)} nearby names")
        except Exception as e:
            logging.warning(f"Nearby name search failed at index {i}: {e}")
            all_nearby_names.append([])

    base_gdf["nearby_named_places"] = all_nearby_names
    return base_gdf

def add_nearest_named_place(base_gdf, named_gdf, name_col="NAME"):
    logging.info("Finding nearest named point feature (fallback method)...")
    base_gdf = base_gdf.copy()
    named_gdf = named_gdf.to_crs(base_gdf.crs)

    named_gdf = named_gdf[named_gdf.geometry.notnull() & named_gdf.geometry.is_valid & ~named_gdf.geometry.is_empty].copy()
    base_gdf = base_gdf[base_gdf.geometry.notnull() & base_gdf.geometry.is_valid & ~base_gdf.geometry.is_empty].copy()

    named_places = [(geom, name) for geom, name in zip(named_gdf.geometry, named_gdf[name_col])]

    nearest_names = []
    for i, geom in enumerate(base_gdf.geometry):
        try:
            centroid = geom.centroid
            nearest_geom, nearest_name = min(named_places, key=lambda x: centroid.distance(x[0]))
            nearest_names.append(str(nearest_name))
            if i % 10 == 0:
                logging.info(f"[{i}] Closest name: {nearest_name}")
        except Exception as e:
            logging.warning(f"Nearest search failed at index {i}: {e}")
            nearest_names.append(None)

    base_gdf["nearest_named_place"] = nearest_names
    return base_gdf

def enrich_with_cantons(base_gdf, canton_gdf, canton_col="alternateName"):
    logging.info("Enriching with intersecting cantons...")
    base_gdf = base_gdf.copy()
    canton_gdf = canton_gdf.to_crs(base_gdf.crs)

    joined = gpd.sjoin(base_gdf, canton_gdf[[canton_col, "geometry"]],
                       how="left", predicate="intersects")

    canton_agg = joined.groupby(joined.index)[canton_col] \
                       .agg(lambda x: sorted(set(filter(None, x)))) \
                       .rename("intersecting_cantons")

    base_gdf = base_gdf.join(canton_agg)

    # Also store as display string
    base_gdf["canton_string"] = base_gdf["intersecting_cantons"].apply(lambda lst: ", ".join(lst) if isinstance(lst, list) else None)

    logging.info(f" → Added canton list and string to {len(canton_agg)} features")
    return base_gdf

def process_file(input_path, id_col, output_path):
    logging.info(f"Processing: {input_path}")
    gdf = gpd.read_file(input_path)

    # Context layers
    seen = gpd.read_file(r"C:\Users\rolan\Downloads\swiss-water\TLM_GEWAESSER\swissTLM3D_TLM_STEHENDES_GEWAESSER.shp")
    gelaende = gpd.read_file(r"C:\Users\rolan\Downloads\TLM_NAMEN\swissTLM3D_TLM_GELAENDENAME.shp")
    gebiet = gpd.read_file(r"C:\Users\rolan\Downloads\TLM_NAMEN\swissTLM3D_TLM_GEBIETSNAME.shp")
    pkt = gpd.read_file(r"C:\Users\rolan\Downloads\TLM_NAMEN\swissTLM3D_TLM_NAME_PKT.shp")

    for other in [seen, gelaende, gebiet, pkt]:
        other.to_crs(gdf.crs, inplace=True)

    # Enrich with nearby features
    gdf = enrich_with_features(gdf, id_col, seen, "NAME", 1000, "nearby_lakes")
    gdf = enrich_with_features(gdf, id_col, gelaende, "NAME", 1000, "nearby_terrain")
    gdf = enrich_with_features(gdf, id_col, gebiet, "NAME", 1000, "nearby_areas")

    # Add coordinates and list of nearby named points
    gdf = add_coordinates(gdf)
    gdf = add_nearby_named_places(gdf, pkt, name_col="NAME", radius=1500)
    gdf = add_nearest_named_place(gdf, pkt, name_col="NAME")

    gdf.to_file(output_path, driver="GPKG")
    print(f"✅ Saved enriched file: {output_path}")

def main():
    # Define both runs
    tasks = [
        {
            "input_path": r"C:\Users\rolan\OneDrive - Universität Zürich UZH\Desktop\UZH\10_semester\w2\backend\wanderland_2056.shp\2025_shape_wanderland\Etappe_enriched.gpkg",
            "id_col": "LVEtappe_I",
            "output_path": "Etappe_final_enriched.gpkg"
        },
        {
            "input_path": r"C:\Users\rolan\OneDrive - Universität Zürich UZH\Desktop\UZH\10_semester\w2\backend\wanderland_2056.shp\2025_shape_wanderland\Route_enriched.gpkg",
            "id_col": "LVRoute_ID",
            "output_path": "Route_final_enriched.gpkg"
        }
    ]

    for task in tasks:
        process_file(task["input_path"], task["id_col"], task["output_path"])

if __name__ == "__main__":
    main()
