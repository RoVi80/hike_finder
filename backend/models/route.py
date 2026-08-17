# backend/models/route.py

from .hike_base import Hike
from utils.helpers import format_hike_time, percentage_dict
import ast

class Route(Hike):
    def __init__(self, row):
        super().__init__(id=row["LVRoute_ID"], name=row.get("NameR", "Unnamed Route"), geometry=row["geometry"])
        self.start = row.get("AOrt", "Start")
        self.end = row.get("ZOrt", "End")
        self.distance_km = round(row.get("LaengeR", 0) / 1000, 1)
        self.difficulty = row.get("KonditionE", "Overview")
        self.duration_minutes = row.get("ZeitStZiR")
        self.elevation_gain = row.get("HoeheAufR")
        self.elevation_loss = row.get("HoeheAbR")

        self.trail_type = percentage_dict(self._safe_eval(row.get("WegKat")))
        self.surface_type = percentage_dict(self._safe_eval(row.get("BelagTLM")))


    def _safe_eval(self, val):
        try:
            return ast.literal_eval(val) if isinstance(val, str) else val
        except:
            return []

    def to_dict(self):
        base = super().to_dict()
        base.update({
            "from": self.start,
            "to": self.end,
            "distance_km": self.distance_km,
            "difficulty": self.difficulty,
            "type": "route",
            "route_name": self.name,
            "trail_type": self.trail_type,
            "surface_type": self.surface_type,
            "time": format_hike_time(self.duration_minutes),
            "elevation_gain": int(self.elevation_gain) if self.elevation_gain is not None else None,
            "elevation_loss": int(self.elevation_loss) if self.elevation_loss is not None else None,
        })
        return base
