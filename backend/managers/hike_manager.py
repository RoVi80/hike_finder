# backend/managers/hike_manager.py

from models.etappe import Etappe
from models.route import Route

class HikeManager:
    def __init__(self, gdf_etappen, gdf_routes, gtfs_stops):
        self.etappen_df = gdf_etappen
        self.routes_df = gdf_routes
        self.gtfs_stops = gtfs_stops

    def get_etappe_by_id(self, id):
        row = self.etappen_df[self.etappen_df["LVEtappe_I"] == id]
        if row.empty:
            return None
        return Etappe(row.iloc[0], self.gtfs_stops)

    def get_route_by_id(self, id):
        row = self.routes_df[self.routes_df["LVRoute_ID"] == id]
        if row.empty:
            return None
        return Route(row.iloc[0])

    def filter_etappen(self, condition):
        return [Etappe(row, self.gtfs_stops).to_dict() for _, row in self.etappen_df[condition].iterrows()]
