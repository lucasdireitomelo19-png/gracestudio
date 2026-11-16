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


# Estilo da referência: linhas curtas, mesmo tamanho; (palavra, tempo, negrito?) — negrito = destaque
def L(*ws):
    return [(w, t, b) for w, t, b in ws]

CARDS = [
    {"item": 0, "pos": "tl", "lines": [L(("Sabe", 1.60, 0), ("o", 2.16, 0), ("que", 2.30, 0), ("mais", 2.36, 0), ("de", 2.64, 0)),
                                      L(("100", 2.86, 1), ("mil", 2.94, 1), ("brasileiros", 3.14, 0)),
                                      L(("têm", 3.78, 0), ("em", 4.04, 0), ("comum?", 4.22, 1))]},
    {"item": 1, "pos": "c", "lines": [L(("Todos", 5.00, 0), ("escolheram", 5.32, 0)),
                                      L(("a", 5.84, 0), ("BYD!", 5.98, 1))]},
    {"item": 3, "pos": "tl", "lines": [L(("E", 1.94, 0), ("não", 2.42, 0), ("é", 2.90, 0)),
                                      L(("por", 3.10, 1), ("acaso!", 3.26, 1))]},
    {"item": 4, "pos": "c", "lines": [L(("Com", 3.82, 0), ("a", 4.06, 0), ("BYD", 4.14, 1), ("IESA,", 4.62, 1)),
                                      L(("você", 5.22, 0), ("encontra", 5.28, 0), ("a", 5.60, 0)),
                                      L(("tecnologia", 5.74, 1), ("ideal", 6.24, 1)),
                                      L(("para", 6.98, 0), ("o", 7.38, 0), ("seu", 7.50, 0), ("estilo", 7.62, 0), ("de", 7.90, 0), ("vida.", 8.12, 0))]},
    {"item": 5, "pos": "tl", "lines": [L(("100%", 5.70, 1), ("elétrico", 6.40, 1)),
                                      L(("para", 6.90, 0), ("aproveitar", 7.16, 0)),
                                      L(("a", 7.62, 0), ("cidade.", 7.76, 1))]},
    {"item": 7, "pos": "tl", "lines": [L(("Ou", 1.90, 0), ("híbrido", 2.62, 1)),
                                      L(("para", 3.16, 0), ("ir", 3.34, 0))]},
    {"item": 8, "pos": "c", "lines": [L(("mais", 4.72, 1), ("longe", 5.06, 1)),
                                      L(("na", 5.42, 0), ("estrada.", 5.66, 0))]},
    {"item": 10, "pos": "c", "lines": [L(("Já", 2.90, 0), ("imaginou", 3.70, 0), ("rodar", 4.38, 0)),
                                       L(("muito", 4.84, 1), ("mais,", 5.22, 1)),
                                       L(("gastando", 5.72, 0), ("3x", 6.16, 1), ("menos?", 6.84, 1))]},
    {"item": 11, "pos": "tl", "lines": [L(("É", 1.04, 0), ("uma", 1.72, 0), ("nova", 1.90, 1), ("forma", 2.18, 1)),
                                       L(("de", 2.52, 0), ("dirigir,", 2.74, 0), ("com", 3.30, 0), ("mais", 3.46, 0)),
                                       L(("tecnologia", 3.74, 1), ("e", 4.50, 0), ("autonomia.", 4.96, 1))]},
    {"item": 13, "pos": "tl", "lines": [L(("Escolha", 9.34, 0), ("seu", 9.98, 0), ("novo", 10.16, 0), ("BYD", 10.50, 1)),
                                       L(("na", 11.00, 0), ("IESA", 11.20, 1), ("e", 11.72, 0), ("descubra", 11.94, 0)),
                                       L(("até", 12.46, 0), ("onde", 12.76, 0), ("ele", 12.98, 0), ("pode", 13.20, 1), ("chegar!", 13.38, 1))]},
    {"item": 14, "pos": "c", "lines": [L(("Visite", 7.80, 0), ("a", 8.34, 0), ("BYD", 8.50, 1), ("IESA,", 8.98, 1)),
                                       L(("a", 10.10, 0), ("sua", 10.12, 0), ("concessionária", 10.28, 0), ("BYD", 11.06, 1)),
                                       L(("no", 11.50, 0), ("Rio", 11.66, 1), ("Grande", 11.82, 1), ("do", 12.10, 1), ("Sul.", 12.28, 1))]},
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
               ending=f"{ASSETS}/encerramento_grupo_iesa.mp4",
               cor=False,                    # sem correção de cor: mantém o bruto
               reaproveitar=True)
