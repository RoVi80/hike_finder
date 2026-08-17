// App.js
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./Home";
import HikeDetail from "./HikeDetail";
import { BackgroundProvider } from "./BackgroundContext";
import 'leaflet/dist/leaflet.css'
import Results from "./Results";
import SubmitHike from "./SubmitHike";



function App() {
  return (
    <BackgroundProvider>
      <Router>
        <Routes>
          <Route path="/results" element={<Results />} />
          <Route path="/" element={<Home />} />
          <Route path="/hike/:type/:id" element={<HikeDetail />} />
          <Route path="/submit" element={<SubmitHike />} />
        </Routes>
      </Router>
    </BackgroundProvider>

  );
}

export default App;
