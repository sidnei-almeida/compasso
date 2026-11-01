#!/bin/bash
# The Alien: Isolation background-music pack for the episodes, generated locally with Stable Audio 3
# (~/ai/stable-audio-3, Small-Music for beds, Small-SFX for one-shots), all in A minor and in the
# intro's sound family. Beds are 120 s plus a seamless-loop version; cues and one-shots are short.
# Output: brand/music/pack/<folder>/ (not in git) and a copy in ~/Downloads/trilha-alien-pack/.
#   scripts/music-pack.sh [folder-filter]
set -uo pipefail
cd "$(dirname "$0")/.."
SA3=~/ai/stable-audio-3; PACK=brand/music/pack; FILTER="${1:-}"
mkdir -p "$PACK"

gen() { # folder name model duration count prompt...
  local folder=$1 name=$2 model=$3 dur=$4 count=$5; shift 5
  [ -n "$FILTER" ] && [[ "$folder" != *"$FILTER"* ]] && return
  mkdir -p "$PACK/$folder"
  ( cd "$SA3" && .venv/bin/python sa3_gen.py --model "$model" -p "$*" --duration "$dur" --steps 8 -n "$count" -o "$OLDPWD/$PACK/$folder/$name.wav" 2>&1 | grep -E "^OUT|Error" | cut -c1-120 )
  for f in "$PACK/$folder/$name"*.wav; do
    case "$f" in *-48k.wav) continue;; esac
    ffmpeg -v error -y -i "$f" -ar 48000 -c:a pcm_s16le "${f%.wav}-48k.wav" && mv "${f%.wav}-48k.wav" "$f"
  done
}

KEY="A minor, 60 bpm"
# 01 exploration: calm, the intro's identity
gen 01-exploracao sevastopol-quieta small-music 120 2 "calm dark ambient film score, slow sparse piano in $KEY over a warm soft synth pad, deep quiet drone, cold space station atmosphere, sci-fi, melancholic, peaceful, no drums, long reverb"
gen 01-exploracao corredores small-music 120 1 "calm cinematic ambient, slow sustained soft strings and a warm analog pad in $KEY, deep quiet drone, sci-fi space station, mysterious, no drums, no melody, long reverb"
# 02 uneasy: something is wrong
gen 02-inquieto algo-errado small-music 120 2 "dark ambient film score, uneasy, low drone and a rare detuned piano note in $KEY, cold metallic textures, distant creaks, no pulse, no drums, dread slowly creeping, sci-fi horror, long reverb"
# 03 stealth: pulse
gen 03-stealth escondida small-music 120 2 "tense dark ambient film score, slow heartbeat sub bass pulse, low drone, sparse metallic ticks, cold synth pad in $KEY, holding breath, sci-fi horror stealth, no melody, no drums"
gen 03-stealth rastreador small-music 120 1 "tense sci-fi horror underscore, slow pulsing low synth, deep drone, soft tremolo strings rising and falling in $KEY, metallic clicks, suspense, no drums"
# 04 horror: it is near
gen 04-terror perto small-music 120 2 "horror film score, dissonant string clusters swelling and fading, rattling tremolo low strings, deep rumble, scraped metal, no pulse, no drums, pure dread, sci-fi horror, A minor"
# 05 alien chase
gen 05-perseguicao-alien cacada small-music 120 2 "intense orchestral horror chase, driving low string ostinato, pounding taiko and bass drum, dissonant brass stabs, shrieking high strings, relentless, 120 bpm, A minor, film score, no rock drums, no guitars"
# 06 android chase
gen 06-perseguicao-androide working-joe small-music 120 2 "cold mechanical sci-fi horror chase, relentless low synth pulse at 120 bpm, industrial metallic percussion hits, detuned analog synth stabs, deep drone, A minor, menacing, no guitars, film score"
# 07 nest
gen 07-ninho reator small-music 120 1 "dark organic horror ambient, wet dripping textures, low throbbing drone, breathing, distant inhuman choir-like pad, deep reactor hum, no pulse, no drums, A minor, nightmarish"
# 08 LV-426
gen 08-lv426 derrelita small-music 120 1 "vast alien ambient film score, huge cold reverb, slow dissonant string swells, deep sub drone, eerie wind, Jerry Goldsmith Alien 1979 atmosphere, no drums, no pulse, A minor"
# 09 death
gen 09-morte morte small-sfx 12 3 "cinematic death cue: a huge dark orchestral impact, then a descending low drone falling into silence, deep rumble, cold reverb, final"
# 10 relief
gen 10-alivio alivio small-music 30 2 "calm film score, relief after tension, slow sparse piano resolving gently in $KEY, warm soft pad, quiet drone, peaceful but melancholic, no drums, fades out"
# 11 stingers
gen 11-stingers stinger-orquestral small-sfx 5 3 "huge orchestral horror stinger, dissonant brass blast and string stab, bass drum hit, dry and violent, short, then silence"
gen 11-stingers stinger-metal small-sfx 4 2 "sharp metallic horror stinger, struck steel and a sub boom, dry, short, cinematic"
gen 11-stingers stinger-cordas small-sfx 4 2 "screeching violin stab, horror, sudden, short, dry"
gen 11-stingers braam small-sfx 6 2 "deep orchestral brass braam, cinematic horror hit, low trombones and tuba, huge hall reverb tail"
# 12 risers
gen 12-risers riser small-sfx 6 3 "horror riser, tension build up, rising noise and string tremolo, accelerating, ends abruptly in a hit"
gen 12-risers swell small-sfx 8 2 "orchestral string swell, dissonant cluster crescendo from quiet to fortissimo, horror film score, big hall reverb, ends at the peak"
# 13 transitions
gen 13-transicoes whoosh small-sfx 3 2 "cinematic dark whoosh transition, air and low rumble, short"
gen 13-transicoes impacto small-sfx 4 2 "cinematic impact hit with sub boom and dark reverb tail, short, dry"

# seamless loops of the 120 s beds: the last 4 s crossfade into the first 4 s
for f in "$PACK"/0[1-8]-*/*.wav; do
  case "$f" in *-loop.wav) continue;; esac
  [ -n "$FILTER" ] && [[ "$f" != *"$FILTER"* ]] && continue
  python3 -I scripts/make-loop.py "$f" "${f%.wav}-loop.wav" 4
done
rm -rf ~/Downloads/trilha-alien-pack && cp -r "$PACK" ~/Downloads/trilha-alien-pack && cp docs/trilha-pack.md ~/Downloads/trilha-alien-pack/LEIA-ME.md
echo "== pack: $(find "$PACK" -name '*.wav' | wc -l) files, $(du -sh "$PACK" | cut -f1)"
