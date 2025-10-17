from pathlib import Path
from resqme.pipelines.tts.elevenlabs_tts import ElevenLabsTTS

# Resolve project roots safely based on this file location
THIS_FILE = Path(__file__).resolve()

# If this runner lives in ResQme/scripts/, parents[1] == ResQme
# If it lives in ResQme/scripts/tts/, parents[2] == ResQme
CANDIDATE_ROOTS = [THIS_FILE.parents[1], THIS_FILE.parents[2], THIS_FILE.parents[3]]
RESQME_ROOT = next((p for p in CANDIDATE_ROOTS if (p / "src" / "resqme").exists()), None)
if RESQME_ROOT is None:
    raise RuntimeError("Could not locate project root containing src/resqme")

# Build an absolute path to your CSV inside the repo
CSV_PATH = (RESQME_ROOT / "src" / "resqme" / "data" / "processed" / "generated_gpt_calls.csv").resolve()
if not CSV_PATH.exists():
    raise FileNotFoundError(f"CSV not found at: {CSV_PATH}")

OUT_DIR = (RESQME_ROOT / "out" / "tts").resolve()
OUT_DIR.mkdir(parents=True, exist_ok=True)

def main():
    tts = ElevenLabsTTS()
    out_df = tts.synthesize_csv(
        csv_path=str(CSV_PATH),
        output_dir=str(OUT_DIR),
        fixed_voice_id=None,       # supply a specific voice_id, or set random_voice=True below
        text_col=None,             # auto-detects [text, monologue, prompt, content]
        id_col="id",
        random_voice=True,         # <- random voice per row
        model_id="eleven_multilingual_v3",
        output_format="mp3_44100_128",
        stability=0.3,
        similarity_boost=0.75,
        style=0.0,
        speaker_boost=True,
        sleep_sec=0.6,
    )
    print(out_df.to_string(index=False))
    print(f"\nSaved to: {OUT_DIR}")

if __name__ == "__main__":
    main()
