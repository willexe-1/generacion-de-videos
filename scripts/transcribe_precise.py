import subprocess, json, wave
from pathlib import Path
import imageio_ffmpeg
from vosk import Model, KaldiRecognizer

ROOT = Path(r'C:\Users\USER\Videos\camara\WhatsApp Unknown 2026-10-07 at 11.02.10 AM')
SHORT = ROOT / 'WhatsApp Video 2026-09-01 at 9.01.18 PM.mp4'
LONG = ROOT / 'WhatsApp Video 2026-09-01 at 9.01.18 PM (1).mp4'
MODEL = Path(r'C:\Users\USER\AppData\Local\Temp\opencode\vosk-model-small-es-0.42')
TMP = Path(r'C:\Users\USER\AppData\Local\Temp\opencode')
ff = imageio_ffmpeg.get_ffmpeg_exe()
model = Model(str(MODEL))

clips = [
 (SHORT, 0.0, 6.8),
 (LONG, 17.5, 23.2),
 (LONG, 43.0, 48.7),
 (LONG, 68.0, 73.7),
 (LONG, 99.5, 105.2),
 (LONG, 120.0, 125.7),
 (LONG, 159.0, 165.0),
 (LONG, 181.0, 187.0),
 (LONG, 203.0, 209.0),
 (LONG, 224.0, 230.0),
 (LONG, 240.0, 246.8),
]

out = []
for i, (src, st, en) in enumerate(clips):
    wav = TMP / f"seg{i}.wav"
    dur = round(en - st, 3)
    subprocess.run([ff, '-y', '-v', 'error', '-ss', str(st), '-t', str(dur),
                    '-i', str(src), '-ac', '1', '-ar', '16000', '-f', 'wav', str(wav)],
                   check=True)
    wf = wave.open(str(wav), 'rb')
    assert wf.getnchannels() == 1 and wf.getsampwidth() == 2 and wf.getframerate() == 16000
    rec = KaldiRecognizer(model, 16000)
    rec.SetWords(True)
    data = wf.readframes(wf.getnframes())
    step = 32000
    for k in range(0, len(data), step):
        rec.AcceptWaveform(data[k:k+step])
    res = json.loads(rec.FinalResult())
    text = res.get('text', '').strip()
    words = res.get('result', [])
    print(f"CLIP {i} [{st}-{en}]: '{text}' ({len(words)} words)")
    for w in words[:6]:
        print("   ", round(w.get('start',0),2), round(w.get('end',0),2), w.get('word'))
    out.append({"clip": i, "start": st, "end": en, "text": text, "words": words})

TMP.joinpath("transcript_precise.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
print("saved transcript_precise.json")
