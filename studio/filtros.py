#!/usr/bin/env python3
"""Grace Studio — catálogo de filtros e efeitos de imagem (ffmpeg), todos com intensidade 0–100.

Uso no código:  cadeia([("contraste", 30), ("granulado", 20), ("lut:cinema_teal_laranja", 60)])
                -> string de filtro ffmpeg (entrada/saída num único fluxo de vídeo)
Uso na linha de comando:  python3 -m studio.filtros --lista
"""
import os, sys

LUT_DIR = os.environ.get("GRACE_LUTS", "/home/user/gracestudio/work/biblioteca/luts")


def _k(v, lo, hi):
    """Mapeia intensidade 0–100 para o intervalo [lo, hi]."""
    return lo + (hi - lo) * max(0.0, min(100.0, v)) / 100.0


# Cada filtro: (grupo, descrição, função intensidade -> string ffmpeg)
FILTROS = {
    # --- cor e luz ---
    "brilho":        ("Cor e luz", "Clareia (+) ou escurece (−); −100..100", lambda v: f"eq=brightness={v/400:.3f}"),
    "contraste":     ("Cor e luz", "Mais (+) ou menos (−) contraste; −100..100", lambda v: f"eq=contrast={1+v/200:.3f}"),
    "saturacao":     ("Cor e luz", "Mais (+) ou menos (−) cor; −100..100", lambda v: f"eq=saturation={1+v/100:.3f}"),
    "exposicao":     ("Cor e luz", "Exposição em stops; −100..100 = −2..+2", lambda v: f"exposure=exposure={v/50:.2f}"),
    "temperatura":   ("Cor e luz", "Quente (+) ou frio (−); −100..100", lambda v: f"colortemperature=temperature={6500 - v*30:.0f}:mix=1"),
    "matiz":         ("Cor e luz", "Gira as cores; −100..100 = −180°..180°", lambda v: f"hue=h={v*1.8:.1f}"),
    "vibrance":      ("Cor e luz", "Satura só o que está pouco saturado", lambda v: f"vibrance=intensity={_k(v, 0, 0.8):.2f}"),
    "gama":          ("Cor e luz", "Meios-tons mais claros (+) ou escuros (−); −100..100", lambda v: f"eq=gamma={1+v/150:.3f}"),
    "sombras_altas": ("Cor e luz", "Levanta sombras (fade de pretos)", lambda v: f"curves=all='0/{_k(v,0,0.12):.3f} 1/1'"),
    "curva_s":       ("Cor e luz", "Contraste fílmico em S", lambda v: f"curves=all='0/0 0.25/{0.25-_k(v,0,0.07):.3f} 0.75/{0.75+_k(v,0,0.07):.3f} 1/1'"),
    "preto_e_branco":("Cor e luz", "Dessatura até P&B", lambda v: f"hue=s={1-v/100:.2f}"),
    "sepia":         ("Cor e luz", "Tom sépia", lambda v: f"colorchannelmixer=rr={1-_k(v,0,0.607):.3f}:rg={_k(v,0,0.769):.3f}:rb={_k(v,0,0.189):.3f}:gr={_k(v,0,0.349):.3f}:gg={1-_k(v,0,0.314):.3f}:gb={_k(v,0,0.168):.3f}:br={_k(v,0,0.272):.3f}:bg={_k(v,0,0.534):.3f}:bb={1-_k(v,0,0.869):.3f}"),
    "inverter":      ("Cor e luz", "Negativo", lambda v: f"negate,format=yuv420p" if v >= 50 else "null"),
    # --- nitidez e textura ---
    "nitidez":       ("Nitidez e textura", "Detalhe (sharpen adaptativo)", lambda v: f"cas=strength={_k(v, 0, 0.9):.2f}"),
    "suavizar_pele": ("Nitidez e textura", "Suaviza textura mantendo bordas", lambda v: f"bilateral=sigmaS={_k(v,0.1,8):.1f}:sigmaR={_k(v,0.01,0.12):.3f}"),
    "desfoque":      ("Nitidez e textura", "Desfoque gaussiano", lambda v: f"gblur=sigma={_k(v, 0, 25):.1f}"),
    "granulado":     ("Nitidez e textura", "Grão de filme", lambda v: f"noise=alls={_k(v, 0, 28):.0f}:allf=t"),
    "pixelado":      ("Nitidez e textura", "Mosaico/pixel", lambda v: f"scale=iw/{max(2,int(_k(v,2,40)))}:-2:flags=neighbor,scale=iw*{max(2,int(_k(v,2,40)))}:-2:flags=neighbor"),
    "reduzir_ruido": ("Nitidez e textura", "Remove ruído de câmera", lambda v: f"hqdn3d={_k(v,0,6):.1f}:{_k(v,0,5):.1f}:{_k(v,0,8):.1f}:{_k(v,0,6):.1f}"),
    # --- estilo ---
    "vinheta":       ("Estilo", "Escurece as bordas", lambda v: f"vignette=angle={_k(v, 0.1, 0.9):.2f}"),
    "brilho_suave":  ("Estilo", "Glow / bloom nas luzes", lambda v: f"format=gbrp,split[g0][g1];[g1]curves=all='0/0 0.6/0 1/1',gblur=sigma=30[gb];[g0][gb]blend=all_mode=screen:all_opacity={_k(v,0,0.8):.2f},format=yuv420p"),
    "halation":      ("Estilo", "Brilho avermelhado em volta das luzes (filme)", lambda v: f"format=gbrp,split[h0][h1];[h1]curves=all='0/0 0.7/0 1/1',colorchannelmixer=gg=0.3:bb=0.1,gblur=sigma=18[hb];[h0][hb]blend=all_mode=screen:all_opacity={_k(v,0,0.7):.2f},format=yuv420p"),
    "aberracao_cromatica": ("Estilo", "Separação RGB nas bordas", lambda v: f"rgbashift=rh={-int(_k(v,0,14))}:bh={int(_k(v,0,14))}"),
    "vhs":           ("Estilo", "Fita VHS: borrão, cor deslocada, ruído e linhas", lambda v: f"rgbashift=rh={-int(_k(v,0,8))}:bh={int(_k(v,0,8))},noise=alls={_k(v,0,20):.0f}:allf=t,eq=saturation={1-_k(v,0,0.3):.2f},gblur=sigma={_k(v,0,1.5):.1f}"),
    "glitch":        ("Estilo", "Falhas digitais intermitentes", lambda v: f"rgbashift=rh={int(_k(v,4,30))}:bv={int(_k(v,2,18))}:edge=wrap:enable='gt(mod(t\\,1.3)\\,1.18)',noise=alls={_k(v,0,25):.0f}:allf=t+u:enable='gt(mod(t\\,1.3)\\,1.18)'"),
    "letterbox":     ("Estilo", "Faixas pretas de cinema", lambda v: f"drawbox=x=0:y=0:w=iw:h=ih*{_k(v,0,0.12):.3f}:color=black:t=fill,drawbox=x=0:y=ih*{1-_k(v,0,0.12):.3f}:w=iw:h=ih*{_k(v,0,0.12):.3f}:color=black:t=fill"),
    "espelho":       ("Estilo", "Espelha na horizontal", lambda v: "hflip" if v >= 50 else "null"),
    "posterizar":    ("Estilo", "Reduz número de cores", lambda v: f"lutrgb=r='bitand(val,{255 - (2**int(_k(v,0,6))-1)})':g='bitand(val,{255 - (2**int(_k(v,0,6))-1)})':b='bitand(val,{255 - (2**int(_k(v,0,6))-1)})'"),
    "luz_vazada":    ("Estilo", "Light leak quente vindo da lateral", lambda v: f"format=gbrp,split[l0][l1];[l1]geq=r='min(255\\,330*exp(-((X-W*0.9)^2+(Y-H*0.3)^2)/(2*(W*0.55)^2)))':g='min(255\\,200*exp(-((X-W*0.9)^2+(Y-H*0.3)^2)/(2*(W*0.55)^2)))':b='min(255\\,70*exp(-((X-W*0.9)^2+(Y-H*0.3)^2)/(2*(W*0.55)^2)))'[ll];[l0][ll]blend=all_mode=screen:all_opacity={_k(v,0,0.9):.2f},format=yuv420p"),
    "desbotado":     ("Estilo", "Pretos levantados e cores lavadas (matte)", lambda v: f"curves=all='0/{_k(v,0,0.14):.3f} 1/{1-_k(v,0,0.05):.3f}',eq=saturation={1-_k(v,0,0.35):.2f}"),
    "duotone_azul":  ("Estilo", "Duotone azul/creme", lambda v: f"split[d0][d1];[d1]hue=s=0,curves=r='0/0.05 1/0.98':g='0/0.12 1/0.95':b='0/0.35 1/0.85'[dd];[d0][dd]blend=all_mode=normal:all_opacity={_k(v,0,1):.2f}"),
    # --- câmera / movimento ---
    "estabilizar_leve": ("Câmera", "Suaviza tremidos pequenos (deshake)", lambda v: "deshake" if v > 0 else "null"),
    "tremer_camera": ("Câmera", "Tremor de câmera (impacto)", lambda v: f"crop=iw*0.96:ih*0.96:'(iw-ow)/2+{_k(v,0,18):.0f}*sin(t*37)':'(ih-oh)/2+{_k(v,0,18):.0f}*cos(t*29)',scale=iw/0.96:ih/0.96"),
}


