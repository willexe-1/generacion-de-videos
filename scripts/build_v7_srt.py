import json
from pathlib import Path
TMP = Path(r'C:\Users\USER\AppData\Local\Temp\opencode')
ROOT = Path(r'C:\Users\USER\Videos\camara\WhatsApp Unknown 2026-10-07 at 11.02.10 AM')
tr = json.loads((TMP/'transcript_v7_final.json').read_text(encoding='utf-8'))
starts = [3.20,13.00,18.70,24.37,33.47,39.17,44.87,53.07,59.07,71.57,80.94,86.94]
order = [0,1,2,3,4,5,11,6,7,8,9,10]
def fmt(s):
    h=int(s//3600); m=int((s%3600)//60); sec=int(s%60); ms=int((s%1)*1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"
out=[]; idx=1
for pos, ti in enumerate(order):
    st = starts[pos]
    ws = tr[ti]['words']
    if not ws: continue
    cur=[]; cs=None
    for wd in ws:
        ws_ = st+float(wd['start']); we = st+float(wd['end'])
        if cs is None: cs = ws_
        cur.append(wd['word']); txt=' '.join(cur)
        if len(txt) >= 40 or we-cs > 2.6 or wd == ws[-1]:
            out.append(f"{idx}\n{fmt(max(st,cs))} --> {fmt(we+0.15)}\n{txt}\n")
            idx+=1; cur=[]; cs=None
dst = ROOT/'Unboxing Lenovo - vertical v7 FINAL.srt'
dst.write_text('\n'.join(out), encoding='utf-8')
print('srt cues', idx-1, '->', dst.name)
