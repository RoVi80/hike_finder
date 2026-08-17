import httpx

API_URL = "https://api3.geo.admin.ch/rest/services/api/MapServer/identify"

async def fetch_hikes_from_opendata(search_term: str) -> list:
    # Basic bounding box around Switzerland (lon/lat)
    bbox = [5.96, 45.82, 10.49, 47.81]  # [minX, minY, maxX, maxY]

    params = {
        "geometryType": "esriGeometryEnvelope",
        "geometry": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
        "layers": "all:ch.astra.wanderland-sommer",
        "tolerance": 0,
        "mapExtent": ",".join(str(x) for x in bbox),
        "imageDisplay": "800,600,96",
        "lang": "de",
        "returnGeometry": "false",
        "sr": 4326
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()

    results = []
    for feature in data.get("results", []):
        attr = feature.get("attributes", {})
        title = attr.get("title") or attr.get("name") or ""
        if search_term.lower() in title.lower():
            results.append({
                "title": title,
                "id": attr.get("id"),
                "url": f"https://map.geo.admin.ch/?topic=wandern&lang=de&bgLayer=ch.swisstopo.pixelkarte-farbe&layers=ch.astra.wanderland-sommer&layers_visibility=true&layers_opacity=1&layers_timestamp=*&E={feature.get('geometry', {}).get('x', '')}&N={feature.get('geometry', {}).get('y', '')}&zoom=5"
            })

    return results
