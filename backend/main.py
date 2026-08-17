from fastapi import FastAPI, Query, HTTPException, UploadFile, Form, APIRouter, Depends
from fastapi.responses import Response, FileResponse
from typing import Optional, Union, Dict
from shapely.geometry import mapping
from unidecode import unidecode
import geopandas as gpd
from dotenv import load_dotenv
import pandas as pd
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import logging
import openai
import os
import json
import ast
import math
import numpy as np
import posixpath

from fastapi.staticfiles import StaticFiles
from rapidfuzz import process, fuzz
from utils.transport_nearest import load_gtfs_stops, get_nearest_stop
from utils.helpers import format_hike_time, percentage_dict
from upload import router as upload_router
from pydantic import BaseModel
from typing import Optional, Dict
from os.path import basename


#newest ones
from models.etappe import Etappe
from models.route import Route
from models.contribution import ContributionHike
from managers.hike_manager import HikeManager




load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

router = APIRouter()
app = FastAPI()
app.include_router(upload_router)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

download_router = APIRouter()

# ✅ Use a separate route prefix for downloads to force 'attachment' behavior
@download_router.get("/download/{filename}")
async def serve_download(filename: str):
    file_path = os.path.join("uploads", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        file_path,
        media_type="application/gpx+xml",
        filename=filename  # ✅ forces "Save as..." dialog
    )

app.include_router(download_router)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load GeoJSON
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ETAPPE_PATH = os.path.join(BASE_DIR, "Etappe_final_enriched_with_cantons.gpkg")
ROUTE_PATH = os.path.join(BASE_DIR, "Route_final_enriched_with_cantons.gpkg")


def safe_round(val, digits=1):
    try:
        return round(float(val), digits)
    except:
        return None

def load_trail_data():
    gdf = gpd.read_file(ETAPPE_PATH)
    gdf_routes = gpd.read_file(ROUTE_PATH)

    # 🧠 Fix stringified list columns
    list_cols = ["nearby_terrain", "nearby_areas", "nearby_named_places", "BelagTLM", "WegKat", "nearby_lakes"]
    for col in list_cols:
        if col in gdf.columns:
            gdf[col] = gdf[col].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith("[") else x
            )
        if col in gdf_routes.columns:
            gdf_routes[col] = gdf_routes[col].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith("[") else x
            )


    gdf["start_location"] = gdf["NameS"].apply(lambda x: unidecode(str(x)).lower().strip())
    gdf["end_location"] = gdf["NameZ"].apply(lambda x: unidecode(str(x)).lower().strip())

    gdf_routes["route_name"] = gdf_routes["NameR"].apply(lambda x: unidecode(str(x)).lower().strip())
    gdf_routes["route_id_norm"] = gdf_routes["LVRoute_ID"].apply(lambda x: unidecode(str(x)).lower().strip())
    gdf["route_id_norm"] = gdf["LVRoute_ID"].apply(lambda x: unidecode(str(x)).lower().strip())

    route_map = gdf_routes.set_index("route_id_norm")["route_name"].to_dict()
    gdf["route_name"] = gdf["route_id_norm"].map(route_map)

    # ✅ Add is_loop logic here
    gdf["is_loop"] = gdf["NameS"] == gdf["NameZ"]
    gdf_routes["is_loop"] = gdf_routes["HoeheAbR"] == gdf_routes["HoeheAufR"]

    return gdf, gdf_routes


gdf, gdf_routes = load_trail_data()
gtfs_stops = load_gtfs_stops()

hike_manager = HikeManager(gdf, gdf_routes, gtfs_stops)

logger.info(f"GTFS stops count: {len(gtfs_stops)} | Valid geometries: {gtfs_stops.geometry.notnull().sum()}")
logger.info(f"GTFS bounds: {gtfs_stops.total_bounds}")



import re

def extract_elevation_from_prompt(prompt: str) -> Optional[float]:
    """
    Try to extract elevation gain in meters from the raw prompt.
    Looks for phrases like '500m', '500 m', '500 meters', etc.
    """
    match = re.search(r"(\d{2,5})\s*(m|meters|meter|hm|höhenmeter|elevation|climb|gain)", prompt.lower())
    if match:
        try:
            return float(match.group(1))
        except:
            return None
    return None


