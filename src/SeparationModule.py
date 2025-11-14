
import torch
import numpy as np
from speechbrain.pretrained import SpectralMaskEnhancement
from SpeakerEmbedding import SpeakerEmbedder
from utils import SAMPLE_RATE, load_audio, get_cpu_device, ensure_dir

MODEL_NAME = "speechbrain/metricgan-plus-voicebank"  
SAVE_DIR = "pretrained_models/metricgan"

class SeparationModule:
    def __init__(self, model_name=MODEL_NAME):
        ensure_dir(SAVE_DIR)
        self.device = get_cpu_device()
      
        self.enhancer = SpectralMaskEnhancement.from_hparams(
            source=model_name,
            savedir=SAVE_DIR,
            run_opts={"device": str(self.device)}
        )
        self.embedder = SpeakerEmbedder()

    def separate_and_select_target(self, mixture_path: str, target_embedding: np.ndarray):
        wav, sr = load_audio(mixture_path)

        try:
      
            enhanced = self.enhancer.enhance_file(mixture_path)
            if hasattr(enhanced, "cpu"):
                enhanced = enhanced.squeeze().cpu().numpy()
        except Exception as e:
      
            import torch
            wav_tensor = torch.tensor(wav).unsqueeze(0).to(self.device)
            lengths = torch.tensor([wav_tensor.shape[1]], dtype=torch.long)
            with torch.no_grad():
                enhanced_tensor = self.enhancer.enhance_batch(wav_tensor, lengths=lengths)
            enhanced = enhanced_tensor.squeeze().cpu().numpy()

      
        emb = self.embedder.embed_from_audio(enhanced, sr)
        sim = self.embedder.cosine_similarity(emb, target_embedding)
        return {
            "target_audio": enhanced,
            "best_idx": 0,
            "best_sim": float(sim),
            "sims": [float(sim)],
            "all_sources": [enhanced],
            "sr": sr
        }

