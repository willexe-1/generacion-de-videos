# Generación de videos

Repo de trabajo para corrección de color y edición de video vertical estilo TikTok.
Proyecto inicial: unboxing de Lenovo Slim 3 (Ryzen 7 7730HS), de 11 clips de WhatsApp a un solo video vertical con subtítulos, música y gráficos animados.

## Estructura

```text
D:\generacion de videos\
  README.md            <- este archivo
  skills\              <- skills utilizadas (referencia, formato skills.sh)
    davinci-resolve-color-grade-webcam\
    video-color-grading\
    faster-whisper\
    caption-animation\
    hyperframes-animation\
    remotion-motion-graphics\
    technical-video-script\
  tools\
    requirements.txt   <- dependencias Python (pip install -r tools/requirements.txt)
  scripts\             <- pipeline del proyecto unboxing (Python 3.13, Windows)
    make_unboxing_v7.py      <- render del video: montaje + gráficos + subtítulos quemados
    build_v7_audio.py        <- mezcla: voz original + música generada + SFX
    build_v7_srt.py          <- subtítulos laterales .srt desde el transcript
    transcribe_fw.py         <- transcripción base (faster-whisper small, es, word timestamps)
    transcribe_v7.py         <- re-transcripción de segmentos dudosos (faster-whisper medium)
    transcribe_v7b.py        <- cola de frase de encendido (181-190 s)
    transcribe_precise.py    <- primera pasada con Vosk (rápida, menos precisa)
    build_transcript_v7.py   <- transcript final corregido con validación del autor
    validate_audio.py        <- verifica silencio (clip 3) y busca palabras clave (65 W)
  docs\                <- (notas futuras del proyecto)
```

## Herramientas externas

- **DaVinci Resolve 20** — corrección de color primaria + curvas Matiz vs. Matiz, proyecto `CAMARA - CORRECCION DE COLOR`.
- **ffmpeg** (vía `imageio-ffmpeg`) — extracción de segmentos, mux final.
- **Vosk `vosk-model-small-es-0.42`** — primera transcripción rápida y búsqueda de palabras (“sesenta y cinco” en 138,5 s).
- **faster-whisper `small`/`medium` (CPU int8)** — transcript literal con timestamps por palabra.

## Pipeline del video (v1 → v7)

1. Selección de 11 fragmentos representativos (se descartó 1 duplicado idéntico por hash).
2. Corrección base: exposición, contraste, dominantes magenta, curva Matiz vs. Matiz para la vegetación.
3. Montaje vertical 720×1280 @ 30 fps con rótulos y tarjetas animadas (6 inserts a pantalla completa).
4. Transiciones con fundido 0,4 s + barrido naranja; pseudo-3D (cubos isométricos, sombras, barridos de luz).
5. Transcripción literal ES + subtítulos karaoke estilo Hormozi (sin efecto de caída) + tarjetas por palabra clave (65 W, Ryzen 7 7730HS, pantalla, teclado…).
6. Mezcla: voz original al frente, cama musical electrónica con ducking, whoosh en transiciones y pops en tarjetas. Archivo `.srt` lateral.

## Uso rápido

```powershell
pip install -r tools/requirements.txt
python scripts/transcribe_fw.py      # 1. transcribir
python scripts/build_transcript_v7.py # 2. corregir con el autor (editar script)
python scripts/make_unboxing_v7.py    # 3. renderizar video
python scripts/build_v7_audio.py      # 4. mezclar audio
# 5. mux final con ffmpeg (ver scripts)
```

> Los scripts llevan rutas del proyecto original (`C:\Users\USER\Videos\camara\...`).
> Adáptalas a tu máquina antes de correrlos.
