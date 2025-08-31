import os, glob
from src.resqme.pipelines.audio.audio_utils import add_white_noise

IN_DIR = "outputs/audio"
OUT_DIR = "outputs/audio_noisy"
SNR_DB = 15.0

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    for path in glob.glob(os.path.join(IN_DIR, "*.wav")) + glob.glob(os.path.join(IN_DIR, "*.mp3")):
        name = os.path.splitext(os.path.basename(path))[0]
        out = os.path.join(OUT_DIR, f"{name}_noisy.wav")
        add_white_noise(path, out, SNR_DB)
        print("Noisy saved:", out)
