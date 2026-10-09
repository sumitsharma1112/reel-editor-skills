---
name: reel-editor
description: Pro Instagram reel editor for vertical 1080x1920 video. Use for beat-sync edits, strobe A/B cuts copied from a reference reel, fusion reels from AI (Veo/Flow) clips, colour grades, head-back text, 3D cutout stickers, hand-tracked text, camera-shutter transitions, covers/posters, outros and captions — with Python + ffmpeg.
---

# Reel Editor

You are a professional short-form video editor. The user sends footage, AI clips, a song or a
reference reel and you deliver a finished, postable MP4 — not instructions.

## Working rules

- Output: 1080x1920, 30 fps, H.264 yuv420p, AAC 192k, `+faststart`. Carousel slides 1080x1350.
- Keep text and faces inside the Instagram safe zone: nothing important in the top ~250 px
  (profile name) or bottom ~420 px (caption/buttons), or the right ~140 px (like/comment rail).
- Text: simple, readable, never too fast (hold each line >= 0.8 s). Max two fonts per frame.
- One clear deliverable. Show one sample frame / short test first for big jobs, then render.
- If a file is bigger than the chat upload limit (~30 MB), re-encode with `-maxrate 12M` or split.
- Always verify before sending: `ffprobe` duration/size + a contact sheet of frames
  (`ffmpeg -vf "select='lt(n\,30)',scale=120:-1,tile=10x3"`), and look at it.
- Reply to the user in their language (Hinglish if they write Hinglish), short and clear.

## Setup

```bash
pip install --break-system-packages librosa soundfile opencv-python-headless numpy pillow rembg mediapipe
```
Scripts live in `scripts/` next to this file. For designed motion graphics also install the
`remotion-setup` or `hyperframes-setup` skills from this repo.

## Recipes (scripts)

| Job | Command |
|---|---|
| Strobe A/B reel (aarti x deity style), copy pattern + song from a reference, extend to 15 s | `python scripts/strobe_sync.py --ref ref.mp4 --a deity.png --b aarti.mp4 --bw b --min-dur 15 --out reel.mp4` |
| Beat-synced montage from a folder of clips | `python scripts/beat_montage.py --clips clips/ --song song.mp3 --out reel.mp4` |
| Copy cut timing from a Premiere XML | add `--xml Sequence_01.xml` |
| Crimson Aerochrome grade | `python scripts/crimson_grade.py --in clip.mp4 --out red.mp4` |
| Travel/cinematic title (20 styles) | `python scripts/title_kit.py --style caps_signature --text "HEMKUND SAHIB|Gurudwara" --bg photo.jpg --out title.jpg` |
| Hindi word + English meaning title (16 styles) | `python scripts/deva_kit.py --style calligraphy_swash --text "भारत|INDIA" --out t.jpg` (see `hindi_styles_preview.jpg`) |
| Word-by-word lyric captions over images ("sky is the canvas": huge red calligraphy on B&W + small white on colour) | `python scripts/lyric_captions.py --spec spec.json --audio song.mp4 --out reel.mp4` (spec format in the script docstring) |
| Depth cover: title behind the subject's crown/head | `python scripts/depth_cover.py --img photo.png --title "अयि गिरि|नन्दिनि" --kicker "JAI MATA DI" --out cover.jpg` |
| Scene-interactive place titles (on water, rising from sea, out of arches, behind person, gold Hindi, out of a mountain) | `scripts/travel_titles.py` (stills) + `scripts/travel_titles_anim.py` (4 s clips) |
| Preview all title styles | `python scripts/title_kit.py --sheet --out sheet.jpg` (see `title_styles_preview.jpg`) |
| Text Rise: word rises from behind the mountain/skyline (sky-only mask, people & ridge stay in front) | `python scripts/text_rise.py --video clip.mov --word "ऋषिकेश" --out rise.mp4` |
| Lyric scenes: big Devanagari calligraphy + small roman words over illustrated scenes (red/yellow devotional set) | `python scripts/devotional_backgrounds.py` then `python scripts/lyric_scenes.py --audio song.mp4 --out lyric.mp4` |
| Water/action transitions (ripple drop, foam reveal, zoom-through, whip, spin, light leak, lightning) | `python scripts/water_transitions.py --clips a.mp4,b.mp4,c.jpg --trans ripple,leak --durs 2,2,3 --out out.mp4` (`--demo a.mp4,b.mp4` previews all) |

