#!/usr/bin/env python3
"""cue.py: the little sound-design engine behind the Lapso intros (numpy only, 48 kHz stereo).
A cue is a list of events (time in seconds, kind, params) mixed onto a beat grid:
  synth layers   hum, sub, ping, riser, hit, cluster, shriek, tick, drums, score_beat
  samples        layer(path, gain, align_peak=True ...)  any wav; align_peak puts its loudest moment on the event time
                 sample(id, ...)  wavs from SFX_DIR/<id>.wav;  tracker(path, pitch)  a looped one-shot sped up
Grid: set BPM and use bar(b, beat) for times. Render with render(events, length, out, final_at=None).
See README.md and exemplos/.
"""
import math, sys, wave
import numpy as np

SR = 48000
BPM = 60.0
BEAT_S = 60.0 / BPM
def bar(b, beat=0.0): return (b * 4 + beat) * BEAT_S
SFX_DIR = "sfx"          # where sample(id) looks
STING_1 = STING_2 = STING_3 = FINAL = 0.0   # set by the cue if it uses them

# ---- helpers ---------------------------------------------------------------------------------
def n(sec): return int(sec * SR)
def t(sec): return np.arange(n(sec)) / SR
rng = np.random.default_rng(42)

def noise(sec): return rng.standard_normal(n(sec)).astype(np.float32)

def fftfilter(x, lo=None, hi=None, slope=1.0):
    """Band-limit x between lo and hi Hz with soft edges (slope in octaves)."""
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); m = np.ones_like(f)
    if lo: m *= 1 / (1 + (np.maximum(lo, 1) / np.maximum(f, 1)) ** (4 / slope))
    if hi: m *= 1 / (1 + (np.maximum(f, 1) / hi) ** (4 / slope))
    return np.fft.irfft(X * m, len(x)).astype(np.float32)

def env(x, attack, release, hold=None):
    """Attack/release envelope over the whole buffer (hold = seconds at full level after attack)."""
    e = np.ones(len(x), dtype=np.float32); a = n(attack); r = n(release)
    if a: e[:a] = np.linspace(0, 1, a)
    if hold is not None:
        start = min(len(x), a + n(hold)); e[start:] = 0
        if r and start > 0: e[start - r:start] *= np.linspace(1, 0, min(r, start))[-min(r, start):]
    elif r: e[-r:] *= np.linspace(1, 0, r)
    return x * e

def decay(x, tau):
    """Exponential decay with time constant tau seconds."""
    return x * np.exp(-t(len(x) / SR) / tau).astype(np.float32)

def reverb(x, decay_s=2.5, mix=0.3, predelay=0.02):
    ir = decay(noise(decay_s), decay_s / 4) * 0.05
    ir = fftfilter(ir, 80, 9000)
    wet = np.fft.irfft(np.fft.rfft(x, len(x) + len(ir)) * np.fft.rfft(ir, len(x) + len(ir)))[: len(x)]
    wet = np.concatenate([np.zeros(n(predelay)), wet])[: len(x)]
    return (x + mix * wet).astype(np.float32)

def sat(x, drive=1.0): return np.tanh(x * drive) / math.tanh(drive)

def stereo(x, width=0.015):
    """Mono to stereo with a tiny delay on one side (Haas) and a little decorrelated reverb."""
    d = n(width); r = np.concatenate([np.zeros(d), x[: len(x) - d]]) if d else x
    return np.stack([x, r]).astype(np.float32)

# ---- the sounds ------------------------------------------------------------------------------
def hum(length, fade_in):
    x = fftfilter(noise(length), None, 220, 0.6) * 1.2           # brown-ish rumble
    tt = t(length)
    x += 0.5 * np.sin(2 * np.pi * 50 * tt) + 0.35 * np.sin(2 * np.pi * 50.7 * tt + 1)  # mains beating
    x += 0.25 * fftfilter(noise(length), 900, 2600, 0.8) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * tt))  # vent air
    x *= 0.8 + 0.2 * np.sin(2 * np.pi * 0.05 * tt + 2)
    return env(x, fade_in, 0.5) * 0.22

def sub(length, fade_in):
    tt = t(length)
    x = np.sin(2 * np.pi * 55 * tt) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.11 * tt))
    x += 0.3 * np.sin(2 * np.pi * 110 * tt + 0.5)
    x *= 0.85 + 0.15 * np.sin(2 * np.pi * 0.21 * tt)   # breathing
    return env(x, fade_in, 1.0) * 0.5