def parse_prompt_with_gpt(prompt: str) -> tuple[dict, str]:
    system_prompt = (
        "You are an assistant that extracts structured hike filters from natural language. "
        "Return a JSON object with: location, start_only (bool), end_only (bool), "
        "distance_km (float), distance_min (float), distance_max (float), "
        "loop_only (bool), trail_type (string), and surface_type (string). "
        "If the user wants a loop hike, Rundweg, or Rundwanderung, set loop_only to true. "
        "If there's no distance range, just fill distance_km. "
        "If the prompt mentions Wanderweg, Bergwanderweg, or Alpinwanderweg, return that as trail_type. "
        "If it mentions Natur, hart, or Unbekannt surfaces, return that as surface_type. "
        "Return null for any missing field."
    )

    user_message = f"Prompt: {prompt}"

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0
        )

        extracted = response.choices[0].message.content.strip()
        logger.debug(f"Raw GPT output: {extracted}")

        parsed = json.loads(extracted)
        if not isinstance(parsed, dict):
            raise ValueError("Parsed content is not a dict")

        # ✅ Add elevation gain extraction
        parsed["elevation_gain_m"] = extract_elevation_from_prompt(prompt)

        return parsed, extracted

    except Exception as e:
        logger.error(f"Failed to parse GPT output: {e}")
        return {
            "location": None,
            "start_only": None,
            "end_only": None,
            "distance_km": None,
            "distance_min": None,
            "distance_max": None,
            "elevation_gain_m": None  # <-- still include in fallback
        }, ""


def score_hike(row, parsed, location_query: str):
    score = 0.0
    reasons = []

    query_loc = unidecode(location_query.lower().strip())

    # High-weight exact match fields
    text_fields = {
        "route_name": row.get("route_name", ""),
        "NameS": row.get("NameS", ""),
        "NameZ": row.get("NameZ", "")
    }

    # Lower-weight proximity fields (lists)
    list_fields = {
        "nearby_named_places": row.get("nearby_named_places", []),
        "nearby_terrain": row.get("nearby_terrain", []),
        "nearby_areas": row.get("nearby_areas", []),
        "nearby_lakes": row.get("nearby_lakes", [])
    }

    # Proximity zone scoring
    name_score = 0.0
    proximity_hits = []

    for field_name, field_value in text_fields.items():
        if query_loc in unidecode(str(field_value).lower()):
            name_score += 0.2
            proximity_hits.append(f"{field_name}")

    for field_name, field_values in list_fields.items():
        if isinstance(field_values, list):
            if any(query_loc in unidecode(str(item).lower()) for item in field_values):
                name_score += 0.1
                proximity_hits.append(f"{field_name}")

    name_score = min(name_score, 0.6)
    if name_score > 0:
        reasons.append(f"✅ Name match in: {', '.join(proximity_hits)}")

    # Fuzzy bonus
    all_names = row.get("nearby_named_places", []) + [row.get("nearest_named_place", "")]
    all_names = [unidecode(str(x).lower().strip()) for x in all_names]
    fuzz_scores = [fuzz.ratio(query_loc, name) for name in all_names]
    max_fuzz = max(fuzz_scores) if fuzz_scores else 0
    fuzzy_score = (max_fuzz / 100) * 0.2 if max_fuzz > 70 else 0.0
    if fuzzy_score:
        reasons.append(f"✅ Fuzzy name match ({max_fuzz}%)")

    # Canton score
    canton_score = 0.0
    canton_list = row.get("canton_de", "")
    if isinstance(canton_list, str):
        canton_list = [c.strip() for c in canton_list.split(",")]
    if canton_list:
        canton_score = 0.2
        reasons.append(f"🏞️ In cantons: {', '.join(canton_list)}")

    # Distance match
    dist_score = 0.0
    dist_km = row.get("DistanzE", row.get("LaengeR", 0)) / 1000
    target_km = parsed.get("distance_km")
    if target_km:
        diff = abs(dist_km - target_km)
        dist_score = max(0, 1 - (diff / 10)) * 0.3
        reasons.append(f"📏 Distance: {dist_km:.1f} km vs {target_km} km")

    # Elevation gain score
    gain_score = 0.0
    gain = row.get("HoeheAufE") or row.get("HoeheAufR", 0)
    target_gain = parsed.get("elevation_gain_m")

    if target_gain and gain:
        diff = abs(gain - target_gain)
        gain_score = max(0, 1 - (diff / 400)) * 0.2  # Adjust 400 if needed
        reasons.append(f"⛰️ Gain: {int(gain)} m vs {int(target_gain)} m")
    elif gain and target_km:
        expected_gain = target_km * 60
        diff = abs(gain - expected_gain)
        gain_score = max(0, 1 - (diff / 600)) * 0.2
        reasons.append(f"⛰️ Gain: {int(gain)} m")


    # Time score
    time_score = 0.0
    raw_time = row.get("ZeitStZiE") or row.get("ZeitStZiR")
    if raw_time and target_km:
        expected = target_km * 60
        diff = abs(raw_time - expected)
        time_score = max(0, 1 - (diff / 180)) * 0.1
        reasons.append(f"⏱️ Time: {int(raw_time)} min")

    # Total
    total_score = name_score + fuzzy_score + canton_score + dist_score + gain_score + time_score
    final_score = round(min(total_score, 1.0), 3)

    logger.debug(
        f"🏔️ Scored hike: {row.get('NameS', '')} → {row.get('NameZ', '') or row.get('NameR', '')} "
        f"| Score: {final_score} | Components: "
        f"name={name_score:.3f}, fuzzy={fuzzy_score:.3f}, canton={canton_score:.3f}, "
        f"dist={dist_score:.3f}, gain={gain_score:.3f}, time={time_score:.3f} "
        f"| Reasons: {reasons}"
    )

    return final_score, reasons



