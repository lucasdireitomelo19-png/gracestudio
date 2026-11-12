#!/usr/bin/env python3
"""MINI — Arena de Vendas MINI, MINI Cooper S 3 Portas (pasta Drive MINI)."""
from montagem import render, WORK, flares_locucao

RAW = f"{WORK}/mini/raw"

A = [
    ("IMG_9363", 5.15, 9.88),    # dentro do carro, olhando para a câmera
    ("IMG_9369", 2.50, 4.98),
    ("IMG_9372", 0.89, 6.05),    # LOCUÇÃO (câmera no salão) — tomada completa, com "60% de entrada"
    ("IMG_9372", 6.55, 10.62),   #   (corta a pausa antes de "taxa")
    ("IMG_9373", 1.90, 4.98),
    ("IMG_9374", 3.50, 6.49),
    ("IMG_9375", 2.40, 5.58),
]

SUBS = [
    (0, 5.15, 7.05, "Design icônico,\npersonalidade marcante"),
    (0, 7.05, 9.88, "e uma experiência\núnica ao dirigir."),
    (1, 2.50, 4.98, "Esse é o MINI Cooper S\n3 Portas."),
    (2, 0.89, 2.40, "E na Arena de Vendas MINI,"),
    (2, 2.40, 4.30, "você escolhe como\nquer conquistar o seu:"),
    (2, 4.30, 6.05, "FIPE no seu usado"),
    (3, 6.55, 8.70, "ou taxa 0%, com\n60% de entrada"),
    (3, 8.70, 10.62, "em até 24 vezes."),
    (4, 1.90, 4.98, "E tem mais: emplacamento\ntotal por nossa conta."),
    (5, 3.50, 6.49, "Uma oportunidade especial\npara viver a experiência MINI."),
    (6, 2.40, 4.50, "Venha para a IESA MINI!"),
    (6, 4.50, 5.58, "Grupo IESA.\nVamos juntos!"),
]

# Sobreposição em toda a locução (falas 2–3); o áudio das imagens é descartado, fica só a voz
dur = [a[2] - a[1] for a in A]
loc_start = dur[0] + dur[1]
loc_len = dur[2] + dur[3]
BROLL = [   # (arquivo, entrada) — trechos conferidos quadro a quadro, carro bem enquadrado
    ("IMG_9376", 1.0),   # frente 3/4, carro inteiro
    ("IMG_9377", 0.5),   # farol + placa IESA MINI
    ("IMG_9368", 0.3),   # porta abrindo, logo projetado no chão
    ("IMG_9364", 0.2),   # tela redonda central
    ("IMG_9366", 0.2),   # volante
    ("IMG_9381", 1.5),   # interior, bancos e teto solar
    ("IMG_9379", 0.2),   # lanterna Union Jack
    ("IMG_9380", 2.0),   # traseira 3/4, carro inteiro
]
step = loc_len / max(1, len(BROLL))
B = [(loc_start + k * step, step, f, s) for k, (f, s) in enumerate(BROLL)]

if __name__ == "__main__":
    render(RAW, A, SUBS, B, "mini_cooper_s_2k60.mp4", "mini",
           music=f"{WORK}/music/trilha_mini_leve.wav",
           font="Soho Gothic Pro", bold=0,   # IESA Regular (fina); MINI não tem encerramento
           flares=flares_locucao([loc_start], [loc_start + loc_len]))
