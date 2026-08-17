import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useEffect } from 'react';
import L from 'leaflet';
import 'leaflet-gpx';

function GPXViewer({ gpxUrl }) {
  const map = useMap();

  useEffect(() => {
    console.warn("No GPX URL provided");
    if (!gpxUrl) return;


    console.log("Loading GPX from", gpxUrl); // ✅ ADD THIS


    const gpx = new L.GPX(gpxUrl, {
      async: true,
      marker_options: {
        startIconUrl: null,
        endIconUrl: null,
        shadowUrl: null
      }
    });

    gpx.on('loaded', function (e) {
      map.fitBounds(e.target.getBounds());
    });

    gpx.addTo(map);
  }, [gpxUrl, map]);

  return null;
}

export default function GPXMap({ gpxUrl }) {
  return (
    <MapContainer
      style={{ height: "400px", width: "100%", marginTop: "2rem" }}
      center={[46.8, 8.3]} // Default center on CH
      zoom={13}
      scrollWheelZoom={false}
    >
      <TileLayer
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='© OpenStreetMap contributors'
      />
      <GPXViewer gpxUrl={gpxUrl} />
    </MapContainer>
  );
}
