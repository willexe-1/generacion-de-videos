import json
from pathlib import Path
TMP = Path(r'C:\Users\USER\AppData\Local\Temp\opencode')
small = json.loads((TMP/'transcript_fw_small.json').read_text(encoding='utf-8'))
med = json.loads((TMP/'transcript_v7_new.json').read_text(encoding='utf-8'))

def words_of(entry):
    return entry.get('words', [])

# medium c1 words replace small clip1
small[1]['words'] = med['c1']['segments'][0]['words'] if med['c1']['segments'] else []
small[1]['text'] = med['c1']['text']

# clip7: small 181-187 words + tail 186-193.4 words (offset +5.0, tail wav base 186.0, clip base 181.0)
tail = json.loads((TMP/'transcript_fw_small.json').read_text(encoding='utf-8'))  # placeholder, replaced below
import wave
import numpy as np
# tail words were printed; re-derive: transcribe_tail printed only segments, rebuild from small model? Use known values:
# [0.0-7.4] "Todo mundo está esperando, es que prendamos esta maquinota" – need word times; approximate evenly is dishonest.
# Instead reuse: run small words extraction now via faster_whisper on saved wav
from faster_whisper import WhisperModel
model = WhisperModel("small", device="cpu", compute_type="int8")
w = wave.open(str(TMP/'v7_tail.wav'),'rb')
a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)/32768.0
w.close()
segments, info = model.transcribe(a, language="es", word_timestamps=True)
tail_words = []
for s in segments:
    for wd in (s.words or []):
        tail_words.append({"word": wd.word, "start": round(wd.start+5.0,2), "end": round(wd.end+5.0,2)})
print("tail words:", [(w['word'], w['start']) for w in tail_words])
small[7]['words'] = small[7]['words'] + [w for w in tail_words if w['start'] >= 5.0]
small[7]['text'] += " " + " ".join(w['word'] for w in tail_words if w['start'] >= 5.0)
small[7]['end'] = 193.5

# clip8 fixes
for wd in small[8]['words']:
    if wd['word'].lower().startswith('protet'): wd['word'] = 'protector'
    if wd['word'].lower() == 'topa': wd['word'] = 'tapa'

# clip9: map corrected 7 words onto small timestamps
corr9 = ['Ryzen','7','7730HS','y','sus','gráficos','integrados.']
w9 = small[9]['words']
print("c9 small words:", [(w['word'], w['start'], w['end']) for w in w9])
if len(w9) == 7:
    for wd, cw in zip(w9, corr9):
        wd['word'] = cw
small[9]['text'] = ' '.join(corr9)

# clip10 fixes
for wd in small[10]['words']:
    lw = wd['word'].lower()
    if 'vende' in lw: wd['word'] = 'vendedores'
small[10]['text'] = ' '.join(w['word'] for w in small[10]['words'])

# clip2 fix
for wd in small[2]['words']:
    if 'mostrar' in wd['word'].lower(): wd['word'] = 'mostrárselos'

# clip6: keep only 'se siente pesadito' span
w6 = small[6]['words']
print("c6 small words:", [(w['word'], w['start'], w['end']) for w in w6])
i = next((k for k,w in enumerate(w6) if 'siente' in w['word'].lower() or 'pesad' in w['word'].lower()), None)
if i is not None:
    s = max(0, i-1)
    # ensure 'se' present
    span = w6[s:i+2]
    if not any('se' == w['word'].lower() for w in span):
        span[0]['word'] = 'se'
    small[6]['words'] = span
    small[6]['text'] = ' '.join(w['word'] for w in span) + '…'

# new watt clip (index 11): medium sentence 2 words, rebase to clip starting 135.2 (medium seg base 131.0)
watt_words = []
for sg in med['watt']['segments']:
    if sg['start'] >= 4.4:
        for wd in sg['words']:
            watt_words.append({"word": wd['word'], "start": round(wd['start']-4.2,2), "end": round(wd['end']-4.2,2)})
print("watt words:", [(w['word'], w['start']) for w in watt_words])
small.append({"clip": 11, "start": 135.2, "end": 140.0,
              "text": ' '.join(w['word'] for w in watt_words), "words": watt_words})

(TMP/'transcript_v7_final.json').write_text(json.dumps(small, ensure_ascii=False, indent=1), encoding='utf-8')
print("saved transcript_v7_final.json")
for i, e in enumerate(small):
    print(f"CLIP{i}: '{e['text']}' ({len(e['words'])}w)")
