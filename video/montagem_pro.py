#!/usr/bin/env python3
"""Motor de edição "pro" — estilo da referência BMW X2 (texto animado, cartelas, flares, SFX, drop).

Linha do tempo (TIMELINE), em ordem:
  ("fala",   arquivo, ini, fim, zoom)                — pessoa falando (corte ajustado p/ não cortar fala)
  ("insert", arquivo, ini, dur, (x0, y0, largura))   — plano fechado mudo, recortado do 4K (frações do quadro)

Textos (CARDS): {"item": i, "pos": "tl"|"c", "lines": [[(palavra, t_fonte, destaque), ...], ...], "fim": t_fonte|None}
  - palavras aparecem no tempo em que são faladas; linha com destaque entra grande, em negrito itálico, com "pop".
Cartelas (TITLES): {"item": i, "t": seg_no_item, "texto": "BYD", "sub": "…"}  — título digitado letra a letra.
"""
import os, subprocess, wave
import numpy as np
from scipy.signal import butter, sosfilt
from montagem import (W, H, FPS, BITRATE, K, GRADE, WORK, ASSETS, ajustar_corte, run,
                      FLARE_PEAK, FLARE_IN, FLARE_OUT, TAIL)

SR = 48000
SFX = f"{WORK}/sfx"
PUSH = 0.045          # push-in lento em cada plano (4,5 %)
FADE = 0.25           # fade preto antes do logo final


# ---------- utilidades de áudio ----------
def wav_read(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR),
                          "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32).reshape(-1, 2) / 32768


