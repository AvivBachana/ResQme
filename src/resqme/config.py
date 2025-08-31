import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Paths:
    raw_csv: str = os.getenv("SYMPTOM_CSV", "src/resqme/data/raw/symptom_matrix_english_v2.csv")
    outputs_root: str = "outputs"
    out_monologues: str = "outputs/monologues"
    out_audio: str = "outputs/audio"
    out_audio_noisy: str = "outputs/audio_noisy"
