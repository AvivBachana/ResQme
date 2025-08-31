from dataclasses import dataclass
from typing import List, Iterable
import pandas as pd

@dataclass
class GenerationSpec:
    num_calls_per_disease: int = 1

class MonologueGenerator:
    def __init__(self, symptom_df: pd.DataFrame):
        self.symptom_df = symptom_df

    @classmethod
    def from_csv(cls, path: str) -> "MonologueGenerator":
        df = pd.read_csv(path, index_col=0)
        return cls(df)

    def diseases(self) -> List[str]:
        return list(self.symptom_df.index)[:3]  # small sample for tests

    def prompts_for(self, disease: str) -> Iterable[str]:
        yield f"Describe symptoms for triage. Disease to target: {disease}."
