#!/usr/bin/env python3
"""Volvo EX40 Plus (pasta Drive Volvo/1).
A frase do roteiro "100% elétrico, o Volvo EX40 combina design contemporâneo…" não foi gravada.
"""
from montagem import render, WORK, ASSETS, flares_locucao

RAW = f"{WORK}/volvo1/raw"

A = [
    ("IMG_9225", 1.17, 3.63),
    ("IMG_9251", 12.08, 13.35),  # LOCUÇÃO sobre a imagem do carro na rua
    ("IMG_9243", 1.06, 5.15),
    ("IMG_9248", 7.30, 9.85),    # 2ª tomada
    ("IMG_9249", 12.86, 17.99),  # 2ª tomada (a 1ª tem pausa longa no meio do preço)
    ("IMG_9244", 1.19, 5.66),
]

SUBS = [
    (0, 1.17, 3.63, "O futuro da sofisticação\nnão faz barulho."),
    (1, 12.08, 13.35, "E você sente a diferença."),
    (2, 1.06, 3.20, "Uma nova forma de viver\na mobilidade premium,"),
    (2, 3.20, 5.15, "com toda a segurança\ne classe de um Volvo."),
    (3, 7.30, 9.85, "E este é o melhor momento\npara conquistar o seu."),
    (4, 12.86, 15.20, "Neste mês, Volvo EX40 Plus"),
    (4, 15.20, 17.99, "a partir de R$ 289.950."),
    (5, 1.19, 4.00, "Visite a IESA Volvo e aproveite\nas condições especiais."),
    (5, 4.00, 5.66, "Grupo IESA.\nVamos juntos!"),
]

B = []   # a locução já é a imagem do carro (IMG_9251)
dur = [a[2] - a[1] for a in A]

if __name__ == "__main__":
    render(RAW, A, SUBS, B, "volvo_ex40_2k60.mp4", "ex40",
           music=f"{WORK}/music/trilha_calmo.wav",
           font="Volvo Centum App", bold=0,
           ending=f"{ASSETS}/encerramento_volvo.mp4",
           flares=flares_locucao([dur[0]], [dur[0] + dur[1]]))
