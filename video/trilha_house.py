#!/usr/bin/env python3
"""Deep house / techno tranquilo — trilha original gerada por código (sem direitos de terceiros).

Uso: python3 trilha_house.py saida.wav [segundos] [bpm]  (Volvo: 112 bpm)
Estrutura: bumbo 4/4, palma no 2 e 4, chimbal aberto no contratempo, shaker em 16ª,
baixo no contratempo, acordes com 7ª/9ª com sidechain ("pump") e filtro abrindo aos poucos.
"""
import sys, wave
import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
rng = np.random.default_rng(23)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def lp(x, fc, order=2):
    return sosfilt(butter(order, min(fc, SR / 2 - 100), "low", fs=SR, output="sos"), x)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)


def bp(x, f1, f2):
    return sosfilt(butter(2, [f1, f2], "band", fs=SR, output="sos"), x)


def expenv(n, rel, att=0.002):
    t = np.arange(n) / SR
    return np.minimum(1, t / att) * np.exp(-t / rel)


def kick(n):
    t = np.arange(n) / SR
    f = 48 + 110 * np.exp(-t * 40)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * expenv(n, 0.28, 0.001)
    click = hp(rng.standard_normal(n), 3000) * expenv(n, 0.004, 0.0005) * 0.3
    return np.tanh(1.6 * (body + click))


def clap(n):
    x = bp(rng.standard_normal(n), 900, 5000)
    e = np.zeros(n)
    for d in (0.0, 0.011, 0.022):           # 3 batidas rápidas = palma
        k = int(d * SR)
        e[k:] += expenv(n - k, 0.012 if d < 0.02 else 0.12, 0.0008)
    return x * e * 0.8


def hat(n, open_=False):
    x = hp(rng.standard_normal(n), 7000)
    return x * expenv(n, 0.11 if open_ else 0.025, 0.001)


def shaker(n):
    return bp(rng.standard_normal(n), 5000, 12000) * expenv(n, 0.035, 0.008)


def supersaw(freqs, n):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f in freqs:
        for det in (-0.007, -0.002, 0.003, 0.008):
            ph = rng.random()
            out += 2 * ((t * f * (1 + det) + ph) % 1) - 1
    return out / (4 * len(freqs))


