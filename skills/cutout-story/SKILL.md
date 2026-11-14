---
name: cutout-story
description: Premium biography / story reel from a voiceover plus a pack of transparent cutout PNGs - periwinkle "Flow State" stage, cutouts animated as layers (pop, slide, fly, run, swing, orbit, spin), painted B-roll with Ken Burns, frosted-glass word-by-word Hinglish captions, beat motion graphics and varied transitions.
---

# Cutout story reel (international-level biography edit)

Use when Sumit wants a story/biography reel ("Einstein style", "Flow State style", "Vibha se bhi badiya") from a voiceover.

## Inputs
- Voiceover wav, Whisper word timings JSON (`references/whisper-offline.md`).
- 30-50 transparent PNG cutouts made with a ChatGPT prompt like `cutout_prompt_example.txt` (same character design in every image, real alpha, no ground shadow).
- Optional full-frame paintings for B-roll. Never mix faceless paintings of the hero with faced cutouts of the hero.

## Steps
1. Write `CAP` = Roman Hinglish caption lines with start/end times (Whisper misses gaps; fill them from pauses).
2. Write `SC` scenes, one every 2-4 s: `(t, bg, [e(name, x, y, height, delay, anim)], small_italic, BIG_KEYWORD, transition, overlay)`.
   - bg: `'g'` stage, `('g','dark')` dim stage, `('i', n)` painting.
   - anims: pop, up, down, left, right, fade, fly, run, walk, swing, orbit, spin.
   - transitions: zoom, whip, up, iris, blur, flash, fade (rotate them, never the same twice in a row).
   - overlays (`|` to combine): `chapter:NAME`, salary, glow, beam, year, tick, pin, km, energy, curve, corona, stamp, type, blast, follow.
   - Keep the hero out of the hook if the script introduces him later.
3. Stills: `python3 scripts/cutout_story.py stills 2.5,9.8,20 sheet.png` and look at them.
4. Render: `python3 scripts/cutout_story.py out_1080.mp4` (~0.3 s per frame on 2 workers). The master is big because of grain: re-encode crf 24 for 1080p and a 720p copy.

## Look
- Big keyword Anton navy with white glow + gold underline swipe; small italic line (Instrument Serif) above.
- Captions: frosted glass pill at y=1665, chunks of 4 words, upcoming words faded, active word on a navy pill (gold pill for key words).
- Finish: drifting dust, grain, vignette. Sound: soft whoosh on moves, low hit on flashes, pops on element entries, ticks on clocks, risers before chapters, quiet pad. Keep SFX low.
