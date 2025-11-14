"""
SpeakerEmbedding: compute speaker embeddings (ECAPA / EncoderClassifier) using SpeechBrain.
Forced to CPU to avoid MPS issues.
"""
import numpy as np
import torch
from speechbrain.pretrained import EncoderClassifier
from utils import get_cpu_device, SAMPLE_RATE, load_audio

EMBEDDER_NAME = "speechbrain/spkrec-ecapa-voxceleb" 

class SpeakerEmbedder:
    def __init__(self, model_name=EMBEDDER_NAME):
        self.device = get_cpu_device()
       
        self.model = EncoderClassifier.from_hparams(source=model_name, savedir="pretrained_models/spkrec")

        try:
            self.model.to(self.device)
        except Exception:
            pass

    def embed_from_audio(self, wav_np: np.ndarray, sr: int = SAMPLE_RATE) -> np.ndarray:
        
        wav_np = wav_np.astype(np.float32)
       
        import torch
        wav_tensor = torch.tensor(wav_np).unsqueeze(0)
        wav_tensor = wav_tensor.to(self.device)
        with torch.no_grad():
            emb_tensor = self.model.encode_batch(wav_tensor)
        emb = emb_tensor.squeeze().cpu().numpy()
        emb = emb / (np.linalg.norm(emb) + 1e-9)
        return emb

    def embed_from_file(self, path: str):
        wav, sr = load_audio(path)
        return self.embed_from_audio(wav, sr)

    def cosine_similarity(self, e1: np.ndarray, e2: np.ndarray) -> float:
        return float(np.dot(e1, e2) / (np.linalg.norm(e1) * np.linalg.norm(e2) + 1e-9))