@app.get("/recommendations")
async def get_recommendations(prompt: str):
    logger.info(f"Received prompt: '{prompt}'")
    parsed, raw = parse_prompt_with_gpt(prompt)

    start_only = parsed.get("start_only", False)
    end_only = parsed.get("end_only", False)
    distance_km = parsed.get("distance_km")
    min_km = parsed.get("distance_min")
    max_km = parsed.get("distance_max")
    loop_only = parsed.get("loop_only", False)

    location = parsed.get("location")
    best_match = None

    def normalize_string(s):
        return unidecode(str(s)).lower().strip()

    if not location:
        logger.info("📉 No location parsed by GPT. Trying fallback fuzzy match...")

        all_possible_locations = pd.concat([
            gdf["start_location"],
            gdf["end_location"],
            gdf.get("route_name", pd.Series(dtype=str)),
            gdf_routes.get("route_name", pd.Series(dtype=str))
        ]).dropna().unique()

        fallback_match = process.extractOne(prompt.lower(), all_possible_locations)
        if fallback_match and fallback_match[1] >= 85:
            location = fallback_match[0]
            logger.info(f"🔁 Fallback match using prompt: '{prompt}' → '{location}' (score: {fallback_match[1]})")
        else:
            logger.warning("❌ No fallback match found — aborting.")
            return {
                "parsed": parsed,
                "results": [],
                "raw_gpt_output": raw,
                "error": "No location or distance understood. Please rephrase your prompt."
            }

    logger.info(f"Parsed with GPT: {parsed}")
    results = []
    location_filter = gdf["start_location"].notnull()

    if location:
        query_location = normalize_string(location)

        semantic_cols = ["nearby_terrain", "nearby_areas", "nearby_named_places", "nearby_lakes"]

        def list_contains_query(lst):
            if isinstance(lst, list):
                return any(query_location in normalize_string(x) for x in lst)
            return False

        # Etappen filter
        location_mask = pd.Series(False, index=gdf.index)
        for col in semantic_cols:
            if col in gdf.columns:
                location_mask |= gdf[col].apply(list_contains_query)
        if location_mask.sum() == 0:
            for col in ["start_location", "end_location", "route_name"]:
                if col in gdf.columns:
                    location_mask |= gdf[col].astype(str).apply(lambda val: query_location in normalize_string(val))
        location_filter = location_mask
        logger.info(f"📍 Matching location '{query_location}' found in {location_mask.sum()} Etappen")

        # Route filter
        route_location_mask = pd.Series(False, index=gdf_routes.index)
        for col in semantic_cols:
            if col in gdf_routes.columns:
                route_location_mask |= gdf_routes[col].apply(list_contains_query)
        if route_location_mask.sum() == 0:
            if "route_name" in gdf_routes.columns:
                route_location_mask |= gdf_routes["route_name"].astype(str).apply(lambda val: query_location in normalize_string(val))
        logger.info(f"📦 Matching location '{query_location}' found in {route_location_mask.sum()} Routes")

        # Add route matches
        route_matches = gdf_routes[route_location_mask]
        for _, route_row in route_matches.iterrows():
            try:
                route_dict = Route(route_row).to_dict()
                hike_score, hike_reasons = score_hike(route_row, parsed, location)
                route_dict["match_score"] = hike_score
                route_dict["match_reasons"] = hike_reasons
                results.append(route_dict)
            except Exception as e:
                logger.warning(f"Skipping route due to error: {e}")
                
    # Distance filtering for Etappen only
    if min_km and max_km:
        dist_filter = gdf["DistanzE"].between(min_km * 1000, max_km * 1000)
    elif distance_km:
        dist_filter = gdf["DistanzE"].between((distance_km - 2) * 1000, (distance_km + 2) * 1000)
    else:
        dist_filter = gdf["DistanzE"] > 0

    matches = gdf[location_filter & dist_filter]
    target_gain = parsed.get("elevation_gain_m")
    if target_gain:
        matches = matches[
            (gdf["HoeheAufE"] - target_gain).abs() <= 400
        ]

    logger.info(f"📈 Elevation filter applied: ±400m around {target_gain}")

    logger.info(f"Found {len(matches)} matching Etappen.")


    if loop_only:
        matches = matches[matches["is_loop"] == True]
        logger.info(f"Loop-only filter active: {loop_only}")

    if not parsed.get("trail_type"):
        all_types = matches["WegKat"].explode().dropna().unique().tolist()
        parsed["trail_type"] = ", ".join(all_types) if all_types else None

    if not parsed.get("surface_type"):
        all_surfaces = matches["BelagTLM"].explode().dropna().unique().tolist()
        parsed["surface_type"] = ", ".join(all_surfaces) if all_surfaces else None

    for _, row in matches.iterrows():
        try:
            hike_dict = Etappe(row, gtfs_stops).to_dict()
            hike_score, hike_reasons = score_hike(row, parsed, location)
            hike_dict["match_score"] = hike_score
            hike_dict["match_reasons"] = hike_reasons
            results.append(hike_dict)
        except Exception as e:
            logger.warning(f"Skipping hike due to error: {e}")

    # Include contributions
    try:
        contrib_df = pd.read_csv("contributions.csv").fillna("")

        query = unidecode(location.lower()) if location else ""

        for _, row in contrib_df.iterrows():
            contrib_title = unidecode(str(row["title"]).lower())
            contrib_desc = unidecode(str(row["description"]).lower())

            if query not in contrib_title and query not in contrib_desc:
                continue
            
            contrib_id = row["id"]
            contrib_dist = float(row["distance_km"]) if row["distance_km"] else None
            contrib_gain = float(row["elevation_gain"]) if row["elevation_gain"] else None
            contrib_time = float(row["duration_minutes"]) if row["duration_minutes"] else None
            is_loop = bool(row["is_loop"]) if row.get("is_loop") else False

            score = 0.0
            reasons = []

            # Name relevance scoring (0.6 max)
            query = unidecode(location.lower()) if location else ""
            name_score = 0.0
            if query in contrib_title:
                name_score += 0.4
                reasons.append(" Name appears in title")
            if query in contrib_desc:
                name_score += 0.2
                reasons.append(" Name appears in description")
            name_score = min(name_score, 0.6)
            score += name_score

            # Distance match (0.3)
            target_km = parsed.get("distance_km")
            if target_km and contrib_dist:
                diff = abs(contrib_dist - target_km)
                dist_score = max(0, 1 - (diff / 10)) * 0.3
                score += dist_score
                reasons.append(f"📏 Distance: {contrib_dist:.1f} km vs {target_km} km")

            # Elevation gain match (0.2)
            target_gain = parsed.get("elevation_gain_m")
            if contrib_gain:
                if target_gain:
                    diff = abs(contrib_gain - target_gain)
                    gain_score = max(0, 1 - (diff / 400)) * 0.2
                    reasons.append(f"⛰️ Gain: {int(contrib_gain)} m vs {int(target_gain)} m")
                elif target_km:
                    expected_gain = target_km * 60
                    diff = abs(contrib_gain - expected_gain)
                    gain_score = max(0, 1 - (diff / 600)) * 0.2
                    reasons.append(f"⛰️ Gain: {int(contrib_gain)} m")

                score += gain_score

            # Time match (0.1)
            if contrib_time and target_km:
                expected = target_km * 60
                diff = abs(contrib_time - expected)
                time_score = max(0, 1 - (diff / 180)) * 0.1
                score += time_score
                reasons.append(f"⏱️ Time: {int(contrib_time)} min")

            # Loop bonus (0.2)
            if parsed.get("loop_only") and is_loop:
                score += 0.2
                reasons.append("🔁 User wants loop, and it's a loop")

            # Final score clip
            final_score = round(min(score, 1.0), 3)

            hike_dict = {
                "id": contrib_id,
                "title": row["title"],
                "description": row["description"],
                "distance_km": contrib_dist,
                "duration_minutes": contrib_time,
                "difficulty": row["difficulty"],
                "surface_type": row["surface_type"],
                "suitable_for_kids": bool(row["suitable_for_kids"]) if row.get("suitable_for_kids") else None,
                "photo_file": basename(row["photo_file"].replace("\\", "/")) if row["photo_file"] else None,
                "gpx_file": basename(row["gpx_file"].replace("\\", "/")) if row["gpx_file"] else None,
                "trail_type": {"custom": 100},
                "surface_type_pct": {row["surface_type"]: 100} if row["surface_type"] else {},
                "elevation_gain": contrib_gain,
                "elevation_loss": float(row["elevation_loss"]) if row.get("elevation_loss") else None,
                "is_loop": is_loop,
                "time": format_hike_time(contrib_time) if contrib_time else None,
                "nearest_transport": None,
                "match_score": final_score,
                "match_reasons": reasons,
                "type": "contribution",
            }

            results.append(hike_dict)

    except Exception as e:
        logger.warning(f"⚠️ Skipping contribution due to error: {e}")

    
    results = sorted(results, key=lambda x: x["match_score"], reverse=True)

    return {
        "parsed": parsed,
        "results": results,
        "raw_gpt_output": raw,
        "error": None
    }

