import Waveform from "../components/Waveform";
import SpeakerLegend from "../components/SpeakerLegend";
import Timeline from "../components/Timeline";
import SegmentCard from "../components/SegmentCard";
import React from "react";

export default function ResultsPage({ results }) {
  if (!results) return null;
  const jobId = results.jobId;
  const segments = results.result;

  const mixtureUrl = `http://localhost:8000/audio/${jobId}_mixture.wav`;
  const targetUrl  = `http://localhost:8000/audio/${jobId}_target_speaker.wav`;

  return (
    <div className="container">
      <h2>Processing Results</h2>

      <SpeakerLegend />

      <Waveform audioUrl={mixtureUrl} segments={segments} />

      <Timeline segments={segments} />

      <h3 style={{ marginTop: "20px" }}>Transcript Segments</h3>
      {segments.map((seg, idx) => (
        <div key={idx} className="card">
          <SegmentCard seg={seg} />
        </div>
      ))}

      <h3>Target Speaker Audio</h3>
      <audio controls src={targetUrl} style={{ width: "100%" }} />

      <div style={{ marginTop: "20px" }}>
        <a className="button" href={`http://localhost:8000/audio/${jobId}_diarization.json`} download>
          📥 Download JSON
        </a>
        <a className="button" style={{ marginLeft: "10px" }} href={targetUrl} download>
          🎧 Download Target Audio
        </a>
      </div>
    </div>
  );
}
