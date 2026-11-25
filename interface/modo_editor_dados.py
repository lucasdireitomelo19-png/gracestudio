#!/usr/bin/env python3
"""Gera os dados do Modo Editor (replay de uma edição real) a partir de um projeto já renderizado.
Uso: python3 interface/modo_editor_dados.py projetos/byd_aon.json PASTA_SAIDA
Saída: PASTA/dados_editor.json, PASTA/proxy.mp4 (360x640), PASTA/filme.jpg (tira de quadros)."""
import json, os, re, subprocess, sys, wave
import numpy as np

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
proj = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
tmp = os.path.join(RAIZ, "work", f"tmp_{proj['nome']}")
raw = os.path.join(RAIZ, proj["brutos"])
final = os.path.join(RAIZ, "work", "out", proj["saida"])
nome_curto = proj["brutos"].split("/")[1]
words = json.load(open(os.path.join(RAIZ, "work", nome_curto, "words_medium.json")))

def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))

D = dur(final)
segs, t = [], 0.0
for i, it in enumerate(proj["timeline"]):
    d = dur(f"{tmp}/p{i:02d}.mp4")
    s = {"i": i, "tipo": it["tipo"], "arq": it["arquivo"], "t0": round(t, 3), "t1": round(t + d, 3)}
    if it["tipo"] == "fala":
        s.update(ini=it["ini"], fim=it["fim"], zoom=it.get("zoom", 1.0))
    else:
        s.update(ini=it["ini"], fim=it["ini"] + it["dur"], zoom=1.6)
    segs.append(s); t += d
fim_cortes = t

# transcrição bruta de cada clipe usado, com pausas e trechos cortados
clipes, bruto_total = [], 0.0
for arq in dict.fromkeys(s["arq"] for s in segs if s["tipo"] == "fala"):
    ws = words.get(arq, [])
    keep = [(s["ini"], s["fim"]) for s in segs if s["arq"] == arq and s["tipo"] == "fala"]
    dclip = dur(f"{raw}/{arq}.MOV"); bruto_total += dclip
    toks, prev = [], 0.0
    for a, b, w in ws:
        if a - prev >= 0.3:
            toks.append({"p": round(a - prev, 1)})
        dentro = any(k0 - 0.15 <= a and b <= k1 + 0.25 for k0, k1 in keep)
        toks.append({"w": w, "k": int(dentro), "a": a})
        prev = b
    if dclip - prev >= 0.3:
        toks.append({"p": round(dclip - prev, 1)})
    clipes.append({"arq": arq, "dur": round(dclip, 2), "toks": toks})

# legendas e cartelas tiradas do .ass que foi queimado no vídeo
def ts(x):
    h, m, s = x.split(":"); return int(h) * 3600 + int(m) * 60 + float(s)
legendas, cartelas = [], []
for ln in open(f"{tmp}/text.ass", encoding="utf8"):
    if not ln.startswith("Dialogue:"): continue
    p = ln.rstrip("\n").split(",", 9)
    layer, a, b, est, txt = int(p[0].split()[1]), ts(p[1]), ts(p[2]), p[3], p[9]
    if est == "Reg" and layer == 1:
        ws = [{"w": w, "b": int(bb), "t": round(a + int(ms) / 1000, 2)}
                  for bb, ms, w in re.findall(r"\\b(\d)\\alpha&HFF&\\t\((\d+),[^}]*\}([^{]+?)\s*(?=\{|$)", txt)]
        legendas.append({"a": round(a, 2), "b": round(b, 2), "ws": ws})
    elif est in ("Ttl", "Sub") and layer == 3:
        clean = re.sub(r"\{[^}]*\}", "", txt).replace("\\N", " ")
        if est == "Ttl": cartelas.append({"a": round(a, 2), "b": round(b, 2), "t": clean, "s": ""})
        elif cartelas and abs(cartelas[-1]["a"] - a) < 0.01: cartelas[-1]["s"] = clean

def picos(path, n, ini=0.0, dmax=None):
    with wave.open(path) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
    x = np.abs(x.reshape(-1, ch).mean(1)) / 32768
    tot = dmax or len(x) / sr
    x = x[: int(tot * sr)]
    if len(x) < n: x = np.pad(x, (0, n - len(x)))
    v = np.array([c.max() for c in np.array_split(x, n)])
    return [round(float(q), 3) for q in v / (v.max() or 1)]

N = 600
ondas = {"voz": picos(f"{tmp}/voice.wav", N, dmax=D), "musica": picos(f"{tmp}/music.wav", N, dmax=D),
         "efeitos": picos(f"{tmp}/sfx.wav", N, dmax=D)}

# tira de quadros (1 a cada 0,5 s) e proxy leve para tocar na página
passo = 0.5; nq = int(D / passo)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", final, "-vf", f"fps=1/{passo},scale=54:96,tile={nq}x1", "-frames:v", "1", "-q:v", "7", f"{out}/filme.jpg"], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", final, "-vf", "scale=360:640,fps=30", "-c:v", "libx264", "-preset", "slow", "-b:v", "1100k",
                "-maxrate", "1400k", "-bufsize", "2800k", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", f"{out}/proxy.mp4"], check=True)

M = json.load(open(os.path.join(RAIZ, "studio", "marcas.json")))[proj["marca"]]
dados = {"nome": proj["nome"], "marca": M["nome"], "cor": M["cor"], "dur": round(D, 2), "fim_cortes": round(fim_cortes, 2),
         "bruto_total": round(bruto_total, 1), "segs": segs, "clipes": clipes, "legendas": legendas, "cartelas": cartelas,
         "lut": proj.get("lut"), "trilha": proj.get("musica", M["trilha"]), "drop_item": proj.get("drop"),
         "encerramento": M.get("encerramento"), "ondas": ondas, "passo_filme": passo, "n_quadros": nq,
         "saida": {"res": "1440×2560", "fps": 60, "bitrate": "50 Mbps", "arquivo": proj["saida"]}}
json.dump(dados, open(f"{out}/dados_editor.json", "w"), ensure_ascii=False)
print("ok", len(segs), "planos", len(legendas), "legendas", len(cartelas), "cartelas", D)