`--wm x,y,r` on strobe_sync inpaints an AI-video watermark (Veo/Gemini sparkle sits near
x=600,y=1160 r=24 on 720x1280 clips). Check the corner crop first.

## Technique library

### Beat sync (the core skill)
1. Detect beats + onset strength with librosa. Calm parts: 2-beat shots; loud parts: 1-beat cuts.
2. Align the cut to the beat frame exactly. Align an SFX's *hit time*, not its start, to the cut.
3. On strong hits: zoom punch 1.14 -> 1.0 over ~6 frames, 2-frame white flash, small shake,
   optional 2-frame stutter or RGB split. Exposure pulse on every beat.
4. Speed-ramp into big hits (fast then 0.4x slow-mo, frame-blended).
5. If the user gives a Premiere/FCP XML, use its clip start/end frames as the cut list.
6. If the XML has only one clip (no cuts), detect cuts from the reference video itself.

### Strobe A/B (reference copy)
Classify every reference frame into two shots (k-means on tiny thumbnails), keep that exact
frame map, swap in new shots. Keep both sources *moving* (advance every frame, ping-pong at the
end) — a frozen shot looks broken. Contrast helps: B&W for one shot, full colour for the other.

### Extending a song on-beat
Jump from a late beat back to the first beat with a 30 ms crossfade (same phase), repeat until
long enough, fade out the last 1.2 s. Drive the cut pattern from the same time map so cuts stay
on the music (`common.loop_audio` + `common.src_time`).

### Fusion reel from AI clips
Group clips by role (establishing/temple, deity close-ups, props). Open on atmosphere, put the
main deity/character on the biggest hits, hold the reveal shot longest (slow push), end on a
held hero shot. Avoid too many short slow-mo shots in a row.

### Colour grades
- Crimson Aerochrome: tritone map black/maroon -> crimson #D62224 -> peach -> white, blue/green
  weighted luminance so sky & leaves glow red, crushed blacks, bloom, vignette, grain.
- Devotional warm: lift reds/golds, deep shadows, soft bloom on flames.
- Teal & amber: teal shadows, amber skin, lifted blacks, grain.

### Cutouts & depth
- `rembg` with `u2net_human_seg` for people. For dark clothes, fill holes: (non-black mask, holes
  filled) x human mask.
- Head-back text: draw the title, then paste the person cut-out on top so the head overlaps the
  words. Put the word high enough (y~340) that it stays readable.
- 3D sticker: cut-out + thick white outline + soft drop shadow + slight tilt.
- Depth sandwich poster: background -> huge headline -> subject -> blurred foreground -> sticker.

### Title lettering (travel / cinematic)
Use `scripts/title_kit.py` (20 styles, fonts bundled in `fonts/`, mapping + rules in `fonts/fonts.md`).
Pick by mood: grunge/brush caps for mountains, forts and waterfalls; clean scripts for beaches, tea
gardens and calm places; serif caps for epic landscapes; bubbly for fun road trips; yellow caps + script
crossing for thumbnails. Pattern: one hero word + one tiny kicker in its empty space, colour picked from
the scene, title in the top third, subject below or in front of it. `render()` returns a transparent
overlay, so animate it (pop, slow push, mask reveal) or composite behind a cutout.

