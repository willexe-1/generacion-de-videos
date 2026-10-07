import wave, subprocess
from pathlib import Path
import numpy as np
import imageio_ffmpeg

TMP = Path(r'C:\Users\USER\AppData\Local\Temp\opencode')
LONG = Path(r'C:\Users\USER\Videos\camara\WhatsApp Unknown 2026-10-07 at 11.02.10 AM\WhatsApp Video 2026-09-01 at 9.01.18 PM (1).mp4')
ff = imageio_ffmpeg.get_ffmpeg_exe()

# 1. Clip 3 segment energy check (68.0-73.7)
seg = TMP / 'check_seg3.wav'
subprocess.run([ff,'-y','-v','error','-ss','68.0','-t','5.7','-i',str(LONG),
                '-ac','1','-ar','16000','-f','wav',str(seg)], check=True)
w = wave.open(str(seg),'rb'); raw = w.readframes(w.getnframes())
a = np.frombuffer(raw, dtype=np.int16).astype(float)/32768.0
# frame energies 100ms
n = len(a)//1600
e = np.array([np.sqrt((a[i*1600:(i+1)*1600]**2).mean()) for i in range(n)])
print(f"SEG3 dur={len(a)/16000:.1f}s peak={abs(a).max():.3f} meanRMS={e.mean():.4f} maxWin={e.max():.3f}")
print(" speech-like windows (>0.05):", int((e>0.05).sum()), "/", n)

# 2. Full-file Vosk keyword scan for wattage
from vosk import Model, KaldiRecognizer
import json
full = TMP / 'full_16k.wav'
print("extracting full audio...")
subprocess.run([ff,'-y','-v','error','-i',str(LONG),'-ac','1','-ar','16000','-f','wav',str(full)], check=True)
model = Model(str(TMP / 'vosk-model-small-es-0.42'))
rec = KaldiRecognizer(model, 16000)
rec.SetWords(True)
wf = wave.open(str(full),'rb'); data = wf.readframes(wf.getnframes())
for k in range(0, len(data), 64000):
    rec.AcceptWaveform(data[k:k+64000])
res = json.loads(rec.FinalResult())
words = res.get('result', [])
print(f"full words: {len(words)}")
keys = ['sesenta','cinco','vatios','vatios','watts','watt','carga','cargador','w']
for wd in words:
    wl = wd['word'].lower()
    if any(k in wl for k in ['sesenta','cinco','vatio','watt','watts']):
        print(f"  HIT {wd['start']:.1f}s-{wd['end']:.1f}s: {wd['word']}")
# context around carga mentions
cargas = [(wd['start'], wd['word']) for wd in words if 'carg' in wd['word'].lower()]
print("carga mentions:", [(f"{s:.0f}s", w) for s, w in cargas][:12])
