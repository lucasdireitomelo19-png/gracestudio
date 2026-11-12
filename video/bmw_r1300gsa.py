#!/usr/bin/env python3
"""BMW Motorrad — R 1300 GS Adventure, Super Sale (pasta Drive 1LTlrszZ...)."""
from montagem import render, WORK, ASSETS

RAW = f"{WORK}/bmw1/raw"

# Ela fala olhando para a câmera; sobreposição só onde mostrar a moto agrega:
# no nome do modelo e em "taxas a partir de 0% e 3 anos de garantia"
A = [
    ("IMG_9439", 8.40, 13.90),   # 2ª metade (a 1ª tem "vamos ver se vai sair")
    ("IMG_9442", 1.25, 6.40),    # tomada com o preço certo (no IMG_9441 ela erra o valor)
    ("IMG_9443", 2.10, 5.30),
    ("IMG_9444", 1.70, 6.30),
]

SUBS = [
    (0, 8.40, 10.25, "Pronta para\nqualquer aventura,"),
    (0, 10.25, 13.90, "essa é a BMW Motorrad\nR 1300 GS Adventure."),
    (1, 1.25, 2.42, "E no Super Sale,"),
    (1, 2.42, 3.40, "ela pode ser sua"),
    (1, 3.40, 6.40, "por R$ 156.990\nemplacada."),
    (2, 2.10, 3.90, "E ainda tem taxas\na partir de 0%"),
    (2, 3.90, 5.30, "e 3 anos de garantia."),
    (3, 1.70, 4.60, "Visite a IESA BMW Motorrad\ne aproveite."),
    (3, 4.60, 6.30, "Grupo IESA.\nVamos juntos!"),
]

d0 = A[0][2] - A[0][1]
t_modelo = 10.25 - A[0][1]                       # "essa é a BMW Motorrad R 1300 GS Adventure"
t_taxas = d0 + (A[1][2] - A[1][1])               # início da fala 2
d_taxas = A[2][2] - A[2][1]
B = [
    (t_modelo, (d0 - t_modelo) / 2, "IMG_9447", 0.5),
    (t_modelo + (d0 - t_modelo) / 2, (d0 - t_modelo) / 2, "IMG_9449", 0.8),
    (t_taxas, d_taxas / 2, "IMG_9448", 4.0),
    (t_taxas + d_taxas / 2, d_taxas / 2, "IMG_9446", 2.5),
]

if __name__ == "__main__":
    # Fonte fina: IESA Regular (Soho Gothic Pro Regular)
    render(RAW, A, SUBS, B, "bmw_r1300gsa_2k60.mp4", "bmw1",
           music=f"{WORK}/music/trilha_original.wav", music_vol=0.085, music_start=0.0,
           font="Soho Gothic Pro", bold=0, font_scale=1.0,
           ending=f"{ASSETS}/encerramento_bmw.mp4")
