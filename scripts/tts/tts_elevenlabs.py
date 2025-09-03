# tts_elevenlabs.py

#!/usr/bin/env python3
"""
CLI for ElevenLabs TTS with sensible defaults.

Defaults added:
- If no subcommand is provided, default to 'list'.
- If no local 'voices' directory exists, skip any "voice creation" flow and use an existing
  ElevenLabs voice from the account (the first available voice_id).
- If neither --voice-id nor --random-voice is given, auto-pick an existing voice_id.

Project layout (relevant parts):
ResQme/
├── scripts/
│   └── tts/
│       └── tts_elevenlabs.py   <-- this file
└── src/
    └── resqme/
        └── pipelines/
            └── tts/
                └── elevenlabs_tts.py  <-- the class implementation
"""

# --- import & path bootstrap (correct) ---
from __future__ import annotations
import argparse, sys, traceback, os
from pathlib import Path


THIS_FILE = Path(__file__).resolve()
RESQME_ROOT = THIS_FILE.parents[2]          # .../ResQme
SRC_DIR = RESQME_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    # Correct, lower-case package path
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
# -----------------------------------------

VOICES_DIR = RESQME_ROOT / "voices"  # local directory where custom voices might live (optional)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments. Subcommand is optional; default to 'list'."""
    parser = argparse.ArgumentParser(
        description="ElevenLabs TTS CLI (list voices, synthesize single text, or batch via CSV)"
    )
    sub = parser.add_subparsers(dest="cmd")  # not required; we will default to 'list'

    # List voices
    p_list = sub.add_parser("list", help="List voices available in your ElevenLabs account")
    p_list.add_argument("--save-csv", help="Optional path to save voices table as CSV")

    # Single synthesis
    p_single = sub.add_parser("single", help="Synthesize a single text to MP3")
    p_single.add_argument("--text", required=True, help="Text to synthesize")
    p_single.add_argument("--voice-id", help="ElevenLabs voice_id")
    p_single.add_argument("--out", required=True, help="Output MP3 path")
    p_single.add_argument("--model-id", default="eleven_monolingual_v1", help="Model id (default: eleven_monolingual_v1)")
    p_single.add_argument("--stability", type=float, default=0.3, help="Voice setting: stability (0-1)")
    p_single.add_argument("--similarity", type=float, default=0.75, help="Voice setting: similarity_boost (0-1)")
    p_single.add_argument("--style", type=float, default=0.0, help="Voice setting: style (0-1)")
    p_single.add_argument("--speaker-boost", action="store_true", help="Enable speaker boost")

    # Batch CSV
    p_csv = sub.add_parser("csv", help="Batch synthesize from CSV file")
    p_csv.add_argument("--csv", required=True, help="CSV input path with id/text columns")
    p_csv.add_argument("--outdir", required=True, help="Output directory for generated MP3 files")
    p_csv.add_argument("--voice-id", help="Fixed voice id for all rows (omit to use --random-voice or auto-pick)")
    p_csv.add_argument("--random-voice", action="store_true", help="Sample a random available voice per row")
    p_csv.add_argument("--text-col", default="text", help="Column name containing the text (default: text)")
    p_csv.add_argument("--id-col", default="id", help="Column name for the row identifier (default: id)")

    args = parser.parse_args()
    if not args.cmd:
        # Default subcommand when none was provided
        args.cmd = "list"
    return args


def _auto_pick_existing_voice(tts: ElevenLabsTTS) -> Optional[str]:
    """
    Pick an existing voice_id from the ElevenLabs account.
    Returns None if no voices are available.
    """
    try:
        df = tts.list_voices()
    except Exception as e:
        print(f"⚠ Failed to list voices from ElevenLabs: {e}")
        return None

    if "voice_id" in df.columns and not df["voice_id"].dropna().empty:
        # Prefer a deterministic pick: first by name sorted, else first row
        try:
            if "name" in df.columns:
                df_sorted = df.sort_values(by=["name", "voice_id"], na_position="last")
                return str(df_sorted.iloc[0]["voice_id"])
        except Exception:
            pass
        return str(df.iloc[0]["voice_id"])

    return None


def _resolve_voice_id(tts: ElevenLabsTTS, requested_voice_id: Optional[str], allow_random: bool) -> str:
    """
    Resolve voice_id according to the requested flags and environment:
    - If requested_voice_id is provided, use it.
    - Else if allow_random is True, we will rely on synthesize_csv(random_voice=True) path.
    - Else, if local VOICES_DIR is missing (meaning no local voice assets/workflow), auto-pick
      an existing ElevenLabs voice_id from the account and use that.
    - Else (VOICES_DIR exists), still auto-pick from account to avoid any "voice creation" flow.
    """
    if requested_voice_id:
        return requested_voice_id

    if allow_random:
        # Caller will handle random voice sampling inside synthesize_csv
        return ""

    # No requested voice id and no random-voice: pick an account voice
    if not VOICES_DIR.exists():
        print("ℹ No local 'voices' directory found; will use an existing ElevenLabs voice from your account.")
    else:
        print("ℹ Local 'voices' directory exists, but skipping any creation flow; using an existing account voice.")

    picked = _auto_pick_existing_voice(tts)
    if not picked:
        raise SystemExit("No existing voices found in your ElevenLabs account. Please create a voice or provide --voice-id.")
    print(f"✔ Using voice_id: {picked}")
    return picked


def cmd_list(tts: ElevenLabsTTS, save_csv: str | None) -> None:
    """List voices. Optionally save to CSV."""
    df = tts.list_voices(save_csv=save_csv)
    cols = [c for c in ["voice_id", "name", "category"] if c in df.columns]
    if cols:
        print(df[cols].to_string(index=False))
    else:
        print(df.to_string(index=False))


def cmd_single(tts: ElevenLabsTTS, args: argparse.Namespace) -> None:
    """Synthesize a single text to an MP3 file."""
    # Resolve voice_id with the new default behavior
    vid = _resolve_voice_id(tts, args.voice_id, allow_random=False)

    out_path = Path(args.out)
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
    )
    print(f"✔ Saved: {saved}")


def cmd_csv(tts: ElevenLabsTTS, args: argparse.Namespace) -> None:
    """Batch synthesize from CSV."""
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Resolve voice handling:
    # - If --random-voice: we let the pipeline sample per row.
    # - Else: resolve a fixed voice_id (auto-pick if none provided).
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
    )
    print(out_df.to_string(index=False))


def main() -> None:
    args = parse_args()
    try:
        tts = ElevenLabsTTS()
    except Exception as e:
        raise SystemExit(
            "Failed to initialize ElevenLabsTTS. Make sure ELEVENLABS_API_KEY is set in your environment."
        ) from e

    if args.cmd == "list":
        cmd_list(tts, getattr(args, "save_csv", None))
    elif args.cmd == "single":
        cmd_single(tts, args)
    elif args.cmd == "csv":
        cmd_csv(tts, args)
    else:
        # Should not happen, but keep a safe default
        cmd_list(tts, getattr(args, "save_csv", None))


if __name__ == "__main__":
    main()
