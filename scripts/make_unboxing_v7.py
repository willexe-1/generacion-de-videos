import av, math, os, subprocess, wave, json
import numpy as np
from pathlib import Path
from fractions import Fraction
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import imageio_ffmpeg

ROOT = Path(r'C:\Users\USER\Videos\camara\WhatsApp Unknown 2026-10-07 at 11.02.10 AM')
SHORT = ROOT / 'WhatsApp Video 2026-09-01 at 9.01.18 PM.mp4'
LONG = ROOT / 'WhatsApp Video 2026-09-01 at 9.01.18 PM (1).mp4'
OUT = ROOT / 'Unboxing Lenovo - vertical v7.mp4'
SILENT = Path(os.environ.get('TEMP', r'C:\Users\USER\AppData\Local\Temp')) / 'unboxing_v7_silent.mp4'
WAV = Path(os.environ.get('TEMP', r'C:\Users\USER\AppData\Local\Temp')) / 'unboxing_v7_speech.wav'
WIDTH, HEIGHT, FPS = 720, 1280, 30
ORANGE = (255, 133, 38)
WHITE = (250, 246, 239)
DARK = (11, 13, 19)

font_bold = r'C:\Windows\Fonts\arialbd.ttf'
font_reg = r'C:\Windows\Fonts\arial.ttf'
font_heavy = r'C:\Windows\Fonts\impact.ttf'
font_big = ImageFont.truetype(font_heavy, 66)
font_mid = ImageFont.truetype(font_bold, 30)
font_tag = ImageFont.truetype(font_bold, 20)
font_small = ImageFont.truetype(font_reg, 18)
font_sub2 = ImageFont.truetype(font_bold, 22)
TRANS = 12
SUBS = [
 ["Aqui esta la caja sobre el escritorio", "Vamos a revisarla con calma", "Primer vistazo al paquete"],
 ["Cortamos la cinta exterior", "La caja viene bien protegida", "Abrimos sin prisa"],
 ["Primera capa de proteccion", "Todo viene en su sitio", "Buena presentacion"],
 ["Sacamos el empaque interior", "Paso a paso", "Seguimos desempaquetando"],
 ["Que viene adentro?", "Revisamos los accesorios", "Cables y papeles a la vista"],
 ["Documentacion incluida", "Guardamos los accesorios", "Primera revision lista"],
 ["Ahora si, el equipo", "Sale con su funda", "El momento del reveal"],
 ["Vista exterior del equipo", "Diseno sobrio en negro", "Lo giramos para verlo"],
 ["Abrimos la pantalla", "Primer vistazo al teclado", "El equipo se ve nuevo"],
 ["Detalle de cerca", "Teclado y etiquetas", "Buenos acabados"],
 ["Equipo encendido", "Pantalla lista para empezar", "Que te parece?"],
]

def clamp01(x): return max(0.0, min(1.0, x))
def ease(x):
    x = clamp01(x); return x*x*(3-2*x)
def back(x):
    x = clamp01(x); c1=1.70158; c3=c1+1
    return 1 + c3*pow(x-1,3) + c1*pow(x-1,2)

def bg(d, t, glob):
    for i in range(26):
        x = (i*173 + int(glob*28)) % WIDTH
        y = (i*229 + int(t*22)) % HEIGHT
        d.ellipse((x-2,y-2,x+2,y+2), fill=(255,150,70,70))
        if i>0:
            px = ((i-1)*173 + int(glob*28)) % WIDTH
            py = ((i-1)*229 + int(t*22)) % HEIGHT
            if abs(x-px)+abs(y-py) < 220:
                d.line((x,y,px,py), fill=(255,140,60,22), width=1)