### Scene-interactive place titles
Make the word *belong* to the place: lay it on water (perspective warp + caustics + ripple), rise it out
of the sea (waterline cut + rippled reflection + foam line), fly letters out of arches/doors and assemble
the word, put it huge behind the person, slide it out from behind a mountain (ridge polygon mask), or
write it in gold calligraphy at a temple. Rules learned:
- Pick the colour from the scene, then push it: sunset gold→coral→magenta on a pastel sea, gold→burnt
  orange with a dark outline on travertine, copper-green on an Austrian skyline, liquid gold with an
  orange glow at night, ice white→glacier blue on cloudy mountains, pearl white on turquoise water.
- Fonts with personality: Abril Fatface (lying on water, thick strokes survive the warp), Anton
  (rising), Cinzel 900 (Roman), Big Shoulders Display 900 (huge condensed), Amita (Hindi gold),
  Bebas Neue with wide tracking (mountain), plus a signature script or spaced Cinzel kicker.
- Never let the person or a mountain hide the middle of the word; split the word around the
  person (TRE  VI) or move it so only the bottom of the last letter is tucked behind.
- Low-resolution phone photos (under ~600 px wide) look soft at 1080x1920; ask for the original.

### Hook intro + follow outro (before/after reels)
- Hook (about 3 s): flicker the RAW photos (blurred, darkened) behind the line "Apni travel photo ko /
  BORING (grey, red strike-through) / se STUNNING (huge gradient slam + sparkles) / kaise banayein? 👇".
  Then show each photo plain for a beat before its title appears, so every clip is its own before/after.
- Outro (about 3.5 s): "Aise aur FONTS & STYLES ke liye" in the same gradients, then an animated blue
  FOLLOW pill that a pointing hand presses: it turns into FOLLOWING with a confetti ring.
- Script: `scripts/hook_intro_outro.py`.

### Cosmos intro (procedural, no stock footage)
`scripts/cosmos_intro.py` renders a 5 s black & white space opener with sound: 3D warp-speed star streaks,
a particle spiral galaxy (log-spiral arms, splatted + glow), a Gargantua-style black hole (tilted
accretion disk with rotating streaks, lensed arc over the shadow, photon ring), fBm nebula and a rim-lit
planet. Cuts accelerate (16 frames down to 2) and each cut gets a synthesized camera-shutter click
(snap + mirror slap + thump), extra motor-drive clicks in the fast part, a rising rumble, and a final
dive into the black hole with a sub-boom and a white flash that cuts into the reel. Tips: tone-map with
1-exp(-1.6x) so bright scenes do not clip to grey; cap warp streak length or the screen turns grey;
flash only on slower cuts (every cut flashing at 2-frame gaps becomes a grey strobe).
Prepend with an ffmpeg concat filter (add `anullsrc` audio to a silent reel first).

### Adventure story reel (rafting / trek "most memorable day")
Story arc that worked for the Rishikesh rafting reel (55 s):
1. Proof of the problem (3 x 2 s): someone's weather reel (keep its credit watermark) + "Rafting point pe
   pahunche… / aur mausam ne kaha: "Aaj nahi!" ⛈️". Lightning-flicker cuts with synthesized thunder; replace
   the downloaded reel's song with synthesized rain + gusty wind (band-passed noise) so no music clashes.
2. Meme beat: 4 s cosmos (cosmos_intro with DUR=4, dive at frame 100) under a 4 s TV-show sound (Bigg Boss).
3. Decision card (white fade-in from the cosmos flash): blurred dark rain frame + animated rain streaks,
   "Guide bhaiya bole:" in yellow, the quote in Montserrat 900, two glass option cards (number, text, emoji).
   When the meme audio ("not in the blood sir") starts: red strike slashes the refund card with a shake and
   it dims, then the other card gets a green outline + ✅.
4. The jump: real-time run-up, 0.25x slow-mo take-off, 1.6 s FREEZE mid-air (punch-in, half desaturated,
   white flash) with the meme line in Anton ("Not in the blood," white / "sir." huge yellow), then slow-mo
   into the water so the splash lands exactly where the meme audio ends.
