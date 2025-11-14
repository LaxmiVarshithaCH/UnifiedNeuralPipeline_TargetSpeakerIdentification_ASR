import numpy as np
import noisereduce as nr
from utils import SAMPLE_RATE, save_audio

def denoise_audio(wav: np.ndarray, sr: int = SAMPLE_RATE) -> np.ndarray:

    try:
        reduced = nr.reduce_noise(y=wav, sr=sr)
        return reduced
    except Exception as e:

        print("Denoise failed:", e)
        return wav
