import geopandas as gpd
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def enrich_with_cantons(base_gdf, canton_gdf):
    logging.info("Enriching with intersecting cantons...")
    base_gdf = base_gdf.copy()
    canton_gdf = canton_gdf.to_crs(base_gdf.crs)

    # Columns to keep
    name_cols = ["alternateName", "KantonName_de", "KantonName_fr", "KantonName_it", "KantonName_en"]
    joined = gpd.sjoin(base_gdf, canton_gdf[name_cols + ["geometry"]], how="left", predicate="intersects")

    # Aggregate each column
    canton_agg = joined.groupby(joined.index).agg({
        "alternateName": lambda x: sorted(set(filter(None, x))),
        "KantonName_de": lambda x: sorted(set(filter(None, x))),
        "KantonName_fr": lambda x: sorted(set(filter(None, x))),
        "KantonName_it": lambda x: sorted(set(filter(None, x))),
        "KantonName_en": lambda x: sorted(set(filter(None, x))),
    })

    # Add string versions for display
    canton_agg["canton_string"] = canton_agg["alternateName"].apply(lambda x: ", ".join(str(item) for item in x if pd.notnull(item)) if isinstance(x, list) else None)
    canton_agg["canton_de"] = canton_agg["KantonName_de"].apply(lambda x: ", ".join(str(item) for item in x if pd.notnull(item)) if isinstance(x, list) else None)
    canton_agg["canton_fr"] = canton_agg["KantonName_fr"].apply(lambda x: ", ".join(str(item) for item in x if pd.notnull(item)) if isinstance(x, list) else None)
    canton_agg["canton_it"] = canton_agg["KantonName_it"].apply(lambda x: ", ".join(str(item) for item in x if pd.notnull(item)) if isinstance(x, list) else None)
    canton_agg["canton_en"] = canton_agg["KantonName_en"].apply(lambda x: ", ".join(str(item) for item in x if pd.notnull(item)) if isinstance(x, list) else None)

    # Join back to base
    base_gdf = base_gdf.join(canton_agg)
    
    logging.info(f" → Added full canton name mappings to {len(canton_agg)} features")
    return base_gdf

def main():
    canton_path = r"C:\Users\rolan\OneDrive - Universität Zürich UZH\Desktop\UZH\10_semester\w2\backend\landesforstinventar-kantone_2056.geojson"
    canton_gdf = gpd.read_file(canton_path)

    for label in ["Etappe", "Route"]:
        input_path = fr"C:\Users\rolan\OneDrive - Universität Zürich UZH\Desktop\UZH\10_semester\w2\backend\{label}_final_enriched.gpkg"
        output_path = fr"C:\Users\rolan\OneDrive - Universität Zürich UZH\Desktop\UZH\10_semester\w2\backend\{label}_final_enriched_with_cantons.gpkg"

        gdf = gpd.read_file(input_path)
        enriched = enrich_with_cantons(gdf, canton_gdf)
        enriched.to_file(output_path, driver="GPKG")
        print(f"✅ Saved: {output_path}")

if __name__ == "__main__":
    main()
