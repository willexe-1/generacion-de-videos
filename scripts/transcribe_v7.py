import wave, json, subprocess
from pathlib import Path
import numpy as np
import imageio_ffmpeg
from faster_whisper import WhisperModel

TMP = Path(r'C:\Users\USER\AppData\Local\Temp\opencode')
LONG = Path(r'C:\Users\USER\Videos\camara\WhatsApp Unknown 2026-10-07 at 11.02.10 AM\WhatsApp Video 2026-09-01 at 9.01.18 PM (1).mp4')
ff = imageio_ffmpeg.get_ffmpeg_exe()
PROMPT = "unboxing laptop Lenovo, cargador, carga rapida, vatios, pantalla, teclado, Ryzen 7 7730HS, Radeon, accesorios"

def seg_wav(src, st, en, name):
    out = TMP / name
    subprocess.run([ff,'-y','-v','error','-ss',str(st),'-t',str(round(en-st,3)),
                    '-i',str(src),'-ac','1','-ar','16000','-f','wav',str(out)], check=True)
    w = wave.open(str(out),'rb')
    a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)/32768.0
    w.close()
    return a

print("loading medium model (int8, cpu)...")
model = WhisperModel("medium", device="cpu", compute_type="int8")

jobs = {
  "watt": (LONG, 131.0, 141.0),
  "c1": (LONG, 17.5, 23.2),
  "c7": (LONG, 181.0, 187.0),
  "c8": (LONG, 203.0, 209.0),
  "c10": (LONG, 240.0, 246.8),
}
res = {}
for k, (src, st, en) in jobs.items():
    a = seg_wav(src, st, en, f"v7_{k}.wav")
    segments, info = model.transcribe(a, language="es", word_timestamps=True,
                                      initial_prompt=PROMPT, vad_filter=True)
    segs = []
    for s in segments:
        words = [{"word": w.word, "start": round(w.start,2), "end": round(w.end,2)} for w in (s.words or [])]
        segs.append({"start": round(s.start,2), "end": round(s.end,2), "text": s.text.strip(), "words": words})
    full = " ".join(x["text"] for x in segs).strip()
    print(f"{k}: '{full}'")
    res[k] = {"text": full, "segments": segs}
(TMP/"transcript_v7_new.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print("saved transcript_v7_new.json")
