#!/usr/bin/env python3
"""Motor de montagem no padrão IESA (vídeos falados 9:16).

Cada vídeo é um arquivo de configuração (ver harley_*.py) com:
  RAW   pasta dos brutos
  A     falas em ordem: (arquivo, entrada, saída[, zoom])  — zoom >1 = punch-in p/ esconder jump cut
  SUBS  legendas: (índice da fala, início, fim no bruto, texto)  — "\n" quebra linha
  B     coberturas sobre a voz: (início na timeline, duração, arquivo, entrada no bruto)
  OUT   nome do arquivo final
"""
import os, subprocess

W, H, FPS = 1080, 1920, 30
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
WORK = f"{REPO}/work"
ASSETS = f"{REPO}/assets/iesa"

# Filtro de cor (aproximação de 4K 20% + Gastronômico 30% + Hasselblad 20%)
GRADE = ("eq=contrast=1.06:saturation=1.12:gamma=0.98,"
         "colorbalance=rs=0.03:gs=0.0:bs=-0.03:rm=0.02:bm=-0.02,"
         "unsharp=5:5:0.45")

# Legenda: IESA Bold (Soho Gothic Pro), branca, sombra preta 16% desfocada
FONT_SIZE = 66
LINE_GAP = 53       # distância entre linhas
SUB_Y = 0.72        # altura da legenda (fração da tela)

# Trilha: "Big Rock" - Kevin MacLeod (incompetech.com), licença CC BY 4.0
MUSIC = f"{WORK}/music/big_rock.mp3"
MUSIC_VOL = 0.22    # bem baixa, por baixo da voz (~ volume 10 no CapCut)


def run(cmd):
    subprocess.run(cmd, check=True)


def ts(x):
    return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"


def render(RAW, A, SUBS, B, OUT, tmp_name):
    tmp = f"{WORK}/tmp_{tmp_name}"
    os.makedirs(tmp, exist_ok=True)
    A = [a if len(a) == 4 else (*a, 1.0) for a in A]
    starts, t = [], 0.0
    for _, s, e, _ in A:
        starts.append(t)
        t += e - s
    total = t

    # Pedaços de vídeo da timeline: fala, a não ser onde há cobertura
    def a_piece(t0, t1):
        out = []
        for i, (f, s, e, z) in enumerate(A):
            a0, a1 = starts[i], starts[i] + (e - s)
            lo, hi = max(t0, a0), min(t1, a1)
            if hi - lo > 1e-3:
                out.append((f, s + lo - a0, hi - lo, z))
        return out

    pieces, cur = [], 0.0
    for bt, bd, bf, bin_ in sorted(B):
        if bt > cur + 1e-3:
            pieces += a_piece(cur, bt)
        pieces.append((bf, bin_, bd, 1.0))
        cur = bt + bd
    if cur < total - 1e-3:
        pieces += a_piece(cur, total)

    parts = []
    for k, (f, s, d, z) in enumerate(pieces):
        out = f"{tmp}/p{k:02d}.mp4"
        zoom = f"crop=iw/{z}:ih/{z}," if z != 1.0 else ""
        vf = (f"{zoom}scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"fps={FPS},format=yuv420p")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.3f}", "-i", f"{RAW}/{f}.MOV",
             "-t", f"{d:.3f}", "-an", "-vf", vf, "-c:v", "libx264", "-preset", "fast",
             "-crf", "16", out])
        parts.append(out)
    with open(f"{tmp}/vlist.txt", "w") as fh:
        fh.writelines(f"file '{p}'\n" for p in parts)
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{tmp}/vlist.txt",
         "-c", "copy", f"{tmp}/video.mp4"])

    # Voz: falas em sequência com micro-fades, limpa e nivelada
    aparts = []
    for k, (f, s, e, _) in enumerate(A):
        out, d = f"{tmp}/a{k}.wav", e - s
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.3f}", "-i", f"{RAW}/{f}.MOV",
             "-t", f"{d:.3f}", "-vn", "-ac", "2", "-ar", "48000",
             "-af", f"afade=t=in:d=0.02,afade=t=out:st={d-0.03:.3f}:d=0.03", out])
        aparts.append(out)
    with open(f"{tmp}/alist.txt", "w") as fh:
        fh.writelines(f"file '{p}'\n" for p in aparts)
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{tmp}/alist.txt",
         "-af", "highpass=f=80,afftdn=nf=-30,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,"
                "loudnorm=I=-14:TP=-1.5:LRA=7", "-ar", "48000", f"{tmp}/voice.wav"])

    # Legendas
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
    Y = int(H * SUB_Y)
    for i, s, e, text in SUBS:
        base = starts[i] - A[i][1]
        st, en = base + s, base + e
        lines = text.split("\n")
        for j, line in enumerate(lines):
            y = round(Y + (j - (len(lines) - 1) / 2) * LINE_GAP)
            ass += f"Dialogue: 0,{ts(st)},{ts(en)},Shd,,0,0,0,,{{\\pos({W//2+3},{y+4})\\blur14}}{line}\n"
            ass += f"Dialogue: 1,{ts(st)},{ts(en)},Txt,,0,0,0,,{{\\pos({W//2},{y})}}{line}\n"
    with open(f"{tmp}/subs.ass", "w") as fh:
        fh.write(ass)

    # Final: cor + legendas + template Ibama + trilha
    out = f"{WORK}/out/{OUT}"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", "-i", f"{tmp}/video.mp4", "-i", f"{tmp}/voice.wav",
         "-loop", "1", "-i", f"{ASSETS}/template_ibama.png", "-i", MUSIC,
         "-filter_complex",
         f"[0:v]{GRADE},subtitles={tmp}/subs.ass:fontsdir={ASSETS}[g];"
         f"[2:v]scale={W}:{H},format=rgba[t];[g][t]overlay=0:0:shortest=1,format=yuv420p[v];"
         f"[3:a]atrim=start=0.45,asetpts=PTS-STARTPTS,aresample=48000,volume={MUSIC_VOL},"
         f"afade=t=out:st={total-1.5:.3f}:d=1.5[m];[1:a][m]amix=inputs=2:duration=first:normalize=0[a]",
         "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])
    print("OK", out, f"{total:.2f}s")
    return out