@app.get("/gpx")
async def get_gpx_file(
    item_type: str = Query(..., enum=["etappe", "route"]),
    item_id: str = Query(...)
):
    try:
        if item_type == "etappe":
            hike = hike_manager.get_etappe_by_id(item_id)
        elif item_type == "route":
            hike = hike_manager.get_route_by_id(item_id)
        else:
            raise HTTPException(status_code=400, detail="Invalid item_type")

        if not hike:
            raise HTTPException(status_code=404, detail=f"{item_type.title()} not found")

        gpx_data = hike.to_gpx()
        filename = f"{item_type}_{item_id}.gpx"

        return Response(
            content=gpx_data,
            media_type="application/gpx+xml",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    except Exception as e:
        logger.error(f"Error generating GPX: {e}")
        raise HTTPException(status_code=500, detail="GPX generation failed")


@router.post("/upload_hike")
async def upload_hike(
    gpx_file: UploadFile,
    title: str = Form(...),
    description: str = Form(...),
    surface_type: str = Form(...),
    difficulty: str = Form(...),
    duration_minutes: int = Form(...),
    distance_km: float = Form(...),
    suitable_for_kids: bool = Form(...),
    photo: Optional[UploadFile] = None
):
    # ⬅️ Save files to disk / cloud
    # ⬅️ Parse GPX to extract bounding box/points
    # ⬅️ Store metadata in your hike database (could be CSV, SQLite, or Postgres)
    return {"status": "success", "message": "Hike uploaded!"}

def extract_route_data(row, type):
    row_data = row.drop(labels=["geometry"]).to_dict()

    row_data["distance_km"] = round(row.get("DistanzE", row.get("LaengeR", 0)) / 1000, 1)
    raw_time = row.get("ZeitStZiE") if type == "etappe" else row.get("ZeitStZiR")
    row_data["time"] = format_hike_time(raw_time) if raw_time is not None else None
    row_data["difficulty"] = row.get("KonditionE", "n/a")
    row_data["elevation_gain"] = safe_round(
        row.get("HoeheAufE") if type == "etappe" else row.get("HoeheAufR")
    )
    row_data["elevation_loss"] = safe_round(
        row.get("HoeheAbE") if type == "etappe" else row.get("HoeheAbR")
    )

    def safe_eval(val):
        try:
            return ast.literal_eval(val) if isinstance(val, str) else val
        except:
            return []

    trail_values = safe_eval(row.get("WegKat"))
    surface_values = safe_eval(row.get("BelagTLM"))
    row_data["trail_type"] = percentage_dict(trail_values)
    row_data["surface_type"] = percentage_dict(surface_values)

    if type == "etappe":
        line = row.geometry
        if line and line.is_valid and not line.is_empty:
            line_wgs84 = gpd.GeoSeries([line], crs="EPSG:2056").to_crs("EPSG:4326").iloc[0]
            start_point = line_wgs84.interpolate(0.0)
            end_point = line_wgs84.interpolate(line_wgs84.length)
            nearest_start = get_nearest_stop(start_point, gtfs_stops)
            nearest_end = get_nearest_stop(end_point, gtfs_stops)
            row_data["nearest_transport"] = {
                "start": {
                    "name": nearest_start["stop_name"],
                    "distance_m": int(nearest_start["dist"])
                },
                "end": {
                    "name": nearest_end["stop_name"],
                    "distance_m": int(nearest_end["dist"])
                }
            }

    row_data["id"] = row["LVEtappe_I"] if type == "etappe" else row["LVRoute_ID"]

    return {k: (None if pd.isna(v) else v) for k, v in row_data.items()}

class ContributionHike(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    distance_km: Optional[float] = None
    duration_minutes: Optional[int] = None
    difficulty: Optional[str] = None
    surface_type: Optional[str] = None
    suitable_for_kids: Optional[bool] = None
    photo_file: Optional[str] = None
    gpx_file: Optional[str] = None  # ✅ NEW LINE

    trail_type: Dict[str, int] = {"custom": 100}
    surface_type_pct: Dict[str, int] = {}
    time: Optional[str] = None
    nearest_transport: Optional[dict] = None
    elevation_gain: Optional[float] = None
    elevation_loss: Optional[float] = None
    is_loop: Optional[bool] = None

@app.get("/hike", response_model=Union[ContributionHike, dict])
def get_hike(type: str = Query(...), id: str = Query(...)):
    if type == "etappe":
        hike = hike_manager.get_etappe_by_id(id)
        if not hike:
            raise HTTPException(status_code=404, detail="Etappe not found")
        return hike.to_dict()
    elif type == "route":
        hike = hike_manager.get_route_by_id(id)
        if not hike:
            raise HTTPException(status_code=404, detail="Route not found")
        return hike.to_dict()
    elif type == "contribution":
        try:
            contrib_df = pd.read_csv("contributions.csv")
            row = contrib_df[contrib_df["id"] == id]

            if row.empty:
                raise HTTPException(status_code=404, detail="Contribution not found")

            row = row.iloc[0].astype(object).apply(lambda x: x if pd.notnull(x) else None)

            hike = ContributionHike(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                distance_km=float(row["distance_km"]) if row["distance_km"] is not None else None,
                duration_minutes=int(row["duration_minutes"]) if row["duration_minutes"] is not None else None,
                difficulty=row["difficulty"],
                surface_type=row["surface_type"],
                suitable_for_kids=bool(row["suitable_for_kids"]) if row["suitable_for_kids"] is not None else None,
                photo_file=basename(row["photo_file"].replace("\\", "/")) if row["photo_file"] else None,
                gpx_file=basename(row.get("gpx_file", "").replace("\\", "/")) if row.get("gpx_file") else None,
                elevation_gain=float(row["elevation_gain"]) if row.get("elevation_gain") is not None else None,
                elevation_loss=float(row["elevation_loss"]) if row.get("elevation_loss") is not None else None,
                is_loop=bool(row["is_loop"]) if row.get("is_loop") is not None else None,
                surface_type_pct={row["surface_type"]: 100} if row["surface_type"] else {},
                trail_type={"custom": 100},
                nearest_transport=None,
                time=format_hike_time(row["duration_minutes"]) if pd.notnull(row["duration_minutes"]) else None  # ✅ add this
            )

            return hike

        except Exception as e:
            logger.error(f"Error loading contribution hike: {e}")
            raise HTTPException(status_code=500, detail="Failed to load contribution")

    else:
        raise HTTPException(status_code=400, detail="Invalid hike type")


@app.get("/debug/semantic_columns")
def debug_semantic_columns():
    list_cols = ["nearby_terrain", "nearby_areas", "nearby_named_places", "BelagTLM", "WegKat"]
    info = {"etappen": {}, "routes": {}}

    def analyze(df, label):
        for col in list_cols:
            if col not in df.columns:
                info[label][col] = "🚫 Column not found"
                continue

            col_type = str(df[col].dtype)
            sample_value = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
            sample_type = str(type(sample_value)) if sample_value is not None else "None"
            sample_display = sample_value if isinstance(sample_value, list) else str(sample_value)

            info[label][col] = {
                "column_dtype": col_type,
                "first_non_null_value_type": sample_type,
                "first_non_null_value": sample_display
            }

    analyze(gdf, "etappen")
    analyze(gdf_routes, "routes")

    return info

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)