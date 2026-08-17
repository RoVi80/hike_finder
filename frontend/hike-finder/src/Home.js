import React, { useState, useEffect } from "react";
import "./Home.css";
import { useNavigate } from "react-router-dom";
import { useBackground } from "./BackgroundContext";

function Home() {
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState("");
  const { bgImage, setBgImage } = useBackground();

  useEffect(() => {
    const backgrounds = [
      "/backgrounds/this2.jpg",     
      "/backgrounds/this3.jpg",
      "/backgrounds/IMG20220115170646.jpg",
      "/backgrounds/IMG20230707155259.jpg",
      "/backgrounds/IMG20240721065336.jpg",
      "/backgrounds/this1.jpg"
    ];
    const random = backgrounds[Math.floor(Math.random() * backgrounds.length)];
    setBgImage(random);
  }, []);

  const handleSearch = () => {
    if (prompt.trim()) {
      navigate(`/results?prompt=${encodeURIComponent(prompt)}`);
    }
  };

  const backgroundStyle = {
    backgroundImage: `url(${bgImage})`,
    backgroundSize: "cover",
    backgroundPosition: "center",
    padding: "2rem",
    color: "#fff",
    backdropFilter: "blur(2px)"
  };

  return (
    <div>
      <img src={bgImage} alt="Background" className="hero-background" />
      <div className="background-wrapper" style={backgroundStyle}>
        <div className="container centered">
          <div className="App">
            <h1>🏞️ Smart Hike Finder</h1>
            <div className="search-bar">
              <input
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="e.g. A hike near Andermatt of about 12k"
              />
              <button onClick={handleSearch}>Search</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home;
