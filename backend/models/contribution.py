from pydantic import BaseModel
from typing import Optional, Dict
from utils.helpers import format_hike_time

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
    gpx_file: Optional[str] = None

    trail_type: Dict[str, int] = {"custom": 100}
    surface_type_pct: Dict[str, int] = {}
    nearest_transport: Optional[dict] = None
"""
    @property
    def time(self):
        if self.duration_minutes is not None:
            return format_hike_time(self.duration_minutes)
        return None
"""