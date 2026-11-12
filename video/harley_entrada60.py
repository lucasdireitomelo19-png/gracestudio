#!/usr/bin/env python3
"""Harley Black November — versão entrada de 60% + parcelamento (pasta Drive 16ba2d6N...)."""
from montagem import render, WORK

RAW = f"{WORK}/p2/raw"

A = [
    ("IMG_9165", 8.55, 11.15),        # 2ª tomada (a 1ª tinha "vamos de novo")
    ("IMG_9166", 2.22, 3.30),         # "Conquistar uma Harley"
    ("IMG_9166", 6.58, 7.95, 1.15),   # "é viver a liberdade…" (corta o "como é que é?"; zoom esconde o corte)
    ("IMG_9167", 12.00, 15.13),       # 3ª tomada
    ("IMG_9168", 9.62, 13.25),        # locução lida no celular (2ª tomada)
    ("IMG_9168", 13.66, 17.45),
    ("IMG_9168", 17.75, 20.35),
    ("IMG_9169", 2.87, 7.13),
    ("IMG_9170", 2.02, 3.50),
]

SUBS = [
    (0, 8.55, 9.30, "A Black November"),
    (0, 9.30, 11.15, "chegou na IESA\nHarley-Davidson."),
    (1, 2.22, 3.30, "Conquistar uma Harley"),
    (2, 6.58, 7.95, "é viver a liberdade\ndo seu jeito."),
    (3, 12.00, 13.80, "E agora você também\npode escolher"),
    (3, 13.80, 15.13, "como quer\nconquistar a sua."),
    (4, 9.62, 11.80, "Com entrada de 60%\ndo valor da moto,"),
    (4, 11.80, 13.25, "você decide a condição:"),
    (5, 13.66, 14.85, "12x sem juros,"),
    (5, 14.85, 17.45, "24x com taxa de 0,49%"),
    (6, 17.75, 20.35, "ou 36x com\ntaxa de 0,99%."),
    (7, 2.87, 3.86, "Mas atenção,"),
    (7, 3.86, 6.08, "são as últimas\nunidades de 2026."),
    (7, 6.08, 7.13, "Vem aproveitar!"),
    (8, 2.02, 3.50, "Grupo IESA.\nVamos juntos!"),
]

# Coberturas só na locução do celular (falas 4–6), cobrindo-a inteira
loc_start = sum(a[2] - a[1] for a in A[:4])
loc_len = sum(a[2] - a[1] for a in A[4:7])
broll = [("IMG_9171", 1.5), ("IMG_9176", 0.8), ("IMG_9173", 0.8), ("IMG_9179", 1.0),
         ("IMG_9172", 1.0), ("IMG_9174", 2.5), ("IMG_9178", 1.0), ("IMG_9180", 1.5),
         ("IMG_9177", 1.2)]
step = loc_len / len(broll)
B = [(loc_start + k * step, step, f, s) for k, (f, s) in enumerate(broll)]

if __name__ == "__main__":
    render(RAW, A, SUBS, B, "harley_entrada60_v1.mp4", "entrada60")
