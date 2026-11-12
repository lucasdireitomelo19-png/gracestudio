#!/usr/bin/env python3
"""BMW Série 3 — BMW Super Sales (pasta Drive BMW/1)."""
from montagem import render, WORK, ASSETS, flares_locucao

RAW = f"{WORK}/bmw1car/raw"

A = [
    ("IMG_9337", 2.00, 4.90),    # "Tendências passam. Clássicos permanecem."
    ("IMG_9339", 7.10, 17.97),   # LOCUÇÃO (lendo no celular) — 2ª leitura, a 1ª travou
    ("IMG_9340", 5.57, 9.66),
    ("IMG_9341", 2.43, 9.86),
    ("IMG_9352", 2.25, 7.08),
    ("IMG_9353", 6.43, 11.26),   # sem o "fala o Grupo IESA junto ou a gente corta?"
]

SUBS = [
    (0, 2.00, 3.30, "Tendências passam."),
    (0, 3.30, 4.90, "Clássicos permanecem."),
    (1, 7.10, 10.30, "O BMW Série 3 é um\nclássico sedã de luxo,"),
    (1, 10.30, 11.80, "que une design atemporal,"),
    (1, 11.80, 15.10, "esportividade e excelência\nda engenharia alemã"),
    (1, 15.10, 17.97, "em uma experiência de\ncondução inconfundível."),
    (2, 5.57, 7.10, "E na BMW Super Sales,"),
    (2, 7.10, 9.66, "você garante\ncondições exclusivas:"),
    (3, 2.43, 4.10, "emplacamento total cortesia,"),
    (3, 4.10, 6.60, "taxa 0% com\n60% de entrada"),
    (3, 6.60, 8.20, "e o saldo em 36 meses"),
    (3, 8.20, 9.86, "ou FIPE no seu usado."),
    (4, 2.25, 4.50, "Agora é hora de você dirigir"),
    (4, 4.50, 7.08, "um dos modelos mais\nemblemáticos da BMW."),
    (5, 6.43, 9.00, "Fale com o executivo\nde vendas e saiba mais."),
    (5, 9.00, 11.26, "Grupo IESA.\nVamos juntos!"),
]

# Coberturas em toda a locução; áudio das imagens descartado (fica só a voz)
dur = [a[2] - a[1] for a in A]
loc_start, loc_len = dur[0], dur[1]
BROLL = [   # trechos conferidos quadro a quadro, carro bem enquadrado
    ("IMG_9354", 5.0),   # carro inteiro, frente 3/4
    ("IMG_9356", 0.3),   # grade + placa BMW 320 M Sport
    ("IMG_9357", 0.2),   # farol
    ("IMG_9360", 0.2),   # roda
    ("IMG_9358", 1.8),   # lanternas e emblema traseiro
    ("IMG_9345", 3.0),   # painel / tela curva
    ("IMG_9349", 2.0),   # mãos no volante
    ("IMG_9361", 0.3),   # traseira 3/4
    ("IMG_9359", 1.0),   # traseira aberta, carro inteiro
]
step = loc_len / len(BROLL)
B = [(loc_start + k * step, step, f, s) for k, (f, s) in enumerate(BROLL)]

if __name__ == "__main__":
    render(RAW, A, SUBS, B, "bmw_serie3_2k60.mp4", "serie3",
           music=f"{WORK}/music/trilha_house_serie3.wav",
           font="Soho Gothic Pro", bold=0,                 # IESA Regular (fina)
           ending=f"{ASSETS}/encerramento_bmw.mp4",        # encerramento BMW (carros) com fade preto
           flares=flares_locucao([loc_start], [loc_start + loc_len]))
