const COLORS = {
  Target: "#6366f1",
  Speaker_0: "#ef4444",
  Speaker_1: "#22c55e",
  Speaker_2: "#eab308",
  Speaker_3: "#06b6d4",
};

export default function SpeakerLegend() {
  return (
    <div className="card">
      <h4>Speaker Legend</h4>
      {Object.entries(COLORS).map(([speaker, color]) => (
        <div key={speaker} style={{ display: "flex", alignItems: "center", marginBottom: "6px" }}>
          <div style={{
            width: "20px",
            height: "20px",
            background: color,
            marginRight: "10px",
            borderRadius: "4px"
          }}></div>
          {speaker}
        </div>
      ))}
    </div>
  );
}
