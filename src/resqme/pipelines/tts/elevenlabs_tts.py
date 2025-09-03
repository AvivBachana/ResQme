# elevenlabs_tts.py
"""
ElevenLabsTTS wrapper class.
- Does not require pydub for basic TTS (optional mixing only).
- Loads .env automatically if present.
- Strips whitespace from API key to avoid 401 due to hidden characters.
"""

from __future__ import annotations
import os
import io
import random
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

# pydub is optional; only needed for mixing/overlay
try:
    from pydub import AudioSegment  # type: ignore
    _HAS_PYDUB = True
except Exception:
    _HAS_PYDUB = False


class ElevenLabsTTS:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.elevenlabs.io/v1"):
        self.base_url = base_url.rstrip("/")
        # Strip to remove accidental spaces/newlines
        self.api_key = (api_key or os.getenv("ELEVENLABS_API_KEY") or "").strip()
        # self.api_key= "sk_cf5e94e92a0dbaf78480c53f14f3a0c5cd0e2b911bcdfa13"
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
            model_id: str = "eleven_v3",  # default to v3 to support audio tags
            stability: float = 0.3,
            similarity_boost: float = 0.75,
            style: float = 0.0,
            speaker_boost: bool = True,
            mp3_bitrate: str = "192k",
            enable_ssml: bool = False,  # only for true SSML like <break/>, <prosody/>
    ) -> str:
        # Auto-upgrade to v3 if text contains bracket-tags and model isn't v3
        if "[" in text and "]" in text and "v3" not in model_id:
            print("ℹ Detected bracket-style audio tags; switching model to 'eleven_v3' for proper rendering.")
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
            # SSML is optional and different from v3 audio tags. Turn on only if you use <break/>, <prosody>, etc.
            "enable_ssml": bool(enable_ssml)
        }
        r = requests.post(url, headers=self._headers(accept="audio/mpeg"), json=payload, stream=True)

        if r.status_code == 401:
            tail = (self.api_key[-6:] if self.api_key else "None")
            raise RuntimeError(
                f"ElevenLabs 401 Unauthorized during synthesis. Key suffix {tail}."
            )
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
        df = pd.read_csv(csv_path)
        pool: List[str] = []
        if random_voice:
            voices = self.list_voices()
            pool = voices["voice_id"].dropna().astype(str).tolist()
            if not pool:
                raise RuntimeError("No voices available to sample from")

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

        return pd.DataFrame(outputs)

    # -------- Optional: mix speech with SFX (requires pydub) --------
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
        sfx = AudioSegment.from_file(sfx_wav_path, format="wav") + sfx_gain_db
        if len(sfx) < len(speech):
            loops = (len(speech) // len(sfx)) + 1
            sfx = sfx * loops
        sfx = sfx[: len(speech)]
        mixed = speech.overlay(sfx)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        mixed.export(output_path, format="mp3", bitrate="192k")
        return output_path
