import { useState, useEffect } from "react";

export default function AudioPlayer({ audioBuffer, start, end }) {
  const [playing, setPlaying] = useState(false);

  const playSegment = async () => {
    if (!audioBuffer) return;

    const audioCtx = new AudioContext();
    const source = audioCtx.createBufferSource();

    source.buffer = audioBuffer;

    const segment = audioBuffer.getChannelData(0).slice(
      Math.floor(start * audioBuffer.sampleRate),
      Math.floor(end * audioBuffer.sampleRate)
    );

    const segmentBuffer = audioCtx.createBuffer(
      1,
      segment.length,
      audioBuffer.sampleRate
    );

    segmentBuffer.getChannelData(0).set(segment);
    source.buffer = segmentBuffer;

    source.connect(audioCtx.destination);
    source.start();
    setPlaying(true);

    source.onended = () => {
      setPlaying(false);
      audioCtx.close();
    };
  };

  return (
    <button className="button" onClick={playSegment}>
      {playing ? "Playing..." : "▶ Play Segment"}
    </button>
  );
}
