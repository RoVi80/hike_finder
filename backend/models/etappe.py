# backend/models/etappe.py

from .hike_base import Hike
from utils.transport_nearest import get_nearest_stop
from utils.helpers import format_hike_time, percentage_dict

import ast

class Etappe(Hike):
    def __init__(self, row, gtfs_stops):
        super().__init__(id=row["LVEtappe_I"], name=f"{row['NameS']} – {row['NameZ']}", geometry=row["geometry"])
        self.start = row["NameS"]
        self.end = row["NameZ"]
        self.distance_km = round(row["DistanzE"] / 1000, 1)
        self.difficulty = row.get("KonditionE", "n/a")
        self.duration_minutes = row.get("ZeitStZiE")
        self.elevation_gain = int(row.get("HoeheAufE", 0)) if row.get("HoeheAufE") is not None else None
        self.elevation_loss = int(row.get("HoeheAbE", 0)) if row.get("HoeheAbE") is not None else None


        self.trail_type = percentage_dict(self._safe_eval(row.get("WegKat")))
        self.surface_type = percentage_dict(self._safe_eval(row.get("BelagTLM")))
        self.gtfs_stops = gtfs_stops

    def _safe_eval(self, val):
        try:
            return ast.literal_eval(val) if isinstance(val, str) else val
        except:
            return []

    def get_nearest_transport(self):
        wgs_line = self.to_wgs84()
        start_pt = wgs_line.interpolate(0.0)
        end_pt = wgs_line.interpolate(wgs_line.length)

        nearest_start = get_nearest_stop(start_pt, self.gtfs_stops)
        nearest_end = get_nearest_stop(end_pt, self.gtfs_stops)
        return {
            "start": {
                "name": nearest_start["stop_name"],
                "distance_m": int(nearest_start["dist"])
            },
            "end": {
                "name": nearest_end["stop_name"],
                "distance_m": int(nearest_end["dist"])
            }
        }

    def to_dict(self):
        base = super().to_dict()
        base.update({
            "from": self.start,
            "to": self.end,
            "distance_km": self.distance_km,
            "difficulty": self.difficulty,
            "type": "etappe",
            "trail_type": self.trail_type,
            "surface_type": self.surface_type,
            "time": format_hike_time(self.duration_minutes),
            "nearest_transport": self.get_nearest_transport(),
            "elevation_gain": self.elevation_gain,
            "elevation_loss": self.elevation_loss,
        })
        return base
