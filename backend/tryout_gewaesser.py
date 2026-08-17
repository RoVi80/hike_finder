import geopandas as gpd

# Adjust path to your actual extraction folder
path = r"C:\Users\rolan\Downloads\TLM_NAMEN\swissTLM3D_TLM_GEBIETSNAME.shp"  # or GEW_PLY.shp for lakes
gdf_water = gpd.read_file(path)

gdf_water.to_excel("gebietsname_features_preview.xlsx", index=False)

#print(gdf_water.columns)
#print(gdf_water.head(3))