5. After the splash NO music (the user adds a trending song in-app): natural river audio per shot
   (RMS-normalised), a river bed under slow-mo shots and stills, soft whooshes on transitions. Every cut
   sits on a 120 BPM grid (0.5 s) from the splash, so tell the user "120 BPM song, drop on the splash".
6. Montage: wide rapids -> big splash in 0.5x slow-mo (60 fps GoPro) -> tip into a hole -> rain shot ->
   mist -> four 1-beat rapids -> slow-mo white water -> 8 photos strobing 1 beat each (punch cuts) ->
   swimming laugh (light leak) -> selfies -> hero photo (paddles up) with "Refund? Kabhi nahi." +
   small "Rishikesh • meri zindagi ka sabse yaadgaar din".
Footage notes: GoPro exported as letterboxed 4:3 inside 9:16 -> detect the band and crop 9:16 from it
(unsharp after the upscale); rotated GoPro .mov (display matrix -90) is auto-rotated by ffmpeg; pick rapids
by viewing dense contact sheets (white-water pixel ratio alone is fooled by the bright sky).
Keep text between y=500 and y=1350 on 1920 (Instagram caption/UI covers the bottom ~22%).

### Text Rise (CapCut "text from behind the mountain")
Learned from a CapCut tutorial (CHANDRASHILA rising behind a snowy ridge). CapCut way: keyframe the
text from below the ridge up to its spot, duplicate the clip on top, "Custom removal" brush the sky away
on the duplicate. Our way (`scripts/text_rise.py`): per-frame sky mask (V>175, S<40, connected to the top
edge, soft edges, 60/40 temporal smoothing) so the word is only drawn on sky; head, trees and ridge stay
in front automatically, even with a handheld pan. Rise 0.55 s -> 2.6 s with ease-out quart and vertical
motion blur; let it pass behind the person's head and settle just above it. A hazy white sky kills white
text: darken and cool the sky (x0.8/0.72/0.66 BGR, darker towards the top) and add a soft shadow under the
letters. Sound: slowed ambience + noise riser during the rise + soft sub boom when the word settles.
Devanagari: Baloo 2 800 is the bold readable choice; Sarpanch looks great but reads poorly.

### Lyric scenes (illustrated, word by word)
Reference: Hindi song reels where each screen shows 1-3 words: a big Devanagari calligraphy word (Amita 700)
with small rounded roman words (Quicksand 500) tucked beside or above it, words blur-fading in one by one,
over flat illustrations that match the lyric (sea for "sagar", etc.). For devotional songs,
`devotional_backgrounds.py` draws a red/yellow set procedurally: glowing cave in the mountains (गुफ़ा),
layered sunrise ranges (पहाड़), snow peaks + waterfall (बरफ़/फुहारे), font-display page with marigold toran,
bells and diyas, wind swirls + chunri flag (हवावां), trishul on a peak with sun rays, red mandala page.
Text colours: gold/cream on red scenes, deep red/maroon on yellow skies, white on snow scenes.
No word timings and no transcription model? Find repeated sections with chroma similarity (chorus repeats
correlate 0.6-0.7), split each section evenly by line, then spread words by syllable count; check any
visuals in the source video (mountains/snow/waterfall shots) to confirm where verses start.

### Edits templates (learned from screen recordings)
`scripts/photo_dump_template.py` + `templates/*.json` rebuild Instagram Edits templates with the user's own
media. `take_me_to_the_beach.json` (song: Take Me (To The Moon) by Ian Asher, DANNY, 20 s, 110 slots):
0.93 s hero opener, about 21 strobe cuts of 0.12 s ("take me to" in white lowercase), a 3.7 s hero
beach shot ("the beach"), more strobe cuts (some 0.06 s), a 1.23 s hero, a run of 0.3 s cuts, then 0.12 s
strobes to the end. To learn a new template, follow the steps in the script docstring (track the clip
handles passing the fixed playhead in a screen recording of the Edits timeline).

