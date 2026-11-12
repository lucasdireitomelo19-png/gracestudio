#!/usr/bin/env python3
"""Harley Black November — versão entrada de 60% + parcelamento (pasta Drive 16ba2d6N...)."""
from montagem import render, WORK

RAW = f"{WORK}/p2/raw"

A = [
    ("IMG_9165", 8.55, 11.15),        # 2ª tomada (a 1ª tinha "vamos de novo")
    ("IMG_9166", 10.05, 13.18),       # 2ª tomada (a 1ª tinha "como é que é?" no meio)
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
    (1, 10.05, 11.15, "Conquistar uma Harley"),
    (1, 11.15, 13.18, "é viver a liberdade\ndo seu jeito."),
    (2, 12.00, 13.80, "E agora você também\npode escolher"),
    (2, 13.80, 15.13, "como quer\nconquistar a sua."),
    (3, 9.62, 11.80, "Com entrada de 60%\ndo valor da moto,"),
    (3, 11.80, 13.25, "você decide a condição:"),
    (4, 13.66, 14.85, "12x sem juros,"),
    (4, 14.85, 17.45, "24x com taxa de 0,49%"),
    (5, 17.75, 20.35, "ou 36x com\ntaxa de 0,99%."),
    (6, 2.87, 3.86, "Mas atenção,"),
    (6, 3.86, 6.08, "são as últimas\nunidades de 2026."),
    (6, 6.08, 7.13, "Vem aproveitar!"),
    (7, 2.02, 3.50, "Grupo IESA.\nVamos juntos!"),
]

# Coberturas só na locução do celular (falas 3–5), cobrindo-a inteira
loc_start = sum(a[2] - a[1] for a in A[:3])
loc_len = sum(a[2] - a[1] for a in A[3:6])
broll = [("IMG_9171", 1.5), ("IMG_9176", 0.8), ("IMG_9173", 0.8), ("IMG_9179", 1.0),
         ("IMG_9172", 1.0), ("IMG_9174", 2.5), ("IMG_9178", 1.0), ("IMG_9180", 1.5),
         ("IMG_9177", 1.2)]
step = loc_len / len(broll)
B = [(loc_start + k * step, step, f, s) for k, (f, s) in enumerate(broll)]

if __name__ == "__main__":
    # Trilha original gerada por trilha_rock.py (sem direitos de terceiros, não precisa de crédito)
    render(RAW, A, SUBS, B, "harley_entrada60_v4.mp4", "entrada60",
           music=f"{WORK}/music/trilha_original.wav", music_vol=0.085, music_start=0.0)
