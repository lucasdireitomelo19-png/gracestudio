#!/usr/bin/env python3
"""Harley Black November — versão compra à vista, bônus de até R$ 23 mil (pasta Drive 1OMGmLIY...)."""
from montagem import render, WORK

RAW = f"{WORK}/raw"

A = [
    ("IMG_9181", 1.95, 6.00),
    ("IMG_9182", 1.75, 4.82),
    ("IMG_9183", 13.20, 16.50),  # 2ª tomada (a 1ª tinha "vamos de novo")
    ("IMG_9184", 1.58, 9.98),    # locução lida no celular
    ("IMG_9185", 2.02, 6.26),
    ("IMG_9186", 1.80, 3.62),
]

SUBS = [
    (0, 1.95, 3.30, "A Black November"),
    (0, 3.30, 4.30, "da IESA Harley-Davidson"),
    (0, 4.30, 6.00, "chegou com uma\noportunidade imperdível."),
    (1, 1.75, 2.70, "Conquistar uma Harley"),
    (1, 2.70, 4.82, "é viver a liberdade\ndo seu jeito."),
    (2, 13.20, 14.80, "E agora você pode escolher"),
    (2, 14.80, 16.50, "como quer\nconquistar a sua."),
    (3, 1.58, 2.60, "Na compra à vista,"),
    (3, 2.60, 4.80, "aproveite o bônus\nde até R$ 23 mil,"),
    (3, 4.80, 7.60, "uma oportunidade\npor tempo limitado"),
    (3, 7.60, 9.98, "para tirar o sonho de ter\numa Harley da garagem."),
    (4, 2.02, 2.80, "Mas atenção,"),
    (4, 2.80, 5.30, "são as últimas\nunidades de 2026."),
    (4, 5.30, 6.26, "Vem aproveitar!"),
    (5, 1.80, 3.62, "Grupo IESA.\nVamos juntos!"),
]

# Coberturas só na locução do celular (fala 3), cobrindo-a inteira
loc_start = sum(a[2] - a[1] for a in A[:3])
broll = [("IMG_9188", 0.8), ("IMG_9189", 0.6), ("IMG_9191", 1.2), ("IMG_9193", 1.5),
         ("IMG_9194", 1.5), ("IMG_9197", 0.8), ("IMG_9198", 1.2), ("IMG_9199", 2.0)]
B = [(loc_start + k * 1.05, 1.05, f, s) for k, (f, s) in enumerate(broll)]

if __name__ == "__main__":
    render(RAW, A, SUBS, B, "harley_avista_2k60.mp4", "avista")  # trilha: Big Rock (CC BY, pede crédito)