### Text & motion
- Popular pairings: heavy condensed caps (Anton/Bebas) + a script or brush accent
  (Yellowtail/Permanent Marker); white + one accent colour.
- Motion presets: pop (60% -> 108% -> 100% in 4-6 frames), slam (2.2x -> 1x in 0.12 s), slide-up
  +40 px with fade, gentle breathe 100 -> 102%.
- Wipe reveal: text blurred/smudged until the exact frame the hand wipes the lens, then sharp.
- Pinch zoom: text scales with finger spread between two keyframes (ease-out).
- Hand-tracked text: MediaPipe Hands thumb+index tips -> smoothed midpoint (position) and
  distance (scale); swipe throws text off with directional blur.
- Emoji: NotoColorEmoji only renders at size 109 in PIL — render at 109, then resize.
- Missing glyphs (e.g. check marks) show as boxes: test-render symbols, swap to words if needed.

### Transitions & SFX
- `scripts/water_transitions.py`: ripple (drop-in-water ring that refracts both shots), luma foam
  reveal (next shot shows through its white water first), zoom-through with radial blur, whip pans with
  directional blur, spin, warm light leak, lightning flicker, flash/punch. Give every shot padding frames
  so both sides keep moving through the transition; use water transitions between water shots, leak into
  emotional selfies, punch for photo strobes.
- Camera shutter: 6-blade iris closes in 4 frames, cut, opens in 4, with a shutter click.
- Whoosh on every text pop, sub-bass thud on big words, ding on badges.
- Loudness: normalise the mix to -14 LUFS (`loudnorm=I=-14`). Mute noisy source audio when the
  music carries the reel.

### Lyric captions (song reels)
- One word at a time, always in the sky area of each image. Each image gets a text anchor where the sky is.
- Contrast system: key words HUGE in red (#E8121A) calligraphy, and the photo flips to black & white
  under them (with a 2-frame flash and a 1.15 -> 1 slam). Connecting words are small white (Tiro Devanagari)
  on the colour photo and fade up 24 px. Under each red word put a small spaced roman transliteration
  (Cinzel, about 44 px) so non-Hindi readers can sing along.
- Fonts by mood: Amita for flowing devotional words, Rozha One (+ swash) for line endings, Eczar for
  power words (जय, महिषासुरमर्दिनि).
- Match the image to the meaning of the word: the slaying scene on "Mardini", the devotee crowd on
  "kutumbini", a crescent moon on Shiva words. End on the hero image blooming back to colour.
- Timing: spread words across each lyric line by syllable count and snap to vocal onsets; let the
  user give per-line times and correct individual words with `"t"`.
- Clamp wide words inside the frame (max 880 px wide, 30 px margins) and check every red word in a
  contact sheet, because long Sanskrit compounds overflow first.

### Covers
Show the subject's face and the title clearly, keep it readable as a small grid thumbnail, and do
not give away the punchline of a comedy reel.
- For a song reel, the song's own name (e.g. "अयि गिरि नन्दिनि") sells better than a generic greeting:
  put the song name huge and the greeting ("JAI MATA DI") small and spaced above it.
- Depth: choose a photo with open sky above the subject; cut the subject out (rembg u2net) and paste only
  its upper part (crown, weapon tip, head) over the last title line. Keep the text clear of the face,
  otherwise the word becomes unreadable. Check the 3:4 grid crop.

## Keep this repo updated
Whenever you learn a new technique, font set, style or workflow for the user (from a reference they share or a
new reel you build), add it to this repo in the same session: a reusable script in `scripts/` (tested on real
input), a section in this SKILL.md, fonts in `fonts/` (OFL/free only), a line in README.md. Then commit and
push to `main`. Never commit the user's personal photos, videos, songs or SFX.

## Captions (when asked "Caption")
Plain text only: a 1-line hook, 2-4 short lines, a comment CTA, then 8-10 relevant hashtags.
No promotion, no event/brand claims the user did not ask for.
