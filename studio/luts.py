#!/usr/bin/env python3
"""Grace Studio — biblioteca de LUTs originais (.cube 33³), geradas por código. Sem direitos de terceiros.

Uso:  python3 -m studio.luts <pasta_saida>        gera todas
      python3 -m studio.luts <pasta_saida> --lista
Cada LUT é uma função f(rgb) -> rgb sobre valores 0..1 (Rec.709/sRGB, display-referred).
"""
import json, os, sys
import numpy as np

N = 33


# ---------- blocos de construção ----------
def luma(c):
    return c[..., 0:1] * 0.2126 + c[..., 1:2] * 0.7152 + c[..., 2:3] * 0.0722


def sat(c, s):
    y = luma(c)
    return y + (c - y) * s


def contrast(c, k, pivot=0.45):
    return (c - pivot) * k + pivot


def scurve(c, amt):
    """Curva em S suave (contraste fílmico) mantendo pretos/brancos."""
    x = np.clip(c, 0, 1)
    s = x * x * (3 - 2 * x)
    return x + (s - x) * amt


def lift_gamma_gain(c, lift=(0, 0, 0), gamma=(1, 1, 1), gain=(1, 1, 1)):
    lift, gamma, gain = map(np.array, (lift, gamma, gain))
    x = np.clip(c * gain + lift * (1 - c), 0, 1)
    return np.power(x, 1 / gamma)


def temp(c, t, tint=0.0):
    """t>0 aquece (mais vermelho/menos azul); tint>0 puxa magenta."""
    m = np.array([1 + 0.10 * t, 1 - 0.06 * tint, 1 - 0.12 * t])
    return c * m + np.array([0, 0.03 * -tint, 0]) * 0


def split_tone(c, shadow, highlight, amt=0.15, balance=0.5):
    y = luma(c)
    ws = np.clip(1 - y / balance, 0, 1)
    wh = np.clip((y - balance) / (1 - balance), 0, 1)
    return c + amt * (ws * (np.array(shadow) - 0.5) + wh * (np.array(highlight) - 0.5))


def fade(c, black=0.06, white=0.97):
    return black + c * (white - black)


def hue_shift_rgb(c, deg):
    a = np.radians(deg)
    k = np.array([1, 1, 1]) / np.sqrt(3)
    cos, sin = np.cos(a), np.sin(a)
    return c * cos + np.cross(k, c) * sin + k * (c @ k)[..., None] * (1 - cos)


def selective(c, hue_from, hue_to_shift=0.0, sat_mul=1.0, width=40):
    """Mexe numa faixa de matiz (graus): desloca e satura/dessatura só ela."""
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    mx, mn = c.max(-1), c.min(-1)
    d = mx - mn + 1e-9
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    dist = np.abs(((h - hue_from) + 180) % 360 - 180)
    w = np.clip(1 - dist / width, 0, 1)[..., None] * np.clip(d * 3, 0, 1)[..., None]
    out = c
    if hue_to_shift:
        out = out * (1 - w) + hue_shift_rgb(c, hue_to_shift) * w
    if sat_mul != 1.0:
        out = out * (1 - w) + sat(out, sat_mul) * w
    return out


def bw(c, r=0.30, g=0.59, b=0.11):
    y = c[..., 0:1] * r + c[..., 1:2] * g + c[..., 2:3] * b
    return np.repeat(y, 3, -1)


def tone(c, rgb, amt):
    return c * (1 - amt) + luma(c) * np.array(rgb) * amt


