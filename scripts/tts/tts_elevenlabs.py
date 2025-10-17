# tts_elevenlabs.py

#!/usr/bin/env python3
"""
CLI for ElevenLabs TTS with sensible defaults.

Key improvements:
- Default model: eleven_multilingual_v3 (real v3).
- Absolute output paths and clear prints for every saved file.
- CSV text column inference (text/monologue/prompt/content).
- Optional mixing with noise via ffmpeg (no pydub/audioop).
- Small sleep between requests to avoid rate limiting.
"""

from __future__ import annotations
import argparse
import os
import sys
import traceback
import subprocess
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
RESQME_ROOT = THIS_FILE.parents[2]          # .../ResQme
SRC_DIR = RESQME_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from resqme.pipelines.tts.elevenlabs_tts import ElevenLabsTTS
except Exception:
    print("↯ Import error while importing 'resqme.pipelines.tts.elevenlabs_tts':")
    traceback.print_exc()
    print("\nTrying local fallback 'elevenlabs_tts' next to this script...")
    try:
        from elevenlabs_tts import ElevenLabsTTS  # type: ignore
    except Exception:
        print("↯ Fallback import also failed:")
        traceback.print_exc()
        raise SystemExit(
            "Failed to import elevenlabs_tts. Ensure either:\n"
            "1) ResQme/src is on sys.path and src/resqme/pipelines/tts/elevenlabs_tts.py exists\n"
            "2) Or place elevenlabs_tts.py next to this CLI script."
        )

VOICES_DIR = RESQME_ROOT / "voices"  # optional local workspace for custom voices


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ElevenLabs TTS CLI (list voices, synthesize single text, or batch via CSV)"
    )
    sub = parser.add_subparsers(dest="cmd")

    # List
    p_list = sub.add_parser("list", help="List voices available in your ElevenLabs account")
    p_list.add_argument("--save-csv", help="Optional path to save voices table as CSV")

    # Single
    p_single = sub.add_parser("single", help="Synthesize a single text to MP3")
    p_single.add_argument("--text", required=True, help="Text to synthesize")
    p_single.add_argument("--out", required=True, help="Output MP3 path")
    p_single.add_argument("--voice-id", help="ElevenLabs voice_id")
    p_single.add_argument("--model-id", default="eleven_multilingual_v3", help="Model id (default: eleven_multilingual_v3)")
    p_single.add_argument("--stability", type=float, default=0.30)
    p_single.add_argument("--similarity", type=float, default=0.75)
    p_single.add_argument("--style", type=float, default=0.0)
    p_single.add_argument("--speaker-boost", action="store_true", help="Enable speaker boost")
    p_single.add_argument("--output-format", default="mp3_44100_128")

    # CSV
    p_csv = sub.add_parser("csv", help="Batch synthesize from CSV file")
    p_csv.add_argument("--csv", required=True, help="CSV input path (columns: id optional, and text/monologue/prompt/content)")
    p_csv.add_argument("--outdir", required=True, help="Output directory for generated MP3 files")
    p_csv.add_argument("--voice-id", help="Fixed voice id for all rows (omit to use --random-voice or auto-pick)")
    p_csv.add_argument("--random-voice", action="store_true", help="Sample a random available voice per row")
    p_csv.add_argument("--text-col", default=None, help="Explicit text column if not one of [text, monologue, prompt, content]")
    p_csv.add_argument("--id-col", default="id", help="Row identifier column (default: id)")
    p_csv.add_argument("--model-id", default="eleven_multilingual_v3")
    p_csv.add_argument("--stability", type=float, default=0.30)
    p_csv.add_argument("--similarity", type=float, default=0.75)
    p_csv.add_argument("--style", type=float, default=0.0)
    p_csv.add_argument("--speaker-boost", action="store_true")
    p_csv.add_argument("--output-format", default="mp3_44100_128")
    p_csv.add_argument("--sleep", type=float, default=0.6, help="Seconds between requests")

    # Optional noise mixing via ffmpeg
    p_csv.add_argument("--noise", default=None, help="Path to noise WAV/MP3 to mix (optional)")
    p_csv.add_argument("--noise-gain-db", type=float, default=-12.0, help="Noise gain in dB (negative is quieter)")

    args = parser.parse_args()
    if not args.cmd:
        args.cmd = "list"
    return args


def _auto_pick_existing_voice(tts: ElevenLabsTTS) -> str | None:
    try:
        df = tts.list_voices()
    except Exception as e:
        print(f"⚠ Failed to list voices from ElevenLabs: {e}")
        return None

    if "voice_id" in df.columns and not df["voice_id"].dropna().empty:
        try:
            if "name" in df.columns:
                df_sorted = df.sort_values(by=["name", "voice_id"], na_position="last")
                return str(df_sorted.iloc[0]["voice_id"])
        except Exception:
            pass
        return str(df.iloc[0]["voice_id"])
    return None


