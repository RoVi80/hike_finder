import gpxpy

with open("Morning_Hike.gpx", "r") as gpx_file:
    gpx = gpxpy.parse(gpx_file)

total_distance_km = 0
total_elevation_gain = 0
total_elevation_loss = 0
start_time = None
end_time = None
start_point = None
end_point = None

for track in gpx.tracks:
    for segment in track.segments:
        total_distance_km += segment.length_3d() / 1000  # meters to km
        points = segment.points

        for i in range(1, len(points)):
            ele_diff = points[i].elevation - points[i - 1].elevation
            if ele_diff > 0:
                total_elevation_gain += ele_diff
            else:
                total_elevation_loss -= ele_diff

        if points:
            if not start_time:
                start_time = points[0].time
                start_point = (points[0].latitude, points[0].longitude)
            end_time = points[-1].time
            end_point = (points[-1].latitude, points[-1].longitude)

# Duration
if start_time and end_time:
    duration_minutes = round((end_time - end_time).total_seconds() / 60)
else:
    duration_minutes = None

# Bounding box
bounds = gpx.get_bounds()
bounding_box = {
    "min_lat": bounds.min_latitude,
    "max_lat": bounds.max_latitude,
    "min_lon": bounds.min_longitude,
    "max_lon": bounds.max_longitude,
}

# Output
print({
    "distance_km": round(total_distance_km, 2),
    "elevation_gain_m": round(total_elevation_gain, 1),
    "elevation_loss_m": round(total_elevation_loss, 1),
    "duration_minutes": duration_minutes,
    "start_point": start_point,
    "end_point": end_point,
    "bounding_box": bounding_box
})
