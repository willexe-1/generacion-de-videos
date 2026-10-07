import json, wave, subprocess
from pathlib import Path
import numpy as np
import imageio_ffmpeg

TMP = Path(r'C:\Users\USER\AppData\Local\Temp\opencode')
ROOT = Path(r'C:\Users\USER\Videos\camara\WhatsApp Unknown 2026-10-07 at 11.02.10 AM')
ff = imageio_ffmpeg.get_ffmpeg_exe()
SR = 44100

trans = json.loads((TMP / 'transcript_v7_final.json').read_text(encoding='utf-8'))
ORDER=[0,1,2,3,4,5,11,6,7,8,9,10]
# scene order in final timeline (same as v3/v4)
# anim durations and clip durations (measured from v4 render)
scene_defs = [
 ('anim','intro',3.2),('clip',0,6.8),('anim','box',3.0),('clip',1,5.7),('clip',2,5.67),
 ('clip',3,5.7),('anim','contents',3.4),('clip',4,5.7),('clip',5,5.7),('clip',6,4.8),
 ('anim','device',3.4),
 ('clip',7,6.0),('clip',8,12.5),('clip',9,5.97),('anim','details',3.4),('clip',10,6.0),
 ('clip',11,6.83),('anim','outro',3.2),
]
# compute boundaries
bounds=[]; t=0.0
for s in scene_defs:
    dur = s[2]
    bounds.append((t, t+dur, s))
    t+=dur
TOTAL=t
print(f"TOTAL {TOTAL:.2f}s, {len(bounds)} scenes")

# 1. speech track: for anims silence, for clips use original segment audio (44.1k stereo->mono->stereo)
# reuse seg wavs (16k mono) is low quality; instead extract 44.1k stereo per clip segment
SHORT = ROOT / 'WhatsApp Video 2026-09-01 at 9.01.18 PM.mp4'
LONG = ROOT / 'WhatsApp Video 2026-09-01 at 9.01.18 PM (1).mp4'
clip_src = [(SHORT,0.0,6.8),(LONG,17.5,23.2),(LONG,43.0,48.7),(LONG,68.0,73.7),(LONG,99.5,105.2),(LONG,120.0,125.7),(LONG,135.2,140.0),(LONG,159.0,165.0),(LONG,181.0,193.5),(LONG,203.0,209.0),(LONG,224.0,230.0),(LONG,240.0,246.8)]
speech = np.zeros(int(TOTAL*SR), dtype=np.float32)
for bi,(st,en,s) in enumerate(bounds):
    if s[0]!='clip': continue
    # clip index = position among clips
    ci = sum(1 for b in bounds[:bi] if b[2][0]=='clip')
    src, sst, sen = clip_src[ci]
    tmpw = TMP / f"mix_seg{ci}.wav"
    subprocess.run([ff,'-y','-v','error','-ss',str(sst),'-t',str(round(sen-sst,3)),'-i',str(src),
                    '-ac','1','-ar',str(SR),'-f','wav',str(tmpw)], check=True)
    with wave.open(str(tmpw),'rb') as wf:
        raw = wf.readframes(wf.getnframes())
    arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32)/32768.0
    # place at timeline start
    o0 = int(st*SR); o1 = min(len(speech), o0+len(arr))
    speech[o0:o1] += arr[:o1-o0]
    print(f"clip{ci} placed {len(arr)/SR:.2f}s at {st:.2f}")

# 2. music bed: chill tech pad loop, -22dB under speech, -14dB in anims
# chords Am F C G, 90 BPM
bpm=92; beat=60/bpm; bar=beat*4
freqs = {'A2':110,'C3':130.81,'E3':164.81,'F2':87.31,'G2':98,'B2':123.47,'D3':146.83,'G3':196,'C3b':130.81}
prog = [['A2','C3','E3'],['F2','A2','C3'],['C3','E3','G3'],['G2','B2','D3']]
nn = int(TOTAL*SR)
tt = np.arange(nn)/SR
music = np.zeros(nn, dtype=np.float32)
for bi in range(int(TOTAL/bar)+1):
    chord = prog[bi % 4]
    s0 = int(bi*bar*SR); s1 = min(nn, int((bi+1)*bar*SR))
    seg = np.arange(s1-s0)/SR
    env = np.minimum(1, seg/0.8) * np.minimum(1, (len(seg)/SR-(len(seg)/SR-seg))/0.8 + 0.2)
    tone = np.zeros_like(seg, dtype=np.float32)
    for n in chord:
        f = freqs[n]
        tone += 0.33*np.sin(2*np.pi*f*seg) + 0.12*np.sin(2*np.pi*f*2*seg)
    tone *= (0.5+0.5*np.sin(2*np.pi*0.25*seg+bi))
    music[s0:s1] += (tone*env*0.16).astype(np.float32)
