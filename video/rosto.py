#!/usr/bin/env python3
"""Detecta a região da cabeça da pessoa num trecho de vídeo (para a legenda não cobrir o rosto).

Retorna (x0, y0, x1, y1) em frações do quadro FINAL (já com zoom/corte 9:16 aplicados), ou None.
"""
import subprocess
import numpy as np
import cv2

_casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
_prof = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")


def _frame(path, t, w=540):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1",
                          "-vf", f"scale={w}:-2", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True).stdout
    h = len(raw) // w
    return np.frombuffer(raw, np.uint8)[: w * h].reshape(h, w) if h else None


def cabeca(path, s, e, zoom=1.0, amostras=7):
    """Une as detecções de rosto ao longo do trecho e expande para cobrir cabelo/testa."""
    boxes = []
    for k in range(amostras):
        t = s + (e - s) * (k + 0.5) / amostras
        g = _frame(path, t)
        if g is None:
            continue
        H, W = g.shape
        g = cv2.equalizeHist(g)
        found = list(_casc.detectMultiScale(g, 1.1, 5, minSize=(W // 30, W // 30)))
        if not found:
            found = list(_prof.detectMultiScale(g, 1.1, 5, minSize=(W // 30, W // 30)))
        for (x, y, w, h) in found:
            boxes.append((x / W, y / H, (x + w) / W, (y + h) / H))
    if not boxes:
        return None
    b = np.array(boxes)
    # descarta falsos positivos: fica com as detecções coerentes com a mediana (posição e tamanho)
    cx, cy = (b[:, 0] + b[:, 2]) / 2, (b[:, 1] + b[:, 3]) / 2
    sz = b[:, 2] - b[:, 0]
    mcx, mcy, msz = np.median(cx), np.median(cy), np.median(sz)
    ok = (np.abs(cx - mcx) < 0.10) & (np.abs(cy - mcy) < 0.08) & (sz > 0.5 * msz) & (sz < 2 * msz)
    b = b[ok] if ok.any() else b
    x0, y0 = b[:, 0].min(), b[:, 1].min()
    x1, y1 = b[:, 2].max(), b[:, 3].max()
    fw, fh = x1 - x0, y1 - y0
    # cabeça inteira: cabelo acima, queixo/pescoço abaixo, laterais
    x0, x1 = x0 - 0.35 * fw, x1 + 0.35 * fw
    y0, y1 = y0 - 0.55 * fh, y1 + 0.45 * fh
    # aplica o zoom central do plano (z > 1 amplia em torno do centro)
    conv = lambda v: 0.5 + (v - 0.5) * zoom
    return (max(0, conv(x0)), max(0, conv(y0)), min(1, conv(x1)), min(1, conv(y1)))


if __name__ == "__main__":
    import sys
    print(cabeca(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]) if len(sys.argv) > 4 else 1.0))
