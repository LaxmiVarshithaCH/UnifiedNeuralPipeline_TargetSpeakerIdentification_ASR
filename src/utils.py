import os
import soundfile as sf
import numpy as np
import torch
import librosa
from typing import Tuple

SAMPLE_RATE = 16000
DEVICE_CPU = torch.device("cpu")

DEVICE_ASR = torch.device("mps") if (hasattr(torch.backends, "mps") and torch.backends.mps.is_available()) else torch.device("cpu")

def get_asr_device():
    return DEVICE_ASR

def get_cpu_device():
    return DEVICE_CPU

def load_audio(path: str, sr: int = SAMPLE_RATE) -> Tuple[np.ndarray, int]:

    wav, orig_sr = librosa.load(path, sr=sr, mono=True)
    if wav.dtype != np.float32:
        wav = wav.astype(np.float32)
    return wav, sr

def save_audio(path: str, audio: np.ndarray, sr: int = SAMPLE_RATE):

    audio = np.asarray(audio, dtype=np.float32)
    sf.write(path, audio, sr)

def ensure_dir(d: str):
    os.makedirs(d, exist_ok=True)
