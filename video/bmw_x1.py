#!/usr/bin/env python3
"""BMW X1 M Sport — BMW Super Sales (pasta Drive BMW/2).

Locução "design marcante…" gravada à parte (NARRACAO.MOV, só o áudio) → coberta com imagens do X1 e flares.
"""
from montagem import render, WORK, ASSETS, flares_locucao

RAW = f"{WORK}/bmw2car/raw"

A = [
    ("IMG_9309", 9.33, 13.27),
    ("IMG_9310", 10.70, 15.52),  # 2ª tentativa (a 1ª tem "expressão, de uma tradição…" e comentário)
    ("NARRACAO", 15.30, 24.10),  # LOCUÇÃO — 2ª tomada (a 1ª para em "referência")
    ("IMG_9314", 2.07, 8.00),
    ("IMG_9318", 2.64, 10.60),
    ("IMG_9320", 3.36, 8.21),
    ("IMG_9321", 4.00, 9.00),
]

SUBS = [
    (0, 9.33, 12.18, "O verdadeiro clássico não\nprecisa seguir tendências."),
    (0, 12.18, 13.27, "Ele dita o padrão."),
    (1, 10.70, 13.76, "O BMW X1 é a expressão\nde uma tradição"),
    (1, 13.76, 15.52, "que se reconhece\nno primeiro olhar."),
    (2, 15.30, 17.60, "Design marcante,\nesportividade, tecnologia"),
    (2, 17.60, 21.70, "e a engenharia alemã\nque faz da BMW"),
    (2, 21.70, 24.10, "uma referência no\nsegmento premium."),
    (3, 2.07, 3.65, "E na BMW Super Sales,"),
    (3, 3.65, 5.80, "você tem condições exclusivas"),
    (3, 5.80, 8.00, "para levar esse ícone\npara a sua garagem:"),
    (4, 2.64, 4.40, "emplacamento total cortesia,"),
    (4, 4.40, 7.00, "taxa 0% com\n60% de entrada"),
    (4, 7.00, 9.00, "e saldo em 36 meses,"),
    (4, 9.00, 10.60, "ou FIPE no seu usado."),
    (5, 3.36, 5.40, "Essa é a sua chance de garantir"),
    (5, 5.40, 8.21, "o SUV premium mais desejado\npor quem entende de carro."),
    (6, 4.00, 6.80, "Fale com o executivo\nde vendas e saiba mais."),
    (6, 6.80, 9.00, "Grupo IESA.\nVamos juntos!"),
]

dur = [a[2] - a[1] for a in A]
loc_start, loc_len = sum(dur[:2]), dur[2]
BROLL = [   # trechos conferidos quadro a quadro, carro bem enquadrado
    ("IMG_9333", 0.3),   # grade + placa X1
    ("IMG_9334", 0.3),   # farol
    ("IMG_9327", 1.5),   # volante e painel
    ("IMG_9332", 0.2),   # painel curvo
    ("IMG_9324", 4.5),   # placa traseira BMW X1 X-LINE
    ("IMG_9335", 1.0),   # traseira 3/4, carro inteiro
    ("IMG_9325", 10.8),  # traseira de frente
]
step = loc_len / len(BROLL)
B = [(loc_start + k * step, step, f, s0) for k, (f, s0) in enumerate(BROLL)]

if __name__ == "__main__":
    render(RAW, A, SUBS, B, "bmw_x1_2k60.mp4", "x1",
           music=f"{WORK}/music/trilha_premium.wav",
           font="Soho Gothic Pro", bold=0,              # IESA Regular (fina)
           ending=f"{ASSETS}/encerramento_bmw.mp4",     # encerramento BMW (carros) com fade preto
           flares=flares_locucao([loc_start], [loc_start + loc_len]))
