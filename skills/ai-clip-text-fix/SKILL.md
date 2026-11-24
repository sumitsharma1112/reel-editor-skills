---
name: ai-clip-text-fix
description: Fix wrong text that Gemini/Veo/Flow burned into AI video clips (garbled Punjabi/Hindi captions, misspelt signboards) and rebuild the reel with correct Gurmukhi/Devanagari motion graphics. Use when AI clips have wrong on-screen text.
---

# Fix AI-burned text + Gurmukhi motion graphics

Built for the Faridkot Postal Division International Speed Post reel (Nov 2026).

## 1. Find every bad-text window
- Contact sheets at 0.125 s steps around each caption onset (`ffmpeg`/cv2 + timestamps drawn on tiles).
- Note per window: start/end time and the text bbox in source pixels (draw a 50 px grid to read it).
- Keep clean stretches as they are; where the shot is essential, cover the text; otherwise cut it.

## 2. Cover, don't smudge
- `glass()` in `reel_example.py`: frosted band over the bbox (downscale → Gaussian blur → darken 0.45–0.6 → rounded/feathered mask → thin white border).
- Put the CORRECT text on top of that band in screen space, so the cover reads as a designed caption card.
- Static captions: fixed band. Moving captions: band = union of their path.
- Signboards on a camera push-in: track the camera with ORB features + `estimateAffinePartial2D`, chained frame to frame (`track_sign.py`). Map the sign rectangle through it and draw your own sign plate (red #CE2027, white text) over the text part, leaving the AI logo visible.
- Do the cover BEFORE the Ken Burns zoom and place overlay text at the zoom-mapped band centre (`zp()`), so they stay aligned.

## 3. Gurmukhi text that renders correctly
- Fonts: Fontsource ships Baloo Paaji 2 / Mukta Mahee / Anek Gurmukhi as subsets. The Gurmukhi subset has no digits or punctuation, so merge the subsets with `fontTools.merge.Merger` into `*-full.ttf` (bundled in `fonts/`).
- Render with PIL RAQM. In Baloo Paaji 800, double the word spaces (the default spacing is too tight).
- For emoji (flags too), use Noto Color Emoji at 109 px; `txt.render()` handles the split.
- Spell-check every line by eye on a test sheet before rendering.

## 4. Motion-graphics kit (Sattva-style)
- Pop: scale 0.55 → overshoot → 1.0 in 0.32 s (`ease_back`), alpha in 0.1 s.
- Postage-stamp slam ("ਡਾਕਘਰ ਹੈ ਨਾ!"): cream perforated plate, red inner frame, rotated −4°, scale 2.0 → 1.0 in 0.14 s.
- Pills (country names with flags, place names): India Post red, with soft shadow.
- Checklist card ("ਵਜ਼ਨ / ਰਸੀਦ / ਟ੍ਰੈਕਿੰਗ ਨੰਬਰ"): rows tick green one by one.
- Glass CTA end card.
- Cuts: 0.12 s white flash plus a 1.06 → 1.0 punch-in.
- Hook text is on frame 0; no fade-in.

## 5. Board replacement v2 + voice-over sync (added later)
- `sign_plate()` now covers the WHOLE tracked panel. It is a glossy maroon acrylic board with a gold double frame, a drawn gold three-stripe swoosh mark at the left, gold Gurmukhi on top and white English below, raised-letter shadows, and a diagonal light sweep (`shine()`).
- `vo_fit.py`: cut the narrator's wav into speech chunks (−40 dB, 10 ms hop), group the chunks into script lines, cap pauses at 0.38 s (speed never changed), and place each line at its scene start. It writes `timing.json` with per-chunk anchors.
- `reel_vo_sync.py`: scene length comes from the VO. Source clips are retimed piecewise (`pw()`) so key visuals land on words (stamp on "ਡਾਕਘਰ ਹੈ ਨਾ"). Pills, ticks and country names pop on their chunk anchors.
