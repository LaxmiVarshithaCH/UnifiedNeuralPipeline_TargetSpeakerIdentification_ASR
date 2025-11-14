import webrtcvad
import numpy as np
import collections
import math
from SpeakerEmbedding import SpeakerEmbedder
from utils import SAMPLE_RATE, load_audio
from sklearn.cluster import AgglomerativeClustering

FRAME_MS = 30


def frame_generator(wav, sr=SAMPLE_RATE, frame_ms=FRAME_MS):
    n = int(sr * (frame_ms / 1000.0))
    total_frames = len(wav) // n     
    for i in range(total_frames):
        start = i * n
        end = start + n
        frame = wav[start:end]
        yield frame

def vad_segments(wav, sr=SAMPLE_RATE, aggressiveness=1):
    vad = webrtcvad.Vad(aggressiveness)
    frames = list(frame_generator(wav, sr))
    is_speech = []
    for f in frames:
        int16 = (f * 32767).astype(np.int16)
        frame_bytes = int16.tobytes()
        is_speech.append(vad.is_speech(frame_bytes, sample_rate=sr))
    segments = []
    start_frame = None
    for idx, speech in enumerate(is_speech):
        if speech and start_frame is None:
            start_frame = idx
        elif (not speech or idx == len(is_speech)-1) and start_frame is not None:
            end_frame = idx
            start_sec = start_frame * (FRAME_MS/1000.0)
            end_sec = (end_frame+1) * (FRAME_MS/1000.0)
            segments.append((start_sec, end_sec))
            start_frame = None
    return segments

def segment_embeddings(wav, sr, segments, embedder: SpeakerEmbedder):
    embs = []
    seg_times = []
    for s,e in segments:
        s_i = int(s*sr); e_i = int(e*sr)
        chunk = wav[s_i:e_i]
        if len(chunk) < 100: 
            continue
        emb = embedder.embed_from_audio(chunk, sr)
        embs.append(emb)
        seg_times.append((s,e))
    return np.vstack(embs) if embs else np.empty((0,512)), seg_times

def diarize(mixture_path: str, n_speakers: int = None):
    wav, sr = load_audio(mixture_path)
    segments = vad_segments(wav, sr)
    embedder = SpeakerEmbedder()
    embs, seg_times = segment_embeddings(wav, sr, segments, embedder)
    if embs.size == 0:
        return []
    if n_speakers is None:
        n_speakers = min(4, max(2, int(len(embs)/5)+1))
    clustering = AgglomerativeClustering(n_clusters=n_speakers).fit(embs)
    labels = clustering.labels_
    results = []
    for (s,e), lab in zip(seg_times, labels):
        results.append({"speaker": f"Speaker_{lab}", "start": float(s), "end": float(e)})
    return results