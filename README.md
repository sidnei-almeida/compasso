<p align="center">
  <img src="brand/banner.svg" alt="compasso" width="100%">
</p>

<p align="center">
  <b>English</b> · <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <b>Film scoring in code, on the beat.</b><br>
  Beds, percussion and hits generated locally with Stable Audio 3, arranged on a BPM grid by a pure-Python engine.<br>
  No cloud, no subscription, and the result is yours.
</p>

<p align="center">
  <img alt="python" src="https://img.shields.io/badge/python-3.12+-ECE7DF?style=flat-square&labelColor=15171C">
  <img alt="dependencies" src="https://img.shields.io/badge/needs-numpy%20%2B%20ffmpeg-ECE7DF?style=flat-square&labelColor=15171C">
  <img alt="model" src="https://img.shields.io/badge/model-Stable%20Audio%203%20(CPU)-E89B3C?style=flat-square&labelColor=15171C">
  <img alt="license" src="https://img.shields.io/badge/license-MIT-5FB0A6?style=flat-square&labelColor=15171C">
</p>

---

## Why

A film cue isn't "a song". It's **layers on a grid**: a bed (pad, piano, drone), a pulse made from
the score's own percussion, and events (swells, stingers, impacts) that land on strong beats.
The picture cuts on that same grid.

Models that generate *songs* (Suno, ACE-Step) don't fit this: everything turns into verse and chorus.
Compasso splits the two jobs: **the model makes the sounds, the code decides the timing.**

## How it works

```
  Stable Audio 3 ──► layers (wav)         cue.py ──► the arrangement         ffmpeg ──► delivery
  small-music: tonal beds                events in seconds                  loops, loudness,
  small-sfx:   stingers, risers,         align_peak: the peak lands         spectrograms
               impacts, textures         on the downbeat
```

| Layer | Tool |
|---|---|
| Tonal beds (pad, piano, strings, drones, up to 120 s) | Stable Audio 3 **Small-Music** |
| One-shots and textures (stinger, riser, impact, percussion, steam) | Stable Audio 3 **Small-SFX** |
| The arrangement (what comes in when, on the grid) | [`cue.py`](cue.py) |
| Seamless loops | [`make-loop.py`](make-loop.py) |
| Real sounds (a motion tracker, a steam hiss) | samples placed by `cue.py` |

## Quick install

```bash
curl -LsSf https://raw.githubusercontent.com/sidnei-almeida/compasso/main/install.sh | bash
```

The script clones Stable Audio 3 into `~/ai/stable-audio-3`, creates a venv with CPU torch,
**downloads the models for you** (Small-SFX, Small-Music and the text encoder, about 3.5 GB, from
ungated mirrors), installs the generator and runs a 5 s test. It's idempotent: running it again only
checks what's missing. Requires `git`, `curl`, `ffmpeg` and Python 3.10+ (`uv` is installed if
absent). `SA3_DIR` and `COMPASSO_DIR` change the install folders.

## Step by step (if you'd rather do it by hand)

### 1. Stable Audio 3, local and login-free

```bash
git clone https://github.com/Stability-AI/stable-audio-3 ~/ai/stable-audio-3 && cd ~/ai/stable-audio-3
uv venv .venv --python 3.12
uv pip install torch==2.7.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cpu
uv sync --inexact --no-install-package torch --no-install-package torchaudio
uv pip install sentencepiece protobuf
```

The official weights are *gated* on Hugging Face. The `AEmotionStudio/stable-audio-3-mirrors` mirror
has `small-sfx/` and `small-music/` without a gate; the text encoder comes from `LeeAeron/t5gemma-b-b-ul2`
(copy `model.safetensors` and `tokenizer.model` into `weights/<model>/t5gemma-b-b-ul2/`).
Use this repo's [`sa3_gen.py`](sa3_gen.py) inside the Stable Audio folder: it loads everything
from disk and never touches the Hub. **A CPU is enough**: 20 s of audio in 8 s.

