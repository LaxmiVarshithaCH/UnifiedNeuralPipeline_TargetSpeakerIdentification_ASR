import argparse
import json
import os
import tempfile
from typing import Dict, List
import numpy as np
from utils import load_audio, save_audio, ensure_dir, SAMPLE_RATE
from SeparationModule import SeparationModule
from SpeakerEmbedding import SpeakerEmbedder
from ProfessionalDiarizer import ProfessionalDiarizer
from ASRModule import ASRModule
from PunctuateModule import PunctuateModule


SIM_THRESHOLD = 0.85      
SIM_THRESHOLD_STRONG = 0.88
MIN_SEGMENT_DUR = 0.35    
MERGE_TINY_INT = 0.6       
ASR_LANGUAGE = "en"        
ASR_FP16 = False           
CONF_ASR_WEIGHT = 0.6      
CONF_SIM_WEIGHT = 0.4      

def separate_chunk_and_get_target(separator: SeparationModule, chunk: np.ndarray, sr: int):

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_path = tmp.name
    tmp.close()
    try:
        # Save chunk using utils.save_audio (keeps format consistent)
        save_audio(tmp_path, chunk, sr=sr)
        # enhancer.enhance_file returns numpy array or torch tensor; coerce to numpy
        enhanced = separator.enhancer.enhance_file(tmp_path)
        if hasattr(enhanced, "cpu"):
            enhanced = enhanced.squeeze().cpu().numpy()
        # ensure float32 numpy 1D
        enhanced = np.asarray(enhanced, dtype=np.float32).squeeze()
        return enhanced
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def smooth_and_merge_segments(segments: List[Dict], merge_tiny_int: float = MERGE_TINY_INT, min_dur: float = MIN_SEGMENT_DUR):

    if not segments:
        return []

    segments_sorted = sorted(segments, key=lambda s: s["start"])
    merged = []
    i = 0
    while i < len(segments_sorted):
        cur = dict(segments_sorted[i])
        if i + 2 < len(segments_sorted):
            mid = segments_sorted[i + 1]
            nxt = segments_sorted[i + 2]
            mid_dur = mid["end"] - mid["start"]
            if mid_dur < merge_tiny_int and cur["speaker"] == nxt["speaker"]:
                cur["end"] = nxt["end"]
                i += 3
                merged.append(cur)
                continue
        merged.append(cur)
        i += 1

    filtered = []
    for seg in merged:
        if (seg["end"] - seg["start"]) >= min_dur:
            filtered.append(seg)
    return filtered


def map_pyannote_speakers_to_target(diarization_segments: List[Dict], embedder: SpeakerEmbedder, target_emb: np.ndarray, mixture_full: np.ndarray, sr: int):

    speaker_audio = {}
    for seg in diarization_segments:
        sp = seg["speaker"]
        s = int(seg["start"] * sr); e = int(seg["end"] * sr)
        if e <= s:
            continue
        fragment = mixture_full[s:e]
        if fragment.size == 0:
            continue
        speaker_audio.setdefault(sp, []).append(fragment)

    speaker_centroids = {}
    for spk, parts in speaker_audio.items():
        try:
            concat = np.concatenate(parts, axis=0)
        except ValueError:
            continue
        if concat.size == 0:
            continue
        emb = embedder.embed_from_audio(concat, sr)
        speaker_centroids[spk] = emb

    sim_scores = {}
    for spk, emb in speaker_centroids.items():
        sim_scores[spk] = embedder.cosine_similarity(emb, target_emb)

    mapped_to_target = set()
    if sim_scores:
        SIM_THRESHOLD = dynamic_threshold(sim_scores)
        best_spk = max(sim_scores, key=sim_scores.get)
        if sim_scores[best_spk] >= SIM_THRESHOLD:
            mapped_to_target.add(best_spk)
        for spk, sim in sim_scores.items():
            if sim >= SIM_THRESHOLD_STRONG:
                mapped_to_target.add(spk)

    return mapped_to_target, sim_scores


def normalize_sim(sim_value: float) -> float:

    if sim_value is None:
        return 0.0
    if sim_value < -1.0:
        sim_value = -1.0
    if sim_value > 1.0:
        sim_value = 1.0
    return float((sim_value + 1.0) / 2.0)

def dynamic_threshold(sim_scores: dict, base_low=0.75, base_high=0.90):

    values = list(sim_scores.values())
    if len(values) <= 1:
        return 0.82

    sorted_vals = sorted(values, reverse=True)
    target_sim = sorted_vals[0]
    non_target = sorted_vals[1:]

    mean_nt = np.mean(non_target)
    std_nt = np.std(non_target)

    thr = mean_nt + 2 * std_nt

    thr = max(base_low, min(base_high, thr))
    print(f"[Dynamic Threshold] mean={mean_nt:.3f} std={std_nt:.3f} → thr={thr:.3f}")
    return thr