def lut(nome, intensidade=100):
    path = f"{LUT_DIR}/{nome}.cube"
    if not os.path.exists(path):
        raise FileNotFoundError(f"LUT não encontrada: {nome}")
    a = max(0, min(100, intensidade)) / 100
    if a >= 0.999:
        return f"lut3d=file='{path}':interp=tetrahedral"
    return (f"format=gbrp,split[lt0][lt1];[lt1]lut3d=file='{path}':interp=tetrahedral[lt2];"
            f"[lt0][lt2]blend=all_mode=normal:all_opacity={a:.3f},format=yuv420p")


def cadeia(passos):
    """passos: [(nome, intensidade)]; nome 'lut:<id>' aplica uma LUT. Retorna filtro único (in→out)."""
    partes = []
    for i, (nome, v) in enumerate(passos):
        f = lut(nome[4:], v) if nome.startswith("lut:") else FILTROS[nome][2](v)
        if f == "null":
            continue
        # rótulos únicos por passo (filtros com split usam rótulos internos)
        if "[" in f:
            f = f.replace("[", f"[s{i}_")
        partes.append(f)
    return ",".join(partes) if partes else "null"


if __name__ == "__main__":
    if "--lista" in sys.argv:
        g0 = None
        for k, (g, d, _) in FILTROS.items():
            if g != g0:
                print(f"\n## {g}")
                g0 = g
            print(f"  {k:22s} {d}")
