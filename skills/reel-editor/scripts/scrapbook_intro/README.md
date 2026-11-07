# Scrapbook motion intro (HTML + Playwright, frame-pure)
After-Effects-style "creator intro" reel: grid paper, torn notes, sticky notes, selection boxes, yellow paper waves,
teal spotlight circle, page-turn, crossroad signboards, red DM swoosh, typed FOLLOW end card. 11 scenes timed to a voice-over.

- `index.html`: every frame is computed by `render(t)` from time alone (closed-form springs, no CSS transitions/timers).
  Scenes are `.sc` divs with `data-a`/`data-b` times; set the phrase start times from `silencedetect` on the VO.
- Avatar "talks": `ENV` = per-frame RMS of the VO; the avatar squashes/bobs slightly while speech is louder.
- `rend.js test` writes check frames; `rend.js full` renders 60 fps screenshots -> ffmpeg `tmix=frames=2,fps=30` (motion blur) + VO.
- Needs `as/` (avatar poses, props, backgrounds as PNG, transparent props) and `fonts/` (Anton, Archivo Black, Instrument Serif
  Italic, Playfair Italic, Inter, Caveat Brush). Asset list = the ChatGPT one-zip prompt (27 files). Personal media is not in the repo.
- Copy a reference reel's STYLE only (layouts, motion, pacing); all text and assets must be the user's own.