def ping(gain=0.6, pitch=1.0):
    length = 0.9; tt = t(length)
    f = 1180 * pitch * (1 + 0.08 * np.exp(-tt * 40))     # tiny pitch drop at the start
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 14)
    x += 0.4 * np.sin(2 * np.pi * 2360 * pitch * tt) * np.exp(-tt * 22)
    x = reverb(x.astype(np.float32), 1.4, 0.5, 0.01)
    return x * gain * 0.35

def riser(length, gain):
    tt = t(length); k = tt / length
    x = noise(length)
    # low-pass opening up and a rising, thickening tone
    out = np.zeros(n(length), dtype=np.float32)
    step = n(0.1)
    for i in range(0, len(x), step):
        hi = 200 + 7000 * (i / len(x)) ** 2
        out[i:i + step] = fftfilter(x[i:i + step], 60, hi, 0.7)
    tone = np.sin(2 * np.pi * np.cumsum(90 * (1 + 3 * k ** 2)) / SR) * 0.5
    y = (out * 0.9 + tone) * (k ** 1.6)
    return (reverb(y.astype(np.float32), 1.5, 0.25) * gain * 0.5).astype(np.float32)

def hit(gain=1.0, size=1.0, tail=2.5):
    length = 1.6 * size + tail; tt = t(length)
    boom = np.sin(2 * np.pi * np.cumsum(38 + 70 * np.exp(-tt * 9)) / SR) * np.exp(-tt * (1.6 / size))
    crash = fftfilter(noise(length), 150, 7000, 0.8) * np.exp(-tt * (6 / size)) * 0.9
    ring = sum(np.sin(2 * np.pi * f * tt + p) * np.exp(-tt * d) for f, p, d in
               ((1123, 0.3, 3.5), (1710, 1.1, 4.5), (2920, 2.0, 6.0), (437, 0.7, 2.5))) * 0.25
    x = sat(boom * 1.6 + crash + ring, 1.8)
    x = reverb(x.astype(np.float32), 3.0 * size, 0.35, 0.015)
    return x * gain * 0.9

def cluster(length, gain, tremolo=12, rise=False):
    """Dissonant low string-like cluster (detuned saws), shaking with a fast tremolo: the 'prrr'."""
    tt = t(length)
    freqs = [55, 58.3, 61.7, 65.4, 110, 116.5, 123.5]   # A, Bb, B, C cluster, two octaves
    x = np.zeros(n(length), dtype=np.float32)
    for i, f in enumerate(freqs):
        ph = np.cumsum(f * (1 + 0.004 * np.sin(2 * np.pi * (0.3 + 0.1 * i) * tt))) / SR
        saw = 2 * (ph % 1) - 1
        x += saw * (0.6 if f < 100 else 0.3)
    x = fftfilter(x, 40, 1800 if not rise else 4000, 0.8)
    trem = 0.55 + 0.45 * np.sign(np.sin(2 * np.pi * (tremolo * (1 + (0.8 * tt / length if rise else 0))) * tt))
    x *= trem
    shape = (tt / length) ** 0.7 if rise else np.exp(-tt * (2.2 / length))
    x = sat(x * shape, 2.5)
    x = reverb(x.astype(np.float32), 2.0, 0.3)
    return x * gain * 0.45

def shriek(gain=0.5, pitch=1.0):
    """A creature-like screech: noisy, bending formant tones."""
    length = 1.1; tt = t(length)
    f0 = 620 * pitch * (1 + 0.6 * np.sin(2 * np.pi * 1.3 * tt) ** 2) * (1 + 0.4 * np.exp(-tt * 6))
    x = sum(np.sin(2 * np.pi * np.cumsum(f0 * k) / SR) * w for k, w in ((1, 1), (2.02, 0.5), (3.1, 0.35), (4.7, 0.2)))
    x = x * (0.6 + 0.4 * fftfilter(noise(length), 300, 6000)) + 0.5 * fftfilter(noise(length), 1200, 7000, 0.6)
    x = sat(x * env(np.ones(n(length), dtype=np.float32), 0.03, 0.5), 3.0)
    x = reverb(x.astype(np.float32), 2.2, 0.4)
    return x * gain * 0.3

