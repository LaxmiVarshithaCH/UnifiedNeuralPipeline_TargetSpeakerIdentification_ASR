export default function SegmentCard({ seg }) {
  return (
    <div className="card">
      <strong>{seg.speaker}</strong><br/>
      {seg.start.toFixed(2)}s → {seg.end.toFixed(2)}s<br/><br/>
      <em>{seg.text}</em><br/>
      <small>Confidence: {(seg.confidence * 100).toFixed(1)}%</small>
    </div>
  );
}
