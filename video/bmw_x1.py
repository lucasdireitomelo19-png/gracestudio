#!/usr/bin/env python3
"""BMW X1 M Sport — BMW Super Sales (pasta Drive BMW/2).

Todas as falas são olhando para a câmera (sem locução) → sem sobreposição e sem flare.
A frase do roteiro "design marcante, esportividade, tecnologia…" não foi gravada.
"""
from montagem import render, WORK, ASSETS

RAW = f"{WORK}/bmw2car/raw"

A = [
    ("IMG_9309", 9.33, 13.27),
    ("IMG_9310", 10.70, 15.52),  # 2ª tentativa (a 1ª tem "expressão, de uma tradição…" e comentário)
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
    (2, 2.07, 3.65, "E na BMW Super Sales,"),
    (2, 3.65, 5.80, "você tem condições exclusivas"),
    (2, 5.80, 8.00, "para levar esse ícone\npara a sua garagem:"),
    (3, 2.64, 4.40, "emplacamento total cortesia,"),
    (3, 4.40, 7.00, "taxa 0% com\n60% de entrada"),
    (3, 7.00, 9.00, "e saldo em 36 meses,"),
    (3, 9.00, 10.60, "ou FIPE no seu usado."),
    (4, 3.36, 5.40, "Essa é a sua chance de garantir"),
    (4, 5.40, 8.21, "o SUV premium mais desejado\npor quem entende de carro."),
    (5, 4.00, 6.80, "Fale com o executivo\nde vendas e saiba mais."),
    (5, 6.80, 9.00, "Grupo IESA.\nVamos juntos!"),
]

B = []

if __name__ == "__main__":
    render(RAW, A, SUBS, B, "bmw_x1_2k60.mp4", "x1",
           music=f"{WORK}/music/trilha_premium.wav",
           font="Soho Gothic Pro", bold=0,              # IESA Regular (fina)
           ending=f"{ASSETS}/encerramento_bmw.mp4")     # encerramento BMW (carros) com fade preto
