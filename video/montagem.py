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

W, H, FPS = 1440, 2560, 60   # 2K vertical, 60 fps
BITRATE = "50M"              # taxa de bits final
K = W / 1080                  # escala da legenda em relação ao layout original 1080p
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
WORK = f"{REPO}/work"
ASSETS = f"{REPO}/assets/iesa"

# Filtro de cor (aproximação de 4K 20% + Gastronômico 30% + Hasselblad 20%)
GRADE = ("eq=contrast=1.06:saturation=1.12:gamma=0.98,"
         "colorbalance=rs=0.03:gs=0.0:bs=-0.03:rm=0.02:bm=-0.02,"
         "unsharp=5:5:0.45")

# Legenda: IESA Bold (Soho Gothic Pro), branca, sombra preta 16% desfocada
FONT_SIZE = round(66 * K)
LINE_GAP = round(53 * K)   # distância entre linhas
SUB_Y = 0.72        # altura da legenda (fração da tela)

# Trilhas originais por marca (trilhas.py / trilha_rock.py): sem direitos de terceiros
MUSIC = f"{WORK}/music/trilha_original.wav"   # rock (Harley)
MUSIC_LUFS = -30    # trilha nivelada bem baixa, ~16 dB abaixo da voz (~ volume 10 no CapCut)


# Transições
FLARE_PEAK, FLARE_IN, FLARE_OUT = 1.72, 1.45, 2.05   # pico do flash e trecho usado do arquivo (s)
FADE = 0.4                             # esmaecimento preto antes do encerramento da marca


def flares_locucao(cortes_entrada, cortes_saida):
    """Lista de flares: flash branco ao entrar na locução, dourado ao voltar para a pessoa."""
    return ([(t, f"{ASSETS}/flare1.mov") for t in cortes_entrada] +
            [(t, f"{ASSETS}/flare2.mov") for t in cortes_saida])


def run(cmd):
    subprocess.run(cmd, check=True)


def ts(x):
    return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"


def render(RAW, A, SUBS, B, OUT, tmp_name, music=None, music_vol=None, music_start=0.0,
           font="Soho Gothic Pro", bold=1, font_scale=1.0, ending=None, flares=None):
    """ending: vídeo de encerramento da marca, emendado no fim com esmaecimento preto.
    flares: [(tempo_do_corte, arquivo)] — flash rápido nos cortes pessoa falando <-> locução."""
    fsize = round(FONT_SIZE * font_scale)
    music = music or MUSIC
    def src(f):  # "pasta/arquivo" = relativo a work/; senão, da pasta RAW
        return f"{WORK}/{f}.MOV" if "/" in f else f"{RAW}/{f}.MOV"
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
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.3f}", "-i", src(f),
             "-t", f"{d:.3f}", "-an", "-vf", vf, "-c:v", "libx264", "-preset", "fast",
             "-crf", "12", out])
        parts.append(out)
    with open(f"{tmp}/vlist.txt", "w") as fh:
        fh.writelines(f"file '{p}'\n" for p in parts)
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{tmp}/vlist.txt",
         "-c", "copy", f"{tmp}/video.mp4"])

    # Voz: falas em sequência com micro-fades, limpa e nivelada
    aparts = []
    for k, (f, s, e, _) in enumerate(A):
        out, d = f"{tmp}/a{k}.wav", e - s
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.3f}", "-i", src(f),
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
Style: Txt,{font},{fsize},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,{bold},0,0,0,100,100,0,0,1,0,0,5,{round(60*K)},{round(60*K)},0,1
Style: Shd,{font},{fsize},&H29000000,&H29000000,&H29000000,&H00000000,{bold},0,0,0,100,100,0,0,1,0,0,5,{round(60*K)},{round(60*K)},0,1

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
            ass += f"Dialogue: 0,{ts(st)},{ts(en)},Shd,,0,0,0,,{{\\pos({W//2+round(3*K)},{y+round(4*K)})\\blur{round(14*K)}}}{line}\n"
            ass += f"Dialogue: 1,{ts(st)},{ts(en)},Txt,,0,0,0,,{{\\pos({W//2},{y})}}{line}\n"
    with open(f"{tmp}/subs.ass", "w") as fh:
        fh.write(ass)

    # Final: cor + legendas + template Ibama + trilha
    out = f"{WORK}/out/{OUT}"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    inputs = ["-i", f"{tmp}/video.mp4", "-i", f"{tmp}/voice.wav",
              "-loop", "1", "-i", f"{ASSETS}/template_ibama.png", "-i", music]
    if ending:
        inputs += ["-i", ending]                       # entrada 4
    fc = f"[0:v]{GRADE},subtitles={tmp}/subs.ass:fontsdir={ASSETS}[g];"
    # Flares (overlay rápido em modo screen) nos cortes pessoa falando <-> locução
    if flares:
        fc += f"color=black:s={W}x{H}:r={FPS}:d={total:.3f},format=gbrp[fl0];"
        for k, (tc, ffile) in enumerate(flares):
            idx = 4 + (1 if ending else 0) + k
            inputs += ["-i", ffile]
            # pico do flash em FLARE_PEAK s no arquivo → alinhado ao corte tc
            t0 = tc - (FLARE_PEAK - FLARE_IN)
            fc += (f"[{idx}:v]trim=start={FLARE_IN}:end={FLARE_OUT},setpts=PTS-STARTPTS+{t0:.3f}/TB,"
                   f"fps={FPS},scale={W}:{H},format=gbrp[fk{k}];"
                   f"[fl{k}][fk{k}]overlay=0:0:eof_action=pass[fl{k+1}];")
        fc += f"[g]format=gbrp[gr];[gr][fl{len(flares)}]blend=all_mode=screen,format=yuv420p[g2];"
    else:
        fc += "[g]null[g2];"
    fc += (f"[2:v]scale={W}:{H},format=rgba[t];[g2][t]overlay=0:0:shortest=1,format=yuv420p[v];"
           f"[3:a]atrim=start={music_start},asetpts=PTS-STARTPTS,loudnorm=I={MUSIC_LUFS}:TP=-9:LRA=15,aresample=48000,"
           f"afade=t=out:st={total-1.5:.3f}:d=1.5[m];[1:a][m]amix=inputs=2:duration=first:normalize=0[a]")
    if ending:
        # esmaecimento para o preto entre o último plano e o encerramento da marca
        fc += (f";[v]trim=duration={total:.3f},setpts=PTS-STARTPTS,fade=t=out:st={total-FADE:.3f}:d={FADE}[vm];"
               f"[a]atrim=duration={total:.3f},asetpts=PTS-STARTPTS[am];"
               f"[4:v]scale={W}:{H},fps={FPS},format=yuv420p,setsar=1,fade=t=in:st=0:d={FADE}[ve];"
               f"[4:a]aresample=48000,aformat=channel_layouts=stereo[ae];"
               f"[vm][am][ve][ae]concat=n=2:v=1:a=1[vo][ao]")
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc,
         "-map", "[vo]" if ending else "[v]", "-map", "[ao]" if ending else "[a]",
         *([] if ending else ["-t", f"{total:.3f}"]),
         "-c:v", "libx264", "-preset", "medium", "-b:v", BITRATE, "-minrate", BITRATE,
         "-maxrate", BITRATE, "-bufsize", BITRATE, "-x264-params", "nal-hrd=cbr:force-cfr=1",
         "-profile:v", "high", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])
    print("OK", out, f"{total:.2f}s")
    return out
