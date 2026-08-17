import os
import csv
import uuid
from fastapi import APIRouter, UploadFile, Form, File
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime
import gpxpy

from geopy.distance import geodesic  
from gpxpy import parse as parse_gpx


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()

CSV_FILE = "contributions.csv"

# Write CSV header if not exists
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id","title","description","surface_type","difficulty","duration_minutes","distance_km","elevation_gain","elevation_loss","suitable_for_kids","gpx_file","photo_file","timestamp"])


@router.post("/upload_hike")
async def upload_hike(
    gpx_file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(...),
    surface_type: str = Form(...),
    difficulty: str = Form(...),
    duration_minutes: int = Form(...),
    suitable_for_kids: bool = Form(...),
    photo: Optional[UploadFile] = File(None)
):
    hike_id = str(uuid.uuid4())
    gpx_path = os.path.join(UPLOAD_DIR, f"{hike_id}.gpx")
    with open(gpx_path, "wb") as f:
        f.write(await gpx_file.read())

    # ⛰️ Parse GPX
    with open(gpx_path, "r") as f:
        gpx = gpxpy.parse(f)

    total_distance_km = 0
    elevation_gain = 0
    elevation_loss = 0
    start_point = None
    end_point = None

    for track in gpx.tracks:
        for segment in track.segments:
            total_distance_km += segment.length_3d() / 1000
            points = segment.points
            if points:
                start_point = (points[0].latitude, points[0].longitude)
                end_point = (points[-1].latitude, points[-1].longitude)

            for i in range(1, len(points)):
                diff = points[i].elevation - points[i - 1].elevation
                if diff > 0:
                    elevation_gain += diff
                else:
                    elevation_loss -= diff

    # 🌀 Check if it's a loop (< 300m apart)
    is_loop = False
    if start_point and end_point:
        dist_m = geodesic(start_point, end_point).meters
        is_loop = dist_m < 300

    # Save photo
    photo_path = ""
    if photo:
        photo_path = os.path.join(UPLOAD_DIR, f"{hike_id}_{photo.filename}")
        with open(photo_path, "wb") as f:
            f.write(await photo.read())

    # Save to CSV
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            hike_id, title, description, surface_type, difficulty,
            duration_minutes,  # placeholder for duration, or let user estimate later
            round(total_distance_km, 2),
            round(elevation_gain, 1),
            round(elevation_loss, 1),
            suitable_for_kids,
            gpx_path, photo_path, datetime.utcnow().isoformat(),
            is_loop
        ])

    return {"status": "success", "message": "✅ Hike uploaded!"}

@router.post("/preview_gpx")
async def preview_gpx(gpx_file: UploadFile = File(...)):
    gpx = gpxpy.parse(await gpx_file.read())
    total_distance_km = 0
    gain = 0
    loss = 0
    start = None
    end = None

    for track in gpx.tracks:
        for segment in track.segments:
            total_distance_km += segment.length_3d() / 1000
            points = segment.points
            if points:
                start = (points[0].latitude, points[0].longitude)
                end = (points[-1].latitude, points[-1].longitude)

            for i in range(1, len(points)):
                diff = points[i].elevation - points[i - 1].elevation
                if diff > 0:
                    gain += diff
                else:
                    loss -= diff

    is_loop = geodesic(start, end).meters < 300 if start and end else False

    return {
        "distance_km": round(total_distance_km, 2),
        "elevation_gain": round(gain, 1),
        "elevation_loss": round(loss, 1),
        "is_loop": is_loop
    }
