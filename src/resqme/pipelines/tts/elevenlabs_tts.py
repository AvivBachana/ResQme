# elevenlabs_tts.py
"""
ElevenLabsTTS wrapper class.
- Minimal dependency path: does not require pydub for basic TTS.
- Optional SFX mixing via pydub when available.
"""

from __future__ import annotations
# --- load .env if present (makes local runs painless) ---

try:
    from dotenv import load_dotenv
    load_dotenv()  # looks in CWD/parents (ResQme/.env when running CLI from project root)
except Exception:
    pass
# --------------------------------------------------------
from pathlib import Path

import os
import io
import random
from pathlib import Path
from typing import List, Optional

import requests
import pandas as pd

# pydub is optional; only needed for mixing or format conversion
try:
    from pydub import AudioSegment  # type: ignore
    _HAS_PYDUB = True
except Exception:
    _HAS_PYDUB = False


class ElevenLabsTTS:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.elevenlabs.io/v1"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
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
                f"ElevenLabs returned 401 Unauthorized. API key missing/invalid. "
                f"Key suffix seen: {tail}. "
                f"Fix: rotate key, export ELEVENLABS_API_KEY, or use .env."
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
        model_id: str = "eleven_monolingual_v1",
        stability: float = 0.3,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        speaker_boost: bool = True,
        mp3_bitrate: str = "192k",
    ) -> str:
        """Generate TTS and save raw MP3 bytes to file, avoiding pydub."""
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "use_speaker_boost": speaker_boost,
            },
        }
        r = requests.post(url, headers=self._headers(accept="audio/mpeg"), json=payload, stream=True)
        r.raise_for_status()

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return output_path

    # -------- Batch from CSV --------
    def synthesize_csv(
        self,
        csv_path: str,
        output_dir: str,
        fixed_voice_id: Optional[str] = None,
        text_col: str = "text",
        id_col: str = "id",
        random_voice: bool = False,
    ) -> pd.DataFrame:
        """Batch synthesize. If random_voice=True, sample a voice per row."""
        df = pd.read_csv(csv_path)
        if random_voice:
            voices = self.list_voices()
            pool = voices["voice_id"].dropna().tolist()
            if not pool:
                raise RuntimeError("No voices available to sample from")
        else:
            pool = []

        outputs = []
        for _, row in df.iterrows():
            row_id = str(row[id_col])
            text = str(row[text_col])
            voice_id = fixed_voice_id or (random.choice(pool) if random_voice else None)
            if not voice_id:
                raise ValueError("voice_id must be provided (fixed or random).")
            out_path = str(Path(output_dir) / f"{row_id}.mp3")
            self.synthesize_text(text=text, voice_id=voice_id, output_path=out_path)
            outputs.append({"id": row_id, "voice_id": voice_id, "path": out_path})

        out_df = pd.DataFrame(outputs)
        return out_df

    # -------- Optional: mix speech with SFX (requires pydub + audio backend) --------
    def mix_with_sfx(
        self,
        speech_mp3_path: str,
        sfx_wav_path: str,
        output_path: str,
        sfx_gain_db: float = -12.0,
    ) -> str:
        if not _HAS_PYDUB:
            raise RuntimeError("pydub not available. Install pydub and ensure ffmpeg is installed.")

        speech_bytes = Path(speech_mp3_path).read_bytes()
        sfx_bytes = Path(sfx_wav_path).read_bytes()

        speech = AudioSegment.from_file(io.BytesIO(speech_bytes), format="mp3")
        sfx = AudioSegment.from_file(io.BytesIO(sfx_bytes), format="wav")
        sfx = sfx + sfx_gain_db

        if len(sfx) < len(speech):
            loops = (len(speech) // len(sfx)) + 1
            sfx = sfx * loops
        sfx = sfx[: len(speech)]

        mixed = speech.overlay(sfx)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        mixed.export(output_path, format="mp3", bitrate="192k")
        return output_path
