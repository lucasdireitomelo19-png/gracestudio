#!/usr/bin/env python3
"""Monta o vídeo Harley Black November (v1) a partir dos brutos em work/raw."""
import json, os, subprocess

W, H, FPS = 1080, 1920, 30
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../work"))
RAW = f"{ROOT}/raw"
TMP = f"{ROOT}/tmp"
ASSETS = os.path.abspath(f"{ROOT}/../assets/iesa")
os.makedirs(TMP, exist_ok=True)

# Falas (A-roll): arquivo, entrada, saída — respiros já cortados
A = [
    ("IMG_9181", 1.95, 6.00),
    ("IMG_9182", 1.75, 4.82),
    ("IMG_9183", 13.20, 16.50),  # 2ª tomada (a 1ª tinha "vamos de novo")
    ("IMG_9184", 1.58, 9.98),
    ("IMG_9185", 2.02, 6.26),
    ("IMG_9186", 1.80, 3.62),
]

# Legendas: (índice da fala, início, fim no bruto, texto)
SUBS = [
    (0, 1.95, 3.30, "A Black November"),
    (0, 3.30, 4.30, "da IESA Harley-Davidson"),
    (0, 4.30, 6.00, "chegou com uma\noportunidade imperdível."),
    (1, 1.75, 2.70, "Conquistar uma Harley"),
    (1, 2.70, 4.82, "é viver a liberdade\ndo seu jeito."),
    (2, 13.20, 14.80, "E agora você pode escolher"),
    (2, 14.80, 16.50, "como quer\nconquistar a sua."),
    (3, 1.58, 2.60, "Na compra à vista,"),
    (3, 2.60, 4.80, "aproveite o bônus\nde até R$ 23 mil,"),
    (3, 4.80, 7.60, "uma oportunidade\npor tempo limitado"),
    (3, 7.60, 9.98, "para tirar o sonho de ter\numa Harley da garagem."),
    (4, 2.02, 2.80, "Mas atenção,"),
    (4, 2.80, 5.30, "são as últimas\nunidades de 2026."),
    (4, 5.30, 6.26, "Vem aproveitar!"),
    (5, 1.80, 3.62, "Grupo IESA.\nVamos juntos!"),
]

# Coberturas (B-roll): (índice da fala, segundos dentro da fala, duração, arquivo, entrada no bruto)
B = [
    (1, 1.00, 1.00, "IMG_9189", 0.6),
    (1, 2.00, 1.07, "IMG_9197", 0.8),
    (3, 2.30, 1.00, "IMG_9191", 1.2),
    (3, 3.30, 1.00, "IMG_9193", 1.5),
    (3, 4.30, 1.00, "IMG_9194", 1.5),
    (3, 5.30, 1.00, "IMG_9187", 0.8),
    (3, 6.30, 1.00, "IMG_9198", 1.2),
    (3, 7.30, 0.90, "IMG_9199", 2.0),
]

# Filtro de cor (aproximação de 4K 20% + Gastronômico 30% + Hasselblad 20%)
GRADE = ("eq=contrast=1.06:saturation=1.12:gamma=0.98,"
         "colorbalance=rs=0.03:gs=0.0:bs=-0.03:rm=0.02:bm=-0.02,"
         "unsharp=5:5:0.45")


def run(cmd):
    subprocess.run(cmd, check=True)


def a_start(i):
    return sum(o - s for _, s, o in A[:i])


total = a_start(len(A))

# Lista de pedaços de vídeo: (arquivo, entrada, duração)
pieces = []
for i, (f, s, e) in enumerate(A):
    d = e - s
    cuts = sorted([b for b in B if b[0] == i], key=lambda b: b[1])
    t = 0.0
    for _, bt, bd, bf, bin_ in cuts:
        if bt > t:
            pieces.append((f, s + t, bt - t))
        pieces.append((bf, bin_, bd))
        t = bt + bd
    if t < d - 1e-3:
        pieces.append((f, s + t, d - t))

vf_base = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
           f"fps={FPS},format=yuv420p")
parts = []
for k, (f, s, d) in enumerate(pieces):
    out = f"{TMP}/p{k:02d}.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.3f}", "-i", f"{RAW}/{f}.MOV",
         "-t", f"{d:.3f}", "-an", "-vf", vf_base, "-c:v", "libx264", "-preset", "fast",
         "-crf", "16", f"{out}"])
    parts.append(out)

with open(f"{TMP}/vlist.txt", "w") as fh:
    fh.writelines(f"file '{p}'\n" for p in parts)
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{TMP}/vlist.txt",
     "-c", "copy", f"{TMP}/video.mp4"])

# Áudio: falas em sequência, com micro-fades para não estalar
aparts = []
for k, (f, s, e) in enumerate(A):
    out = f"{TMP}/a{k}.wav"
    d = e - s
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.3f}", "-i", f"{RAW}/{f}.MOV", "-t", f"{d:.3f}",
         "-vn", "-ac", "2", "-ar", "48000",
         "-af", f"afade=t=in:d=0.02,afade=t=out:st={d-0.03:.3f}:d=0.03", out])
    aparts.append(out)
with open(f"{TMP}/alist.txt", "w") as fh:
    fh.writelines(f"file '{p}'\n" for p in aparts)
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{TMP}/alist.txt",
     "-af", "highpass=f=80,afftdn=nf=-30,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,"
            "loudnorm=I=-14:TP=-1.5:LRA=7", "-ar", "48000", f"{TMP}/voice.wav"])

# Legendas ASS: texto branco + sombra preta 16% desfocada
def ts(x):
    h = int(x // 3600); m = int(x % 3600 // 60); sec = x % 60
    return f"{h}:{m:02d}:{sec:05.2f}"

FONT_SIZE = 66
ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Txt,Soho Gothic Pro,{FONT_SIZE},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,0,0,5,60,60,0,1
Style: Shd,Soho Gothic Pro,{FONT_SIZE},&H29000000,&H29000000,&H29000000,&H00000000,1,0,0,0,100,100,0,0,1,0,0,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
Y = int(H * 0.72)
for i, s, e, text in SUBS:
    base = a_start(i) - A[i][1]
    st, en = base + s, base + e
    t = text.replace("\n", "\\N")
    ass += f"Dialogue: 0,{ts(st)},{ts(en)},Shd,,0,0,0,,{{\\pos({W//2+3},{Y+4})\\blur14}}{t}\n"
    ass += f"Dialogue: 1,{ts(st)},{ts(en)},Txt,,0,0,0,,{{\\pos({W//2},{Y})}}{t}\n"
with open(f"{TMP}/subs.ass", "w") as fh:
    fh.write(ass)

# Final: cor + legendas + template Ibama
out = f"{ROOT}/out/harley_black_november_v1.mp4"
os.makedirs(os.path.dirname(out), exist_ok=True)
run(["ffmpeg", "-v", "error", "-y", "-i", f"{TMP}/video.mp4", "-i", f"{TMP}/voice.wav",
     "-loop", "1", "-i", f"{ASSETS}/template_ibama.png",
     "-filter_complex",
     f"[0:v]{GRADE},subtitles={TMP}/subs.ass:fontsdir={ASSETS}[g];"
     f"[2:v]scale={W}:{H},format=rgba[t];[g][t]overlay=0:0:shortest=1,format=yuv420p[v]",
     "-map", "[v]", "-map", "1:a", "-t", f"{total:.3f}",
     "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high",
     "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])
print("OK", out, f"{total:.2f}s")