# ---------- looks ----------
LOOKS = {
    # cinema
    "cinema_teal_laranja": ("Cinema", lambda c: scurve(split_tone(sat(c, 1.05), (0.35, 0.55, 0.65), (0.70, 0.55, 0.40), 0.35), 0.5)),
    "cinema_quente": ("Cinema", lambda c: scurve(temp(sat(c, 1.05), 0.6), 0.45)),
    "cinema_frio": ("Cinema", lambda c: scurve(temp(sat(c, 0.95), -0.6), 0.45)),
    "blockbuster": ("Cinema", lambda c: scurve(split_tone(sat(c, 1.15), (0.30, 0.50, 0.62), (0.72, 0.56, 0.36), 0.45), 0.7)),
    "drama_escuro": ("Cinema", lambda c: scurve(lift_gamma_gain(sat(c, 0.8), (-0.02, -0.01, 0.0), (0.88, 0.9, 0.92), (0.95, 0.95, 0.97)), 0.6)),
    "thriller_verde": ("Cinema", lambda c: scurve(split_tone(sat(c, 0.85), (0.42, 0.56, 0.45), (0.56, 0.58, 0.46), 0.3), 0.55)),
    "noir_azul": ("Cinema", lambda c: scurve(tone(sat(c, 0.4), (0.85, 0.95, 1.15), 0.5), 0.6)),
    "epico_dourado": ("Cinema", lambda c: scurve(split_tone(sat(c, 1.1), (0.40, 0.45, 0.55), (0.78, 0.62, 0.36), 0.4), 0.55)),
    "documental_natural": ("Cinema", lambda c: scurve(sat(c, 1.02), 0.25)),
    "bleach_bypass": ("Cinema", lambda c: scurve(contrast(sat(c, 0.45), 1.18), 0.5)),
    # filme
    "filme_classico_70": ("Filme", lambda c: fade(scurve(split_tone(sat(c, 1.12), (0.45, 0.48, 0.42), (0.66, 0.58, 0.44), 0.3), 0.5), 0.05, 0.96)),
    "filme_retrato_suave": ("Filme", lambda c: fade(scurve(split_tone(sat(c, 0.9), (0.48, 0.5, 0.52), (0.6, 0.55, 0.5), 0.2), 0.3), 0.04, 0.98)),
    "filme_desbotado": ("Filme", lambda c: fade(sat(c, 0.75), 0.10, 0.94)),
    "filme_instantanea": ("Filme", lambda c: fade(split_tone(sat(c, 0.85), (0.45, 0.55, 0.58), (0.68, 0.6, 0.48), 0.35), 0.08, 0.95)),
    "filme_cross_process": ("Filme", lambda c: scurve(lift_gamma_gain(c, (0.0, 0.02, 0.06), (1.15, 1.0, 0.85), (1.0, 1.04, 0.92)), 0.6)),
    "filme_vintage": ("Filme", lambda c: fade(tone(sat(c, 0.7), (1.12, 1.0, 0.78), 0.35), 0.07, 0.95)),
    "filme_kodak_like_quente": ("Filme", lambda c: scurve(split_tone(sat(c, 1.08), (0.46, 0.48, 0.5), (0.7, 0.58, 0.42), 0.3), 0.45)),
    "filme_fuji_like_verde": ("Filme", lambda c: scurve(split_tone(selective(sat(c, 1.0), 120, 0, 1.15), (0.45, 0.54, 0.52), (0.6, 0.6, 0.5), 0.25), 0.4)),
    # preto e branco
    "pb_alto_contraste": ("P&B", lambda c: scurve(contrast(bw(c), 1.25), 0.6)),
    "pb_suave": ("P&B", lambda c: fade(bw(c), 0.05, 0.96)),
    "pb_filtro_vermelho": ("P&B", lambda c: scurve(bw(c, 0.6, 0.35, 0.05), 0.4)),
    "pb_sepia": ("P&B", lambda c: tone(bw(c), (1.12, 1.0, 0.78), 1.0)),
    "pb_selenio": ("P&B", lambda c: tone(bw(c), (0.95, 0.95, 1.08), 1.0)),
    # carros / showroom
    "auto_showroom_limpo": ("Automotivo", lambda c: scurve(temp(sat(c, 1.08), -0.15), 0.35)),
    "auto_premium_escuro": ("Automotivo", lambda c: scurve(lift_gamma_gain(sat(c, 0.92), (-0.02, -0.02, -0.01), (0.9, 0.92, 0.95), (1.0, 1.0, 1.02)), 0.6)),
    "auto_metal_frio": ("Automotivo", lambda c: scurve(split_tone(sat(c, 0.85), (0.38, 0.48, 0.6), (0.52, 0.56, 0.62), 0.3), 0.5)),
    "auto_por_do_sol": ("Automotivo", lambda c: scurve(split_tone(sat(c, 1.12), (0.42, 0.42, 0.56), (0.80, 0.56, 0.36), 0.4), 0.45)),
    "auto_esportivo": ("Automotivo", lambda c: scurve(contrast(sat(c, 1.2), 1.1), 0.5)),
    "auto_vermelho_intenso": ("Automotivo", lambda c: scurve(selective(sat(c, 1.0), 0, 0, 1.4), 0.4)),
    "auto_eletrico_azul": ("Automotivo", lambda c: scurve(selective(temp(sat(c, 1.05), -0.25), 210, 0, 1.3), 0.4)),
    # estilo / redes
    "vibrante": ("Redes", lambda c: sat(scurve(c, 0.3), 1.35)),
    "natural_pop": ("Redes", lambda c: sat(scurve(c, 0.25), 1.15)),
    "pastel": ("Redes", lambda c: fade(sat(c, 0.7), 0.08, 1.0) + 0.02),
    "clean_branco": ("Redes", lambda c: lift_gamma_gain(sat(c, 0.95), (0.03, 0.03, 0.03), (1.08, 1.08, 1.08), (1.02, 1.02, 1.02))),
    "moody": ("Redes", lambda c: fade(scurve(sat(c, 0.75), 0.4), 0.06, 0.92)),
    "golden_hour": ("Redes", lambda c: scurve(temp(sat(c, 1.1), 0.8, 0.1), 0.35)),
    "verao": ("Redes", lambda c: sat(temp(scurve(c, 0.3), 0.4), 1.2)),
    "inverno": ("Redes", lambda c: sat(temp(fade(c, 0.03, 0.99), -0.7), 0.85)),
    "rosa_suave": ("Redes", lambda c: split_tone(sat(c, 0.9), (0.55, 0.48, 0.52), (0.62, 0.52, 0.56), 0.3)),
    "cyberpunk": ("Redes", lambda c: scurve(split_tone(sat(c, 1.2), (0.42, 0.40, 0.70), (0.72, 0.42, 0.66), 0.5), 0.5)),
    "neon_noite": ("Redes", lambda c: scurve(selective(selective(sat(c, 1.25), 300, 0, 1.4), 190, 0, 1.4), 0.5)),
    "deserto": ("Redes", lambda c: scurve(tone(sat(c, 0.9), (1.1, 0.98, 0.82), 0.3), 0.4)),
    "floresta": ("Redes", lambda c: scurve(selective(sat(c, 1.05), 110, -10, 1.2), 0.35)),
    "oceano": ("Redes", lambda c: scurve(selective(sat(c, 1.05), 200, 0, 1.3), 0.35)),
    "matte_preto": ("Redes", lambda c: fade(scurve(c, 0.4), 0.09, 1.0)),
    # técnicos
    "log_para_rec709": ("Técnico", lambda c: scurve(contrast(sat(c, 1.35), 1.35, 0.42), 0.6)),
    "neutro": ("Técnico", lambda c: c),
}


def cube(fn, path, title):
    g = np.linspace(0, 1, N)
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")          # .cube: R varia mais rápido
    c = np.stack([r, gg, b], -1).reshape(-1, 3)
    out = np.clip(fn(c), 0, 1)
    with open(path, "w") as f:
        f.write(f'TITLE "{title}"\nLUT_3D_SIZE {N}\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n')
        np.savetxt(f, out, fmt="%.6f")


def gerar(dest):
    os.makedirs(dest, exist_ok=True)
    cat = []
    for name, (grupo, fn) in LOOKS.items():
        cube(fn, f"{dest}/{name}.cube", name)
        cat.append({"id": name, "grupo": grupo, "arquivo": f"{name}.cube"})
    json.dump(cat, open(f"{dest}/catalogo.json", "w"), ensure_ascii=False, indent=1)
    return cat


if __name__ == "__main__":
    dest = sys.argv[1] if len(sys.argv) > 1 else "biblioteca/luts"
    if "--lista" in sys.argv:
        for k, (g, _) in LOOKS.items():
            print(f"{g:12s} {k}")
    else:
        print(len(gerar(dest)), "LUTs em", dest)
