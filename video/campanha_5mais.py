#!/usr/bin/env python3
"""BMW e MINI — Campanha 5+ (pós-venda, troca de óleo) (pasta Drive BMW pós-venda)."""
from montagem import render, WORK, flares_locucao

RAW = f"{WORK}/posvenda/raw"

A = [
    ("IMG_9401", 2.22, 7.46),    # cena 1, sofá
    ("IMG_9403", 5.48, 8.37),    # "Vou te explicar…" (2ª tomada, close)
    ("IMG_9405", 2.86, 8.39),    # cena 2, caminhando (sem o "eu vou caminhando?")
    ("IMG_9406", 6.72, 15.86),   # cena 3 — LOCUÇÃO (lendo no celular), 2ª leitura
    ("IMG_9407", 3.36, 4.36),    # cena 4 — "E não é só óleo!"
    ("IMG_9411", 0.62, 2.03),    # "A manutenção…"
    ("IMG_9411", 2.94, 8.23),    # "…inclui também o filtro…" (corta a pausa)
    ("IMG_9412", 10.48, 13.46),  # cena 5 — prazo (ver observação no relatório)
    ("IMG_9415", 2.03, 6.11),
    ("IMG_9416", 3.31, 7.03),    # "Agende sua manutenção conosco. Grupo IESA, vamos juntos!"
]

SUBS = [
    (0, 2.22, 4.50, "Você sabia que seu BMW ou MINI\ncom mais de 5 anos"),
    (0, 4.50, 7.46, "tem uma condição especial\nna troca de óleo?"),
    (1, 5.48, 8.37, "Vou te explicar como\nfunciona a Campanha 5+!"),
    (2, 2.86, 6.75, "Veículos BMW e MINI\nfabricados até março de 2021"),
    (2, 6.75, 8.39, "podem aproveitar\nessa condição."),
    (3, 6.72, 9.40, "Na realização da troca de óleo\naqui na concessionária,"),
    (3, 9.40, 11.70, "você ganha 2 litros\nde óleo com desconto:"),
    (3, 11.70, 15.86, "1 litro de óleo Raízen e\n1 litro de óleo original BMW."),
    (4, 3.36, 4.36, "E não é só óleo!"),
    (5, 0.62, 2.03, "A manutenção inclui"),
    (6, 2.94, 6.25, "também o filtro de óleo\ne a mão de obra,"),
    (6, 6.25, 8.23, "seguindo todos os\npadrões de manutenção."),
    (7, 10.48, 13.46, "A campanha é válida\naté dezembro de 2026."),
    (8, 2.03, 4.85, "Então, se o seu BMW ou MINI\ntem mais de 5 anos,"),
    (8, 4.85, 6.11, "aproveite essa condição."),
    (9, 3.31, 5.15, "Agende sua manutenção conosco."),
    (9, 5.15, 7.03, "Grupo IESA.\nVamos juntos!"),
]

# Coberturas em toda a locução (fala 3); áudio das imagens descartado
dur = [a[2] - a[1] for a in A]
loc_start, loc_len = sum(dur[:3]), dur[3]
BROLL = [   # oficina — trechos conferidos, carro bem enquadrado
    ("IMG_9417", 0.3),   # carro no elevador
    ("IMG_9425", 0.3),   # X1 na oficina
    ("IMG_9419", 0.3),   # motor BMW, capô aberto
    ("IMG_9427", 0.5),   # capô aberto, frente
    ("IMG_9421", 0.3),   # motor + farol
    ("IMG_9423", 0.3),   # MINI verde
    ("IMG_9418", 0.3),   # X4 traseira
]
step = loc_len / len(BROLL)
B = [(loc_start + k * step, step, f, s) for k, (f, s) in enumerate(BROLL)]

if __name__ == "__main__":
    render(RAW, A, SUBS, B, "campanha_5mais_2k60.mp4", "5mais",
           music=f"{WORK}/music/trilha_corporativo.wav",
           font="Soho Gothic Pro", bold=0,   # IESA Regular (fina); sem encerramento
           flares=flares_locucao([loc_start], [loc_start + loc_len]))
