import os
from typing import List, Dict, Optional

import numpy as np

try:
    from pyannote.audio import Pipeline
    PYANNOTE_AVAILABLE = True
except Exception:
    PYANNOTE_AVAILABLE = False


class ProfessionalDiarizer:
    def __init__(self, hf_token: Optional[str] = None,
                 min_segment_dur: float = 0.4,
                 merge_gap: float = 0.25):

        self.hf_token = hf_token or os.environ.get("HUGGINGFACE_HUB_TOKEN")
        self.min_segment_dur = min_segment_dur
        self.merge_gap = merge_gap

        self.pipeline = None

        if PYANNOTE_AVAILABLE:
            try:

                self.pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=self.hf_token
                )
                print("Loaded pyannote 3.1 diarization.")
            except Exception as e:
                print("❌ Failed to load pyannote pipeline:", e)
                self.pipeline = None
        else:
            print("❌ pyannote not installed.")

    def _annotation_to_segments(self, annotation) -> List[Dict]:
        raw = []
        for turn, _, speaker in annotation.itertracks(yield_label=True):
            raw.append({
                "speaker": speaker,
                "start": float(turn.start),
                "end": float(turn.end),
            })

        if not raw:
            return []

        raw.sort(key=lambda x: x["start"])

        merged = []
        curr = raw[0].copy()

        for seg in raw[1:]:
            if seg["speaker"] == curr["speaker"] and seg["start"] - curr["end"] <= self.merge_gap:
                curr["end"] = seg["end"]
            else:
                merged.append(curr)
                curr = seg.copy()

        merged.append(curr)
        merged = [s for s in merged if (s["end"] - s["start"]) >= self.min_segment_dur]

        unique_speakers = sorted({s["speaker"] for s in merged})
        mapping = {spk: f"Speaker_{i}" for i, spk in enumerate(unique_speakers)}

        for s in merged:
            s["speaker"] = mapping[s["speaker"]]

        return merged

    def diarize(self, audio_path: str) -> List[Dict]:
        if self.pipeline is None:
            raise RuntimeError("pyannote diarization pipeline not loaded.")

        print("🔊 Running pyannote diarization...")
        annotation = self.pipeline(audio_path)
        segments = self._annotation_to_segments(annotation)
        return segments
