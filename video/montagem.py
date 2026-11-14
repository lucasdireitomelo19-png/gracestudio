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
import numpy as np

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
TAIL = 1.0                             # segundo extra no fim do último plano (sorriso final)
FADE = 0.4                            # esmaecimento preto antes do encerramento da marca


def flares_locucao(cortes_entrada, cortes_saida):
    """Lista de flares: flash dourado ao entrar na locução e ao voltar para a pessoa (como a referência)."""
    return ([(t, f"{ASSETS}/flare2.mov") for t in cortes_entrada] +
            [(t, f"{ASSETS}/flare2.mov") for t in cortes_saida])


_audio_cache = {}


def _rms_db(path):
    """Envelope de volume (dBFS) em janelas de 10 ms do áudio do arquivo."""
    if path not in _audio_cache:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", "16000",
                              "-f", "s16le", "-"], capture_output=True).stdout
        x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
        n = len(x) // 160
        r = np.sqrt((x[: n * 160].reshape(n, 160) ** 2).mean(1)) + 1e-9
        _audio_cache[path] = 20 * np.log10(r)
    return _audio_cache[path]


def ajustar_corte(path, s, e, max_fim=0.5, max_ini=0.2, quieto_ms=150, folga=0.20):
    """Estica o fim do corte até a última palavra terminar (e o início até a primeira começar).
    Fala = acima do piso de ruído + 5 dB (mínimo -52 dBFS); folga de 0,2 s após a última palavra."""
    db = _rms_db(path)
    piso = max(-52.0, float(np.percentile(db, 10)) + 5)
    n = len(db)
    q = quieto_ms // 10
    # fim: anda para frente até achar `quieto_ms` seguidos abaixo do piso
    i, run_q, fim = int(e * 100), 0, None
    lim = min(n, int((e + max_fim) * 100))
    while i < lim:
        run_q = run_q + 1 if db[i] < piso else 0
        if run_q >= q:
            fim = (i - q + 1) / 100 + folga
            break
        i += 1
    novo_e = e if fim is None and int(e * 100) >= n else (fim if fim is not None else e + max_fim)
    novo_e = min(max(e, novo_e), n / 100 - 0.02)
    # início: anda para trás enquanto ainda há fala antes do ponto marcado
    j, run_q, ini = int(s * 100) - 1, 0, None
    lim0 = max(0, int((s - max_ini) * 100))
    while j >= lim0:
        run_q = run_q + 1 if db[j] < piso else 0
        if run_q >= q // 2:
            ini = (j + q // 2) / 100 - 0.04
            break
        j -= 1
    novo_s = min(s, ini if ini is not None else s - max_ini)
    return max(0.0, novo_s), novo_e


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
    # Entradas de A: (arquivo, ini, fim[, zoom[, "trava"]]) — "trava" = não ajustar o corte automaticamente
    locked = [len(a) == 5 and a[4] == "trava" for a in A]
    A = [(a[0], a[1], a[2], a[3] if len(a) >= 4 else 1.0) for a in A]
    # Não cortar fala: estica o início/fim de cada corte até a fala realmente começar/terminar
    A_old = list(A)
    A = [(f, *ajustar_corte(src(f), s, e), z) if not lk else (f, s, e, z)
         for (f, s, e, z), lk in zip(A, locked)]
    SUBS = [(i, (A[i][1] if abs(s - A_old[i][1]) < 0.02 else s),
             (A[i][2] if abs(e - A_old[i][2]) < 0.02 else e), txt) for i, s, e, txt in SUBS]
    # +1s no último plano: não corta a pessoa terminando de falar / sorrindo
    f_last, s_last, e_last, z_last = A[-1]
    dur_last = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src(f_last)],
        capture_output=True, text=True).stdout.strip() or e_last)
    e_new = min(e_last + TAIL, dur_last - 0.05)
    A[-1] = (f_last, s_last, max(e_last, e_new), z_last)
    SUBS = [(i, s, (A[-1][2] if (i == len(A) - 1 and abs(e - e_last) < 0.05) else e), txt)
            for i, s, e, txt in SUBS]
    starts, t = [], 0.0
    for _, s, e, _ in A:
        starts.append(t)
        t += e - s
    total = t

    # Coberturas e flares vêm nos tempos dos cortes originais → reposiciona nos cortes ajustados
    old_starts, t = [], 0.0
    for _, s, e, _ in A_old:
        old_starts.append(t)
        t += e - s
    old_durs = [e - s for _, s, e, _ in A_old]
    new_durs = [e - s for _, s, e, _ in A]

    def remap(tt):
        for i in range(len(A_old)):
            a0, d0 = old_starts[i], old_durs[i]
            if a0 - 1e-6 <= tt < a0 + d0 - 1e-6 or i == len(A_old) - 1:
                return starts[i] + (tt - a0) * new_durs[i] / d0
        return tt

    B = [(remap(bt), remap(bt + bd) - remap(bt), bf, bin_) for bt, bd, bf, bin_ in B]
    if flares:
        flares = [(remap(tc), ff) for tc, ff in flares]

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
        # nivela cada tomada (gravações em aparelhos diferentes têm volumes diferentes)
        lu = subprocess.run(["ffmpeg", "-i", out, "-af", "ebur128", "-f", "null", "-"],
                            capture_output=True, text=True).stderr
        try:
            i_lufs = float([l for l in lu.splitlines() if l.strip().startswith("I:")][-1].split()[1])
            gain = max(-15.0, min(15.0, -24.0 - i_lufs))
        except (IndexError, ValueError):
            gain = 0.0
        if abs(gain) > 1.0:
            lv = out[:-4] + "_lv.wav"
            run(["ffmpeg", "-v", "error", "-y", "-i", out, "-af", f"volume={gain:.1f}dB,alimiter=limit=0.95", lv])
            os.replace(lv, out)
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
    # duração total, incluindo o encerramento da marca (a música continua por baixo do logo)
    ed = 0.0
    if ending:
        ed = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "csv=p=0", ending], capture_output=True, text=True).stdout.strip())
    full = total + ed
    fc += (f"[2:v]scale={W}:{H},format=rgba[t];[g2][t]overlay=0:0:shortest=1,format=yuv420p[v];"
           f"[3:a]atrim=start={music_start},asetpts=PTS-STARTPTS,loudnorm=I={MUSIC_LUFS}:TP=-9:LRA=15,aresample=48000,"
           f"aformat=channel_layouts=stereo,apad,atrim=duration={full:.3f},"
           f"afade=t=out:st={full-1.5:.3f}:d=1.5[m];"
           f"[1:a]aformat=channel_layouts=stereo,apad,atrim=duration={full:.3f}[vp];")
    if ending:
        dms = int(round(total * 1000))
        # esmaecimento para o preto entre o último plano e o encerramento da marca
        fc += (f"[v]trim=duration={total:.3f},setpts=PTS-STARTPTS,fade=t=out:st={total-FADE:.3f}:d={FADE}[vm];"
               f"[4:v]scale={W}:{H},fps={FPS},format=yuv420p,setsar=1,fade=t=in:st=0:d={FADE}[ve];"
               f"[vm][ve]concat=n=2:v=1:a=0[vo];"
               f"[4:a]aresample=48000,aformat=channel_layouts=stereo,adelay={dms}|{dms},apad,"
               f"atrim=duration={full:.3f}[ea];"
               f"[vp][ea][m]amix=inputs=3:duration=first:normalize=0[ao]")
    else:
        fc += "[vp][m]amix=inputs=2:duration=first:normalize=0[a]"
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc,
         "-map", "[vo]" if ending else "[v]", "-map", "[ao]" if ending else "[a]",
         "-t", f"{full:.3f}",
         "-c:v", "libx264", "-preset", "medium", "-b:v", BITRATE, "-minrate", BITRATE,
         "-maxrate", BITRATE, "-bufsize", BITRATE, "-x264-params", "nal-hrd=cbr:force-cfr=1",
         "-profile:v", "high", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])
    print("OK", out, f"{total:.2f}s")
    return out
