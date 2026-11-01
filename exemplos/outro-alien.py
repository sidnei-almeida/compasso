#!/usr/bin/env python3
"""The outro's sound: relief after the episode, still Sevastopol. Reuses the intro's engine
(scripts/intro-sound.py): a calm Stable Audio bed, the station hum far away and a soft impact under
the film burn. No tracker: the owner wants it purely chill.

  python3 -I scripts/outro-sound.py [out.wav] [outro-piano-1|outro-pad-1|outro-strings-1]
"""
import importlib.util, math, sys, wave
import numpy as np

spec = importlib.util.spec_from_file_location("intro", __file__.replace("outro-sound.py", "intro-sound.py"))
intro = importlib.util.module_from_spec(spec)
sys.argv, saved = sys.argv[:1], sys.argv   # the intro module reads its own argv at import
spec.loader.exec_module(intro)
sys.argv = saved

SR, n = intro.SR, intro.n
LENGTH = 30.0
BED = sys.argv[2] if len(sys.argv) > 2 else "mix"   # "mix" = strings crossfading into piano; or one bed name
BEAT_S = 1.0    # the intro's 60 bpm, the tracker keeps it

EVENTS = [
    # the bed: strings for the first half, crossfading into the piano (or a single bed)
    *([(0.0, "layer", dict(path="brand/music/sa3/outro-strings-1.wav", gain=0.85, fade=0.8, length=18, fade_out=5.0)),
       (11.0, "layer", dict(path="brand/music/sa3/outro-piano-1.wav", gain=0.9, fade=5.0))]
      if BED == "mix" else [(0.0, "layer", dict(path=f"brand/music/sa3/{BED}.wav", gain=0.85, fade=0.8))]),
    (0.0, "hum", dict(length=LENGTH, fade_in=2.5)),
    (0.45, "layer", dict(path="brand/music/sa3/impact-orch-2.wav", gain=0.3, align_peak=True)),   # under the burn, soft
]

def main(out):
    total = n(LENGTH + 2)
    mix = np.zeros((2, total), dtype=np.float32)
    for when, kind, params in EVENTS:
        x = intro.GEN[kind](**params)
        off = 0
        if isinstance(x, tuple): x, off = x
        s = intro.stereo(x, width=0.0 if kind == "hum" else 0.01)
        if kind == "tracker":
            pan = intro.rng.uniform(-0.5, 0.5); s[0] *= 1 - max(0, pan); s[1] *= 1 + min(0, pan)
        i = n(when) - off; c = max(0, -i); i = max(0, i); s = s[:, c:]; j = min(total, i + s.shape[1])
        mix[:, i:j] += s[:, : j - i]
    end = n(LENGTH); f = n(4.0)
    mix[:, end - f:end] *= np.linspace(1, 0, f); mix = mix[:, :end]
    peak = np.abs(mix).max(); mix = np.tanh(mix / peak * 1.3) / math.tanh(1.3) * 0.9
    with wave.open(out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix.T * 32767).astype("<i2").tobytes())
    print(out, f"{LENGTH:.0f}s bed={BED}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "public/alien/music-outro-sd.wav")
