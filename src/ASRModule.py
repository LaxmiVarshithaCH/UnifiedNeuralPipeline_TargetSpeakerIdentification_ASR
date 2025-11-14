import whisper
import numpy as np
import tempfile
import soundfile as sf
import librosa
import torch

class ASRModule:
    def __init__(self, model_size: str = "small"):
     
        if torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"

        try:
            self.model = whisper.load_model(model_size, device="cpu")
            self.use_whisper = True
        except Exception as e:
            print("[WARN] Whisper load failed:", e)
            self.use_whisper = False
            self.model = None

    def transcribe(self, audio_np: np.ndarray, sr: int = 16000):
        if audio_np is None or len(audio_np) == 0:
            return {"text": "", "confidence": 0.0}

        audio = audio_np.astype(np.float32)

        max_val = np.max(np.abs(audio)) + 1e-9
        if max_val > 1:
            audio = audio / max_val

        if sr != 16000:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        sf.write(tmp.name, audio, 16000)

        if self.use_whisper:
            res = self.model.transcribe(
                tmp.name,
                language="en",
                fp16=False
            )

            text = res.get("text", "").strip()
            avg_logprob = res.get("avg_logprob", None)
            conf = float(np.exp(avg_logprob)) if avg_logprob is not None else 0.5

            return {
                "text": text,
                "confidence": conf
            }

        return {"text": "", "confidence": 0.0}
