#!/usr/bin/env python3
"""Stable Audio 3 Small-SFX from local files (no Hugging Face login), on CPU or XPU.
The weights come from the ungated mirror in weights/small-sfx/ (model.safetensors, model_config.json
and the bundled T5-Gemma text encoder).

  sa3_gen.py -p "dark sci-fi drone" [-n 2] [--duration 30] [--steps 8] [--cfg 7] [--seed -1]
             [--init in.wav --init-noise 0.8] [--device cpu|xpu] -o out.wav
"""
import argparse, json, os, sys, time
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import torch, torchaudio
from stable_audio_3.loading_utils import load_diffusion_cond
from stable_audio_3.model import StableAudioModel

ap = argparse.ArgumentParser()
ap.add_argument("-p", "--prompt", required=True)
ap.add_argument("--negative", default="")
ap.add_argument("-n", type=int, default=1)
ap.add_argument("--duration", type=float, default=30)
ap.add_argument("--steps", type=int, default=8)
ap.add_argument("--cfg", type=float, default=None)
ap.add_argument("--seed", type=int, default=-1)
ap.add_argument("--init", help="audio-to-audio source wav")
ap.add_argument("--init-noise", type=float, default=0.8)
ap.add_argument("--inpaint", nargs=3, metavar=("SRC","START","END"), help="keep SRC outside START-END seconds, regenerate inside (END past the file length = continuation)")
ap.add_argument("--model", default="small-sfx")
ap.add_argument("--device", default="cpu")
ap.add_argument("-o", "--out", required=True)
a = ap.parse_args()

wdir = os.path.join(ROOT, "weights", a.model)
with open(os.path.join(wdir, "model_config.json")) as f:
    cfg = json.load(f)
# point every text conditioner at the bundled encoder instead of google/t5gemma on the Hub
local_t5 = next((os.path.join(wdir, d) for d in os.listdir(wdir) if d.startswith("t5gemma") and os.path.isdir(os.path.join(wdir, d))), None)
def patch(node):
    if isinstance(node, dict):
        if node.get("type") == "t5gemma" and local_t5:
            c = node.setdefault("config", {}); c["model_path"] = local_t5; c["repo_id"] = None; c["subfolder"] = None
        for v in node.values(): patch(v)
    elif isinstance(node, list):
        for v in node: patch(v)
patch(cfg)

t0 = time.time()
model = load_diffusion_cond(cfg, os.path.join(wdir, "model.safetensors"), device=a.device, model_half=False)
model.use_lora = False; model.lora_names = []
sa = StableAudioModel(model, cfg, a.device, False)
print(f"loaded {a.model} on {a.device} in {time.time()-t0:.0f}s", file=sys.stderr)

kw = dict(prompt=a.prompt, duration=a.duration, steps=a.steps)
if a.negative: kw["negative_prompt"] = a.negative
if a.cfg is not None: kw["cfg_scale"] = a.cfg
if a.init:
    wav, sr = torchaudio.load(a.init); kw["init_audio"] = (sr, wav); kw["init_noise_level"] = a.init_noise
if a.inpaint:
    wav, sr = torchaudio.load(a.inpaint[0]); kw["inpaint_audio"] = (sr, wav); kw["inpaint_mask_start_seconds"] = float(a.inpaint[1]); kw["inpaint_mask_end_seconds"] = float(a.inpaint[2])
base, ext = os.path.splitext(a.out)
for i in range(a.n):
    seed = a.seed if a.seed >= 0 else int(torch.randint(0, 2**31 - 1, (1,)))
    t0 = time.time()
    audio = sa.generate(seed=seed, **kw)
    if isinstance(audio, (list, tuple)): audio = audio[0]
    audio = audio.detach().float().cpu()
    if audio.dim() == 3: audio = audio[0]
    sr = cfg.get("sample_rate", 44100)
    out = a.out if a.n == 1 else f"{base}-{i+1}{ext}"
    torchaudio.save(out, audio, sr)
    print(f"OUT {out} seed={seed} {audio.shape[-1]/sr:.1f}s in {time.time()-t0:.0f}s")