def wav_write(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def db(g):
    return 10 ** (g / 20)


def dur_of(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip())


# ---------- texto (ASS) ----------
def ts(x):
    x = max(0.0, x)
    return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"


def ass_header(font, font_bold):
    reg, big, title = round(58 * K), round(112 * K), round(240 * K)
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Reg,{font},{reg},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Big,{font_bold},{big},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,1,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Ttl,{font_bold},{title},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,1,0,0,100,100,4,0,1,0,0,8,0,0,0,1
Style: Sub,{font},{round(64 * K)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,2,0,1,0,0,8,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""", reg, big, title


def ass_line(st, en, style, tags, text, layer=1, shadow=True, x=0, y=0, mv=None):
    """Linha com camada de sombra suave (preto 55 %, desfocada) por baixo."""
    out = ""
    pos = (f"\\move({x+round(4*K)},{y+mv+round(5*K)},{x+round(4*K)},{y+round(5*K)},0,200)" if mv
           else f"\\pos({x+round(4*K)},{y+round(5*K)})")
    if shadow:
        out += (f"Dialogue: {layer-1},{ts(st)},{ts(en)},{style},,0,0,0,,"
                f"{{{pos}\\1c&H000000&\\1a&H70&\\blur{round(10*K)}{tags}}}{text}\n")
    pos = f"\\move({x},{y+mv},{x},{y},0,200)" if mv else f"\\pos({x},{y})"
    out += f"Dialogue: {layer},{ts(st)},{ts(en)},{style},,0,0,0,,{{{pos}{tags}}}{text}\n"
    return out


def reveal(words, t0):
    """Texto com cada palavra surgindo (alpha) no seu tempo, relativo ao início da linha."""
    s = ""
    for w, tw in words:
        a = max(0, int((tw - t0) * 1000))
        s += f"{{\\alpha&HFF&\\t({a},{a+110},\\alpha&H00&)}}{w} "
    return s.strip()


# ---------- montagem ----------
def render_pro(RAW, TIMELINE, CARDS, TITLES, OUT, tmp_name, music, font="Soho Gothic Pro",
               font_bold="Soho Gothic Pro", drop_item=None, ending=None, music_lufs=-21.0):
    tmp = f"{WORK}/tmp_{tmp_name}"
    os.makedirs(tmp, exist_ok=True)
    src = lambda f: f"{RAW}/{f}.MOV"

    # 1) ajusta cortes de fala e calcula a linha do tempo
    items, t = [], 0.0
    for k, it in enumerate(TIMELINE):
        if it[0] == "fala":
            _, f, s, e, z = it
            s2, e2 = ajustar_corte(src(f), s, e)
            if k == len(TIMELINE) - 1:      # +1 s no último plano (sorriso final)
                e2 = min(e2 + TAIL, dur_of(src(f)) - 0.05)
            items.append(dict(kind="fala", f=f, s=s2, e=e2, d=e2 - s2, z=z, t0=t, s_orig=s))
        else:
            _, f, s, d, crop = it
            items.append(dict(kind="insert", f=f, s=s, e=s + d, d=d, crop=crop, t0=t))
        t += items[-1]["d"]
    total = t
    cuts = [it["t0"] for it in items[1:]]

    # 2) vídeo: cada plano com push-in lento; inserts recortados do 4K
    parts = []
    for k, it in enumerate(items):
        out = f"{tmp}/p{k:02d}.mp4"
        pre = ""
        if it["kind"] == "insert":
            x0, y0, wf = it["crop"]
            pre = f"crop=w=iw*{wf}:h=iw*{wf}*16/9:x=iw*{x0}:y=ih*{y0},"
            z = 1.0
        else:
            z = it["z"]
        push = PUSH * (1.6 if it["kind"] == "insert" else 1.0)
        vf = (f"{pre}scale=w='{W}*{z}*(1+{push}*t/{it['d']:.3f})':h=-2:eval=frame,"
              f"crop={W}:{H},fps={FPS},format=yuv420p")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{it['s']:.3f}", "-i", src(it["f"]),
             "-t", f"{it['d']:.3f}", "-an", "-vf", vf, "-c:v", "libx264", "-preset", "fast",
             "-crf", "12", out])
        parts.append(out)
    with open(f"{tmp}/vlist.txt", "w") as fh:
        fh.writelines(f"file '{p}'\n" for p in parts)
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{tmp}/vlist.txt",
         "-c", "copy", f"{tmp}/video.mp4"])

    # 3) voz: falas niveladas; inserts = silêncio
    voice = np.zeros((int((total + 6) * SR), 2), np.float32)
    for it in items:
        if it["kind"] != "fala":
            continue
        seg = f"{tmp}/v_{it['f']}_{it['s']:.2f}.wav"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{it['s']:.3f}", "-i", src(it["f"]),
             "-t", f"{it['d']:.3f}", "-vn", "-ac", "2", "-ar", str(SR),
             "-af", f"highpass=f=80,afftdn=nf=-30,loudnorm=I=-16:TP=-2:LRA=7,"
                    f"afade=t=in:d=0.02,afade=t=out:st={it['d']-0.04:.3f}:d=0.04", seg])
        x = wav_read(seg)
        a = int(it["t0"] * SR)
        voice[a:a + len(x)] += x[: len(voice) - a]

    # 4) efeitos sonoros e flares nos cortes de/para inserts
    sfx_ev, flares = [], []
    ins_idx = [k for k, it in enumerate(items) if it["kind"] == "insert"]
    for k in ins_idx:
        tin = items[k]["t0"]
        tout = tin + items[k]["d"]
        flares.append(tin)
        sfx_ev.append((tin - 0.35, "whoosh.wav", -9))
        if k == drop_item:
            sfx_ev.append((tin - 1.8, "riser.wav", -12))
            sfx_ev.append((tin, "boom.wav", -6))
        if k + 1 < len(items):
            flares.append(tout)
            sfx_ev.append((tout - 0.25, "whoosh_rev.wav", -13))
    # pop nas linhas de destaque e tick nas letras das cartelas
    text_ev = []
    for c in CARDS:
        it = items[c["item"]]
        for line in c["lines"]:
            if any(e for _, _, e in line):
                tl = it["t0"] + (line[0][1] - it["s"])
                text_ev.append(tl)
                sfx_ev.append((tl, "pop.wav", -20))
    for ti in TITLES:
        it = items[ti["item"]]
        for j in range(len(ti["texto"])):
            sfx_ev.append((it["t0"] + ti["t"] + 0.12 + j * 0.07, "tick.wav", -22))
    sfx_bus = np.zeros_like(voice)
    cache = {}
    for tt, f, g in sfx_ev:
        if f not in cache:
            cache[f] = wav_read(f"{SFX}/{f}")
        x = cache[f] * db(g)
        a = max(0, int(tt * SR))
        n = min(len(x), len(sfx_bus) - a)
        sfx_bus[a:a + n] += x[:n]

    # 5) música: filtrada e baixa até o "drop", cheia depois; downbeat alinhado ao drop
    ed = dur_of(ending) if ending else 0.0
    full = total + ed
    mus = wav_read(music)
    t_drop = items[drop_item]["t0"] if drop_item is not None else 0.0
    bpm_bar = 4 * 60 / 116
    off = (-t_drop) % bpm_bar
    a = int(off * SR)
    mus = mus[a: a + int(full * SR) + SR]
    nd = int(t_drop * SR)
    if nd > 0:
        intro = sosfilt(butter(2, 380, "low", fs=SR, output="sos"), mus[:nd], axis=0) * db(-4)
        xf = int(0.08 * SR)
        mus = mus.copy()
        mus[:nd] = intro
        mus[nd - xf:nd] *= np.linspace(1, 0.6, xf)[:, None]
    nf = int(1.8 * SR)
    end = int(full * SR)
    mus = mus[:end]
    mus[-nf:] *= np.linspace(1, 0, nf)[:, None]
    wav_write(f"{tmp}/music_raw.wav", mus)
    run(["ffmpeg", "-v", "error", "-y", "-i", f"{tmp}/music_raw.wav", "-af",
         f"loudnorm=I={music_lufs}:TP=-3:LRA=20", "-ar", str(SR), f"{tmp}/music.wav"])
    wav_write(f"{tmp}/voice.wav", voice[:end])
    wav_write(f"{tmp}/sfx.wav", sfx_bus[:end])

    # 6) textos animados + cartelas
    hdr, reg, big, ttl = ass_header(font, font_bold)
    ass = hdr
    shadow_x = 0
    for ci, c in enumerate(CARDS):
        it = items[c["item"]]
        conv = lambda tf: it["t0"] + (tf - it["s"])
        st = conv(c["lines"][0][0][1]) - 0.05
        if c.get("fim") is not None:
            en = conv(c["fim"])
        else:
            nxt = [conv2 for conv2 in []]
            en = it["t0"] + it["d"]
        en = min(en, total)
        if c["pos"] == "tl":
            x, y = round(0.07 * W), round(0.13 * H)
            an = "\\an7"
        else:
            x, y = W // 2, round(0.60 * H)
            an = "\\an8"
        for line in c["lines"]:
            words = [(w, conv(tw)) for w, tw, _ in line]
            emph = any(e for _, _, e in line)
            l0 = words[0][1]
            if emph:
                txt = " ".join(w for w, _ in words)
                tags = (f"{an}\\fscx125\\fscy125\\t(0,180,\\fscx100\\fscy100)"
                        f"\\alpha&HFF&\\t(0,90,\\alpha&H00&)\\blur{round(6*K)}\\t(0,200,\\blur0)")
                ass += ass_line(l0 - 0.02, en, "Big", tags, txt, x=x, y=y, mv=round(40 * K))
                y += round(big * 1.02)
            else:
                ass += ass_line(st, en, "Reg", an, reveal(words, st), x=x, y=y)
                y += round(reg * 1.18)
    for ti in TITLES:
        it = items[ti["item"]]
        t0 = it["t0"] + ti["t"]
        t1 = it["t0"] + it["d"]
        txt = ti["texto"]
        letters = "".join(f"{{\\alpha&HFF&\\t({120+j*70},{170+j*70},\\alpha&H00&)}}{ch}"
                          for j, ch in enumerate(txt))
        y = round(ti.get("y", 0.16) * H)
        tags = "\\an8\\fscx105\\fscy105\\t(0,800,\\fscx100\\fscy100)"
        ass += ass_line(t0, t1, "Ttl", tags, letters, x=W // 2, y=y, layer=3)
        if ti.get("sub"):
            ts_ = 0.12 + len(txt) * 0.07 + 0.1
            ass += ass_line(t0, t1, "Sub", f"\\an8\\alpha&HFF&\\t({int(ts_*1000)},{int(ts_*1000)+200},\\alpha&H00&)",
                            ti["sub"], x=W // 2, y=y + round(ttl * 1.02), layer=3)
    with open(f"{tmp}/text.ass", "w") as fh:
        fh.write(ass)

    # 7) composição final: cor + flares + texto + template Ibama + logo final; mix de áudio
    inputs = ["-i", f"{tmp}/video.mp4", "-i", f"{tmp}/voice.wav", "-i", f"{tmp}/music.wav",
              "-i", f"{tmp}/sfx.wav", "-loop", "1", "-i", f"{ASSETS}/template_ibama.png"]
    if ending:
        inputs += ["-i", ending]                        # 5
    fc = f"[0:v]{GRADE},format=gbrp[g0];"
    fc += f"color=black:s={W}x{H}:r={FPS}:d={total:.3f},format=gbrp[fl0];"
    for k, tc in enumerate(flares):
        idx = 5 + (1 if ending else 0) + k
        inputs += ["-i", f"{ASSETS}/flare2.mov"]
        t0 = tc - (FLARE_PEAK - FLARE_IN)
        fc += (f"[{idx}:v]trim=start={FLARE_IN}:end={FLARE_OUT},setpts=PTS-STARTPTS+{t0:.3f}/TB,"
               f"fps={FPS},scale={W}:{H},format=gbrp[fk{k}];[fl{k}][fk{k}]overlay=0:0:eof_action=pass[fl{k+1}];")
    fc += (f"[g0][fl{len(flares)}]blend=all_mode=screen,format=yuv420p,"
           f"subtitles={tmp}/text.ass:fontsdir={ASSETS}[g1];"
           f"[4:v]scale={W}:{H},format=rgba[tp];[g1][tp]overlay=0:0:shortest=1,format=yuv420p[v];")
    if ending:
        fc += (f"[v]trim=duration={total:.3f},setpts=PTS-STARTPTS,fade=t=out:st={total-FADE:.3f}:d={FADE}[vm];"
               f"[5:v]scale={W}:{H},fps={FPS},format=yuv420p,setsar=1[ve];[vm][ve]concat=n=2:v=1:a=0[vo];")
    else:
        fc += "[v]null[vo];"
    fc += ("[1:a]asplit=2[vo1][vo2];"
           "[2:a][vo1]sidechaincompress=threshold=0.04:ratio=5:attack=15:release=350:makeup=1[md];"
           "[vo2][md][3:a]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.95[ao]")
    out = f"{WORK}/out/{OUT}"
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[vo]", "-map", "[ao]",
         "-t", f"{full:.3f}", "-c:v", "libx264", "-preset", "medium", "-b:v", BITRATE, "-minrate", BITRATE,
         "-maxrate", BITRATE, "-bufsize", BITRATE, "-x264-params", "nal-hrd=cbr:force-cfr=1",
         "-profile:v", "high", "-r", str(FPS), "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", out])
    print("OK", out, f"{full:.2f}s")
    return items