def render(seconds=45, bpm=122, style="deep"):
    beat = 60 / bpm
    s16 = beat / 4
    bar = 4 * beat
    total = int(seconds * SR)
    L = total + SR
    kick_t, clap_t, oh_t, ch_t, sh_t, bass_t, chords = (np.zeros(L) for _ in range(7))

    # Am9 – Fmaj9 – Cmaj9 – Em9 (uma por compasso): sofisticado, calmo
    prog = [
        (45, [57, 60, 64, 67, 71]),   # Am9
        (41, [57, 60, 64, 65, 69]),   # Fmaj9 (voicing alto)
        (48, [55, 59, 62, 64, 67]),   # Cmaj9
        (40, [55, 59, 62, 66, 67]),   # Em9
    ]
    if style == "deep_d":     # Volvo XC60 — Dm9, Bbmaj9, Fmaj9, Cadd9
        prog = [(38, [53, 57, 60, 64, 65]), (46, [53, 57, 58, 62, 65]),
                (41, [52, 55, 57, 60, 64]), (36, [52, 55, 60, 62, 64])]
    if style == "deep_g":     # BMW Série 3 — Gm9, Ebmaj9, Bbmaj9, F6/9
        prog = [(43, [58, 62, 65, 69, 70]), (39, [55, 58, 62, 65, 67]),
                (46, [57, 60, 62, 65, 69]), (41, [55, 57, 60, 62, 65])]
    if style in ("funky", "leve"):
        # Cmaj7 – Am7 – Dm7 – G9: maior, leve (MINI). "leve" = acordes longos como o deep
        prog = [
            (48, [64, 67, 71, 72, 76]),   # Cmaj7
            (45, [64, 67, 69, 72, 76]),   # Am7
            (50, [65, 69, 72, 74, 77]),   # Dm7
            (43, [65, 67, 71, 74, 81]),   # G9
        ]

    def put(buf, pos, seg, g=1.0):
        e = min(len(buf), pos + len(seg))
        if e > pos:
            buf[pos:e] += g * seg[: e - pos]

    nbars = int(np.ceil(seconds / bar)) + 1
    for b in range(nbars):
        p0 = int(b * bar * SR)
        root, notes = prog[b % 4]
        # acordes sustentados no compasso (vão receber filtro + sidechain depois)
        if style == "funky":
            # stabs curtos e sincopados (padrão disco): 16ª 2, 5, 7, 10, 13, 15
            for k in (2, 5, 7, 10, 13, 15):
                n = int(s16 * 0.85 * SR)
                put(chords, p0 + int(k * s16 * SR),
                    supersaw([midi(m) for m in notes], n) * expenv(n, 0.09, 0.003), 2.8)
        else:
            put(chords, p0, supersaw([midi(m) for m in notes], int(bar * SR)))
        for q in range(4):
            pq = p0 + int(q * beat * SR)
            put(kick_t, pq, kick(int(0.35 * SR)))
            if q in (1, 3):
                put(clap_t, pq, clap(int(0.3 * SR)))
            put(oh_t, pq + int(beat / 2 * SR), hat(int(0.2 * SR), True))   # contratempo
            for k in range(4):
                put(sh_t, pq + int(k * s16 * SR), shaker(int(0.06 * SR)) * (1.0 if k % 2 else 0.55))
            # baixo no contratempo (e uma nota extra na última 16ª de alguns tempos)
            nb = int(beat / 2 * 0.9 * SR)
            f = midi(root - 12)
            t = np.arange(nb) / SR
            bnote = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * expenv(nb, 0.18, 0.004)
            put(bass_t, pq + int(beat / 2 * SR), bnote)
            if style == "funky":   # baixo de oitava pulando (disco)
                nb3 = int(s16 * 0.8 * SR)
                t3 = np.arange(nb3) / SR
                put(bass_t, pq + int(3 * s16 * SR),
                    np.sin(2 * np.pi * midi(root) * t3) * expenv(nb3, 0.07, 0.003), 0.7)
            if q == 3 and b % 2 == 1:
                nb2 = int(s16 * 0.9 * SR)
                t2 = np.arange(nb2) / SR
                put(bass_t, pq + int(3 * s16 * SR),
                    np.sin(2 * np.pi * midi(root - 5) * t2) * expenv(nb2, 0.08, 0.003), 0.8)

    t = np.arange(L) / SR
    # filtro dos acordes abrindo lentamente + LFO suave
    chords_f = np.zeros(L)
    blk = int(0.05 * SR)
    for i in range(0, L, blk):
        tt = i / SR
        fc = 1400 + 2600 * min(1, tt / 12) + 600 * np.sin(2 * np.pi * tt / (bar * 2))
        if style == "funky":
            fc = 3500 + 1500 * np.sin(2 * np.pi * tt / (bar * 2))
        seg = chords[max(0, i - blk): i + blk]
        y = lp(seg, fc, 2)
        chords_f[i: i + blk] = y[-min(blk, L - i):] if i else y[:blk]
    # sidechain: tudo menos bumbo abaixa logo após cada batida
    pos_in_beat = (t % beat) / beat
    duck = 0.35 + 0.65 * np.minimum(1, pos_in_beat / 0.45) ** 1.5

    drums = 0.55 * kick_t + 0.35 * clap_t + 0.22 * oh_t + 0.12 * sh_t
    music = (0.45 * lp(bass_t, 700) + 1.6 * chords_f) * duck
    # reverb simples (delays com feedback) nos acordes/palmas
    wet = np.zeros(L)
    src = 1.2 * chords_f * duck + 0.2 * clap_t
    for d, g in ((0.031, 0.5), (0.047, 0.4), (0.071, 0.33), (0.113, 0.25), (0.173, 0.18)):
        k = int(d * SR)
        wet[k:] += g * src[:-k]
    wet = lp(wet, 4500)
    mix = (drums + music + 0.5 * wet)[:total]
    f = int(0.02 * SR)
    mix[:f] *= np.linspace(0, 1, f)
    mix = np.tanh(1.2 * mix / (np.max(np.abs(mix)) + 1e-9))
    mix /= np.max(np.abs(mix)) + 1e-9
    right = np.roll(mix, int(0.009 * SR)) * 0.96 + 0.04 * mix
    return np.stack([mix, right], 1) * 0.89


if __name__ == "__main__":
    out = sys.argv[1]
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 45
    bpm = float(sys.argv[3]) if len(sys.argv) > 3 else 122
    style = sys.argv[4] if len(sys.argv) > 4 else "deep"   # deep (Volvo) | leve (MINI) | funky
    y = render(secs, bpm, style)
    with wave.open(out, "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((y * 32767).astype(np.int16).tobytes())
    print("OK", out)
