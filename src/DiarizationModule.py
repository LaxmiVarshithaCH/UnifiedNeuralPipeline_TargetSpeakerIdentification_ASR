
from pyannote.audio import Pipeline
from typing import List, Dict
import numpy as np
from utils import SAMPLE_RATE
import torch

DIARIZATION_PIPELINE = "pyannote/speaker-diarization"

class DiarizationModule:
    def __init__(self, pipeline_name=DIARIZATION_PIPELINE):
        self.pipeline = Pipeline.from_pretrained(pipeline_name)

    def diarize(self, audio_path: str) -> List[Dict]:
        diarization = self.pipeline(audio_path)
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "speaker": speaker,
                "start": float(turn.start),
                "end": float(turn.end)
            })
        return segments

    def get_annotation(self, audio_path: str):
        return self.pipeline(audio_path)
