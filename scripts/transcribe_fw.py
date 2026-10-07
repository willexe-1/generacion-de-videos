import json
from pathlib import Path
from faster_whisper import WhisperModel

TMP = Path(r'C:\Users\USER\AppData\Local\Temp\opencode')
# reuse precise seg wavs (16k mono) created earlier: seg0..seg10.wav
model = WhisperModel("small", device="cpu", compute_type="int8")
out=[]
import wave as _wv, numpy as _np
for i in range(11):
    wav = TMP / f"seg{i}.wav"
    _w = _wv.open(str(wav),'rb'); _a = _np.frombuffer(_w.readframes(_w.getnframes()), dtype=_np.int16).astype(_np.float32)/32768.0; _w.close()
    segments, info = model.transcribe(_a, language="es", word_timestamps=True,
        initial_prompt="unboxing laptop Lenovo, cargador, pantalla, teclado, Ryzen 7, accesorios")
    segs=[]
    for s in segments:
        words=[{"word": w.word, "start": round(w.start,2), "end": round(w.end,2)} for w in (s.words or [])]
        segs.append({"start": round(s.start,2), "end": round(s.end,2), "text": s.text.strip(), "words": words})
    full=" ".join(x["text"] for x in segs).strip()
    print(f"CLIP {i} lang={info.language} p={round(info.language_probability,2)}: '{full}'")
    # flatten words
    flat=[]
    for sg in segs:
        flat.extend(sg["words"])
    out.append({"clip": i, "text": full, "segments": segs, "words": flat})
(TMP/"transcript_fw_small.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("saved transcript_fw_small.json")
