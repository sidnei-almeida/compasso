#!/usr/bin/env python3
"""Make a bed loop seamlessly: the last X seconds are crossfaded into the first X seconds, and the
result is shorter by X. Equal-power crossfade, 16-bit WAV in and out.
  make-loop.py in.wav out.wav [seconds]
"""
import sys, wave
import numpy as np

src, dst = sys.argv[1], sys.argv[2]
x_s = float(sys.argv[3]) if len(sys.argv) > 3 else 4.0
with wave.open(src, "rb") as w:
    sr, ch = w.getframerate(), w.getnchannels()
    a = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32).reshape(-1, ch) / 32768
n = int(x_s * sr)
if len(a) <= 2 * n:
    sys.exit(f"{src}: too short for a {x_s}s crossfade")
head, body, tail = a[:n], a[n:-n], a[-n:]
t = np.linspace(0, 1, n, dtype=np.float32)[:, None]
mixed = tail * np.cos(t * np.pi / 2) + head * np.sin(t * np.pi / 2)   # tail fades out, head fades in
out = np.concatenate([mixed, body])  # the loop point is the file's end -> start
with wave.open(dst, "wb") as w:
    w.setnchannels(ch); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((np.clip(out, -1, 1) * 32767).astype("<i2").tobytes())
print(dst, f"{len(out)/sr:.1f}s")
