#!/usr/bin/env python3
"""Volvo XC60 Ultra (pasta Drive Volvo/2)."""
from montagem import render, WORK, ASSETS, flares_locucao

RAW = f"{WORK}/volvo2/raw"

A = [
    ("IMG_9202", 1.02, 3.06),
    ("IMG_9203", 7.38, 9.53),    # 2ª tomada
    ("IMG_9204", 1.12, 4.76),
    ("IMG_9205", 1.53, 10.40),   # LOCUÇÃO (câmera no carro, ele fora de quadro)
    ("IMG_9206", 3.28, 10.79),   # "…a partir de 429.950" (no IMG_9207 ele diz "partiu de")
    ("IMG_9208", 3.27, 7.96),
]

SUBS = [
    (0, 1.02, 3.06, "Algumas escolhas\ndizem muito sobre você."),
    (1, 7.38, 9.53, "O seu próximo Volvo\npode ser uma delas."),
    (2, 1.12, 2.58, "O Volvo XC60"),
    (2, 2.58, 4.76, "traduz sofisticação\nem cada detalhe."),
    (3, 1.53, 3.70, "Design marcante,\nconforto excepcional"),
    (3, 3.70, 5.20, "e tecnologia avançada"),
    (3, 5.20, 7.00, "se encontram em um SUV\ncriado para tornar"),
    (3, 7.00, 10.40, "cada trajeto uma experiência\nclássica e extraordinária."),
    (4, 3.28, 5.60, "E este é o melhor momento\npara conquistar o seu."),
    (4, 5.60, 7.90, "Neste mês, Volvo XC60 Ultra"),
    (4, 7.90, 10.79, "a partir de R$ 429.950."),
    (5, 3.27, 6.30, "Visite a IESA Volvo e aproveite\nas condições especiais."),
    (5, 6.30, 7.96, "Grupo IESA.\nVamos juntos!"),
]

dur = [a[2] - a[1] for a in A]
loc_start, loc_len = sum(dur[:3]), dur[3]
BROLL = [   # trechos conferidos quadro a quadro, carro bem enquadrado
    ("IMG_9209", 3.0),   # frente 3/4
    ("IMG_9210", 0.2),   # grade XC60
    ("IMG_9213", 2.5),   # bancos dianteiros
    ("IMG_9215", 0.2),   # bancos traseiros
    ("IMG_9216", 1.0),   # tela central
    ("IMG_9212", 0.5),   # volante
    ("IMG_9218", 2.0),   # traseira 3/4
    ("IMG_9220", 0.5),   # traseira com XC60
]
step = loc_len / len(BROLL)
B = [(loc_start + k * step, step, f, s) for k, (f, s) in enumerate(BROLL)]

if __name__ == "__main__":
    render(RAW, A, SUBS, B, "volvo_xc60_2k60.mp4", "xc60",
           music=f"{WORK}/music/trilha_house.wav",
           font="Volvo Centum App", bold=0,                 # fonte Volvo
           ending=f"{ASSETS}/encerramento_volvo.mp4",       # encerramento Volvo com fade preto
           flares=flares_locucao([loc_start], [loc_start + loc_len]))
