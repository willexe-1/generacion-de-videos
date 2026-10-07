import wave, json
from pathlib import Path
import numpy as np
from faster_whisper import WhisperModel

TMP = Path(r'C:\Users\USER\AppData\Local\Temp\opencode')
model = WhisperModel("small", device="cpu", compute_type="int8")
w = wave.open(str(TMP / 'v7_c7.wav'), 'rb') if (TMP / 'v7_c7.wav').exists() else None
if w is None:
    import subprocess, imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    LONG = Path(r'C:\Users\USER\Videos\camara\WhatsApp Unknown 2026-10-07 at 11.02.10 AM\WhatsApp Video 2026-09-01 at 9.01.18 PM (1).mp4')
    subprocess.run([ff,'-y','-v','error','-ss','181.0','-t','9.0','-i',str(LONG),
                    '-ac','1','-ar','16000','-f','wav',str(TMP/'v7_c7.wav')], check=True)
    w = wave.open(str(TMP / 'v7_c7.wav'), 'rb')
a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)/32768.0
w.close()
segments, info = model.transcribe(a, language="es", word_timestamps=True,
    initial_prompt="vamos a proceder con lo que todo mundo quiere, prender, encender")
for s in segments:
    print(f"[{s.start:.1f}-{s.end:.1f}] {s.text.strip()}")
    for wd in (s.words or []):
        print(f"   {wd.start:.2f} {wd.word}")
