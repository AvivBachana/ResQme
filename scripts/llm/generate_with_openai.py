# generate_monologues.py
# All comments are in English only.

from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import argparse
import csv
import os
import random
import time

import pandas as pd
from dotenv import load_dotenv

# Load .env (OPENAI_API_KEY, etc.) if present
load_dotenv()

try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # Checked at runtime


# ---------- Resolve project paths relative to this file ----------
HERE = Path(__file__).resolve()
# File is at: src/resqme/pipelines/llm/generate_monologues.py
RESQME_DIR = HERE.parents[2]              # .../src/resqme
DATA_DIR = RESQME_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "text"

DEFAULT_SYMPTOM_NAME = "disease_symptom_matrix.csv"
DEFAULT_SYMPTOM_CSV = RAW_DIR / DEFAULT_SYMPTOM_NAME
DEFAULT_OUT_CSV = PROCESSED_DIR / "generated_gpt_calls.csv"

# ---------- Prompt template ----------

PROMPT = (
    "You are writing text that will be fed directly to ElevenLabs TTS (Eleven v3 Audio Tags).\n\n"
    "TASK\n"
    "Write a short emergency-call monologue in English by a distressed civilian.\n\n"
    "CONTENT REQUIREMENTS\n"
    "- Naturally include and describe these symptoms without naming any disease: {symptom_list}\n"
    "- Only the caller’s words. No dispatcher. No headings, bullets, quotes, or explanations.\n\n"
    "STYLE & DELIVERY\n"
    "- Realistic, emotional speech under stress: hesitations, fillers (uh/um), repetitions, stutters (I— I…), ellipses (…) and em-dashes (—).\n"
    "- Vary vocabulary and intensity across samples. Avoid templatey phrasing.\n\n"
    "ELEVENLABS AUDIO TAGS (MANDATORY)\n"
    "- Use inline audio tags in square brackets to direct delivery and non-speech sounds (2–5 total), e.g.:\n"
    "  [sobbing], [crying], [gasping], [breathing heavily], [whispering], [shouting], [coughing], [wheezing], [sighs]\n"
    "- Optionally ONE environmental tag if relevant: e.g., [sirens in distance], [traffic noise], [wind].\n"
    "- Place tags inline with the words (no colons), e.g.: “I— I can’t— [gasping] he just fell…”\n"
    "- Do not invent new formatting beyond bracketed tags.\n\n"
    "LENGTH & FORM\n"
    "- 90–160 words total (about 8–20 seconds).\n"
    "- 1–2 short paragraphs; 1–3 sentences per paragraph.\n"
    "- ASCII punctuation only. No metadata, no speaker labels.\n\n"
    "OUTPUT\n"
    "- Output ONLY the monologue text itself.\n"
    "Now write the monologue."
)


@dataclass
class GenerationSpec:
    symptom_csv: str = str(DEFAULT_SYMPTOM_CSV)
    out_csv: str = str(DEFAULT_OUT_CSV)
    num_calls_per_disease: int = 10
    symptoms_per_call: int = 3
    max_diseases: Optional[int] = None
    seed: Optional[int] = 42
    model: str = "gpt-3.5-turbo"
    temperature: float = 1.0
    max_tokens: int = 500
    delay_seconds: float = 2.0
    max_retries: int = 3
    retry_backoff: float = 2.0
    verbose: bool = True


