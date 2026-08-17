import React, { useState } from "react";
import axios from "axios";

export default function SubmitHike() {
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    surface_type: "",
    difficulty: "",
    duration_minutes: "",
    distance_km: "",
    elevation_gain: "",
    elevation_loss: "",
    suitable_for_kids: false,
    is_loop: false,
  });

  const [file, setFile] = useState(null);
  const [photo, setPhoto] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const data = new FormData();

    // Append form fields
    data.append("title", formData.title);
    data.append("description", formData.description);
    data.append("surface_type", formData.surface_type);
    data.append("difficulty", formData.difficulty);
    data.append("duration_minutes", formData.duration_minutes);
    data.append("distance_km", formData.distance_km);
    data.append("elevation_gain", formData.elevation_gain);
    data.append("elevation_loss", formData.elevation_loss);
    data.append("suitable_for_kids", formData.suitable_for_kids ? "true" : "false");
    data.append("is_loop", formData.is_loop ? "true" : "false");

    // Append files
    data.append("gpx_file", file);
    if (photo) data.append("photo", photo);

    try {
      const res = await axios.post("http://localhost:8000/upload_hike", data);
      alert(res.data.message);
    } catch (error) {
      console.error("Upload failed:", error);
      alert("❌ Upload failed. See console for details.");
    }
  };

  const handleGpxUpload = async (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);

    if (selectedFile) {
      const formData = new FormData();
      formData.append("gpx_file", selectedFile);

      try {
        const res = await axios.post("http://localhost:8000/preview_gpx", formData);
        const data = res.data;

        setFormData((prev) => ({
          ...prev,
          distance_km: data.distance_km,
          elevation_gain: data.elevation_gain,
          elevation_loss: data.elevation_loss,
          is_loop: data.is_loop,
        }));
      } catch (err) {
        console.error("Failed to preview GPX:", err);
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem", maxWidth: "400px" }}>
      <input type="text" placeholder="Title" onChange={e => setFormData({ ...formData, title: e.target.value })} />

      <input type="file" accept=".gpx" onChange={handleGpxUpload} />

      <input type="text" placeholder="Description" onChange={e => setFormData({ ...formData, description: e.target.value })} />

      <select onChange={e => setFormData({ ...formData, surface_type: e.target.value })}>
        <option value="">Surface</option>
        <option value="natural">Natural</option>
        <option value="asphalt">Asphalt</option>
      </select>

      <input type="text" placeholder="Difficulty" onChange={e => setFormData({ ...formData, difficulty: e.target.value })} />

      <input type="number" placeholder="Duration (min)" onChange={e => setFormData({ ...formData, duration_minutes: e.target.value })} />

      <input type="number" placeholder="Distance (km)" step="0.1" value={formData.distance_km} readOnly />
      <input type="number" placeholder="Elevation Gain (m)" step="1" value={formData.elevation_gain} readOnly />
      <input type="number" placeholder="Elevation Loss (m)" step="1" value={formData.elevation_loss} readOnly />

      <p>🔄 Loop Hike: {formData.is_loop ? "Yes" : "No"}</p>

      <label>
        <input
          type="checkbox"
          onChange={e => setFormData({ ...formData, suitable_for_kids: e.target.checked })}
        />
        Kid-friendly
      </label>

      <input type="file" accept="image/*" onChange={e => setPhoto(e.target.files[0])} />

      <button type="submit">Submit Hike</button>
    </form>
  );
}
