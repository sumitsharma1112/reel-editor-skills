---
name: story-ama
description: 12-second animated 9:16 "Ask Me Anything" Instagram story for @aitricksbysumit: wall-projection title, AI neon grid, his AI avatar pointing at the question-sticker slot, frosted-glass topic chips with prop icons, soft synthesized SFX. Use when Sumit asks for an AMA / question-box story.
---
# Ask Me Anything story (v3)
1. Cutouts: generate with `AMA_Story_Cutout_Prompts.txt` (avatar reference = intro asset 01_avatar_wave.png on white). Remove backgrounds with rembg `isnet-general-use`, threshold alpha <25, crop to bbox → `cz/`.
2. `python3 scripts/ama3.py 8.0` → preview still; `python3 scripts/ama3.py` → ama3_video.mp4 (~100 s render).
3. `python3 scripts/sfx.py` → sfx.wav (synthesized: soft whoosh on wall swing, low thuds on ASK/ME/ANYTHING, tiny glitch blip, quiet typing ticks, chip pops, shimmer on slot). Mux at volume -3 dB (mean about -30 dB, peak about -7 dB) and also export a silent copy so Instagram music can go on top.

Look: dark room + cyan perspective grid (AI), cream wall panel warped with cv2.getPerspectiveTransform, cyan neon edge, RGB-split glitch while words slam (Anton), kicker in Space Mono, typed Instrument Serif italic mint line with blinking cursor, AI chip + robot cutouts, frosted glass = blurred background composited through a mask. Story safe zones: nothing above y=250; chips end by y=1680.
