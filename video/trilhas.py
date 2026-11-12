#!/usr/bin/env python3
"""Trilhas originais por marca (geradas por código: sem direitos de terceiros, sem crédito).

Uso: python3 trilhas.py <estilo> saida.wav [segundos]
Estilos: premium (BMW carros), aventura (BMW Motorrad), pop (MINI), calmo (Volvo), corporativo (pós-venda)
O rock da Harley fica em trilha_rock.py.
"""
import sys, wave
import numpy as np

SR = 48000
rng = np.random.default_rng(11)


def midi(n):
    return 440 * 2 ** ((n - 69) / 12)


def env(n, a=0.005, r=0.3):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / r)


def adsr(n, a=0.3, rel=0.4):
    t = np.arange(n) / SR
    up = np.minimum(1, t / a)
    down = np.clip((n / SR - t) / rel, 0, 1)
    return up * down


def onepole(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def saw(f, n, det=0.0):
    t = np.arange(n) / SR
    return 2 * ((t * f * (1 + det)) % 1) - 1


def sine(f, n):
    return np.sin(2 * np.pi * f * np.arange(n) / SR)


def kick(n, punch=1.0):
    t = np.arange(n) / SR
    f = 45 + 80 * punch * np.exp(-t * 35)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.22)


def clap(n):
    x = rng.standard_normal(n)
    x = x - onepole(x, 1200)
    return x * env(n, 0.002, 0.07)


def hat(n):
    x = rng.standard_normal(n)
    x = x - np.convolve(x, np.ones(6) / 6, "same")
    return x * env(n, 0.001, 0.03)


def pad(notes, n, cutoff=1800):
    x = sum(saw(midi(m), n, d) for m in notes for d in (-0.006, 0.0, 0.006))
    return onepole(x / (3 * len(notes)), cutoff) * adsr(n, 0.4, 0.5)


def pluck(note, n, bright=0.5):
    f = midi(note)
    x = sine(f, n) + bright * 0.5 * sine(2 * f, n) + bright * 0.25 * sine(3 * f, n)
    return x * env(n, 0.003, 0.25)


def piano(note, n):
    f = midi(note)
    x = sum(sine(f * k, n) * (0.6 ** (k - 1)) for k in range(1, 6))
    return x * env(n, 0.004, 0.9)


def add(buf, pos, seg, gain=1.0):
    end = min(len(buf), pos + len(seg))
    if end > pos:
        buf[pos:end] += gain * seg[: end - pos]


def render(style, seconds, bpm_override=None, transpose=0):
    cfg = {
        #            bpm, progressão (raízes midi), acordes menores?, ...
        "premium":     (100, [57, 53, 60, 55]),   # Am F C G — elegante, sóbrio
        "aventura":    (118, [52, 48, 55, 50]),   # Em C G D — energia de estrada
        "pop":         (124, [60, 67, 69, 65]),   # C G Am F — leve, divertido
        "calmo":       (78,  [53, 57, 48, 55]),   # F Am C G — sereno, minimalista
        "corporativo": (106, [60, 65, 57, 67]),   # C F Am G — positivo
    }[style]
    bpm, prog = cfg
    bpm = bpm_override or bpm
    prog = [r + transpose for r in prog]
    beat = 60 / bpm
    bar = int(4 * beat * SR)
    total = int(seconds * SR)
    L = total + SR
    drums, bass, harm, lead = (np.zeros(L) for _ in range(4))

    def chord(root):
        minor = root in (57, 52, 69, 50) if style != "calmo" else root == 57
        return [root, root + (3 if minor else 4), root + 7, root + 12]

    b = 0
    while b * bar < total:
        pos = b * bar
        root = prog[b % 4]
        notes = chord(root)
        # harmonia
        if style in ("premium", "aventura", "corporativo", "calmo"):
            add(harm, pos, pad([n for n in notes[:3]], bar, 1400 if style == "calmo" else 2200))
        if style == "calmo":
            for k, m in enumerate([notes[0] + 12, notes[2] + 12, notes[1] + 24, notes[2] + 12]):
                add(lead, pos + int(k * beat * SR), piano(m, int(2 * beat * SR)), 0.5)
        # baixo
        steps = 8
        for s in range(steps):
            p = pos + int(s * beat / 2 * SR)
            n8 = int(beat / 2 * SR)
            if style in ("premium", "aventura"):
                add(bass, p, np.tanh(2 * sine(midi(root - 24), n8)) * env(n8, 0.003, 0.12))
            elif style in ("pop", "corporativo") and s % 2 == 0:
                add(bass, p, sine(midi(root - 24), n8 * 2) * env(n8 * 2, 0.003, 0.2))
            elif style == "calmo" and s == 0:
                add(bass, p, sine(midi(root - 24), bar) * adsr(bar, 0.2, 0.6), 0.8)
        # arpejo / melodia
        if style in ("premium", "aventura", "pop", "corporativo"):
            arp = [notes[0] + 12, notes[1] + 12, notes[2] + 12, notes[3] + 12]
            div = 4 if style in ("aventura", "pop") else 2   # semicolcheias ou colcheias
            for s in range(4 * div):
                p = pos + int(s * beat / div * SR)
                m = arp[s % 4] + (12 if style == "pop" and s % 8 == 7 else 0)
                add(lead, p, pluck(m, int(beat / div * SR * 1.5), 0.9 if style == "pop" else 0.4), 0.35)
        # bateria
        for q in range(4):
            p = pos + int(q * beat * SR)
            if style == "calmo":
                if q == 0:
                    add(drums, p, kick(int(0.3 * SR), 0.6), 0.5)
                continue
            if style in ("pop", "aventura") or q in (0, 2):
                add(drums, p, kick(int(0.3 * SR)), 0.9)
            if q in (1, 3):
                add(drums, p, clap(int(0.2 * SR)), 0.45 if style != "premium" else 0.3)
            for h in range(2):
                add(drums, p + int(h * beat / 2 * SR), hat(int(0.05 * SR)), 0.12 if h else 0.06)
        b += 1

    mixes = {
        "premium":     (0.7, 0.5, 0.45, 0.35),
        "aventura":    (0.8, 0.5, 0.4, 0.4),
        "pop":         (0.75, 0.45, 0.0, 0.5),
        "calmo":       (0.4, 0.4, 0.6, 0.6),
        "corporativo": (0.6, 0.45, 0.4, 0.45),
    }[style]
    mix = mixes[0] * drums + mixes[1] * onepole(bass, 600) + mixes[2] * harm + mixes[3] * onepole(lead, 5000)
    mix = mix[:total]
    f = int(0.02 * SR)
    mix[:f] *= np.linspace(0, 1, f)
    mix = np.tanh(1.3 * mix / (np.max(np.abs(mix)) + 1e-9))
    mix /= np.max(np.abs(mix)) + 1e-9
    st = np.stack([mix, np.roll(mix, int(0.011 * SR))], 1) * 0.89
    return st


if __name__ == "__main__":
    style, out = sys.argv[1], sys.argv[2]
    secs = float(sys.argv[3]) if len(sys.argv) > 3 else 45
    bpm = float(sys.argv[4]) if len(sys.argv) > 4 else None
    tr = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    y = render(style, secs, bpm, tr)
    with wave.open(out, "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((y * 32767).astype(np.int16).tobytes())
    print("OK", out)
