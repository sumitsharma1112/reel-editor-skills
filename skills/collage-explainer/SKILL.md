---
name: collage-explainer
description: Faceless talking-avatar explainer reel in the paper-collage + app-window style (cloud sky, torn-paper hills, gingham; numbered chapter cards, typing app windows, WhatsApp notification rows, departure board, film strip, stickers, pixel mascot; 1-2 word italic captions) using Sumit's cartoon avatar and voiceover.
---

# Collage explainer (with Sumit's avatar)

Use when Sumit wants an AI/tips explainer "like Vibha's Day-3 reel", "collage style", or a faceless explainer with his avatar.

## Inputs
- Voiceover wav (his Cartesia/own voice). Avatar folder with poses `01_avatar_wave.png ... 06_avatar_thumbs_up.png`, props and backgrounds (Sumit_Intro_Assets.zip).
- Optional: screen-recording frames folder (blur private data first with `screen_record_privacy_blur.py`), reel thumbnails for the film strip.

## Steps
1. Transcribe with Whisper word timings (`skills/earshot/scripts/whisper_words.py`). Write captions in Hinglish Roman, one entry per sentence with its start-end time.
2. Write a plan JSON (see `example_plan.json`): one scene per idea, each with `bg` (`sky`, `hills`, `dusk`, `gingham`, `gingham-pink`, `gingham-yellow` or an image file from the avatar folder), a `pose`, and `items`:
   - `chapter` {n, title}: yellow Notes card with a big pink number
   - `window` {title, lines, type_dur, label}: mac-style app window that types its lines
   - `notifs` {rows:[[app,msg]...], gap}: notification rows sliding in
   - `board` {rows}: split-flap departure board that settles letter by letter
   - `filmstrip` {images}: scrolling film strip of thumbnails
   - `phone` {frames}: phone frame playing a screen recording
   - `stencil` / `pill` {text}: bold stencil title / rounded tag
   - `sticker` {file}: prop from the avatar folder
   - `poster` {title, sub, handle}: end CTA card
   Items use `t` (seconds after scene start), `t_end`, `x`, `y` (0-1), `rot`. Keep items in the top ~55%; the avatar stands in the bottom ~43%.
3. Check stills: `python3 scripts/collage_explainer.py plan.json sheet.png --stills 1,5,9,...` and look at them.
4. Render: `python3 scripts/rend_par.py plan.json out.mp4` (2 workers, ~1.5 min per minute of video). Sound: soft impact on the hook, click per scene cut, bell per chapter card, pops per notification, key clicks while windows type, quiet pad; voice stays on top.

## Notes
- Captions show 1-2 words at a time in white italic serif with a soft shadow (Playfair Display Italic).
- A white flash marks every scene cut; the pixel mascot blinks in the corner.
- Style learned from a reel by @vibha.in.progress; all code and drawings are original.