def tick(gain=0.35):
    """A small metal click somewhere in the station."""
    length = 0.5; tt = t(length)
    f = rng.uniform(1500, 4200)
    x = fftfilter(noise(length), 800, 9000) * np.exp(-tt * 90) + np.sin(2 * np.pi * f * tt) * np.exp(-tt * 25) * 0.4
    x = reverb(x.astype(np.float32), 1.8, 0.6, 0.03)
    return x * gain * 0.5

SFX = SFX_DIR
def sample(id, gain=1.0, start=0.0, length=None, fade=0.05, lo=None, hi=None):
    """A game sound from brand/music/sfx/<id>.wav (48 kHz stereo), summed to mono."""
    with wave.open(f"{SFX}/{id}.wav", "rb") as w:
        ch = w.getnchannels(); raw = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768
    x = raw.reshape(-1, ch).mean(1)
    x = x[n(start):]
    if length: x = x[: n(length)]
    if lo or hi: x = fftfilter(x, lo, hi)
    x = env(x, fade, fade)
    return (x / (np.abs(x).max() + 1e-6) * gain * 0.6).astype(np.float32)

def tracker(gain=0.6, pitch=1.0, path="ref/tracker-cycle.wav"):
    """The game's motion tracker (from the owner's reference recording), sped up to raise its pitch."""
    with wave.open(path, "rb") as w:
        ch = w.getnchannels(); raw = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768
    x = raw.reshape(-1, ch).mean(1)
    if pitch != 1.0:
        x = np.interp(np.arange(0, len(x), pitch), np.arange(len(x)), x).astype(np.float32)
    return (x / (np.abs(x).max() + 1e-6) * gain * 0.5).astype(np.float32)

def layer(path, gain=1.0, align_peak=False, fade=0.01, lo=None, hi=None, length=None, fade_out=None):
    """Any wav (e.g. a Stable Audio 3 layer in brand/music/sa3/), resampled to 48 kHz, mono. With
    align_peak the buffer's loudest moment is placed on the event time (it may start before it)."""
    with wave.open(path, "rb") as w:
        sr = w.getframerate(); ch = w.getnchannels(); raw = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768
    x = raw.reshape(-1, ch).mean(1)
    if sr != SR: x = np.interp(np.arange(0, len(x), sr / SR), np.arange(len(x)), x).astype(np.float32)
    if length: x = x[: n(length)]
    if lo or hi: x = fftfilter(x, lo, hi)
    x = env(x, fade, fade_out if fade_out is not None else max(fade, 0.2))
    x = (x / (np.abs(x).max() + 1e-6) * gain * 0.6).astype(np.float32)
    offset = 0
    if align_peak:
        e = np.convolve(np.abs(x), np.ones(n(0.02)) / n(0.02), mode="same"); offset = int(np.argmax(e))
    return x, offset

def drums(bars, gain=0.7, fade_in=4.0, swing=0.06):
    """Slow lo-fi beat on the grid: kick on 1 and 3, lazy snare on 2 and 4, soft eighth hats with a
    little swing, a ghost kick now and then; low-passed and saturated like tape, with vinyl crackle."""
    length = bars * 4 * BEAT_S; out = np.zeros(n(length), dtype=np.float32)
    def put(x, at):
        i = n(at); j = min(len(out), i + len(x)); out[i:j] += x[: j - i]
    tt = t(0.4); kick = np.sin(2 * np.pi * np.cumsum(48 + 90 * np.exp(-tt * 25)) / SR) * np.exp(-tt * 9)
    tt = t(0.25); snare = (fftfilter(noise(0.25), 180, 4500) * 0.8 + np.sin(2 * np.pi * 185 * tt) * 0.5) * np.exp(-tt * 18)
    tt = t(0.08); hat = fftfilter(noise(0.08), 5000, 12000) * np.exp(-tt * 60) * 0.25
    for b in range(bars):
        base = b * 4 * BEAT_S
        put(kick, base); put(kick * 0.9, base + 2 * BEAT_S)
        if rng.uniform() < 0.5: put(kick * 0.45, base + 3.5 * BEAT_S)
        put(snare, base + 1 * BEAT_S + swing * 0.5); put(snare * 0.95, base + 3 * BEAT_S + swing * 0.5)
        for e in range(8):
            put(hat * (0.6 if e % 2 else 1.0), base + e * 0.5 * BEAT_S + (swing if e % 2 else 0))
    out = fftfilter(sat(out, 1.6), 30, 4200, 0.8)
    out += fftfilter(noise(length), 2000, 9000) * 0.012 * (1 + 0.5 * np.sin(2 * np.pi * 0.6 * t(length)))  # crackle
    tail = n(1.0); out[-tail:] *= np.linspace(1, 0, tail)
    return env(out, fade_in, 0.1) * gain * 0.5

