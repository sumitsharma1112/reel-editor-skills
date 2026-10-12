# Remotion white-page doodle reels

Reference-inspired page hinges over black, half-turns, zoom settles, ink pulses,
small gold serif lyrics and gentle artwork bobbing. All animation is driven by
`useCurrentFrame()`, not CSS animation timers. This is not a verified app preset.

```bash
npm ci
npm run check
mkdir -p public/fonts public/media
cp ../skills/reel-editor/fonts/cormorant-garamond-700i.ttf public/fonts/serif.ttf
npm run studio
npm run render -- out/reel.mp4 --props=edit.local.json
```

Put your matching audio and transparent black-ink sprites in `public/media/`.
Those files, renders and local props are ignored by git. White-page originals
need ink alpha extraction before ink tinting; avoid a white opaque sprite box.
`font` is optional; if provided, it is loaded locally before capture.

Example `edit.local.json` (seconds, paths relative to `public/`):

```json
{
  "duration": 6,
  "audio": "media/song.wav",
  "font": "fonts/serif.ttf",
  "scenes": [
    {"start":0,"end":3,"image":"media/a.png","lines":["First lyric"],"motion":"none"},
    {"start":3,"end":6,"image":"media/b.png","lines":["Next lyric"],"motion":"hinge"}
  ]
}
```

Scenes form one data-controlled template. Their start/end times remain fixed;
outgoing and incoming transitions happen around the same lyric boundary without
shortening the composition or shifting audio. Supported `motion` values:
`none`, `hinge`, `spin`, `zoom`. Keep captions upright after transitions.
Whole-sprite bobbing does not animate individual hands, mouths or eyes.

Use `--browser-executable=/path/to/chrome` when the standard browser download is
unavailable. Tested with Remotion 4.0.535, TypeScript and a rendered bhajan scene.