class MonologueGenerator:
    def __init__(self, symptom_df: pd.DataFrame, spec: GenerationSpec):
        self.symptom_df = symptom_df
        self.spec = spec
        self.client = None
        # Prepare output path once
        out_path = Path(self.spec.out_csv)
        if out_path.is_dir():
            out_path = out_path / "generated_gpt_calls.csv"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        self.out_path = out_path
        self.header = ["disease", "symptoms_used", "generated_call"]
        # Create header if file does not exist
        if not self.out_path.exists():
            with self.out_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.header)
                writer.writeheader()

    @classmethod
    def from_csv(cls, path: str, spec: GenerationSpec) -> "MonologueGenerator":
        """Create generator from a CSV file or a directory containing it."""
        csv_path = Path(path)
        if csv_path.is_dir():
            csv_path = csv_path / DEFAULT_SYMPTOM_NAME
        if not csv_path.exists():
            raise FileNotFoundError(
                f"Symptom CSV not found at: {csv_path}\n"
                f"Tip: pass --symptom-csv {RAW_DIR} (directory) or the full file path."
            )
        # Robust read: handle UTF-8 with or without BOM
        try:
            df = pd.read_csv(csv_path, index_col=0, encoding="utf-8-sig")
        except UnicodeDecodeError:
            df = pd.read_csv(csv_path, index_col=0)
        return cls(df, spec)

    def init_client(self) -> None:
        """Initialize OpenAI client; requires OPENAI_API_KEY env var."""
        if OpenAI is None:
            raise RuntimeError("openai package is not available in this environment.")
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
        self.client = OpenAI()

    def diseases(self) -> List[str]:
        """Return disease names. Optionally cap for quick tests."""
        diseases = list(self.symptom_df.index)
        if self.spec.max_diseases is not None:
            diseases = diseases[: self.spec.max_diseases]
        return diseases

    def _build_prompt(self, symptoms: List[str]) -> str:
        """Compose the user prompt for the chat model."""
        symptom_list = ", ".join(symptoms)
        return ( PROMPT )

    def _call_gpt(self, prompt: str) -> Optional[str]:
        """Call the chat model with retries and backoff."""
        assert self.client is not None, "Client must be initialized before calling GPT."
        last_err: Optional[Exception] = None
        delay = self.spec.delay_seconds

        for attempt in range(1, self.spec.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.spec.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.spec.temperature,
                    max_tokens=self.spec.max_tokens,
                )
                return response.choices[0].message.content
            except Exception as e:
                last_err = e
                if self.spec.verbose:
                    print(f"[warn] Attempt {attempt} failed: {e}")
                if attempt < self.spec.max_retries:
                    time.sleep(delay)
                    delay *= self.spec.retry_backoff

        if self.spec.verbose and last_err:
            print(f"[error] All retries failed: {last_err}")
        return None

    def _present_symptoms_for(self, disease: str) -> List[str]:
        """Return names of symptoms with truthy values for this disease row."""
        row = self.symptom_df.loc[disease]
        return row[row.astype(bool)].index.tolist()

    def _sample_symptoms(self, symptoms: List[str]) -> List[str]:
        """Sample up to symptoms_per_call symptoms without replacement."""
        k = min(self.spec.symptoms_per_call, len(symptoms))
        return random.sample(symptoms, k) if k > 0 else []

    def _append_row_immediately(self, record: Dict[str, Any]) -> None:
        """Append a single record immediately to the CSV (write-as-you-go)."""
        with self.out_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.header)
            writer.writerow(record)

    def generate_for_disease(self, disease: str) -> List[Dict[str, Any]]:
        """Generate N monologues for a given disease and append each row immediately."""
        present_symptoms = self._present_symptoms_for(disease)
        if not present_symptoms:
            return []

        outputs: List[Dict[str, Any]] = []
        for _ in range(self.spec.num_calls_per_disease):
            sampled = self._sample_symptoms(present_symptoms)
            if not sampled:
                continue
            prompt = self._build_prompt(sampled)
            result = self._call_gpt(prompt)
            if result:
                record = {
                    "disease": disease,
                    "symptoms_used": ", ".join(sampled),
                    "generated_call": result.strip(),
                }
                outputs.append(record)
                print( record )
                self._append_row_immediately(record)   # <-- immediate write
            time.sleep(self.spec.delay_seconds)
        return outputs

    def run_all(self) -> List[Dict[str, Any]]:
        """Run generation across all diseases."""
        if self.spec.seed is not None:
            random.seed(self.spec.seed)
        self.init_client()

        all_rows: List[Dict[str, Any]] = []
        for disease in self.diseases():
            if self.spec.verbose:
                print(f"\n[info] Generating for disease: {disease}")
            rows = self.generate_for_disease(disease)
            all_rows.extend(rows)

        if self.spec.verbose:
            print(f"\n[done] Wrote {len(all_rows)} rows to {self.out_path}")
        return all_rows


def parse_args() -> GenerationSpec:
    p = argparse.ArgumentParser(description="Generate emergency-call monologues from a symptom matrix CSV.")
    p.add_argument("--symptom-csv", default=str(DEFAULT_SYMPTOM_CSV),
                   help="Path to the symptom matrix CSV or a directory containing it.")
    p.add_argument("--out-csv", default=str(DEFAULT_OUT_CSV),
                   help="Path to the output CSV (or a directory to write into).")
    p.add_argument("--num-calls-per-disease", type=int, default=10)
    p.add_argument("--symptoms-per-call", type=int, default=3)
    p.add_argument("--max-diseases", type=int, default=None)
    p.add_argument("--seed", type=int, default=42,
                   help="Random seed for reproducibility. Use -1 to disable.")
    p.add_argument("--model", default="gpt-3.5-turbo")
    p.add_argument("--temperature", type=float, default=1.0)
    p.add_argument("--max-tokens", type=int, default=500)
    p.add_argument("--delay-seconds", type=float, default=2.0)
    p.add_argument("--max-retries", type=int, default=3)
    p.add_argument("--retry-backoff", type=float, default=2.0)
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    seed_val = None if args.seed == -1 else args.seed

    return GenerationSpec(
        symptom_csv=args.symptom_csv,
        out_csv=args.out_csv,
        num_calls_per_disease=args.num_calls_per_disease,
        symptoms_per_call=args.symptoms_per_call,
        max_diseases=args.max_diseases,
        seed=seed_val,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        delay_seconds=args.delay_seconds,
        max_retries=args.max_retries,
        retry_backoff=args.retry_backoff,
        verbose=not args.quiet,
    )


def main() -> None:
    spec = parse_args()
    gen = MonologueGenerator.from_csv(spec.symptom_csv, spec)
    gen.run_all()


if __name__ == "__main__":
    main()