def score_beat(bars, gain=0.7, fade_in=4.0, taiko="perc-taiko-1", metal="perc-metal-1", heart="perc-heart-1", tick="perc-tick-1"):
    """The beat with the score's own percussion (Stable Audio one-shots in brand/music/sa3/):
    taiko on 1, a metal hit on 3, a muffled heartbeat on 2 and 4, soft ticks on the off-beats."""
    length = bars * 4 * BEAT_S; out = np.zeros(n(length), dtype=np.float32)
    def shot(name, g, hi=None):
        x, off = layer(f"sa3/{name}.wav", gain=g, align_peak=True, fade=0.003, hi=hi); return x, off
    tk, tko = shot(taiko, 1.0, 6000); mt, mto = shot(metal, 0.85); hb, hbo = shot(heart, 1.0, 300); tc, tco = shot(tick, 0.4)
    def put(x, off, at):
        i = n(at) - off; c = max(0, -i); i = max(0, i); j = min(len(out), i + len(x) - c); out[i:j] += x[c:c + (j - i)]
    for b in range(bars):
        base = b * 4 * BEAT_S
        put(tk, tko, base); put(hb, hbo, base + 1 * BEAT_S); put(mt, mto, base + 2 * BEAT_S); put(hb, hbo, base + 3 * BEAT_S)
        for e in (1, 3, 5, 7):
            if rng.uniform() < 0.7: put(tc, tco, base + e * 0.5 * BEAT_S)
    out = fftfilter(sat(out, 1.6), 30, 9000, 0.8)
    tail = n(1.0); out[-tail:] *= np.linspace(1, 0, tail)
    return env(out, fade_in, 0.1) * gain * 0.6

GEN = {"score_beat": score_beat, "drums": drums, "layer": layer, "sample": sample, "tracker": tracker, "hum": hum, "sub": sub, "ping": ping, "riser": riser, "hit": hit, "cluster": cluster, "shriek": shriek, "tick": tick}



# ---- mix -------------------------------------------------------------------------------------
def render(events, length, out, final_at=None, breath=0.45, fade_out=3.0, drive=1.6):
    """Mix the events into `out` (16-bit stereo wav). With final_at, everything but the hit/layer
    events at that time is silenced for `breath` seconds before it (the breath before the impact)."""
    total = n(length + 6)
    bed = np.zeros((2, total), dtype=np.float32); final = np.zeros((2, total), dtype=np.float32)
    for when, kind, params in events:
        x = GEN[kind](**params); off = 0
        if isinstance(x, tuple): x, off = x
        s = stereo(x, width=0.0 if kind in ("sub", "hum") else rng.uniform(0.004, 0.02))
        if kind in ("ping", "tick", "tracker"):
            pan = rng.uniform(-0.7, 0.7); s[0] *= 1 - max(0, pan); s[1] *= 1 + min(0, pan)
        i = n(when) - off; c = max(0, -i); i = max(0, i); s = s[:, c:]; j = min(total, i + s.shape[1])
        target = final if (final_at is not None and kind in ("hit", "layer") and abs(when - final_at) < 1e-6) else bed
        target[:, i:j] += s[:, : j - i]
    if final_at is not None:
        a, b = n(final_at - breath), n(final_at); f = n(0.06)
        bed[:, a - f:a] *= np.linspace(1, 0, f); bed[:, a:b] = 0
    mix = bed + final
    end = n(length); f = n(fade_out); mix[:, end - f:end] *= np.linspace(1, 0, f); mix = mix[:, :end]
    peak = np.abs(mix).max() + 1e-9; mix = np.tanh(mix / peak * drive) / math.tanh(drive) * 0.95
    with wave.open(out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix.T * 32767).astype("<i2").tobytes())
    return out
