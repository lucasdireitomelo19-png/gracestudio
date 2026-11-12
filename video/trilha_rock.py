#!/usr/bin/env python3
"""Gera uma trilha de rock original (sem direitos de terceiros): bateria, baixo e guitarra distorcida.

Uso: python3 trilha_rock.py saida.wav [segundos]
"""
import sys, wave
import numpy as np

SR = 48000
BPM = 112
BEAT = 60 / BPM
rng = np.random.default_rng(7)


def env(n, a=0.002, r=0.1):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / r)


def kick(n):
    t = np.arange(n) / SR
    f = 50 + 90 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.18)


def snare(n):
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    noise = np.convolve(noise, [1, -0.6], "same")
    return (0.7 * noise * env(n, 0.001, 0.09) + 0.4 * np.sin(2 * np.pi * 190 * t) * env(n, 0.001, 0.06))


def hat(n):
    noise = rng.standard_normal(n)
    noise = noise - np.convolve(noise, np.ones(4) / 4, "same")
    return noise * env(n, 0.001, 0.025)


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.zeros_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def saw(freq, n, detune=0.0):
    t = np.arange(n) / SR
    f = freq * (1 + detune)
    return 2 * ((t * f) % 1) - 1


def power_chord(root, n):
    # quinta + oitava, 2 vozes desafinadas cada, distorção suave
    x = sum(saw(root * m, n, d) for m in (1, 1.4983, 2) for d in (-0.004, 0.004))
    x = np.tanh(3.5 * x / 3)
    return x * env(n, 0.004, 0.9)


def midi(n):
    return 440 * 2 ** ((n - 69) / 12)


def make(seconds):
    total = int(seconds * SR)
    mix = np.zeros(total + SR * 2)
    eighth = int(BEAT / 2 * SR)

    # riff em Mi: E5 . E5 G5 | A5 . A5 G5  (colcheias), 2 compassos repetindo
    riff = [40, None, 40, 43, 45, None, 45, 43, 40, None, 40, 43, 38, None, 38, 35]
    bass = [28, 28, 28, 31, 33, 33, 33, 31, 28, 28, 28, 31, 26, 26, 26, 23]
    gtr = np.zeros_like(mix)
    bss = np.zeros_like(mix)
    drm = np.zeros_like(mix)

    step = 0
    pos = 0
    while pos < total:
        i = step % 16
        # guitarra
        note = riff[i]
        if note is not None:
            hold = eighth * (2 if (i + 1 < 16 and riff[(i + 1) % 16] is None) else 1)
            seg = power_chord(midi(note), hold)
            gtr[pos:pos + hold] += seg[: len(gtr) - pos]
        # baixo
        bseg = np.tanh(2 * saw(midi(bass[i]), eighth)) * env(eighth, 0.003, 0.25)
        bss[pos:pos + eighth] += bseg[: len(bss) - pos]
        # bateria: bumbo 1 e 3 (+ síncope), caixa 2 e 4, chimbal em colcheias
        beat_in_bar = i % 8
        if beat_in_bar in (0, 5):
            k = kick(int(0.3 * SR)); drm[pos:pos + len(k)] += k[: len(drm) - pos]
        if beat_in_bar in (2, 6):
            s = snare(int(0.25 * SR)); drm[pos:pos + len(s)] += 0.8 * s[: len(drm) - pos]
        h = hat(int(0.08 * SR)); drm[pos:pos + len(h)] += 0.18 * h[: len(drm) - pos]
        pos += eighth
        step += 1

    gtr = lowpass(gtr, 3200)
    bss = lowpass(bss, 900)
    drm = lowpass(drm, 7000)
    mix = 0.33 * gtr + 0.45 * bss + 0.6 * drm
    mix = mix[:total]
    fade = int(0.02 * SR)
    mix[:fade] *= np.linspace(0, 1, fade)
    mix = np.tanh(1.2 * mix)
    mix /= np.max(np.abs(mix)) + 1e-9
    stereo = np.stack([mix, np.roll(mix, int(0.012 * SR))], axis=1) * 0.89
    return stereo


if __name__ == "__main__":
    out = sys.argv[1]
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 40
    y = make(secs)
    with wave.open(out, "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((y * 32767).astype(np.int16).tobytes())
    print("OK", out)
