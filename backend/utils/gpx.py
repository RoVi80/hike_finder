import gpxpy.gpx
from shapely.geometry import LineString, MultiLineString
import geopandas as gpd
from typing import Union


def generate_gpx_from_geometry(geometry: Union[LineString, MultiLineString], source_crs="EPSG:2056") -> str:
    gdf_row = gpd.GeoDataFrame(index=[0], geometry=[geometry], crs=source_crs)
    gdf_row = gdf_row.to_crs(epsg=4326)
    geometry = gdf_row.geometry.iloc[0]

    # Handle LineString or MultiLineString
    if isinstance(geometry, MultiLineString):
        lines = geometry.geoms
    elif isinstance(geometry, LineString):
        lines = [geometry]
    else:
        raise ValueError("Unsupported geometry type")

    # Build GPX
    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    for line in lines:
        for coords in line.coords:
            if len(coords) == 3:
                lon, lat, ele = coords
                gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=lat, longitude=lon, elevation=ele))
            else:
                lon, lat = coords
                gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=lat, longitude=lon))

    return gpx.to_xml()
