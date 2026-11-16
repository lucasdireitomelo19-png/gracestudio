#!/usr/bin/env python3
"""Grace Studio — biblioteca de fontes.

Pega as famílias OFL do Google Fonts (clone esparso em /home/user/tools/gfonts), gera instâncias estáticas
Regular / Bold / Black das fontes variáveis (para o libass/ffmpeg achar o negrito), junta as fontes das
marcas (IESA, Volvo) e grava catalogo.json com família, estilos, categoria e licença.

Uso: python3 -m studio.fontes [pasta_saida]
"""
import json, os, re, shutil, sys, glob
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

GF = "/home/user/tools/gfonts/ofl"
ASSETS = "/home/user/gracestudio/assets/iesa"

CATEGORIAS = {
    "Sem serifa": "montserrat poppins inter roboto opensans lato raleway nunito worksans dmsans manrope plusjakartasans "
                  "outfit sora urbanist lexend spacegrotesk ibmplexsans barlow archivo rubik figtree redhatdisplay jost "
                  "lexenddeca bricolagegrotesque unbounded syne familjengrotesk instrumentsans kanit",
    "Condensada / impacto": "oswald barlowcondensed sairacondensed archivonarrow bebasneue anton leaguegothic fjallaone teko "
                            "archivoblack russoone blackopsone",
    "Serifa / elegante": "playfairdisplay dmserifdisplay librebaskerville cormorantgaramond lora merriweather abrilfatface alfaslabone",
    "Manuscrita": "pacifico dancingscript caveat greatvibes lobster shadowsintolight",
    "Tecnológica / display": "orbitron audiowide exo2 rajdhani chakrapetch michroma tektur righteous bangers",
}
PESOS = {"Regular": 400, "Bold": 700, "Black": 900}


def nome_familia(path):
    f = TTFont(path, lazy=True)
    n = f["name"]
    fam = n.getDebugName(16) or n.getDebugName(1)
    f.close()
    return fam


def renomear(font, familia, estilo):
    """Ajusta a tabela name para (família, estilo) e o bit de negrito, para o libass casar com \\b1."""
    nm = font["name"]
    full = f"{familia} {estilo}" if estilo != "Regular" else familia
    ps = re.sub(r"[^A-Za-z0-9-]", "", f"{familia}-{estilo}")
    for rec in list(nm.names):
        if rec.nameID in (1, 2, 4, 6, 16, 17):
            nm.removeNames(nameID=rec.nameID)
    sub = "Bold" if estilo == "Bold" else "Regular"
    fam1 = familia if estilo in ("Regular", "Bold") else f"{familia} {estilo}"
    for nid, val in ((1, fam1), (2, sub), (4, full), (6, ps), (16, familia), (17, estilo)):
        nm.setName(val, nid, 3, 1, 0x409)
    os2 = font["OS/2"]
    os2.usWeightClass = PESOS.get(estilo, 400)
    os2.fsSelection = (os2.fsSelection & ~0b1100001) | (0b100000 if estilo == "Bold" else 0b1000000)
    font["head"].macStyle = 1 if estilo == "Bold" else 0


def gerar(dest):
    os.makedirs(dest, exist_ok=True)
    cat = []
    for categoria, fams in CATEGORIAS.items():
        for pasta in fams.split():
            d = f"{GF}/{pasta}"
            if not os.path.isdir(d):
                continue
            ttfs = sorted(glob.glob(f"{d}/*.ttf"))
            uprights = [t for t in ttfs if "Italic" not in os.path.basename(t)]
            if not uprights:
                continue
            familia = nome_familia(uprights[0])
            estilos = []
            var = [t for t in uprights if "[" in t]
            if var:
                f = TTFont(var[0])
                eixos = {a.axisTag: (a.minValue, a.maxValue) for a in f["fvar"].axes} if "fvar" in f else {}
                for estilo, w in PESOS.items():
                    if "wght" in eixos and not (eixos["wght"][0] <= w <= eixos["wght"][1]):
                        continue
                    loc = {tag: (min(max(w, lo), hi) if tag == "wght" else
                                 (min(max(100, lo), hi) if tag == "wdth" else None))
                           for tag, (lo, hi) in eixos.items()}
                    loc = {k: v for k, v in loc.items() if v is not None}
                    inst = instancer.instantiateVariableFont(TTFont(var[0]), loc, updateFontNames=False)
                    renomear(inst, familia, estilo)
                    out = f"{dest}/{re.sub(r'[^A-Za-z0-9]', '', familia)}-{estilo}.ttf"
                    inst.save(out)
                    estilos.append(estilo)
            else:
                for estilo in PESOS:
                    cand = [t for t in uprights if t.endswith(f"-{estilo}.ttf")]
                    if cand:
                        out = f"{dest}/{os.path.basename(cand[0])}"
                        shutil.copy(cand[0], out)
                        estilos.append(estilo)
                if not estilos:                       # família de um peso só (display)
                    shutil.copy(uprights[0], f"{dest}/{os.path.basename(uprights[0])}")
                    estilos.append("Regular")
            for lic in ("OFL.txt", "LICENSE.txt"):
                if os.path.exists(f"{d}/{lic}"):
                    shutil.copy(f"{d}/{lic}", f"{dest}/LICENCA-{re.sub(r'[^A-Za-z0-9]', '', familia)}.txt")
            cat.append({"familia": familia, "categoria": categoria, "estilos": estilos, "licenca": "SIL OFL 1.1",
                        "fonte": f"github.com/google/fonts/tree/main/ofl/{pasta}"})
    # fontes das marcas (arquivos do cliente, não redistribuir)
    for fam, cat_m, arqs in (("Soho Gothic Pro", "Marca: IESA", ("SohoGothicPro-Regular.otf", "SohoGothicPro-Bold.otf")),
                             ("Volvo Centum App", "Marca: Volvo", ("VolvoCentum-Regular.ttf", "VolvoCentum-MediumItalic.ttf"))):
        ok = [a for a in arqs if os.path.exists(f"{ASSETS}/{a}")]
        for a in ok:
            shutil.copy(f"{ASSETS}/{a}", f"{dest}/{a}")
        if ok:
            cat.append({"familia": fam, "categoria": cat_m, "estilos": ["Regular", "Bold"] if "Bold" in " ".join(ok) else ["Regular"],
                        "licenca": "fonte do cliente (uso interno)", "fonte": "Drive do cliente"})
    json.dump(cat, open(f"{dest}/catalogo.json", "w"), ensure_ascii=False, indent=1)
    return cat


if __name__ == "__main__":
    dest = sys.argv[1] if len(sys.argv) > 1 else "/home/user/gracestudio/work/biblioteca/fontes"
    c = gerar(dest)
    print(len(c), "famílias,", sum(len(x["estilos"]) for x in c), "estilos em", dest)
