#!/usr/bin/env python3
"""BMW Motorrad — R 1300 RT, Super Sales (pasta Drive BMW Motorrad/2)."""
from montagem import render, WORK

RAW = f"{WORK}/motorrad2/raw"

A = [
    ("IMG_9429", 18.05, 24.50),  # 2ª tomada
    ("IMG_9430", 3.00, 7.62),
    ("IMG_9431", 1.70, 5.08),    # "taxa 0% em até 24 vezes" (o IMG_9432 diz "24 meses", fora do roteiro)
    ("IMG_9431", 6.15, 7.05),    # "e 3 anos de garantia" (corta a pausa e o "né?" final)
    ("IMG_9433", 3.17, 7.66),
]

SUBS = [
    (0, 18.05, 20.72, "Conforto e tecnologia\npara ir muito mais longe."),
    (0, 20.72, 24.50, "Essa é a BMW Motorrad\nR 1300 RT."),
    (1, 3.00, 4.88, "Na Super Sales,\nela pode ser sua"),
    (1, 4.88, 7.62, "por R$ 163.990\nemplacada!"),
    (2, 1.70, 2.40, "E tem mais:"),
    (2, 2.40, 5.08, "taxa 0% em\naté 24 vezes"),
    (3, 6.15, 7.05, "e 3 anos de garantia."),
    (4, 3.17, 6.00, "Visite a IESA BMW Motorrad\ne aproveite!"),
    (4, 6.00, 7.66, "Grupo IESA.\nVamos juntos!"),
]

# Sobreposição só onde mostrar a moto agrega: nome do modelo e condições (trechos com a moto bem enquadrada)
dur = [a[2] - a[1] for a in A]
t_nome = 21.00 - A[0][1]
d_nome = dur[0] - t_nome
t_cond = dur[0] + dur[1]
d_cond = dur[2] + dur[3]
B = [
    (t_nome, d_nome / 2, "IMG_9435", 1.0),          # frente 3/4, moto inteira
    (t_nome + d_nome / 2, d_nome / 2, "IMG_9436", 0.0),  # carenagem de perto
    (t_cond, d_cond / 2, "IMG_9437", 0.3),          # traseira 3/4 com baú
    (t_cond + d_cond / 2, d_cond / 2, "IMG_9434", 0.3),  # painel e tanque "R 1300"
]

if __name__ == "__main__":
    render(RAW, A, SUBS, B, "bmw_r1300rt_2k60.mp4", "rt",
           music=f"{WORK}/music/trilha_aventura.wav",
           font="Soho Gothic Pro", bold=0)   # IESA Regular (fina) para BMW Motorrad
