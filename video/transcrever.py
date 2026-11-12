#!/usr/bin/env python3
"""Transcreve audio/*.wav de uma pasta de projeto com tempos por palavra -> transcripts.json"""
import glob, json, os, sys, wave
import numpy as np
from faster_whisper import WhisperModel

os.chdir(sys.argv[1])
m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)
out = {}
for f in sorted(glob.glob("audio/*.wav")):
    n = os.path.basename(f)[:-4]
    w = wave.open(f)
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    segs, _ = m.transcribe(a, language="pt", word_timestamps=True)
    out[n] = [[round(x.start, 2), round(x.end, 2), x.word.strip()] for s in segs for x in s.words]
    print(n, " ".join(x[2] for x in out[n]), flush=True)
json.dump(out, open("transcripts.json", "w"), ensure_ascii=False, indent=0)
