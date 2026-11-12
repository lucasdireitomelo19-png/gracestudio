#!/usr/bin/env python3
"""Volvo EX40 Plus (pasta Drive Volvo/1).
Locução "100% elétrico…" gravada à parte (LOCUCAO.MOV, só o áudio) → coberta com imagens do EX40 e flares.
"""
from montagem import render, WORK, ASSETS, flares_locucao

RAW = f"{WORK}/volvo1/raw"

A = [
    ("IMG_9225", 1.17, 3.63),
    ("IMG_9251", 10.60, 13.35),  # carro elétrico chegando em silêncio + ele fala pela janela (olhando para a câmera)
    ("LOCUCAO", 0.00, 12.75),    # LOCUÇÃO "100% elétrico…"
    ("IMG_9243", 1.06, 5.15),
    ("IMG_9248", 7.30, 9.85),    # 2ª tomada
    ("IMG_9249", 12.86, 17.99),  # 2ª tomada (a 1ª tem pausa longa no meio do preço)
    ("IMG_9244", 1.19, 5.66),
]

SUBS = [
    (0, 1.17, 3.63, "O futuro da sofisticação\nnão faz barulho."),
    (1, 12.08, 13.35, "E você sente a diferença."),
    (2, 0.00, 2.90, "100% elétrico,"),
    (2, 2.90, 6.40, "o Volvo EX40 combina\ndesign contemporâneo,"),
    (2, 6.40, 8.46, "desempenho e\ntecnologia inteligente"),
    (2, 8.46, 10.95, "em uma experiência de\ncondução silenciosa,"),
    (2, 10.95, 12.75, "envolvente e refinada."),
    (3, 1.06, 3.20, "Uma nova forma de viver\na mobilidade premium,"),
    (3, 3.20, 5.15, "com toda a segurança\ne classe de um Volvo."),
    (4, 7.30, 9.85, "E este é o melhor momento\npara conquistar o seu."),
    (5, 12.86, 15.20, "Neste mês, Volvo EX40 Plus"),
    (5, 15.20, 17.99, "a partir de R$ 289.950."),
    (6, 1.19, 4.00, "Visite a IESA Volvo e aproveite\nas condições especiais."),
    (6, 4.00, 5.66, "Grupo IESA.\nVamos juntos!"),
]

dur = [a[2] - a[1] for a in A]
loc_start, loc_len = sum(dur[:2]), dur[2]
BROLL = [   # trechos conferidos quadro a quadro, carro bem enquadrado
    ("IMG_9239", 2.0),   # frente 3/4, carro inteiro
    ("IMG_9241", 0.3),   # grade + EX40
    ("IMG_9245", 0.5),   # emblema Volvo + placa EX40
    ("IMG_9230", 1.8),   # tela central
    ("IMG_9228", 0.5),   # volante
    ("IMG_9232", 3.5),   # bancos traseiros, teto
    ("IMG_9233", 6.0),   # traseira 3/4, carro inteiro
    ("IMG_9234", 0.3),   # lanterna
    ("IMG_9235", 1.5),   # traseira VOLVO + EX40
]
step = loc_len / len(BROLL)
B = [(loc_start + k * step, step, f, s0) for k, (f, s0) in enumerate(BROLL)]

if __name__ == "__main__":
    render(RAW, A, SUBS, B, "volvo_ex40_2k60.mp4", "ex40",
           music=f"{WORK}/music/trilha_house.wav",
           font="Volvo Centum App", bold=0,
           ending=f"{ASSETS}/encerramento_volvo.mp4",
           flares=flares_locucao([loc_start], [loc_start + loc_len]))
