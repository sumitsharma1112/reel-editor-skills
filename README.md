# reel-editor-skills

Claude skills for editing Instagram reels: beat-sync cuts, strobe "aarti x deity" edits copied from
a reference reel, fusion reels from AI clips, colour grades, head-back text, cutout stickers and
motion graphics.

Made by [@sumitsharma1112](https://github.com/sumitsharma1112) with Claude.

## What's inside

| Skill | What it does |
|---|---|
| `skills/reel-editor` | Main editor skill: techniques, rules, and tested Python + ffmpeg scripts |
| `skills/remotion-setup` | Installs Remotion's official agent skills (motion graphics in React) |
| `skills/hyperframes-setup` | Installs HeyGen's HyperFrames skills (HTML -> MP4 motion graphics) |

Scripts in `skills/reel-editor/scripts/`:

- `strobe_sync.py`: alternate two shots every few frames, copying the cut pattern and song from a reference reel; extends the song on-beat.
- `beat_montage.py`: cut a folder of clips onto the beats of a song (or a Premiere XML cut list).
- `crimson_grade.py`: crimson Aerochrome colour grade.
- `title_kit.py`: 20 travel/cinematic title lettering styles (Ladakh, Kerala Tales, Jodhpur Blue City...) with bundled free fonts. Preview: `skills/reel-editor/title_styles_preview.jpg`.
- `deva_kit.py`: 16 Hindi (Devanagari) calligraphy title styles: swash tails, hairlines, headline bar, chalk, grunge, plus the English meaning line. Preview: `skills/reel-editor/hindi_styles_preview.jpg`.
- `lyric_captions.py`: word-by-word song lyric captions over still images (huge red calligraphy on black & white + small white words on colour, with roman transliteration), timed to the vocals.
- `depth_cover.py`: reel cover with a huge title behind the subject (rembg cut-out) and a small spaced kicker.
- `travel_titles.py` / `travel_titles_anim.py`: place names that interact with the scene: lying on water, rising from the sea, flying out of arches, huge behind you, gold Hindi calligraphy, sliding out of a mountain. Stills and animated clips.
- `cosmos_intro.py`: 5 s black & white cosmos opener (warp stars, galaxy, black hole, nebula, planet) with accelerating cuts and camera-shutter sound.
- `hook_intro_outro.py`: "BORING se STUNNING" hook intro and animated FOLLOW outro.
- `common.py`: shared helpers (ffmpeg I/O, beat detection, on-beat audio loop).

## How to use

**Claude (claude.ai / desktop):** in a new chat say:

> Clone github.com/sumitsharma1112/reel-editor-skills and use the reel-editor skill.

**Claude Code:** copy the skills into your skills folder:

```bash
git clone https://github.com/sumitsharma1112/reel-editor-skills
cp -r reel-editor-skills/skills/* ~/.claude/skills/
pip install librosa soundfile opencv-python-headless numpy pillow rembg mediapipe
```

**Without Claude:** run the scripts yourself, for example:

```bash
python skills/reel-editor/scripts/strobe_sync.py --ref reference.mp4 --a deity.png --b aarti.mp4 --bw b --min-dur 15 --out reel.mp4
```

Needs Python 3.10+ and ffmpeg.

## Notes

- Remotion is free for individuals and small teams; companies need a licence (see remotion.dev).
- Only use music and reference videos you have the right to use.

## License

Code: MIT. Fonts in `skills/reel-editor/fonts/` are Google Fonts under the SIL Open Font License.
