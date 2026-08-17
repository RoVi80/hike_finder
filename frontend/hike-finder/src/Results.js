import React, { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import axios from "axios";
import { getBackendUrl } from "./config";
import { useBackground } from "./BackgroundContext";

function Results() {
  const { bgImage } = useBackground();
  const navigate = useNavigate();
  const location = useLocation();


  const queryPrompt = new URLSearchParams(location.search).get("prompt") || "";
  const [promptInput, setPromptInput] = useState(queryPrompt);
  const [results, setResults] = useState([]);
  const [parsed, setParsed] = useState(null);
  const [viewMode, setViewMode] = useState("grid");
  const [error, setError] = useState(null);
  

  // Prevent unnecessary re-fetching
  const lastFetchedPrompt = useRef("");

  // Load cached results (once)
  useEffect(() => {
    if (!queryPrompt) return;
  
    const cached = sessionStorage.getItem(`results:${queryPrompt}`);
    if (cached) {
      const { results: cachedResults, parsed: cachedParsed } = JSON.parse(cached);
      setResults(cachedResults);
      setParsed(cachedParsed);
      console.log("💾 Loaded from cache:", queryPrompt);
      return;
    }
  
    // Avoid refetching the same thing unnecessarily
    if (lastFetchedPrompt.current === queryPrompt && results.length > 0) return;
  
    setPromptInput(queryPrompt);
    lastFetchedPrompt.current = queryPrompt;
  
    console.log("🔁 Fetching for:", queryPrompt);
  
    const fetchHikes = async () => {
      try {
        const res = await axios.get(`${getBackendUrl()}/recommendations`, {
          params: { prompt: queryPrompt },
        });

        console.log("✅ Full response from backend:", res.data); // <-- ADD THIS

        if (res.data.error) {
          setError(res.data.error);
          setResults([]);
          setParsed(null);
        } else {
          const newResults = res.data.results || [];
          const newParsed = res.data.parsed || null;
  
          setResults(newResults);
          setParsed(newParsed);
          setError(null);
  
          console.log("Results returned:", newResults);

          sessionStorage.setItem(
            `results:${queryPrompt}`,
            JSON.stringify({ results: newResults, parsed: newParsed })
          );
        }
      } catch (err) {
        console.error("Error fetching recommendations:", err);
        setError("Error fetching recommendations. Try again.");
        setResults([]);
        setParsed(null);
      }
    };
  
    fetchHikes();
  }, [queryPrompt, results.length]);
  

  const handleSearch = () => {
    if (promptInput.trim()) {
      const encoded = encodeURIComponent(promptInput.trim());
      navigate(`/results?prompt=${encoded}`);
    }
  };

  return (
    <>
      {bgImage && <img src={bgImage} alt="Background" className="hero-background" />}
      <div
        className="background-wrapper"
        style={{
          backgroundImage: `url(${bgImage})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          padding: "2rem",
          color: "#fff",
          backdropFilter: "blur(2px)",
        }}
      >
        <div className="container top">
          <div className="App">
            <h1>🏞️ Smart Hike Finder Results</h1>

            <div className="search-bar" style={{ marginBottom: "1rem" }}>
              <input
                type="text"
                value={promptInput}
                onChange={(e) => setPromptInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSearch();
                }}
                placeholder="e.g. A hike near Andermatt of about 12k"
              />
              <button onClick={handleSearch}>Search</button>
            </div>

            <div className="view-toggle">
              <button onClick={() => setViewMode("list")} disabled={viewMode === "list"}>
                List View
              </button>
              <button onClick={() => setViewMode("grid")} disabled={viewMode === "grid"}>
                Grid View
              </button>
            </div>

            {parsed && (
              <div className="parsed-info">
                <strong>🔍 Parsed Input:</strong>
                <br />
                Location: {parsed.location || "n/a"} | Start only: {parsed.start_only ? "yes" : "no"} | End only:{" "}
                {parsed.end_only ? "yes" : "no"}
                <br />
                Distance: {parsed.distance_km || `${parsed.distance_min || "?"}–${parsed.distance_max || "?"}`} km
                <br />
                Trail type: {parsed.trail_type || "n/a"} | Surface type: {parsed.surface_type || "n/a"} | Loop:{" "}
                {parsed.loop ? "yes" : "no"}
              </div>
            )}

            {error && <div className="error-message">⚠️ {error}</div>}
          </div>

          <div className={`results ${viewMode}`}>
            {results.map((hike, idx) => (
              <div
                className="card"
                key={idx}
                onClick={() => {
                  navigate(`/hike/${hike.type}/${hike.id}`, {
                    state: { results, prompt: promptInput, parsed },
                    });
                  }}
                style={{
                  cursor: "pointer",
                  opacity: hike.type === "contribution" ? 0.95 : 1,
                }}
              >
              

                <>
                  <div className={`type-badge ${hike.type === "contribution" ? "contribution" : hike.type}`}>
                    {hike.type === "contribution"
                    ? "CONTRIBUTION"
                    : (hike.type || "unknown").toUpperCase()}
                  </div>

                  {hike.type === "contribution" ? (
                    <>
                    <h2>{hike.title}</h2>

                    <p>
                      <strong>Distance:</strong> {hike.distance_km ?? "?"} km
                    </p>
                    <p>
                      <strong>Difficulty:</strong> {hike.difficulty ?? "n/a"}
                    </p>
                    {hike.time && (
                      <p>
                        <strong>Time:</strong> {hike.time}
                      </p>
                    )}

                    <p>
                      <strong>Trail type:</strong>
                      <br />
                      {hike.trail_type && typeof hike.trail_type === "object"
                        ? Object.entries(hike.trail_type).map(([type, pct]) => (
                            <span key={type}>
                              {type}: {pct}%<br />
                            </span>
                          ))
                        : "n/a"}
                    </p>

                    <p>
                      <strong>Surface:</strong>
                      <br />
                      {hike.surface_type_pct && typeof hike.surface_type_pct === "object"
                        ? Object.entries(hike.surface_type_pct).map(([type, pct]) => (
                            <span key={type}>
                              {type}: {pct}%<br />
                            </span>
                          ))
                        : "n/a"}
                    </p>

                    {hike.match_score !== undefined && (
                      <div className="match-info">
                        <p>
                          <strong>🔍 Match score:</strong> {Math.round(hike.match_score * 100)}%
                        </p>
                        {Array.isArray(hike.match_reasons) && (
                          <ul>
                            {hike.match_reasons.map((reason, i) => (
                              <li key={i}>{reason}</li>
                            ))}
                          </ul>
                        )}
                      </div>
                    )}

                    </>
                  ) : (
                    <>
                      <h2>
                        {hike.type === "route"
                        ? hike.route_name || "Unnamed Route"
                        : hike.type === "etappe"
                        ? `${hike.from} → ${hike.to}`
                        : hike.title}
                      </h2>
                      <p>
                        <strong>Distance:</strong> {hike.distance_km} km
                      </p>
                      <p>
                        <strong>Difficulty:</strong> {hike.difficulty}
                      </p>
                      {hike.time && (
                        <p>
                          <strong>Time:</strong> {hike.time}
                        </p>
                      )}
                      <p>
                        <strong>Trail type:</strong>
                        <br />
                        {hike.trail_type && typeof hike.trail_type === "object"
                          ? Object.entries(hike.trail_type).map(([type, pct]) => (
                              <span key={type}>
                                {type}: {pct}%<br />
                              </span>
                            ))
                          : "n/a"}
                      </p>
                      <p>
                        <strong>Surface:</strong>
                        <br />
                        {hike.surface_type && typeof hike.surface_type === "object"
                          ? Object.entries(hike.surface_type).map(([type, pct]) => (
                              <span key={type}>
                                {type}: {pct}%<br />
                              </span>
                            ))
                          : "n/a"}
                      </p>
                      {hike.nearest_transport && (
                        <>
                          <p>
                            <strong>Start near:</strong> {hike.nearest_transport.start.name} (
                            {hike.nearest_transport.start.distance_m} m)
                          </p>
                          <p>
                            <strong>End near:</strong> {hike.nearest_transport.end.name} (
                            {hike.nearest_transport.end.distance_m} m)
                          </p>
                        </>
                      )}
                        {hike.match_score !== undefined && (
                        <div className="match-info">
                          <p>
                            <strong>🔍 Match score:</strong> {Math.round(hike.match_score * 100)}%
                          </p>
                          {Array.isArray(hike.match_reasons) && (
                            <ul>
                              {hike.match_reasons.map((reason, i) => (
                                <li key={i}>{reason}</li>
                              ))}
                            </ul>
                          )}
                        </div>
                      )}
                    </>
                  )}
                </>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}



export default Results;
