# backend/models/hike_base.py

from shapely.geometry import LineString
import geopandas as gpd

class Hike:
    def __init__(self, id: str, name: str, geometry: LineString):
        self.id = id
        self.name = name
        self.geometry = geometry

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        }

    def to_gpx(self):
        from utils.gpx import generate_gpx_from_geometry
        return generate_gpx_from_geometry(self.geometry, source_crs="EPSG:2056")


    def to_wgs84(self):
        return gpd.GeoSeries([self.geometry], crs="EPSG:2056").to_crs("EPSG:4326").iloc[0]
