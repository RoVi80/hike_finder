import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import math

def load_gtfs_stops(gtfs_path: str = None) -> gpd.GeoDataFrame:
    if gtfs_path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        gtfs_path = os.path.join(base_dir, "..", "data", "stops.txt")

    stops = pd.read_csv(gtfs_path)
    return gpd.GeoDataFrame(
        stops,
        geometry=gpd.points_from_xy(stops.stop_lon, stops.stop_lat),
        crs="EPSG:4326"
    )


def get_nearest_stop(point: Point, stops_gdf: gpd.GeoDataFrame, dist_col: str = "dist") -> pd.Series:
    # Convert both to metric
    stops_projected = stops_gdf.to_crs("EPSG:2056")

    point_gdf = gpd.GeoSeries([point], crs="EPSG:4326").to_crs("EPSG:2056")
    point_proj = point_gdf.iloc[0]

    # Safety check
    if not point_proj.is_valid or point_proj.is_empty:
        raise ValueError("Invalid projected point")

    stops_projected[dist_col] = stops_projected.geometry.distance(point_proj)
    nearest = stops_projected.sort_values(dist_col).iloc[0]

    if not math.isfinite(nearest[dist_col]):
        raise ValueError("Distance calculation failed: non-finite result")

    return nearest