### 2. Generate layers

```bash
cd ~/ai/stable-audio-3
.venv/bin/python sa3_gen.py --model small-music -p "calm dark ambient, slow sparse piano in A minor, 60 bpm, no drums" --duration 45 -n 2 -o pad.wav
.venv/bin/python sa3_gen.py --model small-sfx   -p "huge orchestral horror stinger, dry, short" --duration 5 -n 2 -o stinger.wav
.venv/bin/python sa3_gen.py --model small-music -p "..." --inpaint pad.wav 30 120 --duration 120 -o cont.wav   # continuation
ffmpeg -i pad.wav -ar 48000 -c:a pcm_s16le pad48.wav   # output is 44.1 kHz float; cue.py reads 16-bit 48 kHz
```

### 3. Arrange on the grid

```python
import cue
cue.BPM = 60; cue.BEAT_S = 60 / cue.BPM; bar = cue.bar

EVENTS = [
    (0.0,     "layer",      dict(path="sa3/pad.wav", gain=0.8, fade=3.0)),
    (bar(2),  "score_beat", dict(bars=9, gain=1.25)),                              # taiko, metal, heartbeat
    (bar(5),  "layer",      dict(path="sa3/swell.wav", gain=0.9, align_peak=True)), # the peak lands on the downbeat
    (bar(5),  "layer",      dict(path="sa3/stinger.wav", gain=0.8, align_peak=True)),
    (bar(11), "layer",      dict(path="sa3/impact.wav", gain=1.0, align_peak=True)),
]
cue.render(EVENTS, length=bar(12), out="intro.wav", final_at=bar(11))  # 0.45 s breath before the final impact
```

Event types: `layer` (any wav; `align_peak` puts the loudest point on the event's time),
`sample` (wav at `SFX_DIR/<id>.wav`), `tracker` (a one-shot sped up to rise in pitch), and the
synthesized `hum`, `sub`, `ping`, `riser`, `hit`, `cluster`, `shriek`, `tick`, `drums`, `score_beat`.

## Examples

The example files are in Portuguese (`exemplos/`).

| File | What |
|---|---|
| [`exemplos/intro-alien.py`](exemplos/intro-alien.py) | the approved 48 s Alien: Isolation intro for the Lapso channel: piano in A minor, score percussion, a real motion tracker subdividing the beat, three hits on bars 5, 8 and 10, impact on 11 |
| [`exemplos/outro-alien.py`](exemplos/outro-alien.py) | the outro: strings crossing into piano, 30 s, no pulse |
| [`exemplos/music-pack.sh`](exemplos/music-pack.sh) | a background pack for a 90-minute video: 13 moods, looping 2-minute beds, stingers, risers, transitions |
| [`exemplos/guia-de-edicao.md`](exemplos/guia-de-edicao.md) | how to use the pack in an edit: one bed per scene, ducking, silence before the scare, stinger on the cut |

## Lessons learned

- **The beat is the grid.** A beat thrown over the effects doesn't work; every event lands on a beat.
- **Score percussion, not a drum machine.** Taiko, metal, heartbeat. Never lo-fi kick and snare.
- **One key and one sound family per project**, written into every layer's prompt.
- **Horror is silence and space.** One stinger on the cut beats ten layered ones. Layered screams: no.
- **Real sounds win.** The game's own tracker, not a synthesized beep. But game audio is a reference,
  not something that goes in the video (rights), except for small, approved SFX.
- **"More cinematic"** = orchestral swells coming in on the hits, a big room, fewer dry stabs.
- **Nobody listens to the render here.** Check it by spectrogram and loudness, describe each
  candidate, and let whoever decides choose.

## Brand

Kit in [`brand/`](brand/README.md): mark, logo, banner, colours and voice.

## License

Code: MIT. Audio generated with Stable Audio 3: [Stability AI Community License](https://stability.ai/license)
(free up to US$1 million in annual revenue).