# soft kick + hats
for b in range(int(TOTAL/beat)):
    k0=int(b*beat*SR)
    L=int(0.12*SR)
    if k0+L<nn and b%2==0:
        env=np.exp(-np.arange(L)/(0.03*SR))
        sweep=50+70*np.exp(-np.arange(L)/(0.02*SR))
        ph=np.cumsum(sweep/SR*2*np.pi)
        music[k0:k0+L]+=0.22*np.sin(ph)*env
    h0=int((b+0.5)*beat*SR); HL=int(0.04*SR)
    if h0+HL<nn:
        music[h0:h0+HL]+=0.05*np.random.randn(HL)*np.exp(-np.arange(HL)/(0.012*SR))
# ducking: 0.35 in clips (speech present), 0.8 in anims
duck=np.ones(nn,dtype=np.float32)*0.8
for (st,en,s) in bounds:
    if s[0]=='clip':
        duck[int(st*SR):int(en*SR)]=0.32
# smooth duck transitions 0.3s
k=int(0.3*SR)
ker=np.ones(k)/k
duck=np.convolve(duck,ker,mode='same')
music*=duck

# 3. SFX: whoosh at each boundary + pops inside anims
sfx=np.zeros(nn,dtype=np.float32)
def add_whoosh(at):
    L=int(0.45*SR); o=int(at*SR)-L//2
    if o<0 or o+L>=nn: return
    n=np.random.randn(L)
    # simple lowpass sweep via cumulative blend
    env=np.sin(np.pi*np.arange(L)/L)**1.5
    sfx[o:o+L]+= (n*env*0.28).astype(np.float32)
def add_pop(at,f=720):
    L=int(0.09*SR); o=int(at*SR)
    if o<0 or o+L>=nn: return
    seg=np.sin(2*np.pi*f*np.arange(L)/SR)*np.exp(-np.arange(L)/(0.025*SR))
    sfx[o:o+L]+= (seg*0.30).astype(np.float32)
for (st,en,s) in bounds[1:]:
    add_whoosh(st)
# pops for cards/podium/checks (offsets inside anims)
pop_offsets={'intro':[0.5,1.2],'box':[0.6,1.4],'contents':[0.6,0.85,1.1,1.6],'device':[1.0,1.25,1.5],'details':[0.55,0.8,1.05,1.8],'outro':[0.7,1.6]}
for (st,en,s) in bounds:
    if s[0]=='anim' and s[1] in pop_offsets:
        for off in pop_offsets[s[1]]:
            if off < (en-st):
                add_pop(st+off, 660 if s[1]!='outro' else 520)

mix = speech*0.95 + music + sfx*0.9
mix = np.clip(mix, -0.98, 0.98)
stereo = np.stack([mix, mix], axis=1)
pcm = (stereo*32767).astype(np.int16)
out_wav = TMP / 'v7_mix.wav'
with wave.open(str(out_wav),'wb') as wf:
    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes(pcm.tobytes())
print(f"saved {out_wav} {len(pcm)/SR:.1f}s")

# 4. SRT from precise transcript mapped to timeline
def fmt(s):
    h=int(s//3600); m=int((s%3600)//60); sec=int(s%60); ms=int((s%1)*1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"
srt=[]
idx=1; clip_i=0
for (st,en,s) in bounds:
    if s[0]!='clip': continue
    w = trans[ORDER[clip_i]]['words']
    if not w:
        srt.append(f"{idx}\n{fmt(st+0.2)} --> {fmt(min(en,st+2.2))}\n[sonido del desempaque]\n")
        idx+=1; clip_i+=1; continue
    # group words into lines of <=42 chars
    cur=[]; cur_s=None
    for wd in w:
        ws=st+float(wd['start']); we=st+float(wd['end'])
        if cur_s is None: cur_s=ws
        cur.append((wd['word'],ws,we))
        txt=' '.join(c[0] for c in cur)
        if len(txt)>=40 or we-cur_s>2.4 or wd==w[-1]:
            srt.append(f"{idx}\n{fmt(max(st,cur_s))} --> {fmt(min(en,we+0.15))}\n{txt}\n")
            idx+=1; cur=[]; cur_s=None
    clip_i+=1
TMP.joinpath('v7_subs.srt').write_text('\n'.join(srt), encoding='utf-8')
print(f"saved v5_subs.srt with {idx-1} cues")
