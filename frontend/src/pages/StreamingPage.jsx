import { useState, useRef } from "react";

export default function StreamingPage() {
  const [text, setText] = useState("");
  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);

  const startStreaming = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    wsRef.current = new WebSocket("ws://localhost:8000/ws/stream");
    wsRef.current.onmessage = (msg) => {
      setText(prev => prev + "\n" + msg.data);
    };

    mediaRecorderRef.current = new MediaRecorder(stream, {
      mimeType: "audio/webm"
    });

    mediaRecorderRef.current.ondataavailable = (e) => {
      wsRef.current.send(e.data);
    };

    mediaRecorderRef.current.start(200); // send chunk every 200ms
  };

  const stopStreaming = () => {
    mediaRecorderRef.current.stop();
    wsRef.current.close();
  };

  return (
    <div className="container">
      <h2>Real-time Streaming ASR + Target Speaker Detection</h2>

      <button className="button" onClick={startStreaming}>🎤 Start</button>
      <button className="button" onClick={stopStreaming} style={{ marginLeft:"10px" }}>
        ⛔ Stop
      </button>

      <h3 style={{ marginTop:"20px" }}>Live Transcript</h3>
      <pre className="card" style={{ height:"200px", overflow:"auto" }}>
        {text}
      </pre>
    </div>
  );
}
