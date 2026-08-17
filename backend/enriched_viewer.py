import geopandas as gpd

# Load enriched Etappen and Routes
#etappen = gpd.read_file(r"C:\Users\rolan\OneDrive - Universität Zürich UZH\Desktop\UZH\10_semester\w2\backend\Etappe_final_enriched.gpkg")
#routes = gpd.read_file(r"C:\Users\rolan\OneDrive - Universität Zürich UZH\Desktop\UZH\10_semester\w2\backend\Route_final_enriched.gpkg")

# Drop geometry for easy preview/export
#etappen_no_geom = etappen.drop(columns="geometry")
#routes_no_geom = routes.drop(columns="geometry")

# Export to Excel
#etappen.to_excel("etappen_final_enriched_preview.xlsx", index=False)
#routes.to_excel("routes_enriched_preview.xlsx", index=False)


# Load enriched Etappen and Routes
etappen = gpd.read_file(r"C:\Users\rolan\OneDrive - Universität Zürich UZH\Desktop\UZH\10_semester\w2\backend\Etappe_final_enriched_with_cantons.gpkg")
routes = gpd.read_file(r"C:\Users\rolan\OneDrive - Universität Zürich UZH\Desktop\UZH\10_semester\w2\backend\Route_final_enriched_with_cantons.gpkg")

# Drop geometry for easy preview/export
#etappen_no_geom = etappen.drop(columns="geometry")
#routes_no_geom = routes.drop(columns="geometry")

# Export to Excel
etappen.to_excel("etappen_final_enriched_cantons_preview.xlsx", index=False)
routes.to_excel("route_final_enriched_cantons_preview.xlsx", index=False)
