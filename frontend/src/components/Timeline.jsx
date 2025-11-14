export default function Timeline({ segments }) {
  if (!segments.length) return null;

  const totalDuration = segments[segments.length - 1].end;

  const speakerColors = {
    Target: "#6366f1",
    Speaker_0: "#ef4444",
    Speaker_1: "#22c55e",
    Speaker_2: "#eab308",
    Speaker_3: "#06b6d4"
  };

  return (
    <div style={{
      display: "flex",
      width: "100%",
      height: "60px",
      borderRadius: "8px",
      overflow: "hidden",
      background: "#e5e7eb",
      marginBottom: "20px"
    }}>
      {segments.map((seg, i) => {
        const width = ((seg.end - seg.start) / totalDuration) * 100;

        return (
          <div key={i}
               style={{
                 width: `${width}%`,
                 background: speakerColors[seg.speaker] || "#9ca3af"
               }}
               title={`${seg.speaker} (${seg.start}s → ${seg.end}s)`}
          />
        );
      })}
    </div>
  );
}