def run_offline(mixture_path: str, target_sample_path: str, out_json_path: str, out_target_wav: str, sim_threshold: float = SIM_THRESHOLD):

    ensure_dir(os.path.dirname(out_json_path) or ".")

    embedder = SpeakerEmbedder()
    target_wav, sr = load_audio(target_sample_path)
    target_emb = embedder.embed_from_audio(target_wav, sr)

    separator = SeparationModule()
    sep_res = separator.separate_and_select_target(mixture_path, target_emb)
    target_audio = sep_res["target_audio"]
    save_audio(out_target_wav, target_audio, sr=sep_res.get("sr", SAMPLE_RATE))

    diarizer = ProfessionalDiarizer(hf_token=os.environ.get("HUGGINGFACE_HUB_TOKEN"))
    diarization_segments = diarizer.diarize(mixture_path)
    if not diarization_segments:
        print("No diarization segments produced — aborting.")
        return

    diarization_segments = smooth_and_merge_segments(diarization_segments, merge_tiny_int=MERGE_TINY_INT, min_dur=MIN_SEGMENT_DUR)
    print(f"[INFO] {len(diarization_segments)} segments after smoothing")

    mixture_full, sr = load_audio(mixture_path)
    mapped_to_target, sim_scores = map_pyannote_speakers_to_target(diarization_segments, embedder, target_emb, mixture_full, sr)
    print("Per-speaker similarity to target (centroid):", sim_scores)
    print("Mapped pyannote speakers -> Target set:", mapped_to_target)

    asr = ASRModule()
    punct = PunctuateModule()

    non_target_speakers = sorted({seg["speaker"] for seg in diarization_segments if seg["speaker"] not in mapped_to_target})
    speaker_name_map = {sp: f"Speaker_{i}" for i, sp in enumerate(non_target_speakers)}

    results = []
    for seg in diarization_segments:
        sp = seg["speaker"]

        label = "Target" if seg["speaker"] in mapped_to_target else seg["speaker"]
        s = int(seg["start"] * sr); e = int(seg["end"] * sr)
        if e <= s:
            continue
        raw_chunk = mixture_full[s:e]

        try:
            if label == "Target":
                seg_audio = separate_chunk_and_get_target(separator, raw_chunk, sr)
            else:

                seg_audio = raw_chunk
        except Exception as ex:
            print(f"[WARN] per-segment separation failed for segment {seg}: {ex}")
            seg_audio = raw_chunk

        try:
            asr_out = asr.transcribe(seg_audio, sr=sr)
        except Exception as e:
            print(f"[WARN] ASR failed on segment {seg} with error {e}, using empty transcript.")
            asr_out = {"text": "", "confidence": 0.0}

        text = asr_out.get("text", "").strip()
        asr_conf = float(asr_out.get("confidence", 0.5))

        seg_spk_sim = sim_scores.get(sp, None)
        seg_sim_norm = normalize_sim(seg_spk_sim) 

        confidence = float(CONF_ASR_WEIGHT * asr_conf + CONF_SIM_WEIGHT * seg_sim_norm)

        text = punct.restore(text)

        results.append({
            "speaker": label,
            "start": float(seg["start"]),
            "end": float(seg["end"]),
            "text": text,
            "confidence": confidence
        })

    final = []
    for seg in results:
        if not final:
            final.append(seg)
            continue
        last = final[-1]
        if seg["speaker"] == last["speaker"] and abs(seg["start"] - last["end"]) <= 0.5:
            last["end"] = seg["end"]
         
            if last["text"] and seg["text"]:
                last["text"] = last["text"].rstrip() + " " + seg["text"].lstrip()
            elif seg["text"]:
                last["text"] = seg["text"]
           
            last["confidence"] = float((last["confidence"] + seg["confidence"]) / 2.0)
        else:
            final.append(seg)

    with open(out_json_path, "w") as f:
        json.dump(final, f, indent=2)

    print("Saved JSON:", out_json_path)
    print("Saved isolated target audio:", out_target_wav)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="main.py")
    parser.add_argument("--mixture", default="../audio/mixture_long.wav", help="Mixture audio path")
    parser.add_argument("--target", default="../audio/speaker_A.wav", help="Target sample path")
    parser.add_argument("--out_json", default="../audio/diarization.json", help="Output JSON path")
    parser.add_argument("--out_wav", default="../audio/target_speaker.wav", help="Output isolated WAV path")
    args = parser.parse_args()
    run_offline(args.mixture, args.target, args.out_json, args.out_wav)