def mascot_box(d, x, y, s, mood=1.0, alpha=255):
    w=int(64*s); h=int(56*s)
    d.rounded_rectangle((x-w//2,y-h//2,x+w//2,y+h//2), radius=int(10*s), fill=(232,116,32,alpha), outline=(255,255,255,alpha), width=3)
    d.line((x-w//2,y-h//2+int(14*s),x+w//2,y-h//2+int(14*s)), fill=(255,255,255,alpha), width=2)
    ex=int(11*s); ey=int(10*s); yo=int(math.sin(mood*6)*2*s)
    d.ellipse((x-ex-8*s,y+ey+yo-8*s,x-ex+8*s,y+ey+yo+8*s), fill=(255,255,255,alpha))
    d.ellipse((x+ex-8*s,y+ey+yo-8*s,x+ex+8*s,y+ey+yo+8*s), fill=(255,255,255,alpha))
    d.ellipse((x-ex-3*s,y+ey+yo-3*s,x-ex+3*s,y+ey+yo+3*s), fill=(20,20,25,alpha))
    d.ellipse((x+ex-3*s,y+ey+yo-3*s,x+ex+3*s,y+ey+yo+3*s), fill=(20,20,25,alpha))
    d.line((x-ex-10*s,y-14*s,x-ex+10*s,y-10*s), fill=(20,20,25,alpha), width=3)
    d.line((x+ex-10*s,y-10*s,x+ex+10*s,y-14*s), fill=(20,20,25,alpha), width=3)

def mascot_lap(d, x, y, s, mood=1.0, alpha=255):
    w=int(70*s); h=int(52*s)
    hop=int(abs(math.sin(mood*5))*8*s)
    y-=hop
    d.rounded_rectangle((x-w//2,y-h//2,x+w//2,y+h//2), radius=int(9*s), fill=(58,122,199,alpha), outline=(255,255,255,alpha), width=3)
    d.line((x-w//2-8*s,y+h//2,x+w//2+8*s,y+h//2), fill=(255,255,255,alpha), width=4)
    d.ellipse((x-14*s,y-6*s,x-2*s,y+6*s), fill=(255,255,255,alpha))
    d.ellipse((x+2*s,y-6*s,x+14*s,y+6*s), fill=(255,255,255,alpha))
    d.ellipse((x-11*s,y-3*s,x-5*s,y+3*s), fill=(20,20,25,alpha))
    d.ellipse((x+5*s,y-3*s,x+11*s,y+3*s), fill=(20,20,25,alpha))

V5_TRANS = json.loads(Path(r'C:\Users\USER\AppData\Local\Temp\opencode\transcript_v7_final.json').read_text(encoding='utf-8'))
KW = [
 (('cargador','carga','cable'), 'CARGA', 'bolt'),
 (('pantalla',), 'PANTALLA', 'screen'),
 (('teclado',), 'TECLADO', 'keys'),
 (('ryzen',), 'RYZEN 7', 'chip'),
 (('grafic','radeon','radio','integrada'), 'GPU', 'chip'),
 (('pesa','pesadito','kilos'), 'PESO', 'weight'),
 (('prender','enciende','proceder','encendido'), 'ENCENDIDO', 'power'),
 (('caja',), 'CAJA', 'box'),
 (('protector','proteto','topa'), 'PROTECTOR', 'shield'),
 (('compran','internet','necesarias'), 'COMPRA ONLINE', 'cart'),
 (('vendedores','muchachos','comentar'), 'COMENTARIOS', 'chat'),
 (('rapidamente','rapido'), 'RAPIDO', 'flash'),
 (('watts','vatios','65'), '65 W', 'bolt'),
]
def kw_active(cidx, lt):
    try: ws = V5_TRANS[cidx]['words']
    except: return None
    for w in ws:
        wl = w['word'].lower()
        if float(w['start'])-0.5 <= lt <= float(w['end'])+0.8:
            for keys, label, icon in KW:
                if any(k in wl for k in keys):
                    return (label, icon)
    return None

def draw_kw_badge(d, label, icon, alpha, pulse):
    bx0, by0 = 430, 108; bw, bh = 252, 64
    d.rounded_rectangle((bx0,by0,bx0+bw,by0+bh), radius=14, fill=(12,15,22,225), outline=ORANGE+(255,), width=2)
    d.ellipse((bx0+14,by0+18,bx0+38,by0+42), fill=ORANGE+(255,))
    d.text((bx0+20,by0+24), '!', font=font_tag, fill=(15,15,15,255))
    sc = 1.0 + 0.06*pulse
    import math as _m
    d.text((bx0+52,by0+16), label, font=font_tag, fill=WHITE+(alpha,))
    # mini icon
    ix, iy = bx0+bw-44, by0+32
    if icon == 'bolt':
        d.polygon([(ix+6,iy-14),(ix-6,iy+2),(ix-1,iy+2),(ix-6,iy+14),(ix+6,iy-2),(ix+1,iy-2)], fill=ORANGE+(alpha,))
    elif icon == 'screen':
        d.rectangle((ix-14,iy-10,ix+14,iy+10), outline=WHITE+(alpha,), width=2)
        d.line((ix-10,iy+14,ix+10,iy+14), fill=ORANGE+(alpha,), width=2)
    elif icon == 'keys':
        for r in range(2):
            for c_ in range(4):
                d.rectangle((ix-16+c_*9,iy-7+r*9,ix-10+c_*9,iy-1+r*9), fill=WHITE+(alpha,))
    elif icon == 'chip':
        d.rectangle((ix-11,iy-11,ix+11,iy+11), outline=WHITE+(alpha,), width=2)
        for px in (-14,14):
            for py in (-6,0,6):
                d.line((ix+px,iy+py,ix+11 if px<0 else ix-11,iy+py), fill=ORANGE+(alpha,), width=2)
    elif icon == 'power':
        d.ellipse((ix-11,iy-11,ix+11,iy+11), outline=WHITE+(alpha,), width=2)
        d.line((ix,iy-8,ix,iy+2), fill=ORANGE+(alpha,), width=3)
    elif icon == 'box':
        d.polygon([(ix-13,iy-4),(ix,iy-11),(ix+13,iy-4),(ix,iy+3)], fill=ORANGE+(alpha,))
        d.polygon([(ix-13,iy-4),(ix,iy+3),(ix,iy+13),(ix-13,iy+6)], fill=WHITE+(alpha,))
    else:
        d.ellipse((ix-8,iy-8,ix+8,iy+8), outline=ORANGE+(alpha,), width=2)

def v5_line(cidx, lt):
    try:
        w = V5_TRANS[cidx]['words']
    except: return ("", -1)
    if not w: return ("[sonido del desempaque]", -2)
    cur = -1
    for i, wd in enumerate(w):
        if float(wd['start']) <= lt <= float(wd['end']) + 0.12:
            cur = i; break
    if cur == -1:
        # nearest past word window
        past = [i for i, wd in enumerate(w) if float(wd['end']) < lt]
        cur = past[-1] if past else 0
    s = max(0, cur-3); e = min(len(w), s+7); s = max(0, e-7)
    return (" ".join(x['word'] for x in w[s:e]), cur-s)

def shadow_el(d,x,y,w,a=90):
    d.ellipse((x-w//2,y-10,x+w//2,y+12),fill=(0,0,0,a))

def cube3d(d,cx,cy,s,ang,alpha=255):
    import math as _m
    dx=int(_m.cos(ang)*s*.38); dy=int(_m.sin(ang)*s*.22)
    d.polygon([(cx-s//2+dx,cy-s//2+dy),(cx+s//2+dx,cy-s//2+dy),(cx+s//2,cy-s//2),(cx-s//2,cy-s//2)],fill=(255,150,60,alpha))
    d.rounded_rectangle((cx-s//2,cy-s//2,cx+s//2,cy+s//2),radius=9,fill=(38,45,58,alpha),outline=ORANGE+(alpha,),width=2)
    d.ellipse((cx-7,cy-7,cx+7,cy+7),fill=WHITE+(alpha,))

KW_DESC = {
 'CARGA': 'Revisamos el cargador y los cables',
 'PANTALLA': 'Protector y primer vistazo',
 'TECLADO': 'Amplio, con teclado numérico',
 'RYZEN 7': '7730HS con gráficos Radeon',
 'GPU': 'Gráficos integrados Radeon',
 'PESO': 'Se siente pesadito en mano',
 'ENCENDIDO': 'El momento de prenderla',
 'CAJA': 'Empaque original de la compra',
 'PROTECTOR': 'Protege la pantalla nueva',
 'COMPRA ONLINE': 'Pedida por internet',
 'COMENTARIOS': '¿Qué juego pruebo primero?',
 'RAPIDO': 'Vista rápida del contenido',
 '65 W': 'Lo que marca el cargador',
}
def draw_kw_card(d, label, icon, cidx, lt, alpha):
    import math as _m
    try: ws = V5_TRANS[cidx]['words']
    except: ws = []
    hits = []
    for _w in ws:
        _wl = _w['word'].lower()
        for _keys, _lab, _ic in KW:
            if _lab == label and any(_k in _wl for _k in _keys):
                hits.append(_w); break
    if hits:
        t0 = float(hits[0]['start']); t1 = float(hits[-1]['end'])
    else:
        t0, t1 = lt, lt+1
    age = lt - (t0-0.35)
    if age < 0: return
    k = max(0, 1-min(1, age/0.42))
    xx = 130 + int(580*k*k)
    yy = 296 + int(4*_m.sin(lt*2.2))
    desc = KW_DESC.get(label, '')
    if cidx == 11 and label in ('CARGA',):
        label, desc = '65 W', 'Carga rápida según tu medición'
    CW, CH = 580, 132
    d.ellipse((xx+40, yy+CH-6, xx+CW-40, yy+CH+14), fill=(0,0,0,90))
    d.rounded_rectangle((xx, yy, xx+CW, yy+CH), radius=18, fill=(14,17,25,235),
                        outline=ORANGE+(alpha,), width=3)
    d.ellipse((xx+22, yy+26, xx+86, yy+90), fill=ORANGE+(255,))
    d.ellipse((xx+30, yy+34, xx+78, yy+82), fill=(14,17,25,255))
    ix, iy = xx+54, yy+58
    _ic = icon
    if _ic == 'bolt':
        d.polygon([(ix+7,iy-15),(ix-7,iy+2),(ix-1,iy+2),(ix-7,iy+15),(ix+7,iy-2),(ix+1,iy-2)], fill=ORANGE+(alpha,))
    elif _ic == 'screen':
        d.rectangle((ix-15,iy-11,ix+15,iy+9), outline=WHITE+(alpha,), width=3)
        d.line((ix-10,iy+14,ix+10,iy+14), fill=ORANGE+(alpha,), width=3)
    elif _ic == 'keys':
        for _r in range(2):
            for _c in range(4):
                d.rectangle((ix-17+_c*9,iy-8+_r*9,ix-11+_c*9,iy-2+_r*9), fill=WHITE+(alpha,))
    elif _ic == 'chip':
        d.rectangle((ix-12,iy-12,ix+12,iy+12), outline=WHITE+(alpha,), width=3)
        d.rectangle((ix-6,iy-6,ix+6,iy+6), fill=ORANGE+(alpha,))
    elif _ic == 'power':
        d.ellipse((ix-12,iy-12,ix+12,iy+12), outline=WHITE+(alpha,), width=3)
        d.line((ix,iy-9,ix,iy+1), fill=ORANGE+(alpha,), width=4)
    elif _ic == 'box':
        d.polygon([(ix-14,iy-5),(ix,iy-12),(ix+14,iy-5),(ix,iy+2)], fill=ORANGE+(alpha,))
        d.polygon([(ix-14,iy-5),(ix,iy+2),(ix,iy+13),(ix-14,iy+6)], fill=WHITE+(alpha,))
    elif _ic == 'shield':
        d.polygon([(ix,iy-14),(ix+11,iy-8),(ix+11,iy+2),(ix,iy+14),(ix-11,iy+2),(ix-11,iy-8)], outline=ORANGE+(alpha,), width=3)
    elif _ic == 'cart':
        d.polygon([(ix-13,iy-4),(ix+13,iy-4),(ix+9,iy+10),(ix-9,iy+10)], outline=WHITE+(alpha,), width=3)
        d.ellipse((ix-7,iy+12,ix-3,iy+16), fill=ORANGE+(alpha,)); d.ellipse((ix+3,iy+12,ix+7,iy+16), fill=ORANGE+(alpha,))
    elif _ic == 'chat':
        d.rounded_rectangle((ix-15,iy-11,ix+15,iy+7), radius=6, outline=WHITE+(alpha,), width=3)
        d.polygon([(ix-4,iy+7),(ix+4,iy+7),(ix,iy+13)], fill=WHITE+(alpha,))
    elif _ic == 'flash':
        d.polygon([(ix+4,iy-14),(ix-8,iy+1),(ix-1,iy+1),(ix-4,iy+14),(ix+8,iy-1),(ix+1,iy-1)], fill=ORANGE+(alpha,))
    else:
        d.ellipse((ix-9,iy-9,ix+9,iy+9), outline=ORANGE+(alpha,), width=3)
    f_t = ImageFont.truetype(font_bold, 30)
    d.text((xx+108, yy+20), label, font=f_t, fill=WHITE+(alpha,))
    f_d = ImageFont.truetype(font_reg, 21)
    d.text((xx+108, yy+60), desc[:34], font=f_d, fill=(210,200,185,alpha))
    span = max(0.1, t1-t0+0.8)
    pr = min(1, max(0, (lt-(t0-0.3))/span))
    d.rounded_rectangle((xx+108, yy+102, xx+CW-24, yy+110), radius=4, fill=(255,255,255,45))
    if pr > 0.02:
        d.rounded_rectangle((xx+108, yy+102, xx+108+int((CW-132)*pr), yy+110), radius=4, fill=ORANGE+(255,))
    sx = int((WIDTH+260)*(((lt-t0)*0.5) % 1.3)) - 160
    d.polygon([(sx,yy-4),(sx+64,yy-4),(sx+14,yy+CH+4),(sx-50,yy+CH+4)], fill=(255,255,255,14))

def draw_sub_pill(d,text,y,alpha):
    bb=d.textbbox((0,0),text,font=font_sub2)
    tw=bb[2]-bb[0]; x0=(WIDTH-tw)//2-16
    d.rounded_rectangle((x0-10,y-10,x0+tw+42,y+36),radius=13,fill=(0,0,0,int(190*alpha/255)),outline=(255,255,255,70),width=1)
    d.text((x0+8,y),text,font=font_sub2,fill=WHITE+(alpha,))

def title_pop(d, l1, l2, t):
    a1 = back(t/.38); a2 = back((t-.14)/.38)
    s1 = .6+.4*max(0,min(1,a1)); s2 = .6+.4*max(0,min(1,a2))
    f1 = ImageFont.truetype(font_heavy, int(66*s1)); f2 = ImageFont.truetype(font_heavy, int(66*s2))
    al = int(255*ease(t/.25))
    b1=d.textbbox((0,0),l1,font=f1,stroke_width=2); b2=d.textbbox((0,0),l2,font=f2,stroke_width=2)
    d.text(((WIDTH-(b1[2]-b1[0]))//2,148),l1,font=f1,fill=WHITE+(al,),stroke_width=2,stroke_fill=(0,0,0,al))
    d.text(((WIDTH-(b2[2]-b2[0]))//2,218),l2,font=f2,fill=ORANGE+(al,),stroke_width=2,stroke_fill=(0,0,0,al))
    return al

def frame_base(kind, t, glob):
    im=Image.new('RGB',(WIDTH,HEIGHT),DARK)
    d=ImageDraw.Draw(im,'RGBA')
    bg(d,t,glob)
    for _ci in range(5):
        _cx=(120+_ci*118+int(glob*14))%WIDTH; _cy=220+((_ci*307)%760)
        _s=22+(_ci%3)*10; shadow_el(d,_cx,_cy+_s//2+14,_s*2,50)
        cube3d(d,_cx,_cy,_s,glob*.9+_ci,110)
    d.rounded_rectangle((22,20,WIDTH-22,HEIGHT-20),radius=24,outline=(255,255,255,36),width=2)
    d.rounded_rectangle((38,46,268,90),radius=11,fill=(16,19,27,245),outline=ORANGE+(230,),width=2)
    d.text((54,57),'TECH  /  UNBOXING',font=font_tag,fill=WHITE+(255,))
    d.text((WIDTH-54,57),f'{int(glob):02d}s',font=font_small,fill=(255,255,255,120),anchor='ra')
    return im,d

def draw_intro(t,L,glob):
    im,d=frame_base('intro',t,glob)
    al=title_pop(d,'UNBOXING','SLIM 3',t)
    # pista
    y0=520; y1=760
    d.rounded_rectangle((48,y0,WIDTH-48,y1),radius=26,fill=(20,24,32,250),outline=(255,255,255,50),width=2)
    for yy in (y0+70,y0+140):
        for xx in range(70,WIDTH-70,34):
            d.line((xx,yy,xx+18,yy),fill=(255,255,255,110),width=3)
    d.line((70,y0+20,70,y1-20),fill=(255,255,255,200),width=4)
    for i in range(4):
        xx=70+i*8; yy=y0+20+i*8
        d.rectangle((xx,yy,xx+8,yy+8),fill=(0,0,0,220) if (i%2==0) else (255,255,255,220))
    for i in range(4):
        xx=WIDTH-70-32+i*8; yy=y0+20+i*8
        d.rectangle((xx,yy,xx+8,yy+8),fill=(0,0,0,220) if (i%2==0) else (255,255,255,220))
    prog=ease(t/L)
    xb=int(110+(WIDTH-220)*prog); xl=int(110+(WIDTH-220)*ease(max(0,(t-.35))/L))
    mascot_box(d,xb,y0+115,1.0,t,al)
    mascot_lap(d,xl,y0+185,1.0,t+.4,al)
    d.rounded_rectangle((48,830,WIDTH-48,930),radius=16,fill=(22,26,35,245),outline=(255,255,255,60),width=1)
    d.text((WIDTH//2,852),'CAJA  →  CONTENIDO  →  EQUIPO',font=font_tag,fill=WHITE+(al,),anchor='ma')
    d.text((WIDTH//2,886),'LENOVO SLIM 3 - DE LA CAJA AL PRIMER ARRANQUE',font=font_small,fill=(210,200,185,al),anchor='ma')
    return im,d,al

def draw_box(t,L,glob):
    im,d=frame_base('box',t,glob)
    al=title_pop(d,'ABRIMOS','LA CAJA',t)
    cx=WIDTH//2; cy=700; q=ease((t-.3)/.9)
    d.polygon([(cx-190,cy-90),(cx,cy-10),(cx+190,cy-90),(cx,cy-175)],fill=(120,72,36,255))
    d.polygon([(cx-190,cy-90),(cx,cy-10),(cx,cy+170),(cx-190,cy+80)],fill=(150,95,48,255),outline=WHITE+(200,))
    d.polygon([(cx,cy-10),(cx+190,cy-90),(cx+190,cy+80),(cx,cy+170)],fill=(88,60,38,255),outline=WHITE+(200,))
    flap=int(90*q)
    d.polygon([(cx-190,cy-90),(cx-150,cy-190-flap),(cx,cy-120-flap),(cx,cy-10)],fill=(185,118,58,255),outline=ORANGE+(255,))
    d.polygon([(cx+190,cy-90),(cx+150,cy-190-flap),(cx,cy-120-flap),(cx,cy-10)],fill=(160,100,52,255),outline=ORANGE+(255,))
    # partículas
    for i in range(12):
        ang=i/12*6.28+t*3; r=120+60*q
        px=cx+int(math.cos(ang)*r); py=cy-40+int(math.sin(ang)*r*.6)
        d.ellipse((px-3,py-3,px+3,py+3),fill=ORANGE+(int(200*q),))
    mascot_box(d,cx-120,cy+230,.8,t,al)
    mascot_lap(d,cx+120,cy+230,.8,t+.3,al)
    d.rounded_rectangle((48,930,WIDTH-48,1000),radius=14,fill=(22,26,35,245))
    d.text((WIDTH//2,950),'EMPAQUE  •  PROTECCIÓN  •  PRIMER VISTAZO',font=font_small,fill=WHITE+(al,),anchor='mm')
    return im,d,al

def draw_contents(t,L,glob):
    im,d=frame_base('contents',t,glob)
    al=title_pop(d,'¿QUÉ HAY','EN LA CAJA?',t)
    for i,(lab,sub) in enumerate([('EQUIPO','lo principal'),('DOCUMENTOS','papel y guías'),('ACCESORIOS','cables y más')]):
        q=back((t-(.35+i*.25))/.45)
        if q<=0: continue
        s=max(.3,min(1.15,q)); w=int(190*s); h=int(250*s)
        x=62+i*202; y=540
        d.rounded_rectangle((x,y,x+190,y+270),radius=18,fill=(24,28,36,250),outline=ORANGE+(255,),width=3)
        cx=x+95
        if i==0:
            d.rounded_rectangle((cx-52,y+40,cx+52,y+120),radius=8,fill=(15,20,28,255),outline=WHITE+(255,),width=3)
            d.polygon([(cx-66,y+128),(cx+66,y+128),(cx+80,y+142),(cx-80,y+142)],fill=(170,175,182,255))
        elif i==1:
            d.rectangle((cx-44,y+38,cx+44,y+135),fill=(238,231,216,255),outline=ORANGE+(255,),width=2)
            for k in range(3): d.line((cx-30,y+70+k*18,cx+30,y+70+k*18),fill=(80,80,80,220),width=3)
        else:
            d.rounded_rectangle((cx-48,y+45,cx+48,y+125),radius=16,fill=(45,52,64,255),outline=WHITE+(255,),width=3)
            d.ellipse((cx-10,y+75,cx+10,y+95),fill=ORANGE+(255,))
        # tick
        if t>.9+i*.25:
            d.ellipse((x+140,y+200,x+172,y+232),fill=ORANGE+(255,))
            d.line((x+147,y+216,x+153,y+222,x+165,y+208),fill=(15,15,15,255),width=3)
        d.text((cx,y+195),lab,font=font_tag,fill=ORANGE+(255,),anchor='mm')
        d.text((cx,y+222),sub,font=font_small,fill=WHITE+(220,),anchor='mm')
    return im,d,al

def draw_device(t,L,glob):
    im,d=frame_base('device',t,glob)
    al=title_pop(d,'AHORA SÍ','EL EQUIPO',t)
    q=ease((t-.25)/1.0)
    cx=WIDTH//2; top=int(620-90*q); Wd=int(460*q+80); Ht=int(280*q+50)
    if q>.05:
        d.rounded_rectangle((cx-Wd//2,top-Ht//2,cx+Wd//2,top+Ht//2),radius=18,fill=(14,19,28,255),outline=WHITE+(255,),width=4)
        d.rounded_rectangle((cx-Wd//2+16,top-Ht//2+16,cx+Wd//2-16,top+Ht//2-30),radius=10,fill=(30,48,66,255),outline=ORANGE+(255,),width=2)
        d.ellipse((cx+Wd//2-70,top-Ht//2+22,cx+Wd//2-22,top-Ht//2+70),fill=(255,120,30,90))
        d.polygon([(cx-Wd//2-30,top+Ht//2+8),(cx+Wd//2+30,top+Ht//2+8),(cx+Wd//2+58,top+Ht//2+38),(cx-Wd//2-58,top+Ht//2+38)],fill=(150,158,166,255))
        for i,lab in enumerate(['EXTERIOR','TECLADO','PANTALLA']):
            k=ease((t-(.9+i*.25))/.35)
            if k>0:
                yy=880+i*0
                xx=58+i*205
                d.rounded_rectangle((xx,880,xx+190,935),radius=12,fill=(20,24,32,250),outline=ORANGE+(255,),width=2)
                d.text((xx+95,907),lab,font=font_tag,fill=WHITE+(255,),anchor='mm')
                d.line((xx+95,880,cx-120+i*110,top+Ht//2),fill=(255,255,255,120),width=2)
    return im,d,al

def draw_details(t,L,glob):
    im,d=frame_base('details',t,glob)
    al=title_pop(d,'3 PUNTOS','A REVISAR',t)
    base=860
    hs=[150,220,180]
    labs=['2  ACCESORIOS','1  EQUIPO','3  ENCENDIDO']
    for i in range(3):
        q=back((t-(.3+i*.22))/.5)
        if q<=0: continue
        h=int(hs[i]*max(.2,min(1,q))); x=90+i*180
        col=ORANGE if i==1 else (70,78,90)
        d.rectangle((x,base-h,x+140,base),fill=col+(255,),outline=WHITE+(200,),width=2)
        d.text((x+70,base-h-36),labs[i].split()[0],font=font_mid,fill=WHITE+(255,),anchor='mm')
        d.text((x+70,base+22),labs[i].split(maxsplit=1)[1],font=font_small,fill=WHITE+(220,),anchor='mm')
        if i==1:
            # corona
            cy=base-h-72
            d.polygon([(x+50,cy),(x+70,cy-18),(x+90,cy),(x+90,cy+14),(x+50,cy+14)],fill=(255,200,60,255))
    # barras de energía
    for i,lab in enumerate(['DISEÑO','DETALLE','PANTALLA']):
        q=ease((t-(.5+i*.2))/.6); w=int(560*q)
        d.rounded_rectangle((80,980+i*45,640,1000+i*45),radius=8,fill=(255,255,255,40))
        d.rounded_rectangle((80,980+i*45,80+w,1000+i*45),radius=8,fill=ORANGE+(255,))
    return im,d,al

def draw_outro(t,L,glob):
    im,d=frame_base('outro',t,glob)
    al=title_pop(d,'¿QUÉ TE','PARECE?',t)
    q=ease((t-.4)/.6); bw=int(560*q); bx=(WIDTH-bw)//2; by=620
    if q>0:
        d.rounded_rectangle((bx,by,bx+bw,by+170),radius=22,fill=(24,29,39,250),outline=ORANGE+(255,),width=3)
        d.polygon([(WIDTH//2-20,by+170),(WIDTH//2+20,by+170),(WIDTH//2,by+205)],fill=ORANGE+(255,))
        dots=int((t*3)%4)
        d.text((WIDTH//2,by+70),'●'*dots if dots else '...',font=font_mid,fill=ORANGE+(255,),anchor='mm')
    d.rounded_rectangle((90,880,WIDTH-90,960),radius=16,fill=ORANGE+(255,))
    d.text((WIDTH//2,920),'COMENTA  TU  PARTE  FAVORITA',font=font_tag,fill=(15,15,15,255),anchor='mm')
    return im,d,al

ANIMS={'intro':draw_intro,'box':draw_box,'contents':draw_contents,'device':draw_device,'details':draw_details,'outro':draw_outro}

def draw_motion(kind,t,length,glob,total):
    im,d,al=ANIMS[kind](t,length,glob)
    d=ImageDraw.Draw(im,'RGBA')
    # barrido de luz para dar volumen a la tarjeta
    sx=int(WIDTH*((t*.7)%1.2))-120
    sw=Image.new('RGBA',(WIDTH,HEIGHT),(0,0,0,0)); sd2=ImageDraw.Draw(sw)
    sd2.polygon([(sx,0),(sx+90,0),(sx+10,HEIGHT),(sx-80,HEIGHT)],fill=(255,255,255,18))
    im=Image.alpha_composite(im.convert('RGBA'),sw).convert('RGB')
    d=ImageDraw.Draw(im,'RGBA')
    py=HEIGHT-34
    d.rounded_rectangle((34,py,WIDTH-34,py+7),radius=3,fill=(255,255,255,55))
    done=int((WIDTH-68)*clamp01(glob/total))
    if done>0: d.rounded_rectangle((34,py,34+done,py+7),radius=3,fill=ORANGE+(255,))
    if t<.14 or length-t<.14:
        e=ease(min(t/.14,(length-t)/.14))
        ov=Image.new('RGBA',(WIDTH,HEIGHT),(5,6,10,int(210*(1-e))))
        im=Image.alpha_composite(im.convert('RGBA'),ov).convert('RGB')
    return im

def portrait(frame, zoom=1.0):
    img=frame.to_image()
    if getattr(frame,'rotation',0) in (-90,270) or (img.width>img.height and img.width==1024):
        img=img.rotate(-90,expand=True)
    r=max(WIDTH*zoom/img.width, HEIGHT*zoom/img.height)
    img=img.resize((round(img.width*r),round(img.height*r)), Image.Resampling.LANCZOS)
    l=(img.width-WIDTH)//2; tp=(img.height-HEIGHT)//2
    return img.crop((l,tp,l+WIDTH,tp+HEIGHT))

def overlay_clip(img, t1, t2, sub, lt, ll, gt, total, cidx=0):
    im=img.convert('RGBA')
    rgb=Image.merge('RGB',im.split()[:3])
    from PIL import ImageEnhance as IE
    rgb=IE.Color(rgb).enhance(1.07); rgb=IE.Contrast(rgb).enhance(1.07)
    im=rgb.convert('RGBA')
    sh=Image.new('RGBA',(WIDTH,HEIGHT),(0,0,0,0)); sd=ImageDraw.Draw(sh)
    for y in range(0,400,4): sd.rectangle((0,y,WIDTH,y+4),fill=(8,10,15,int(118*(1-y/400))))
    for y in range(HEIGHT-260,HEIGHT,4): sd.rectangle((0,y,WIDTH,y+4),fill=(7,8,12,int(128*((y-(HEIGHT-260))/260))))
    im=Image.alpha_composite(im,sh)
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((34,42,250,83),radius=10,fill=(10,12,17,205),outline=ORANGE+(255,),width=2)
    d.text((48,51),'TECH  /  UNBOXING',font=font_tag,fill=WHITE+(255,))
    intro=ease(lt/.3); a=int(255*intro*ease((ll-lt)/.25)); yo=int((1-intro)*20)
    f1=ImageFont.truetype(font_heavy,58)
    d.text((34,135+yo),t1,font=f1,fill=WHITE+(a,),stroke_width=2,stroke_fill=(10,10,12,a))
    d.text((34,200+yo),t2,font=f1,fill=ORANGE+(a,),stroke_width=2,stroke_fill=(10,10,12,a))
    d.rounded_rectangle((28,HEIGHT-155,WIDTH-28,HEIGHT-49),radius=15,fill=(9,11,16,194),outline=(255,255,255,90),width=1)
    d.rectangle((28,HEIGHT-140,34,HEIGHT-64),fill=ORANGE+(230,))
    d.text((52,HEIGHT-128),sub,font=font_mid,fill=WHITE+(a,))
    try:
        ws = V5_TRANS[cidx]['words'] if cidx < len(V5_TRANS) else []
        act = -1
        for k2, wd in enumerate(ws):
            if float(wd['start']) <= lt <= float(wd['end']) + 0.12:
                act = k2; break
        if not ws:
            pass
        else:
            if act < 0:
                past = [k2 for k2, wd in enumerate(ws) if float(wd['end']) < lt]
                act = past[-1] if past else 0
            # Hormozi pages: max 3 words, page fades/scales in as a whole — no vertical fall
            s0 = max(0, act-1); e0 = min(len(ws), s0+3); s0 = max(0, e0-3)
            page = ws[s0:e0]
            page_age = lt - float(page[0]['start'])
            pg = 0.55 + 0.45*min(1, max(0, page_age/0.16))
            pa = int(a * (0.35 + 0.65*min(1, max(0, page_age/0.16))))
            f_act = ImageFont.truetype(font_bold, 37); f_in = ImageFont.truetype(font_bold, 31)
            widths = []
            for k2, wd in enumerate(page):
                gi = s0+k2
                f = f_act if gi == act else f_in
                bb = d.textbbox((0,0), wd['word'].upper(), font=f, stroke_width=2)
                widths.append(bb[2]-bb[0]+26)
            tot = sum(widths)
            sc = min(1.0, 620/max(1, tot))
            tot = int(tot*sc)
            widths = [int(w*sc) for w in widths]
            tx = (WIDTH-tot)//2; cy = 806
            d.rounded_rectangle((tx-18, cy-20, tx+tot+18, cy+50), radius=16,
                                fill=(0,0,0,int(185*pa/255)), outline=(255,255,255,70), width=1)
            for k2, wd in enumerate(page):
                gi = s0+k2
                txt = wd['word'].upper()
                if gi == act:
                    f = ImageFont.truetype(font_bold, int(37*sc*pg))
                    col = ORANGE+(pa,)
                else:
                    f = ImageFont.truetype(font_bold, int(31*sc))
                    col = WHITE+(pa,)
                d.text((tx, cy), txt, font=f, fill=col, stroke_width=2, stroke_fill=(0,0,0,pa))
                tx += widths[k2]
        kw = kw_active(cidx, lt)
        if kw:
            import math as _m
            draw_kw_card(d, kw[0], kw[1], cidx, lt, a)
    except Exception as _e: pass
    # sutil infobar 3D: sombra + brillo de barrido
    d.ellipse((WIDTH//2-180,HEIGHT-70,WIDTH//2+180,HEIGHT-52),fill=(0,0,0,70))
    py=HEIGHT-22
    d.rounded_rectangle((28,py,WIDTH-28,py+6),radius=3,fill=(255,255,255,70))
    done=int((WIDTH-56)*clamp01(gt/total))
    if done>2: d.rounded_rectangle((28,py,28+done,py+6),radius=3,fill=ORANGE+(255,))
    return im.convert('RGB')

scenes=[
 ('anim','intro',3.2),
 ('clip',SHORT,0.0,6.8,'UNBOXING','LENOVO SLIM 3','PRIMER VISTAZO'),
 ('anim','box',3.0),
 ('clip',LONG,17.5,23.2,'VAMOS A ABRIR','LA CAJA','SIN ADELANTAR EL FINAL'),
 ('clip',LONG,43.0,48.7,'PRIMERA CAPA','PROTECCIÓN','TODO EN SU SITIO'),
 ('clip',LONG,68.0,73.7,'EMPIEZA EL','DESEMPAQUE','PASO A PASO'),
 ('anim','contents',3.4),
 ('clip',LONG,99.5,105.2,'¿QUÉ VIENE','EN LA CAJA?','REVISAMOS ACCESORIOS'),
 ('clip',LONG,120.0,125.7,'ACCESORIOS','Y PAPELES','PRIMERA REVISIÓN'),
 ('clip',LONG,135.2,140.0,'65 W','CARGA RAPIDA','LO QUE MARCA EL CARGADOR'),
 ('anim','device',3.4),
 ('clip',LONG,159.0,165.0,'AHORA SÍ…','LA LAPTOP','EL MOMENTO DEL REVEAL'),
 ('clip',LONG,181.0,193.5,'VAMOS A PROCEDER','TODO MUNDO QUIERE','PRENDEMOS LA MAQUINOTA'),
 ('clip',LONG,203.0,209.0,'ABRIMOS','LA PANTALLA','PRIMER VISTAZO'),
 ('anim','details',3.4),
 ('clip',LONG,224.0,230.0,'DETALLES','DE CERCA','TECLADO Y ACABADOS'),
 ('clip',LONG,240.0,246.8,'LISTA PARA','EMPEZAR','¿QUÉ TE PARECE?'),
 ('anim','outro',3.2),
]
total=sum((s[3]-s[2]) if s[0]=='clip' else s[2] for s in scenes)
vo=av.open(str(SILENT),'w',format='mp4')
vout=vo.add_stream('libx264',rate=FPS); vout.width,vout.height=WIDTH,HEIGHT; vout.pix_fmt='yuv420p'
vout.options={'preset':'veryfast','crf':'20'}
gt=0.0; aparts=[]; rs=av.AudioResampler(format='s16p',layout='stereo',rate=44100); prev=None; clip_no=0
CLIP_ORDER = [0,1,2,3,4,5,11,6,7,8,9,10]
for idx,s in enumerate(scenes):
    if s[0]=='anim':
        _,kind,dur=s; n=round(dur*FPS)
        for fi in range(n):
            lt=fi/FPS
            out=draw_motion(kind,lt,dur,gt+lt,total)
            if prev is not None and fi<TRANS:
                a2=fi/TRANS
                out=Image.blend(prev,out,a2)
                dd=ImageDraw.Draw(out,'RGBA')
                dd.line((int(WIDTH*a2),0,int(WIDTH*a2),HEIGHT),fill=ORANGE+(255,),width=7)
            vf=av.VideoFrame.from_image(out); vf.pts=round((gt+lt)*FPS); vf.time_base=Fraction(1,FPS)
            for p in vout.encode(vf): vo.mux(p)
            prev=out.copy()
        aparts.append(np.zeros((2,round(n*44100/FPS)),dtype=np.int16))
        gt+=n/FPS
        print(f'anim {idx+1} {kind} {n}f')
        continue
    _,src,st,en,t1,t2,sub=s
    c=av.open(str(src)); vs=c.streams.video[0]
    c.seek(max(0,int(st/float(vs.time_base))),stream=vs,backward=True)
    nf=0
    for fr in c.decode(video=0):
        tt=float(fr.time) if fr.time is not None else -1
        if tt<st: continue
        if tt>=en: break
        zoom=1.0+0.07*(nf/FPS/max(.1,(en-st)))
        por=portrait(fr,zoom)
        out=overlay_clip(por,t1,t2,sub,nf/FPS,en-st,gt+nf/FPS,total,CLIP_ORDER[clip_no])
        if prev is not None and nf<TRANS:
            a2=nf/TRANS
            out=Image.blend(prev,out,a2)
            dd=ImageDraw.Draw(out,'RGBA')
            dd.line((int(WIDTH*a2),0,int(WIDTH*a2),HEIGHT),fill=ORANGE+(255,),width=7)
        vf=av.VideoFrame.from_image(out); vf.pts=round((gt+nf/FPS)*FPS); vf.time_base=Fraction(1,FPS)
        for p in vout.encode(vf): vo.mux(p)
        prev=out.copy()
        nf+=1
    au=c.streams.audio[0]
    c.seek(max(0,int(st/float(au.time_base))),stream=au,backward=True)
    import math as _m
    for pkt in c.demux(au):
        for af in pkt.decode():
            if af.time is None: continue
            at=float(af.time); rate=af.sample_rate or 44100; cnt=af.samples
            lo=max(0,int(_m.ceil((st-at)*rate))); hi=min(cnt,int(_m.floor((en-at)*rate)))
            if hi<=lo: continue
            arr=af.to_ndarray()[:,lo:hi]
            cr=av.AudioFrame.from_ndarray(arr,format=af.format.name,layout=af.layout.name); cr.sample_rate=rate
            for rf in rs.resample(cr): aparts.append(rf.to_ndarray())
            if at+cnt/rate>=en: break
    c.close()
    print(f'clip {idx+1} {nf}f')
    clip_no+=1
    gt+=nf/FPS
for p in vout.encode(): vo.mux(p)
vo.close()
aud=np.concatenate(aparts,axis=1)
with wave.open(str(WAV),'wb') as wf:
    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(44100)
    wf.writeframes(aud.T.astype('<i2',copy=False).tobytes())
ff=imageio_ffmpeg.get_ffmpeg_exe()
import subprocess as sp
sp.run([ff,'-y','-i',str(SILENT),'-i',str(WAV),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','160k','-movflags','+faststart',str(OUT)],check=True,stdout=sp.DEVNULL,stderr=sp.DEVNULL)
print(f'OUTPUT={OUT} {gt:.1f}s')
