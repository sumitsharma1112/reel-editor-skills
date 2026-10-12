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

`BrandedReel` wraps the same composition in matching white-page opening and closing
cards. Additional props: `introSeconds`, `outroSeconds`, `introLines`, `outroLines`,
`handle`, and optional `brandImage`. Render with composition ID `BrandedReel`.
The audio starts with the main sequence; captions use its local frame, avoiding drift.
Use a personal-workflow claim such as "No manual editing" only when accurate for
the creator, and don't present generated views as proof of trending performance.

`ColourfulReel` starts directly with matching audio and ends with a follow card.
Props: `duration`, `outroSeconds`, `handle`, optional `audio`/`font`/`endingImage`,
`scenes` (`start`, `image`, `background`, optional `mouth`), `energy` and `beats`.
Images are transparent RGBA sprites normalized to a 1000x1000 canvas. Optional
mouth coordinates use that same canvas; calibrate them on the actual artwork.
Energy values and beat positions are indexed in 30-fps frames. The mouth opening
responds to full-mix amplitude, not verified vocal phonemes or exact lip sync.
Keep motion subtle; colour/pose changes and page swings should not become strobing.

`PaintedLyricReel` uses full-frame paintings with slow drift, soft crossfades and
cream/gold serif + script lyric groups. Props: `duration`, `outroSeconds`, `audio`,
`serifFont`, `scriptFont`, `handle`, `paintings` (`start`, `image`) and `lyrics`
(`start`, `end`, `above`, `hero`, `below`). Use quiet painted regions for captions.
Letter reveals adapt to short phrases; the image timeline never shifts audio.
Read captions already embedded in supplied footage before attempting lyric guesses.
OCR can suggest timings, but must be checked visually; creator watermarks are not lyrics.
