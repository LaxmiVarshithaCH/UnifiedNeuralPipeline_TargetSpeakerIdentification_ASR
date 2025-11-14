import { useEffect, useRef } from "react";
import WaveSurfer from "wavesurfer.js";
import RegionsPlugin from "wavesurfer.js/dist/plugins/regions.js";

const COLORS = {
  Target: "#6366f180",
  Speaker_0: "#ef444480",
  Speaker_1: "#22c55e80",
  Speaker_2: "#eab30880",
  Speaker_3: "#06b6d480",
};

export default function Waveform({ audioUrl, segments }) {
  const containerRef = useRef(null);
  const wavesurferRef = useRef(null);

  useEffect(() => {
    if (!audioUrl) return;

    const ws = WaveSurfer.create({
      container: containerRef.current,
      waveColor: "#94a3b8",
      progressColor: "#4f46e5",
      height: 120,
      responsive: true,
      plugins: [
        RegionsPlugin.create()
      ]
    });

    wavesurferRef.current = ws;

    ws.load(audioUrl);

    ws.on("ready", () => {
      console.log("Waveform loaded");

      segments.forEach(seg => {
        ws.addRegion({
          start: seg.start,
          end: seg.end,
          color: COLORS[seg.speaker] || "#9ca3af80"
        });
      });
    });

    return () => {
      ws.destroy();
    };
  }, [audioUrl]);

  return (
    <div className="card">
      <h3>Waveform Visualization</h3>
      <div ref={containerRef}></div>
    </div>
  );
}
