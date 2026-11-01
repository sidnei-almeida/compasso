# trilha — música e desenho de som por código

Como as trilhas do canal Lapso são feitas: tudo local, sem nuvem, sem assinatura, e o resultado é
nosso. Nasceu na intro de Alien: Isolation (2026-11-01). O que está aqui é o método, o motor de
cues e as regras de gosto que foram aprendidas na marra.

## A ideia

Trilha de cinema não é "uma música": é **camadas num grid**. Uma cama (pad, piano, drone), um
pulso (percussão da própria trilha), e eventos (swells, stingers, impactos) que caem em tempos
fortes. A imagem corta nesse mesmo grid. Modelos que geram *canções* (Suno, ACE-Step) não servem
para isso: tudo vira verso e refrão. O que serve:

| Camada | Ferramenta |
|---|---|
| Camas tonais (pad, piano, cordas, até 120 s) | Stable Audio 3 **Small-Music** |
| One-shots e texturas (stinger, riser, impacto, percussão, vapor) | Stable Audio 3 **Small-SFX** |
| O arranjo (quem entra quando, alinhado no grid) | `cue.py` (numpy, sem dependências) |
| Loops sem emenda | `make-loop.py` |
| Sons reais (rastreador, SFX do jogo) | amostras, posicionadas pelo `cue.py` |

## Instalação do Stable Audio 3 (uma vez)

Clone oficial em `~/ai/stable-audio-3` (`git clone https://github.com/Stability-AI/stable-audio-3`),
venv com torch CPU (`uv venv .venv --python 3.12`, `uv pip install torch==2.7.1 torchaudio==2.7.1
--index-url https://download.pytorch.org/whl/cpu`, `uv sync --inexact --no-install-package torch
--no-install-package torchaudio`, `uv pip install sentencepiece protobuf`). Pesos em `weights/`:
os oficiais são gated no Hugging Face; o espelho `AEmotionStudio/stable-audio-3-mirrors` tem
`small-sfx/` e `small-music/` sem gate, e o codificador de texto vem de `LeeAeron/t5gemma-b-b-ul2`
(copiar `model.safetensors` e `tokenizer.model` para `weights/<modelo>/t5gemma-b-b-ul2/`).
`sa3_gen.py` (está lá) carrega tudo de arquivo e nunca toca no Hub. CPU basta: 20 s em 8 s.

```bash
cd ~/ai/stable-audio-3
.venv/bin/python sa3_gen.py --model small-music -p "calm dark ambient, slow sparse piano in A minor, 60 bpm, no drums" --duration 45 -n 2 -o bed.wav
.venv/bin/python sa3_gen.py --model small-sfx   -p "huge orchestral horror stinger, dry, short" --duration 5 -n 2 -o stinger.wav
.venv/bin/python sa3_gen.py --model small-music -p "..." --inpaint bed.wav 30 120 --duration 120 -o cont.wav   # continuação
ffmpeg -i x.wav -ar 48000 -c:a pcm_s16le x48.wav    # a saída é float 44.1k; o cue.py lê 16-bit
```

## O motor: `cue.py`

```python
import cue
cue.BPM = 60; cue.BEAT_S = 60 / cue.BPM; bar = cue.bar
EVENTS = [
    (0.0,    "layer", dict(path="sa3/pad.wav", gain=0.8, fade=3.0)),
    (bar(2), "score_beat", dict(bars=9, gain=1.25)),                         # taiko/metal/batimento no grid
    (bar(5), "layer", dict(path="sa3/swell.wav", gain=0.9, align_peak=True)),  # o pico cai no tempo forte
    (bar(5), "layer", dict(path="sa3/stinger.wav", gain=0.8, align_peak=True)),
    (bar(11), "layer", dict(path="sa3/impact.wav", gain=1.0, align_peak=True)),
]
cue.render(EVENTS, length=bar(12), out="intro.wav", final_at=bar(11))   # respiro de 0,45 s antes do impacto final
```

Tipos de evento: `layer` (qualquer wav; `align_peak` coloca o ponto mais alto no tempo do evento),
`sample` (wav em `SFX_DIR/<id>.wav`), `tracker` (one-shot acelerado para subir o tom), e os
sintetizados `hum`, `sub`, `ping`, `riser`, `hit`, `cluster`, `shriek`, `tick`, `drums`,
`score_beat`. Veja `exemplos/intro-alien.py`, que é a intro aprovada.

## Regras de gosto (do dono do canal)

- Um tom e uma família de som por projeto; gere cada camada já com isso no prompt.
- O beat é o grid. Beat jogado por cima dos efeitos foi recusado; drum machine ("tuts, tac") foi
  recusada; percussão da trilha (taiko, metal, batimento) ou nada.
- Terror é silêncio, espaço e um stinger no corte. Gritos em camada: "demais".
- Sons reais do jogo (rastreador, vapor) ganham dos sintetizados; mas áudio do jogo é referência,
  não entra no vídeo, salvo SFX pequeno aprovado.
- "Mais cinematográfico": swells orquestrais entrando nos golpes, sala grande, menos stab seco.
- "Chill mas dark": piano esparso ou pad em menor sobre drone. A outro não tem rastreador.
- Pack para vídeo longo: camas de 2 min por clima em loop, stingers e risers soltos, e peças
  próprias para os picos (parte 1 + continuação pelo modelo). Guia de edição: uma cama por cena,
  ducking na fala, silêncio antes do susto, stinger no quadro do corte.
- Ninguém aqui ouve: confira por espectrograma e loudness, descreva cada candidata, e deixe o
  dono escolher. Entregue em `~/Downloads/`.

## Onde está o resto

- Intro e outro de Alien: `~/ai/lapso/scripts/intro-sound.py`, `outro-sound.py`; pack:
  `music-pack.sh`, `music-pack-especiais.sh`; guia de edição: `docs/trilha-pack.md`.
- Render de vídeo longo cortado no grid: `~/ai/lapso/scripts/render-chunks.sh`.
- Skill do Claude Code: `~/.claude/skills/trilha/SKILL.md`.
