# ElevenLabsTTS.py
"""
ElevenLabsTTS wrapper class.
- No pydub required for core TTS (optional mixing only via pydub if available).
- Loads .env automatically if present.
- Strips whitespace from API key to avoid 401 due to hidden characters.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, List

# Optional .env support
try:
    from dotenv import load_dotenv  # pip install python-dotenv
    load_dotenv()
except Exception:
    pass

import requests
import pandas as pd

# pydub is optional; only needed for overlay if you want it here
try:
    from pydub import AudioSegment  # type: ignore
    _HAS_PYDUB = True
except Exception:
    _HAS_PYDUB = False


class ElevenLabsTTS:
    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self, api_key: Optional[str] = None, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.api_key = (api_key or os.getenv("ELEVENLABS_API_KEY") or "").strip()
        if not self.api_key:
            raise RuntimeError("Missing ELEVENLABS_API_KEY")

    def _headers(self, accept: str = "application/json") -> dict:
        return {
            "xi-api-key": self.api_key,
            "accept": accept,
            "content-type": "application/json",
        }

    # -------- Voices --------
    def list_voices(self, save_csv: Optional[str] = None) -> pd.DataFrame:
        url = f"{self.base_url}/voices"
        r = requests.get(url, headers=self._headers())
        if r.status_code == 401:
            tail = (self.api_key[-6:] if self.api_key else "None")
            raise RuntimeError(
                f"ElevenLabs 401 Unauthorized. Check ELEVENLABS_API_KEY (suffix {tail}). "
                f"Fix: rotate key, remove hidden whitespace, ensure env is loaded."
            )
        r.raise_for_status()
        data = r.json().get("voices", [])
        df = pd.DataFrame(data)
        if save_csv:
            Path(save_csv).parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(save_csv, index=False)
        return df

    # -------- Core TTS (no pydub required) --------
    def synthesize_text(
        self,
        text: str,
        voice_id: str,
        output_path: str,
        model_id: str = "eleven_v3",
        stability: float = 0.30,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        speaker_boost: bool = True,
        output_format: str = "mp3_44100_128",
        enable_ssml: bool = False,
    ) -> str:
        """
        Calls ElevenLabs TTS REST API and writes an audio file to output_path.
        output_format follows ElevenLabs presets, e.g., mp3_44100_128, pcm_16000, etc.
        """
        # If the text has v3-style bracket tags and model isn't v3, upgrade model
        if "[" in text and "]" in text and "v3" not in model_id:
            print("ℹ Detected bracket-style tags; switching model to 'eleven_v3'.")
            model_id = "eleven_v3"

        url = f"{self.base_url}/text-to-speech/{voice_id}"
        payload = {
            "text": text if not enable_ssml else f"<speak>{text}</speak>",
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "use_speaker_boost": speaker_boost,
            },
            "output_format": output_format,
            "enable_ssml": bool(enable_ssml),
        }
        r = requests.post(url, headers=self._headers(accept="audio/mpeg"), json=payload, stream=True, timeout=120)
        if r.status_code == 401:
            tail = (self.api_key[-6:] if self.api_key else "None")
            raise RuntimeError(f"ElevenLabs 401 Unauthorized during synthesis. Key suffix {tail}.")
        if r.status_code != 200:
            # Try to surface server message
            try:
                detail = r.json()
            except Exception:
                detail = r.text
            raise RuntimeError(f"TTS failed ({r.status_code}). Detail: {detail}")

        outp = Path(output_path)
        outp.parent.mkdir(parents=True, exist_ok=True)
        with open(outp, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return str(outp.resolve())

    # -------- Batch from CSV --------
    def synthesize_csv(
        self,
        csv_path: str,
        output_dir: str,
        fixed_voice_id: Optional[str] = None,
        text_col: Optional[str] = None,
        id_col: str = "id",
        random_voice: bool = False,
        model_id: str = "eleven_v3",
        output_format: str = "mp3_44100_128",
        stability: float = 0.30,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        speaker_boost: bool = True,
        sleep_sec: float = 0.6,
    ) -> pd.DataFrame:
        """
        Reads a CSV and generates one clip per row.
        - If text_col is None, tries ['text','monologue','prompt','content'].
        - If id_col missing, creates 'utt_XXXX'.
        """
        df = pd.read_csv(csv_path)
        # Infer text column if needed
        if text_col is None:
            for c in ["text", "monologue", "prompt", "content","generated_call"]:
                if c in df.columns:
                    text_col = c
                    break
        if not text_col or text_col not in df.columns:
            raise ValueError(f"Could not find text column. Available: {list(df.columns)}. Provide text_col.")

        if id_col not in df.columns:
            df[id_col] = [f"utt_{i:04d}" for i in range(len(df))]

        # Voice pool if random is requested
        pool: List[str] = []
        if random_voice:
            voices = self.list_voices()
            pool = voices["voice_id"].dropna().astype(str).tolist()
            if not pool:
                raise RuntimeError("No voices available to sample from")

        out_dir = Path(output_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        rows = []
        import time, random
        for _, row in df.iterrows():
            row_id = str(row[id_col])
            text = str(row[text_col]).strip()
            if not text:
                print(f"[warn] Empty text for id={row_id}, skipping.")
                continue

            voice_id = fixed_voice_id or (random.choice(pool) if random_voice else None)
            if not voice_id:
                raise ValueError("voice_id must be provided (fixed or random).")

            out_path = out_dir / f"{row_id}.mp3"
            try:
                saved = self.synthesize_text(
                    text=text,
                    voice_id=voice_id,
                    output_path=str(out_path),
                    model_id=model_id,
                    stability=stability,
                    similarity_boost=similarity_boost,
                    style=style,
                    speaker_boost=speaker_boost,
                    output_format=output_format,
                )
                print(f"[ok] {row_id} -> {saved}")
                rows.append({"id": row_id, "voice_id": voice_id, "path": saved})
            except Exception as e:
                print(f"[error] id={row_id}: {e}")
            time.sleep(sleep_sec)

        return pd.DataFrame(rows)

    # -------- Optional: mix with SFX using pydub (not required) --------
    def mix_with_sfx(
        self,
        speech_mp3_path: str,
        sfx_wav_path: str,
        output_path: str,
        sfx_gain_db: float = -12.0,
    ) -> str:
        if not _HAS_PYDUB:
            raise RuntimeError("pydub not available. Install pydub and ensure ffmpeg is installed.")
        speech = AudioSegment.from_file(speech_mp3_path, format="mp3")
        sfx = AudioSegment.from_file(sfx_wav_path) + sfx_gain_db
        if len(sfx) < len(speech):
            loops = (len(speech) // len(sfx)) + 1
            sfx = sfx * loops
        sfx = sfx[: len(speech)]
        mixed = speech.overlay(sfx)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        mixed.export(output_path, format="mp3", bitrate="192k")
        return str(Path(output_path).resolve())
