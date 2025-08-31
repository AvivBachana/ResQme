import os
from typing import Optional
from pydub import AudioSegment

def to_wav(in_path: str, out_path: Optional[str] = None, target_sr: int = 16000, mono: bool = True, normalize: bool = True) -> str:
    # Load any format supported by FFmpeg via pydub
    audio = AudioSegment.from_file(in_path)
    if mono:
        audio = audio.set_channels(1)
    audio = audio.set_frame_rate(target_sr)
    if normalize:
        audio = audio.normalize()

    out_path = out_path or os.path.splitext(in_path)[0] + ".wav"
    audio.export(out_path, format="wav")
    return out_path
