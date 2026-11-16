#!/usr/bin/env python3
"""Monta o BYD AON (estilo da referência) como projeto FilmCraft editável, com camadas:

  V1  falas + planos fechados dos carros (zoom lento com keyframes) + encerramento Grupo IESA
  V2  flares (modo de mesclagem Tela) nos cortes de/para os carros
  V3–V8  textos animados (fonte IESA Regular): linhas da fala e cartelas dos carros
  V9  template Ibama
  A1  voz (áudio das falas, nivelado por tomada)
  A2  trilha BYD (mais baixa até o "drop" no logo da BYD)
  A3  efeitos sonoros (whoosh, riser, impacto, pop)

Depois exporta: projeto .fcproj, XML do Premiere (FCP7 XML), FCPXML (Final Cut) e um MP4 de conferência.
Uso: python3 filmcraft_byd.py <pasta_saida>
"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from montagem import ajustar_corte, TAIL, FLARE_PEAK, FLARE_IN, FLARE_OUT, WORK, ASSETS
from montagem_pro import posicao_texto, PUSH, dur_of
from rosto import cabeca
import byd_aon as cfg

FC = "/home/user/tools/filmcraft/target/release/filmcraft-cli"
TK = 254_016_000_000            # ticks por segundo no FilmCraft
W, H = 1440, 2560
K = W / 1080
REG, BIG, TTL = round(58 * K), round(120 * K), round(240 * K)
SRC_W, SRC_H = 2160, 3840       # bruto 4K em pé (já girado)
OUT = sys.argv[1] if len(sys.argv) > 1 else f"{WORK}/out/byd_filmcraft"
os.makedirs(OUT, exist_ok=True)
PROJ = f"{OUT}/BYD_AON.fcproj"
SFX = f"{WORK}/sfx"
MUSIC = f"{WORK}/music/trilha_byd.wav"
ENDING = f"{ASSETS}/encerramento_grupo_iesa.mp4"


def run(lines, name):
    path = f"{OUT}/{name}.jsonl"
    with open(path, "w") as fh:
        fh.writelines(json.dumps(l, ensure_ascii=False) + "\n" for l in lines)
    res = [json.loads(x) for x in subprocess.run([FC, "run", path], capture_output=True, text=True).stdout.splitlines()
           if x.startswith("{")]
    bad = [r for r in res if not r.get("ok")]
    if bad:
        raise SystemExit(f"{name}: {bad[0]}")
    return res


def lufs(path, s, d):
    o = subprocess.run(["ffmpeg", "-ss", f"{s}", "-t", f"{d}", "-i", path, "-af", "ebur128", "-vn", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    try:
        return float([l for l in o.splitlines() if l.strip().startswith("I:")][-1].split()[1])
    except (IndexError, ValueError):
        return -24.0


# ---------- 1) plano da edição (mesma lógica do render que foi aprovado) ----------
src = lambda f: f"{cfg.RAW}/{f}.MOV"
items, t = [], 0.0
for k, it in enumerate(cfg.TIMELINE):
    if it[0] == "fala":
        _, f, s, e, z = it
        s2, e2 = ajustar_corte(src(f), s, e)
        if k == len(cfg.TIMELINE) - 1:
            e2 = min(e2 + TAIL, dur_of(src(f)) - 0.05)
        items.append(dict(kind="fala", f=f, s=s2, d=e2 - s2, z=z, t0=t))
    else:
        _, f, s, d, crop = it
        items.append(dict(kind="insert", f=f, s=s, d=d, crop=crop, t0=t))
    t += items[-1]["d"]
total = t
end_d = dur_of(ENDING)

flares, sfx = [], []
for k, it in enumerate(items):
    if it["kind"] != "insert":
        continue
    tin, tout = it["t0"], it["t0"] + it["d"]
    flares.append(tin)
    sfx.append((tin - 0.35, "whoosh.wav", -9))
    if k == 2:
        sfx += [(tin - 1.8, "riser.wav", -12), (tin, "boom.wav", -6)]
    if k + 1 < len(items):
        flares.append(tout)
        sfx.append((tout - 0.25, "whoosh_rev.wav", -13))

# ---------- 2) importa e monta a timeline ----------
files = sorted({src(it["f"]) for it in items}) + [f"{ASSETS}/flare2.mov", f"{ASSETS}/template_ibama.png",
                                                  ENDING, MUSIC] + [f"{SFX}/{n}" for n in
                                                                   ("whoosh.wav", "whoosh_rev.wav", "riser.wav", "boom.wav", "pop.wav")]
L = [{"id": "file.newProject", "params": {"name": "BYD AON"}},
     {"id": "file.import", "params": {"paths": files}},
     {"id": "file.newSequence", "params": {"name": "BYD AON 2K 60fps", "width": W, "height": H, "fps": 60,
                                           "video": 9, "audio": 3}}]
idx = {p: i + 1 for i, p in enumerate(files)}            # ids dos itens importados (ordem da importação)
for it in items:
    L.append({"id": "timeline.place", "params": {"item": idx[src(it["f"])], "track": "V1", "audioTrack": "A1",
              "seconds": round(it["t0"], 4), "insert": False, "sourceIn": {"seconds": round(it["s"], 4)},
              "duration": {"seconds": round(it["d"], 4)}, "audio": it["kind"] == "fala"}})
L.append({"id": "timeline.place", "params": {"item": idx[ENDING], "track": "V1", "seconds": round(total, 4),
          "insert": False, "audio": False}})
for tc in flares:
    L.append({"id": "timeline.place", "params": {"item": idx[f"{ASSETS}/flare2.mov"], "track": "V2",
              "seconds": round(tc - (FLARE_PEAK - FLARE_IN), 4), "insert": False,
              "sourceIn": {"seconds": FLARE_IN}, "duration": {"seconds": FLARE_OUT - FLARE_IN}, "audio": False}})
L.append({"id": "timeline.place", "params": {"item": idx[f"{ASSETS}/template_ibama.png"], "track": "V9", "seconds": 0,
          "insert": False, "duration": {"seconds": round(total, 4)}}})
# trilha: compasso alinhado ao drop
t_drop = items[2]["t0"]
off = (-t_drop) % (4 * 60 / 116)
L.append({"id": "timeline.place", "params": {"item": idx[MUSIC], "track": "A2", "seconds": 0, "insert": False,
          "video": False, "sourceIn": {"seconds": round(off, 4)}, "duration": {"seconds": round(total + end_d, 4)}}})
for tt, n, g in sfx:
    L.append({"id": "timeline.place", "params": {"item": idx[f"{SFX}/{n}"], "track": "A3", "seconds": round(max(0, tt), 4),
              "insert": False, "video": False}})
L += [{"id": "file.saveAs", "params": {"path": PROJ}}, {"id": "sequence.inspect", "params": {}}]
res = run(L, "1_montagem")
seq = res[-1]["result"]

# ids dos clipes por trilha, na ordem do tempo
def clips(kind, name):
    tr = [x for x in seq[kind] if x["name"] == name][0]
    return sorted(tr["items"], key=lambda c: c["start"])
v1, v2, a1 = clips("video", "Video 1"), clips("video", "Video 2"), clips("audio", "Audio 1")
a2, a3, v4 = clips("audio", "Audio 2"), clips("audio", "Audio 3"), clips("video", "Video 9")

# ---------- 3) movimento, mesclagem, volumes e textos ----------
L = [{"id": "file.open", "params": {"path": PROJ}}]
fill = W / SRC_W * 100
for it, c in zip(items, v1):
    cid, d = c["clip"], it["d"]
    if it["kind"] == "fala":
        s0, pos = fill * it["z"], [W / 2, H / 2]
        push = PUSH
    else:
        x0, y0, wf = it["crop"]
        s0 = W / (wf * SRC_W) * 100
        cx = (x0 + wf / 2) * SRC_W
        cy = y0 * SRC_H + wf * SRC_W * 16 / 9 / 2
        k = s0 / 100
        pos = [W / 2 - (cx - SRC_W / 2) * k, H / 2 - (cy - SRC_H / 2) * k]
        push = PUSH * 1.6
    L += [{"id": "effects.setParam", "params": {"clip": cid, "effect": "motion", "param": "position", "value": pos}},
          {"id": "effects.setParam", "params": {"clip": cid, "effect": "motion", "param": "scale",
                                                 "value": round(s0, 3), "time": round(it["t0"] * TK), "keyframe": True}},
          {"id": "effects.setParam", "params": {"clip": cid, "effect": "motion", "param": "scale",
                                                 "value": round(s0 * (1 + push), 3),
                                                 "time": round((it["t0"] + d) * TK) - 1, "keyframe": True}}]
# fade para o preto antes do logo final
last = v1[len(items) - 1]["clip"]
for tt, val in ((total - 0.25, 100), (total - 0.01, 0)):
    L.append({"id": "effects.setParam", "params": {"clip": last, "effect": "opacity", "param": "opacity",
              "value": val, "time": round(tt * TK), "keyframe": True}})
for c in v2:
    L.append({"id": "effects.setParam", "params": {"clip": c["clip"], "effect": "opacity", "param": "blend", "value": "Screen"}})
for c in v4:
    L.append({"id": "effects.setParam", "params": {"clip": c["clip"], "effect": "motion", "param": "scale", "value": fill}})
# voz nivelada por tomada
falas = [it for it in items if it["kind"] == "fala"]
for it, c in zip(falas, a1):
    L.append({"id": "clip.audioGain", "params": {"clips": [c["clip"]], "mode": "set",
              "db": round(max(-15, min(15, -18 - lufs(src(it["f"]), it["s"], it["d"]))), 1)}})
# trilha: -28 dB até o drop, -20 dB depois; fade no fim
mg = round(-21 - lufs(MUSIC, 0, 30), 1)
L.append({"id": "clip.audioGain", "params": {"clips": [a2[0]["clip"]], "mode": "set", "db": mg}})
for tt, v in ((0, -9), (t_drop - 0.05, -9), (t_drop, 0), (total + end_d - 1.8, 0), (total + end_d - 0.02, -60)):
    L.append({"id": "effects.setParam", "params": {"clip": a2[0]["clip"], "effect": "volume", "param": "level",
              "value": v, "time": round(tt * TK), "keyframe": True}})
for (tt, n, g), c in zip(sorted(sfx), a3):
    L.append({"id": "clip.audioGain", "params": {"clips": [c["clip"]], "mode": "set", "db": g}})

# textos: uma camada por linha, entrando com fade + leve subida (destaques maiores, com "pop")
text_ops, pops = [], []
cabs = {}
for c in cfg.CARDS:
    it = items[c["item"]]
    if c["item"] not in cabs:
        cabs[c["item"]] = cabeca(src(it["f"]), it["s"], it["s"] + it["d"], it["z"])
    conv = lambda tf: it["t0"] + (tf - cfg.TIMELINE[c["item"]][2]) - (cfg.TIMELINE[c["item"]][2] - it["s"]) * 0
    conv = lambda tf, it=it, c=c: it["t0"] + (tf - it["s"])
    bloco = sum(round(BIG * 1.02) if any(e for _, _, e in ln) else round(REG * 1.18) for ln in c["lines"])
    y = posicao_texto(cabs[c["item"]], bloco, c["pos"])
    end = it["t0"] + it["d"]
    for ln in c["lines"]:
        emph = any(e for _, _, e in ln)
        size = BIG if emph else REG
        t0 = max(it["t0"], conv(ln[0][1]) - 0.03)
        txt = " ".join(w for w, _, _ in ln)
        x = round(0.07 * W) if c["pos"] == "tl" else W // 2
        base = y + round(size * 0.8)
        text_ops.append(dict(text=txt, t0=t0, t1=end, x=x, y=base, size=size, center=c["pos"] != "tl", emph=emph))
        if emph:
            pops.append(t0)
        y += round(size * 1.02) if emph else round(size * 1.18)
for ti in cfg.TITLES:
    it = items[ti["item"]]
    t0, t1 = it["t0"] + ti["t"], it["t0"] + it["d"]
    fit = min(100, int(100 * 0.86 * W / (len(ti["texto"]) * 0.66 * TTL)))
    size = round(TTL * fit / 100)
    y = round(ti.get("y", 0.16) * H) + round(size * 0.8)
    text_ops.append(dict(text=ti["texto"], t0=t0, t1=t1, x=W // 2, y=y, size=size, center=True, emph=True))
    if ti.get("sub"):
        text_ops.append(dict(text=ti["sub"], t0=t0 + 0.25, t1=t1, x=W // 2, y=y + round(size * 0.55) + round(64 * K),
                             size=round(64 * K), center=True, emph=False))
lanes = []                      # fim do último texto em cada trilha de texto (V3…V8)
for op in sorted(text_ops, key=lambda o: o["t0"]):
    lane = next((i for i, e in enumerate(lanes) if e <= op["t0"] - 0.02), None)
    if lane is None:
        lanes.append(0.0)
        lane = len(lanes) - 1
    if lane > 5:
        raise SystemExit("textos demais sobrepostos")
    lanes[lane] = op["t1"]
    op["track"] = 2 + lane
for op in text_ops:
    L.append({"id": "graphics.newText", "params": {"text": op["text"], "position": [op["x"], op["y"]], "size": op["size"],
              "font": "Soho Gothic Pro", "fontStyle": "Regular", "seconds": round(op["t1"] - op["t0"], 4),
              "track": op["track"], "time": round(op["t0"] * TK), "newClip": True}})
    props = {"shadow": True, "fill_color": "#ffffff"}
    if op["center"]:
        props["align"] = "center"
    L.append({"id": "graphics.set", "params": {"props": props}})
    a, b = round(op["t0"] * TK), round((op["t0"] + (0.18 if op["emph"] else 0.12)) * TK)
    L.append({"id": "graphics.set", "params": {"props": {"opacity": 0, "position": [op["x"], op["y"] + round(30 * K)],
              **({"scale": 125} if op["emph"] else {})}, "time": a, "keyframe": True}})
    L.append({"id": "graphics.set", "params": {"props": {"opacity": 100, "position": [op["x"], op["y"]],
              **({"scale": 100} if op["emph"] else {})}, "time": b, "keyframe": True}})
L += [{"id": "file.save", "params": {}},
      {"id": "file.exportFcp7Xml", "params": {"path": f"{OUT}/BYD_AON_Premiere.xml"}},
      {"id": "file.exportFcpxml", "params": {"path": f"{OUT}/BYD_AON_FinalCut.fcpxml"}},
      {"id": "file.exportFrame", "params": {"path": f"{OUT}/quadro_12s.png", "format": "png", "target": "program",
                                            "time": round(12.5 * TK)}},
      {"id": "file.exportFrame", "params": {"path": f"{OUT}/quadro_carro.png", "format": "png", "target": "program",
                                            "time": round((items[6]["t0"] + 0.6) * TK)}}]
run(L, "2_efeitos_textos")
print("OK", PROJ, f"{total + end_d:.2f}s", len(text_ops), "textos", len(flares), "flares", len(sfx), "efeitos sonoros")