def _resolve_voice_id(tts: ElevenLabsTTS, requested_voice_id: str | None, allow_random: bool) -> str:
    if requested_voice_id:
        return requested_voice_id
    if allow_random:
        return ""
    if not VOICES_DIR.exists():
        print("ℹ No local 'voices' directory found; will use an existing ElevenLabs voice from your account.")
    else:
        print("ℹ Local 'voices' directory exists, but skipping any creation flow; using an existing account voice.")
    picked = _auto_pick_existing_voice(tts)
    if not picked:
        raise SystemExit("No existing voices found in your ElevenLabs account. Provide --voice-id or create a voice.")
    print(f"✔ Using voice_id: {picked}")
    return picked


def _mix_with_noise_ffmpeg(speech_path: Path, noise_path: Path, out_path: Path, noise_gain_db: float = -12.0) -> None:
    """
    Mix speech with noise using ffmpeg, avoiding pydub/audioop issues.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", str(speech_path),
        "-i", str(noise_path),
        "-filter_complex", f"[1:a]volume={noise_gain_db}dB[n];[0:a][n]amix=inputs=2:duration=longest",
        "-c:a", "mp3",
        str(out_path)
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg mix failed: {proc.stderr.decode('utf-8', errors='ignore')}")


def cmd_list(tts: ElevenLabsTTS, save_csv: str | None) -> None:
    df = tts.list_voices(save_csv=save_csv)
    cols = [c for c in ["voice_id", "name", "category"] if c in df.columns]
    if cols:
        print(df[cols].to_string(index=False))
    else:
        print(df.to_string(index=False))


def cmd_single(tts: ElevenLabsTTS, args: argparse.Namespace) -> None:
    vid = _resolve_voice_id(tts, args.voice_id, allow_random=False)
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    saved = tts.synthesize_text(
        text=args.text,
        voice_id=vid,
        output_path=str(out_path),
        model_id=args.model_id,
        stability=args.stability,
        similarity_boost=args.similarity,
        style=args.style,
        speaker_boost=bool(args.speaker_boost),
        output_format=args.output_format,
    )
    print(f"✔ Saved: {saved}")


def cmd_csv(tts: ElevenLabsTTS, args: argparse.Namespace) -> None:
    outdir = Path(args.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    fixed_voice_id = None
    if not args.random_voice:
        fixed_voice_id = _resolve_voice_id(tts, args.voice_id, allow_random=False)

    out_df = tts.synthesize_csv(
        csv_path=args.csv,
        output_dir=str(outdir),
        fixed_voice_id=fixed_voice_id,
        text_col=args.text_col,
        id_col=args.id_col,
        random_voice=bool(args.random_voice),
        model_id=args.model_id,
        output_format=args.output_format,
        stability=args.stability,
        similarity_boost=args.similarity,
        style=args.style,
        speaker_boost=bool(args.speaker_boost),
        sleep_sec=args.sleep,
    )

    # Optional mixing with noise
    if args.noise:
        noise = Path(args.noise).expanduser().resolve()
        if not noise.exists():
            raise SystemExit(f"Noise file not found: {noise}")
        print(f"ℹ Mixing noise from: {noise}")
        mixed_rows = []
        for _, r in out_df.iterrows():
            speech = Path(r["path"])
            mixed = speech.with_name(speech.stem + "_mix.mp3")
            try:
                _mix_with_noise_ffmpeg(speech, noise, mixed, noise_gain_db=args.noise_gain_db)
                print(f"[mix] {speech.name} + noise -> {mixed.name}")
                mixed_rows.append({"id": r["id"], "voice_id": r["voice_id"], "path": str(mixed.resolve())})
            except Exception as e:
                print(f"[mix-error] id={r['id']}: {e}")
        if mixed_rows:
            import pandas as pd
            out_df = pd.DataFrame(mixed_rows)

    # Final explicit print of absolute outdir and sample files
    print("\n=== OUTPUT DIRECTORY ===")
    print(str(outdir))
    print("========================")
    if not out_df.empty:
        print(out_df.to_string(index=False))


def main() -> None:
    args = parse_args()
    try:
        tts = ElevenLabsTTS()
    except Exception as e:
        raise SystemExit("Failed to initialize ElevenLabsTTS. Make sure ELEVENLABS_API_KEY is set.") from e

    if args.cmd == "list":
        cmd_list(tts, getattr(args, "save_csv", None))
    elif args.cmd == "single":
        cmd_single(tts, args)
    elif args.cmd == "csv":
        cmd_csv(tts, args)
    else:
        cmd_list(tts, getattr(args, "save_csv", None))


if __name__ == "__main__":
    main()
