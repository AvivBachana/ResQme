import numpy as np
import soundfile as sf

def add_white_noise(wav_path: str, out_path: str, snr_db: float = 15.0):
    data, sr = sf.read(wav_path)
    if data.ndim == 1:
        data = data[:, None]
    sig_power = float((data**2).mean())
    noise_power = sig_power / (10 ** (snr_db / 10))
    noise = (noise_power ** 0.5) * np.random.randn(*data.shape)
    noisy = np.clip(data + noise, -1.0, 1.0)
    sf.write(out_path, noisy, sr)
    return out_path
