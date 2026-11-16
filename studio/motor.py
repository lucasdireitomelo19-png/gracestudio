#!/usr/bin/env python3
"""Grace Studio — motor de edição a partir de um arquivo de projeto JSON.

Uso:
  python3 -m studio.motor render  projeto.json        renderiza o vídeo final (2K, 60 fps, 50 Mbps)
  python3 -m studio.motor biblioteca                  lista LUTs, filtros, fontes, estilos de texto, widgets e marcas

Projeto (exemplo em projetos/byd_aon.json):
{
  "nome": "byd_aon", "marca": "byd", "brutos": "work/byd/raw", "saida": "byd_aon_2k60.mp4",
  "estilo_texto": "referencia",                       # opcional (padrão da marca)
  "lut": {"id": "auto_showroom_limpo", "intensidade": 40},   # opcional; null = cor original
  "filtros": [["nitidez", 20], ["granulado", 10]],    # opcional
  "musica": "trilha_byd.wav", "drop": 2,              # opcional
  "timeline": [{"tipo": "fala", "arquivo": "C745", "ini": 1.55, "fim": 4.55, "zoom": 1.0},
               {"tipo": "insert", "arquivo": "C755", "ini": 0.3, "dur": 1.2, "recorte": [0.12, 0.03, 0.42]}],
  "textos":   [{"item": 0, "pos": "tl", "linhas": [[["Sabe", 1.60, 0], ["100", 2.86, 1]]]}],
  "cartelas": [{"item": 2, "t": 0.05, "texto": "BYD", "sub": "…", "y": 0.62}],
  "widgets":  [{"tipo": "etiqueta_preco", "item": 13, "t": 0.5, "dur": 3, "params": {"preco": "R$ 156.990"}}]
}
"""
import json, os, sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(RAIZ, "video"))
sys.path.insert(0, RAIZ)
WORK = os.path.join(RAIZ, "work")
ASSETS = os.path.join(RAIZ, "assets", "iesa")
MARCAS = json.load(open(os.path.join(RAIZ, "studio", "marcas.json")))


def _abs(p, base):
    return p if os.path.isabs(p) else os.path.join(base, p)


def render(proj_path):
    from montagem_pro import render_pro
    from studio.filtros import cadeia
    P = json.load(open(proj_path))
    m = MARCAS[P["marca"]]
    raw = _abs(P["brutos"], RAIZ)
    timeline = []
    for it in P["timeline"]:
        if it["tipo"] == "fala":
            timeline.append(("fala", it["arquivo"], it["ini"], it["fim"], it.get("zoom", 1.0)))
        else:
            timeline.append(("insert", it["arquivo"], it["ini"], it["dur"], tuple(it["recorte"])))
    cards = [{"item": c["item"], "pos": c.get("pos", "tl"),
              "lines": [[(w, t, b) for w, t, b in ln] for ln in c["linhas"]]} for c in P.get("textos", [])]
    titles = P.get("cartelas", [])
    passos = []
    if P.get("lut", m.get("lut")):
        l = P.get("lut", m.get("lut"))
        passos.append((f"lut:{l['id']}", l.get("intensidade", 100)))
    passos += [tuple(f) for f in P.get("filtros", [])]
    filtros = cadeia(passos) if passos else None
    musica = _abs(P.get("musica", m["trilha"]), os.path.join(WORK, "music"))
    enc = P.get("encerramento", m.get("encerramento"))
    ending = _abs(enc, ASSETS) if enc else None
    return render_pro(raw, timeline, cards, titles, P.get("saida", f"{P['nome']}_2k60.mp4"), P["nome"], musica,
                      font=m["fonte"], font_bold=m["fonte_bold"], drop_item=P.get("drop"), ending=ending,
                      cor=False, reaproveitar=P.get("reaproveitar", True),
                      estilo_texto=P.get("estilo_texto", m.get("estilo_texto", "referencia")),
                      cor_marca=P.get("cor", m["cor"]), widgets=P.get("widgets", []), filtros=filtros)


def biblioteca():
    from studio.filtros import FILTROS
    from studio.estilos_texto import ESTILOS
    from studio.widgets import WIDGETS
    luts = json.load(open(os.path.join(WORK, "biblioteca", "luts", "catalogo.json")))
    fontes = json.load(open(os.path.join(WORK, "biblioteca", "fontes", "catalogo.json")))
    print(f"LUTs ({len(luts)}):", ", ".join(l["id"] for l in luts))
    print(f"\nFiltros ({len(FILTROS)}):", ", ".join(FILTROS))
    print(f"\nFontes ({len(fontes)} famílias):", ", ".join(f["familia"] for f in fontes))
    print(f"\nEstilos de texto ({len(ESTILOS)}):", ", ".join(ESTILOS))
    print(f"\nWidgets ({len(WIDGETS)}):", ", ".join(WIDGETS))
    print(f"\nMarcas ({len(MARCAS)}):", ", ".join(MARCAS))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "biblioteca"
    if cmd == "render":
        render(sys.argv[2])
    else:
        biblioteca()
