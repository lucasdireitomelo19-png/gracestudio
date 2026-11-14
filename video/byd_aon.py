#!/usr/bin/env python3
"""BYD AON — estilo da referência BMW X2 (texto animado, cartelas, flares, SFX, drop). Pasta Drive BYD."""
from montagem import WORK, ASSETS
from montagem_pro import render_pro

RAW = f"{WORK}/byd/raw"

# Ela fala olhando para a câmera o tempo todo → os planos de carro entram só nos respiros entre frases
TIMELINE = [
    ("fala", "C745", 1.55, 4.55, 1.00),             # 0  Sabe o que mais de 100 mil brasileiros têm em comum?
    ("fala", "C745", 4.95, 6.45, 1.18),             # 1  Todos escolheram a BYD!   (punch-in)
    ("insert", "C755", 0.30, 1.20, (0.12, 0.03, 0.42)),   # 2  logo BYD na parede  → DROP
    ("fala", "C749", 1.90, 3.78, 1.00),             # 3  E não é por acaso!
    ("fala", "C749", 3.80, 8.40, 1.15),             # 4  Com a BYD IESA… estilo de vida.
    ("fala", "C751", 5.60, 8.20, 1.00),             # 5  100% elétrico para aproveitar a cidade.
    ("insert", "C751", 8.55, 1.10, (0.00, 0.30, 0.48)),   # 6  Dolphin Mini, frente
    ("fala", "C752", 1.85, 3.58, 1.00),             # 7  Ou híbrido para ir
    ("fala", "C752", 4.08, 5.90, 1.15),             # 8  mais longe na estrada.
    ("insert", "C752", 10.40, 1.15, (0.00, 0.24, 0.50)),  # 9  Song Premium, frente
    ("fala", "C753", 2.85, 7.30, 1.00),             # 10 Já imaginou rodar muito mais, gastando 3 vezes menos?
    ("fala", "C754", 1.00, 5.75, 1.00),             # 11 É uma nova forma de dirigir…
    ("insert", "C744", 0.20, 1.20, (0.45, 0.45, 0.55)),   # 12 Seal, frente
    ("fala", "C755", 9.30, 13.80, 1.00),            # 13 Escolha seu novo BYD na IESA…
    ("fala", "C756", 7.75, 12.60, 1.15),            # 14 Visite a BYD IESA… Rio Grande do Sul.
]

R = lambda *ws: [(w, t, False) for w, t in ws]
E = lambda *ws: [(w, t, True) for w, t in ws]

CARDS = [
    {"item": 0, "pos": "tl", "lines": [R(("Sabe", 1.60), ("o", 2.16), ("que", 2.30), ("mais", 2.36), ("de", 2.64)),
                                      E(("100 MIL", 2.86)),
                                      R(("brasileiros", 3.14), ("têm", 3.78), ("em", 4.04), ("comum?", 4.22))]},
    {"item": 1, "pos": "c", "lines": [R(("Todos", 5.00), ("escolheram", 5.32), ("a", 5.84)), E(("BYD!", 5.98))]},
    {"item": 3, "pos": "tl", "lines": [R(("E", 1.94), ("não", 2.42), ("é", 2.90)), E(("por acaso!", 3.10))]},
    {"item": 4, "pos": "c", "lines": [R(("Com", 3.82), ("a", 4.06), ("BYD", 4.14), ("IESA,", 4.62), ("você", 5.22),
                                        ("encontra", 5.28), ("a", 5.60)),
                                      E(("tecnologia ideal", 5.74)),
                                      R(("para", 6.98), ("o", 7.38), ("seu", 7.50), ("estilo", 7.62), ("de", 7.90),
                                        ("vida.", 8.12))]},
    {"item": 5, "pos": "tl", "lines": [R(("100%", 5.70), ("elétrico", 6.40), ("para", 6.90), ("aproveitar", 7.16)),
                                      E(("a cidade.", 7.62))]},
    {"item": 7, "pos": "tl", "lines": [R(("Ou", 1.90)), E(("HÍBRIDO", 2.62)), R(("para", 3.16), ("ir", 3.34))]},
    {"item": 8, "pos": "c", "lines": [E(("mais longe", 4.72)), R(("na", 5.42), ("estrada.", 5.66))]},
    {"item": 10, "pos": "c", "lines": [R(("Já", 2.90), ("imaginou", 3.70), ("rodar", 4.38)), E(("muito mais,", 4.84)),
                                       R(("gastando", 5.72)), E(("3x MENOS?", 6.16))]},
    {"item": 11, "pos": "tl", "lines": [R(("É", 1.04), ("uma", 1.72), ("nova", 1.90), ("forma", 2.18), ("de", 2.52),
                                         ("dirigir,", 2.74)),
                                       R(("com", 3.30), ("mais", 3.46)),
                                       E(("tecnologia e autonomia.", 3.74))]},
    {"item": 13, "pos": "tl", "lines": [R(("Escolha", 9.34), ("seu", 9.98), ("novo", 10.16), ("BYD", 10.50),
                                         ("na", 11.00), ("IESA", 11.20)),
                                       R(("e", 11.72), ("descubra", 11.94), ("até", 12.46), ("onde", 12.76)),
                                       E(("ele pode chegar!", 12.98))]},
    {"item": 14, "pos": "c", "lines": [R(("Visite", 7.80), ("a", 8.34)), E(("BYD IESA,", 8.50)),
                                       R(("a", 10.10), ("sua", 10.12), ("concessionária", 10.28), ("BYD", 11.06)),
                                       R(("no", 11.50), ("Rio", 11.66), ("Grande", 11.82), ("do", 12.10), ("Sul.", 12.28))]},
]

TITLES = [
    {"item": 2, "t": 0.05, "texto": "BYD", "sub": "a escolha de mais de 100 mil brasileiros", "y": 0.62},
    {"item": 6, "t": 0.05, "texto": "100% ELÉTRICO", "sub": "BYD Dolphin Mini", "y": 0.16},
    {"item": 9, "t": 0.05, "texto": "HÍBRIDO", "sub": "BYD Song Premium", "y": 0.16},
    {"item": 12, "t": 0.05, "texto": "BYD SEAL", "y": 0.16},
]

if __name__ == "__main__":
    render_pro(RAW, TIMELINE, CARDS, TITLES, "byd_aon_2k60.mp4", "byd",
               music=f"{WORK}/music/trilha_byd.wav", drop_item=2,
               ending=f"{ASSETS}/encerramento_grupo_iesa.mp4")
