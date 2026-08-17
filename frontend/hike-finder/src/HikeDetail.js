import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import axios from "axios";
import { getBackendUrl } from "./config";
import { useBackground } from "./BackgroundContext";
import { useNavigate } from "react-router-dom";
import GPXMap from "./GPXMap";

function HikeDetail() {
  const { type, id } = useParams();
  const [hike, setHike] = useState(null);
  const { bgImage } = useBackground();
  const navigate = useNavigate();

  useEffect(() => {
    axios
      .get(`${getBackendUrl()}/hike`, { params: { type, id } })
      .then((res) => {
        console.log("Loaded hike:", res.data);
        setHike(res.data);
      })
      .catch((err) => console.error("Error loading hike:", err));
  }, [type, id]);

  if (!hike) return <p>Loading...</p>;

  return (
    <>
      <img src={bgImage} alt="Background" className="hero-background" />
      <button onClick={() => navigate(-1)} style={{ marginBottom: '1rem' }}>
        ← Back
      </button>

      <div className="background-wrapper">
        <div className="App">
          {/* Photo for contributions */}
          {type === "contribution" && hike.photo_file && (
            <div style={{ marginBottom: "1rem" }}>
              <img
                src={`${getBackendUrl()}/uploads/${hike.photo_file}`}
                alt="Uploaded by user"
                style={{ maxWidth: "100%", borderRadius: "12px", boxShadow: "0 0 10px rgba(0,0,0,0.4)" }}
              />
            </div>
          )}

          <h1>
            {type === "contribution"
              ? hike.from || hike.title || "User-Contributed Hike"
              : hike.route_name || `${hike.from} → ${hike.to}`}
          </h1>

          <p><strong>Distance:</strong> {hike.distance_km} km</p>
          <p><strong>Time:</strong> {hike.time || "n/a"}</p>
          <p><strong>Difficulty:</strong> {hike.difficulty || "n/a"}</p>
          <p><strong>Elevation gain:</strong> {hike.elevation_gain ?? "?"} m</p>
          <p><strong>Elevation loss:</strong> {hike.elevation_loss ?? "?"} m</p>
          <p><strong>Loop:</strong> {hike.is_loop ? "yes" : "no"}</p>

          {hike.trail_type && typeof hike.trail_type === "object" && (
            <p>
              <strong>Trail type:</strong><br />
              {Object.entries(hike.trail_type).map(([type, pct]) => (
                <span key={type}>{type}: {pct}%<br /></span>
              ))}
            </p>
          )}

          {hike.surface_type && typeof hike.surface_type === "object" && (
            <p>
              <strong>Surface:</strong><br />
              {Object.entries(hike.surface_type).map(([type, pct]) => (
                <span key={type}>{type}: {pct}%<br /></span>
              ))}
            </p>
          )}

          {hike.nearest_transport && (
            <>
              <p><strong>Start near:</strong> {hike.nearest_transport.start.name} ({hike.nearest_transport.start.distance_m} m)</p>
              <p><strong>End near:</strong> {hike.nearest_transport.end.name} ({hike.nearest_transport.end.distance_m} m)</p>
            </>
          )}

          {/* GPX section */}
          {hike.id && (
            <>
              {type === "contribution" ? (
                hike.gpx_file ? (
                  <>
                    <a
                      href={`${getBackendUrl()}/download/${hike.gpx_file}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      download
                    >
                      📥 Download GPX
                    </a>
                    <GPXMap gpxUrl={`${getBackendUrl()}/uploads/${hike.gpx_file}`} />
                  </>
                ) : (
                  <p>No GPX file available.</p>
                )
              ) : (
                <>
                  <a
                    href={`${getBackendUrl()}/gpx?item_type=${type}&item_id=${id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    download
                  >
                    📥 Download GPX
                  </a>
                  <GPXMap gpxUrl={`${getBackendUrl()}/gpx?item_type=${type}&item_id=${id}`} />
                </>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}

export default HikeDetail;
