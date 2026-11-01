#!/usr/bin/env bash
# compasso quick install: Stable Audio 3 (Small-SFX + Small-Music) running locally on the CPU, with
# the weights fetched from ungated mirrors (no Hugging Face login), plus this repo's generator.
# Idempotent: re-running only checks what is missing.
#
#   curl -LsSf https://raw.githubusercontent.com/sidnei-almeida/compasso/main/install.sh | bash
#   SA3_DIR=~/ai/stable-audio-3 COMPASSO_DIR=~/Documents/GitHub/compasso bash install.sh
set -euo pipefail

SA3_DIR="${SA3_DIR:-$HOME/ai/stable-audio-3}"
COMPASSO_DIR="${COMPASSO_DIR:-$HOME/Documents/GitHub/compasso}"
COMPASSO_URL="https://github.com/sidnei-almeida/compasso"
MIRROR="https://huggingface.co/AEmotionStudio/stable-audio-3-mirrors/resolve/main"
T5="https://huggingface.co/LeeAeron/t5gemma-b-b-ul2/resolve/main"
say() { printf '\033[1;33m==>\033[0m %s\n' "$*"; }
need() { command -v "$1" >/dev/null 2>&1 || { echo "missing: $1 ($2)"; exit 1; }; }

need git "install git"; need curl "install curl"; need ffmpeg "install ffmpeg"; need python3 "install python 3.10+"
if ! command -v uv >/dev/null 2>&1; then
  say "installing uv"; curl -LsSf https://astral.sh/uv/install.sh | sh; export PATH="$HOME/.local/bin:$PATH"
fi

# 1. compasso itself (the engine, the examples)
if [ ! -d "$COMPASSO_DIR/.git" ]; then say "cloning compasso -> $COMPASSO_DIR"; git clone -q "$COMPASSO_URL" "$COMPASSO_DIR"; fi

# 2. Stable Audio 3 code + venv with CPU torch
if [ ! -d "$SA3_DIR/.git" ]; then say "cloning Stable Audio 3 -> $SA3_DIR"; git clone -q --depth 1 https://github.com/Stability-AI/stable-audio-3 "$SA3_DIR"; fi
cd "$SA3_DIR"
if [ ! -x .venv/bin/python ]; then
  say "creating the venv (python 3.12, torch cpu)"
  uv venv -q --python 3.12 .venv
  uv sync -q --inexact --no-install-package torch --no-install-package torchaudio
  uv pip install -q --python .venv/bin/python torch==2.7.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cpu
  uv pip install -q --python .venv/bin/python sentencepiece protobuf numpy
fi
cp "$COMPASSO_DIR/sa3_gen.py" "$SA3_DIR/sa3_gen.py"

# 3. weights from the ungated mirrors
fetch() { # url dest
  [ -s "$2" ] && return 0
  mkdir -p "$(dirname "$2")"; say "downloading $(basename "$(dirname "$2")")/$(basename "$2")"
  curl -L --fail --progress-bar -o "$2.part" "$1" && mv "$2.part" "$2"
}
for m in small-sfx small-music; do
  fetch "$MIRROR/$m/model_config.json" "weights/$m/model_config.json"
  fetch "$MIRROR/$m/model.safetensors" "weights/$m/model.safetensors"
  for f in config.json generation_config.json special_tokens_map.json tokenizer_config.json tokenizer.json; do
    fetch "$MIRROR/$m/t5gemma-b-b-ul2/$f" "weights/$m/t5gemma-b-b-ul2/$f"
  done
done
# the text encoder weights are not in the mirror: one copy, shared by both models
fetch "$T5/model.safetensors" "weights/t5gemma/model.safetensors"
fetch "$T5/tokenizer.model" "weights/t5gemma/tokenizer.model"
for m in small-sfx small-music; do
  for f in model.safetensors tokenizer.model; do
    [ -e "weights/$m/t5gemma-b-b-ul2/$f" ] || ln -s "../../t5gemma/$f" "weights/$m/t5gemma-b-b-ul2/$f"
  done
done

# 4. smoke test
say "test: 5 s of drone on the CPU"
.venv/bin/python sa3_gen.py --model small-sfx -p "deep dark sci-fi drone" --duration 5 --steps 8 -o /tmp/compasso-test.wav 2>&1 | grep -E "^OUT|Error" || true
[ -s /tmp/compasso-test.wav ] && say "ok: /tmp/compasso-test.wav" || { echo "the test did not produce audio; see above"; exit 1; }
say "done. generate: cd $SA3_DIR && .venv/bin/python sa3_gen.py --model small-music -p '...' --duration 45 -o out.wav"
say "arrange:  python3 -c 'import sys; sys.path.insert(0, \"$COMPASSO_DIR\"); import cue' (see README)"
