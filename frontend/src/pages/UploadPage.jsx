import { useState } from "react";
import { api } from "../api/api";
import FileInput from "../components/FileInput";

export default function UploadPage({ setResults }) {
  const [mix, setMix] = useState(null);
  const [target, setTarget] = useState(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (!mix || !target) {
      alert("Upload both mixture & target files!");
      return;
    }

    setLoading(true);

    const fd = new FormData();
    fd.append("mixture", mix);
    fd.append("target", target);

    try {
      const res = await api.post("/process", fd);
      setResults(res.data);  
    } catch (err) {
      alert("Processing failed.");
    }

    setLoading(false);
  };

  return (
    <div className="container">
      <h2>Offline Audio Processing</h2>

      <FileInput label="Upload Mixture Audio" onChange={setMix} />
      <FileInput label="Upload Target Speaker Sample" onChange={setTarget} />

      <button className="button" onClick={submit}>
        {loading ? "Processing..." : "Run Pipeline"}
      </button>
    </div>
  );
}
