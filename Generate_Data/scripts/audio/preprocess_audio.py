import os, glob
from ResQme.src.resqme.pipelines.audio.audio_preprocess import to_wav

IN_DIR = "outputs/audio"                      # input: TTS outputs
OUT_DIR = "src/resqme/data/processed/audio"  # output: model-ready WAVs

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    files = []
    files += glob.glob(os.path.join(IN_DIR, "*.mp3"))
    files += glob.glob(os.path.join(IN_DIR, "*.wav"))
    for path in files:
        base = os.path.splitext(os.path.basename(path))[0]
        out = os.path.join(OUT_DIR, f"{base}.wav")
        out = to_wav(path, out_path=out, target_sr=16000, mono=True, normalize=True)
        print("WAV saved:", out)
