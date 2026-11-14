#!/usr/bin/env python3
"""Efeitos sonoros originais gerados por código (sem direitos de terceiros).

Uso: python3 sfx.py <pasta_saida>
Gera: whoosh.wav, whoosh_rev.wav, boom.wav, riser.wav, pop.wav, tick.wav, swish.wav
"""
import os, sys, wave
import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
rng = np.random.default_rng(5)


def save(path, x):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.9
    with wave.open(path, "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def sweep_bp(x, f0, f1, q=1.2, blk=256):
    """Filtro passa-faixa com centro varrendo de f0 a f1 (exponencial)."""
    y = np.zeros_like(x)
    n = len(x)
    zi = None
    for i in range(0, n, blk):
        frac = i / max(1, n - 1)
        fc = f0 * (f1 / f0) ** frac
        lo, hi = fc / (1 + 1 / q), min(fc * (1 + 1 / q), SR / 2 - 200)
        sos = butter(2, [lo, hi], "band", fs=SR, output="sos")
        seg = x[i:i + blk]
        y[i:i + blk] = sosfilt(sos, seg)
    return y


def whoosh(dur=0.7, f0=250, f1=7000, reverse=False):
    n = int(dur * SR)
    t = np.arange(n) / n
    noise = rng.standard_normal(n)
    y = sweep_bp(noise, f0, f1)
    env = np.sin(np.pi * t) ** 1.6 * (0.4 + 0.6 * t)       # cresce e some
    y = y * env
    pan = np.clip(t * 1.4 - 0.2, 0, 1)                      # atravessa da esquerda p/ direita
    st = np.stack([y * np.cos(pan * np.pi / 2), y * np.sin(pan * np.pi / 2)], 1)
    return st[::-1] if reverse else st


def boom(dur=1.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 32 + 48 * np.exp(-t * 9)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.6)
    click = sosfilt(butter(2, 1800, "high", fs=SR, output="sos"), rng.standard_normal(n)) * np.exp(-t * 60) * 0.35
    body = sosfilt(butter(2, [80, 900], "band", fs=SR, output="sos"), rng.standard_normal(n)) * np.exp(-t * 7) * 0.5
    y = np.tanh(1.8 * (sub + click + body))
    # cauda com reverb simples
    tail = np.zeros(n)
    for d, g in ((0.043, 0.35), (0.071, 0.28), (0.113, 0.2), (0.171, 0.14)):
        k = int(d * SR)
        tail[k:] += g * y[:-k]
    y = y + sosfilt(butter(2, 2500, "low", fs=SR, output="sos"), tail)
    return np.stack([y, np.roll(y, int(0.007 * SR))], 1)


def riser(dur=1.8):
    n = int(dur * SR)
    t = np.arange(n) / n
    noise = sweep_bp(rng.standard_normal(n), 400, 9000, q=2.0)
    f = 180 * (8 ** t)
    tone = 2 * ((np.cumsum(f) / SR) % 1) - 1
    tone = sosfilt(butter(2, 3000, "low", fs=SR, output="sos"), tone)
    y = (0.7 * noise + 0.25 * tone) * (t ** 2.2)
    y[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR))
    return y


def pop(dur=0.09, f=1400):
    n = int(dur * SR)
    t = np.arange(n) / SR
    fr = f * (1 + 1.5 * np.exp(-t * 80))
    y = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 55)
    return y


def tick(dur=0.03):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = sosfilt(butter(2, [2500, 7000], "band", fs=SR, output="sos"), rng.standard_normal(n)) * np.exp(-t * 300)
    return y


def swish(dur=0.32):
    return whoosh(dur, 900, 9000)


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    save(f"{out}/whoosh.wav", whoosh())
    save(f"{out}/whoosh_rev.wav", whoosh(0.6, reverse=True))
    save(f"{out}/boom.wav", boom())
    save(f"{out}/riser.wav", riser())
    save(f"{out}/pop.wav", pop())
    save(f"{out}/tick.wav", tick())
    save(f"{out}/swish.wav", swish())
    print("OK", out)
