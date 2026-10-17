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

## Reference-led illustrated reel styles
For the eight romantic/devotional references (double exposure, moonlit lyric scroll,
burgundy curved/typewriter text, metaphor-prop scrapbook, surreal luminous montage,
stacked Indic lyrics, anime foreground parallax, red memory silhouette), read
[the eight-style recipes](references/eight-reel-style-recipes.md). Use
`scripts/inspect_reference.py` for broad and dense timestamped contact sheets.
Keep observed behavior separate from suggested settings; do not apply a single
caption animation to all styles. Verify actual dialogue timing, especially the final
20–30 seconds; silence detection and estimated timestamps do not establish word sync.

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
| Phonetic stretching for held notes (qawwali/classical/ghazal): "naam" -> "naaaaaaam", each new vowel letter rides the singer's pitch | `python scripts/phonetic_stretch.py in.mp4 lyrics.json out.mp4 --y 1050` (lyrics format in the script docstring) |
| Blur one person's face in a reel (privacy), others stay sharp | `python scripts/face_privacy_blur.py --video in.mp4 --hide her1.jpg,her2.jpg --keep me.jpg --models models/ --out out.mp4` |
| Karaoke caption video from a word-timed ASS (stretched vowels, gold active word, velvet bokeh bg) | `python scripts/karaoke_ass_captions.py` (parse ASS to events.json first, see docstring) |
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
Reference look (learned frame by frame): words simply FADE (opacity 0->1 over ~0.6 s, smoothstep, no blur, no
movement), stay still, and the whole screen fades out together (~0.6 s). Big Devanagari words carry a long
calligraphic swash tail (Amita + deva_kit.swash); roman words look hand-sketched (double outline strokes,
slightly offset). Navy text on soft pastel skies. Best backgrounds: user-made ChatGPT images (9:16, top 40%
kept as empty sky); devotional prompts must say 'respectful devotional illustration' or they get blocked.
Instagram safe zone (learned from the user's screenshots): the FEED shows a reel as a centred 4:5 crop
(y 285-1635 on 1920) with the username/audio line on top, and the Reels view puts the 'Reels / Friends'
header over the top ~400 px. Keep every word below y=440 and above ~1500, and cap the block height per
scene (~280-420 px) so it stays in the sky and off faces.
Amita draws the conjunct च्च like ज्ज (नच्चा reads as नज्जा): words with च्च switch to Yatra One. Test-render
every conjunct-heavy word before the full render. Text colours: gold/cream on red scenes, deep red/maroon on yellow skies, white on snow scenes.
No word timings and no transcription model? Find repeated sections with chroma similarity (chorus repeats
correlate 0.6-0.7), split each section evenly by line, then spread words by syllable count; check any
visuals in the source video (mountains/snow/waterfall shots) to confirm where verses start.

### Edits templates (learned from screen recordings)
`scripts/photo_dump_template.py` + `templates/*.json` rebuild Instagram Edits templates with the user's own
media. `take_me_to_the_beach.json` (song: Take Me (To The Moon) by Ian Asher, DANNY, 20 s, 110 slots):
0.93 s hero opener, about 21 strobe cuts of 0.12 s ("take me to" in white lowercase), a 3.7 s hero
beach shot ("the beach"), more strobe cuts (some 0.06 s), a 1.23 s hero, a run of 0.3 s cuts, then 0.12 s
strobes to the end. Extending to ~30 s: keep cuts up to a late cut that sits on a beat (19.383) and then
replay the template from an earlier on-beat cut AFTER the text intro (9.530), shifting those cuts by J-S;
join the song the same way with a 30 ms crossfade (song starts at 1.98 s in the user's Edits recording).
The intro text is not repeated and every cut stays on the music. Use a 3-4 s video for the long hero slot.
`dhivara_slow_cinematic.json` (Dhivara, 29 s, 9 slow slots): reversed tilt-down from the waterfall top
to the person in slot 0, then photos with gentle push/pull and the long video in slot 6.
Learning cuts: when thumbnails make brightness dips unreliable, detect the transition ICONS (yellow
pencil / white rounded box, ~45 px squares) that sit exactly on each clip boundary; scroll speed ~147 px/s
at 1x zoom (measure by profile cross-correlation), cut time = frame_t + (icon_x - playhead_x)/px_per_s.
To learn a new template, follow the steps in the script docstring (track the clip
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

### Phonetic stretching (held notes in qawwali, ghazal, classical)
- When the singer holds a vowel, repeat that vowel letter by letter while the note lasts
  ("naam" -> "naaaaaaaaam", "shyaam" -> "shyaaaaaam"), so viewers can follow the alaap/meend.
- Each new vowel letter is placed higher or lower by the singer's pitch at the moment it appears
  (300 cents = 0.36 x font size, lightly smoothed), so the word draws the melody: vibrato wobbles,
  meend slides, taan jumps. Newest letter pops 1.45 -> 1 in 0.14 s.
- Pitch: pull the voice out of the mix with librosa nn_filter soft-mask (REPET), then pyin
  (fmin 140, fmax 900). Without the separation the harmonium drone wins and pitch sits at 100 Hz.
- Finding the held words: plot the separated-vocal spectrogram + pyin; long wavy harmonics
  (0.8 s and up, often with vibrato) are the held vowels. Map the user's line transcript onto the
  voiced segments; give every word [text, t0, t1] and add the vowel index on held words.
- Colours: sung words white, active word gold (#F2C46D) with soft glow, upcoming words 37% white;
  a small dim preview of the next line underneath. Font: Cormorant Garamond 700 italic (Sufi/ghazal feel).
- Layout is fixed per line at its fully stretched width (later words wait in place and the vowels
  flow into the gap). If a line with several held words is still too wide at 46 px, trim the
  extra-letter budget of the longest-held word until it fits; check a contact sheet.
- Put the lines in empty space (black band under a letterboxed clip), never over faces.

### Covers
Show the subject's face and the title clearly, keep it readable as a small grid thumbnail, and do
not give away the punchline of a comedy reel.
- For a song reel, the song's own name (e.g. "अयि गिरि नन्दिनि") sells better than a generic greeting:
  put the song name huge and the greeting ("JAI MATA DI") small and spaced above it.
- Depth: choose a photo with open sky above the subject; cut the subject out (rembg u2net) and paste only
  its upper part (crown, weapon tip, head) over the last title line. Keep the text clear of the face,
  otherwise the word becomes unreadable. Check the 3:4 grid crop.

## Handle on every reel
Always add the handle `@aitricksbysumit` to every reel for Sumit's own page without asking: small, readable, inside the safe zone (e.g. top-left under the username area, or bottom corner of the card), soft shadow so it reads on any image. Skip only for reels made for someone else (friends/clients) unless he asks.

## Privacy
Never show a family member who asked not to be shown: drop their photos first; for group footage use
`face_privacy_blur.py` (YuNet + SFace recognition, track-level vote, ellipse pixelate). Check frames after.

## Keep this repo updated
Whenever you learn a new technique, font set, style or workflow for the user (from a reference they share or a
new reel you build), add it to this repo in the same session: a reusable script in `scripts/` (tested on real
input), a section in this SKILL.md, fonts in `fonts/` (OFL/free only), a line in README.md. Then commit and
push to `main`. Never commit the user's personal photos, videos, songs or SFX.

### White/gold kinetic captions (reference-led motion)
Use `scripts/kinetic_gold_captions.py --spec edit.json --out reel.mp4` with optional
`--audio matching_song.mp4`. JSON contains `duration`, `scenes` (`start`, `image`), and
`captions` (`start`, `end`, `before`, `accent`, `after`). Image paths are relative to
the JSON. Use `--preview --out preview.jpg` to inspect the first caption's motion.
- Montserrat 700 white #FFFFFF anchors; Great Vibes 400 gold #FFD64A accents with a
  soft glow. Keep glyphs in the open sky; crop photos to full 9:16 without blurred sides.
- Inspect a reference at 4 fps or faster: sparse contact sheets miss brief zooms and
  rotation transitions. Match word assembly, accent entrance and outgoing movement
  independently; a small repeated pop is not a replacement for a camera flip.
- Build white words individually, reveal gold script above them, briefly rotate and
  fade the outgoing stack while introducing the next upright phrase. Outgoing text
  must clear at the end of the transition: never hold old lyrics upside down.
- Use brief large zoom-through cuts with directional blur. Inspect both transition
  frames and settled frames for clipping and overlap before delivery.
- Per-line timestamps provide approximate phrase timing, not verified word sync.
  A style-reference song is not the requested soundtrack. When matching audio is
  absent, deliver a clearly labeled silent visual edit and request the correct audio.
- Tested on a 41-second, ten-photo edit. For longer captions, shorten the display
  groups or reduce type size; review every line, not just the first preview.

### Cloud art on a real sky canvas
Register transparent cloud art in a 1080x1920 canvas within x=100–880, y=400–1160;
reserve y=1180–1420 for captions and leave the top, bottom and right UI areas clear.
Normalize artwork from its alpha bounds, preserving soft edge transparency, then
composite over the original sky photo. Amita 700 with Baloo 2 600 works for Hindi;
cream #F6ECD6 with navy #1E2B57 outlines reads well over sunset skies. Keep full
sprite bounds and flourishes separated, and omit speaker-name labels when requested.
Verify saved images by decoding them before packaging; an intact ZIP CRC alone does
not establish that every embedded PNG is readable.

## Captions (when asked "Caption")
Plain text only: a 1-line hook, 2-4 short lines, a comment CTA, then 8-10 relevant hashtags.
No promotion, no event/brand claims the user did not ask for.

## Red calligraphy lyric video (white page, Barsaat/Banjaare reel style)
`scripts/red_calligraphy_lyrics.py` — pure white 1080x1920, giant red (#EA0000) calligraphy, words appear one by one and stack (max ~3 per screen), hard cuts with a tiny 0.3 s settle-pop.
- Roman lyrics: Berkshire Swash, condensed to 80 % width (tall letters like the reference). Devanagari: Amita 700 (Latin is not in the amita subset).
- Phonetic stretch: `(final, start, stretch_end, base_run)` — the longest repeated letter grows from base→final across the held note (raang → raaaaaaang).
- Long stretched words break into stacked 5-letter chunks (raaaa / aaang), no orphan chunk under 3 letters, so text stays huge.
- Layout scale comes from the group's fully stretched form, so nothing jumps while letters grow. Block centred at y≈980, inside the IG safe zone.

## Masked poster carousel (giant yellow type behind the subject)
`scripts/poster_mask_type.py` — 3:4 (1080x1440) carousel post from ONE original photo, face untouched.
- Headline: Anton, #F5C518 yellow, stretched full width, 2 lines (~420 px each), ink-speckle distress.
- Subject cut out with rembg `u2net_human_seg` (largest blob only) and composited IN FRONT of the letters; place lines so the head overlaps only the lower half of line 2 — the word must still read.
- Warm punchy grade (+contrast, R up, B down) + grain. Small Montserrat caps label above the headline.
- Handwritten Caveat Brush note in white with a soft black shadow + hand-drawn arrow, on a darker area (never on a white shirt).
- Why not ChatGPT: it lays text out with Python boxes (Canva look) or redraws faces. Doing it here keeps the photo 100% original.
- Approved ChatGPT variant (Rishikesh Post 1): one-line full-width "RISHIKESH" in distressed yellow, set in the sky above the horizon with the bridge cables/towers crossing IN FRONT of the letters; dramatic golden-hour cloud sky; small white handwritten note in the sky ("bas chal pada…") with a thin arrow down to the subject's head. Prompt that worked: one photo per post, image generation not code, no boxes/panels/insets, headline 40–60% of frame interacting with the scene, face untouched, "Make one post per reply… wait for next".

## Painting band reel (ChatGPT lyric paintings → 9:16 reel)
`scripts/painting_band_reel.py` — 16:9 ChatGPT paintings with lyric text baked in, shown as a sharp band across the middle of a 9:16 frame over a heavily blurred, darkened copy of the same painting; slow 4 % push-in ANCHORED RIGHT (lyric text sits on the right, never crop it); 0.45 s crossfades; last chorus alternates two images.
- ChatGPT prompt rules that worked: subject left / text right; text = Roman-before + ONE big Devanagari calligraphy word + Roman-after, never repeat the Devanagari word in Roman; spell exactly; same art style as Image 1.
- Ask the user for each image downloaded individually from ChatGPT — screenshots of a grid are tiny strips.

## Exact-timed cream Gurmukhi captions
Use `scripts/timed_caption_stills.py` with pre-rendered RGBA captions and full 9:16 background stills. Shape Punjabi with RAQM and a Gurmukhi-capable font such as Noto Serif Gurmukhi; Berkshire Swash supports Latin only and can be used for Roman transliteration. Cream #F2E6CE with a dark stroke and lower-frame gradient stays readable over golden devotional artwork. Keep verse intervals exact, add a slow 4.5% push and 0.18 s text fade, and leave audio absent when no matching recitation is supplied.

## Black-page kinetic lyric cards
`scripts/black_gold_kinetic.py --spec cards.json --out sample.mp4` renders a black
9:16 page with Montserrat 900 white anchors, Great Vibes gold #EDB84F accents,
and condensed outline variants of the same bold font. JSON has `duration` and
`cards` with `start`, `end`, and `lines` (`text`, `font`, `size`, `y`, `delay`).
Use short stacked groups, a 0.18-second zoom/blur entrance, staggered side slides,
soft glow and brief exits. Keep settled text inside x=80–900 and y=800–1300.
Inspect the reference at 8 fps to distinguish word assembly from card changes.
Tested on a five-second Roman Punjabi sample; timings are approximate until
matching song audio is supplied. Never attach the unrelated style-reference song.

## White-page blob doodles with page turns
Reference studied: a 26.2-second vertical cartoon song reel and its editing-timeline
screen recording. The recording shows grey preview placeholders; derive visual motion
from the finished reel, not guessed app preset names. Inspect transitions at 8–10 fps.

- White paper, thin imperfect black outlines, rounded blob bodies, dot eyes and simple
  mouths. Small looped pose changes (hands, instruments, bell) carry the performance;
  a static drawing with camera motion alone does not reproduce character animation.
- Small muted gold serif lyrics above the drawing; one or two centred lines, occasional
  emoji and repeated vowels for held notes. The exact reference font is unverified;
  bundled Cormorant Garamond is a mood substitute, not a confirmed match.
- Use whole-page 3D yaw over a BLACK surround: page narrows toward edge-on, incoming
  page starts small, swings/expands and settles flat. The clearest example occurs
  around 5.9–7.1 seconds. Keep full white-page corners visible during the turn.
- Alternate with cropped dolly zooms, half-turns, horizontal mirroring and clean cuts.
  The reference sometimes deliberately holds reversed/upside-down text. Prefer upright
  captions after transitions unless that reversal is explicitly requested.
- Pulse outline ink between black, navy, magenta, cyan and warm red; alternate bright
  paper with a grey dark-edge vignette. Temple shots occasionally flash neon green.
  Keep tinting separate from page geometry; hue changes are not new drawings.
- For new reels, move the reference's high caption placement down into the usual
  Instagram safe zone; don't copy its small text location blindly.

`scripts/doodle_page_motion.py --a page_a.png --b page_b.png --effect hinge --out turn.mp4`
provides reusable **reference-inspired approximations**, not exact preset reconstruction:
`hinge`, `halfturn`, `dolly`, and `inkpulse`. Uses Pillow/NumPy/ffmpeg. Tested all four
effects on decoded real reference frames. Supply complete page images; character pose
animation needs separate assets. No reference footage or personal assets belong in git.

### Generated doodle scenes with real bhajan audio
`scripts/doodle_bhajan_reel.py --spec scenes.json --out reel.mp4 --preview preview.jpg`
combines generated white-page drawings, small Roman lyrics in Cormorant Garamond
700 italic (muted gold #9B843E), ink pulses and the studied 3D page swing.
Spec contains `duration`, `audio`, and `scenes` (`start`, `end`, `image`, `lines`).
Generate each distinct scene separately, omit baked-in text, then crop to dark-ink
bounds and fit the drawing inside an 810x660 region. Anchor captions at y=580/660
and art at y=1150, keeping critical content above y=1500. Reuse a scene across
consecutive lyric cards; apply page turns when the scene changes, not every line.
Whole-sprite breathing/bobbing is modest motion, not independent hand/face rigging.
Use uploaded matching audio and user phrase timestamps; word-level sync remains
unverified. Tested with a 23-second, eight-phrase devotional edit and four scenes.

### Remotion implementation of doodle page motion
The `remotion-doodle/` project implements the learned white-page treatment in React:
frame-driven CSS perspective/rotateY page hinges, half-turns, zoom settling and
SVG alpha tinting of transparent ink sprites. Scene times stay fixed and audio
is continuous; transitions do not cumulatively shorten the song timeline.
Run `npm ci`, `npm run check`, then Studio or render with a local JSON props file.
Keep user art/audio in ignored `public/media/`, not in repository commits.
Load the bundled local serif font before capture to avoid fallback-font frames.
No exact new preset can be inferred from screen recordings whose preview remains
grey; use visible timeline information plus the corresponding finished reel.

`BrandedReel` adds same-art text hooks and follow cards around the Remotion reel.
Keep the core song in its own Sequence so prepended hooks shift audio and lyric
timing together. Brand cards use the same loaded serif font and existing art;
English-only requests apply to hooks, CTA, caption and cover text. A "No manual
editing" claim describes the creator's workflow, not the absence of editing by AI.

### Colourful cute singer reels
Remotion `ColourfulReel` preserves generated sprite colours instead of tinting the
ink. Use an original rosy-cheeked rounded singer, warm pastel pages, restrained
floating hearts, sparkle accents and musical-onset bounce (about 2% scale).
Keep critical artwork above y=1500 and the follow-card text below the top UI.
Normalize alpha-bounded assets into a 1000x1000 transparent canvas so mouth masks
and overlays remain registered. Inspect alpha, face and mouth position before
rendering. A calibrated mouth overlay may respond to soundtrack RMS amplitude;
this approximates singing energy, not exact phoneme lip sync. Use a matching
uploaded soundtrack and add no invented lyric captions when transcript is absent.
The latest "no opening hook" request takes precedence over a prior branding intro.
The component plays the song immediately, then adds only a follow-page ending.

### Melancholy painted lyric reels
Remotion `PaintedLyricReel` supports expressive oil-paint backgrounds, quiet navy
caption regions, Cormorant Garamond italic cream #F7EBD8 and Great Vibes gold #F1D28D.
Use original paintings inspired by a requested historical artist rather than copies
of specific paintings. Place figures low and leave y=600–1000 open for caption groups.
Slow pushes (about 3–6%), horizontal drift, 1.15-second picture crossfades and gentle
script reveals fit a sad performance better than repeated spins or flashes.
Derive phrase text from readable user-supplied captions where available. Inspect
a 4-fps cropped caption strip and verify OCR against frames; exclude watermarks.
Embedded caption timing is not independently verified word-level vocal timing.
Short phrase reveals adapt to duration so the complete phrase remains readable.
Render a sample, inspect settled text and transitions, then export with matched audio.

### Photo-first editorial reel frames
When a reference uses huge type integrated into photos, do not substitute cream page headers with small photo boxes. Design directly at 1080x1920 for reels; 1080x1440 is 3:4, not 9:16. Match the reference's photo coverage and lettering scale. Place type in actual sky, walls or floor; use perspective transforms for graphic lettering and original-pixel subject masks only when the mask preserves readable words. Inspect every final frame for obstructed faces and clipped letters. Preserve supplied photography without regenerating people or environments when the user requires exact images. For school-trip content, adapt festival copy to age-appropriate trip humour. Use no more than four source photos per collage. Reel assembly can use a restrained 2.5% push per three-second frame; export without a soundtrack when none is supplied.

### Timed dialogue comedy with illustrated reveals
Use the user's supplied transcript and actual audio duration for alternating speech bubbles and reactions. Draw or generate every visual setup and reveal named in the script, rather than showing only talking heads: currency amount, ordinary/inverted bowl, masked cat, photo-frame cat and final dog are distinct scenes. A photo frame should not become a TV unless the user changes the script. Transparent pose atlases can be cropped into video sprites without changing artwork; inspect alpha rather than judging the RGB backdrop in a viewer. Match dialogue pauses, avoid revealing the final visual early, and add a persistent handle when requested. `DialogueComic.tsx` supplies a reusable tan stage with timed bubbles and native vector props.

### Rebuild a dialogue reel with distinct generated panels
If a user rejects a reused two-sprite scene as unlike a hand-drawn comic reference, generate multiple full narrative illustrations. Keep the same character identities using reference panels; alternate large listener reaction close-ups with questioner-plus-object panels. Illustrate every physical reveal in the same medium, rather than inserting unrelated generic vector props. Composite speech balloons separately so the transcript stays exact and legible. Avoid revealing masks, frames or the dog before their punchline. Keep the original audio intact, use timed hard cuts and restrained image pushes, inspect a contact sheet and actual video frames, and preserve a requested handle on every frame. A ten-image sequence can support seventeen dialogue exchanges without making every shot the same composition.
## Scrapbook collage song animation (paper + die-cut stickers)
Script: `scripts/scrapbook_collage.py scenes.json out.mp4 --audio song.mp3` (`--preview 2.5` renders one frame).
- Cream paper card with grain, fibres and torn green/kraft corner strips, sitting in a dark 9:16 frame (card_y / card_h).
- Every image becomes a sticker: background removed (rembg u2net, largest piece kept), white die-cut border, soft drop shadow.
- One scene per lyric line; stickers enter on cue with back-ease: `pop`, `spin`, `drop`, `slide_l`, `slide_r`, `fade`, then idle float + sway.
- Tiny italic serif caption (Cormorant 600i, dark brown) at the bottom of the card.
- `photo` scenes go full-bleed with a slow push-in (eye close-up endings).
- Pick literal props per line (heart + band-aid for "zakhm pe marham", sunflower for "phool", globe for "jag", planet for "taare").

## Flying birds (aasmaan mein udte panchi)
Script: `scripts/flying_birds.py image out.mp4 --dur 8 --n 14 --sky 0.05 0.3` or `Flock(W, H, n, sky_y).draw(frame, t)` inside any renderer.
- Procedural flock: two curved flapping wings per bird, occasional glide, sine bob, slight tilt.
- Depth: far birds smaller, slower, fainter; flock wraps across the sky.
- Keep `sky_y` above heads/idols so no bird crosses a face.
- Hand-lettered lyrics mode (`"lyrics": [{t0, t1, text, big: [...]}]`, `lyrics_y`): words appear one by one below the card in Caveat Brush / Kaushan (alternating per line), the key word in Permanent Marker caps + accent colour with a small bounce, soft shadow + glow; replaces the small card caption. Move the card up (card_y ≈ 450, card_h ≈ 760) so lyrics sit in the safe zone underneath.

## Film-burn hook intro (trending "save it" credit card)
Script: `scripts/film_burn_hook.py in.mp4 out.mp4 --lyric "first words…" --hook 1.9 --credit "Song" [--top "..."]`
- First `hook` seconds become a black card: orange film-burn light leaks with sprocket holes sweep and flicker, the song's first words type in letter by letter (Cormorant italic), top-right Instagram glyph pops, handle + song credit type in, glyph turns gradient.
- Ends with a burn-flash wipe into the reel; audio untouched so the lyric matches the singer.
- Set `--hook` to the end of the song's first line.
- Title mode (`--title "The Beauty of" --cycle Waiting`): gold serif title + a word flickering through fonts over burn flashes, video fades up under the title.
- Red-word variant: keep Berkshire red word captions running from frame 0 over the burn card (see raft build169 pattern) so the hook already shows the lyric.

## Bam Lahiri word-cut (scripts/bam_word_cut.py)
Full-frame 9:16 living paintings driven by a SEG table `(start, image, line_words, highlight_idx, flow, particles, mode)`.
- Slow spoken intro: one image per half-line, `dip` (dip-to-black) cuts. Never dip the very first frame.
- Drop / war-cry: `flash` cuts (white flash + strong entry punch).
- Fast chant section: ONE IMAGE PER WORD, `cut` mode; the tiny centred Devanagari line stays put and the sung word glows saffron (highlight_idx).
- Snap each start to the nearest audio onset (per-section normalised onset peaks). Masked noise-flow (rembg), particles, warm-pixel fire flicker, handle top-left y≈460.

## Shayari karaoke (scripts/shayari_karaoke.py)
For romantic shayari / nazm reels on AI images (e.g. trending maroon faceless-couple look).
- Whole misra appears at once, dim (0.32 alpha; 0.55 for the first one so frame 0 reads), each word brightens as it is spoken.
- The rhyme word (kitaab / gulaab / sharaab ...) sits on its own line in Great Vibes 190px gold with a warm glow and swells when sung; other words in Cormorant Garamond 700 italic cream.
- Hook: most striking image first (not the literal first line image), first misra visible at frame 0, small gold kicker line "sirf usko bhejna jiske liye ye likha hai" for 3.6 s (share bait).
- Soft 0.3 s crossfades, slow Ken Burns, candle flicker on bright pixels, falling dark-red petals, gold dust, vignette and a soft dark band behind the caption block.

## EffectCraft pipeline (scripts/effectcraft/)
Alternative renderer: EffectCraft (pure-Rust After Effects clone, github.com/storytold/effectcraft) driven headless.
- Build once: `cargo build -p effectcraft-cli --release` (≈19 min on 2 cores; set CARGO_TARGET_DIR outside the clone, LTO off).
- `beats.py` snaps one cut per image to audio onsets -> plan.json; `make_reel.py` writes an After Effects-style JSX:
  cover-fit images with scale punch, Linear Wipe on alternate cuts, white flash + Gaussian Blur pulse on cuts,
  Glow (`ADBE Glo2`) on an adjustment layer, per-word caption text layers with a text animator
  (Opacity 0 + Scale 180%, range selector Start 0→100 over 0.3 s), handle text.
- `effectcraft-cli script reel.jsx --empty --save-as reel.ecproj` then `render --format h264 --audio on`.
- Gotchas: keyframes at the same frame merge (pre-cut keys must be ≥1 frame earlier); a new animator has no selector,
  add `ADBE Text Selector`; fonts by PostScript name from ~/.local/share/fonts (Baloo2-ExtraBold shapes Devanagari fine);
  output is ~15 Mbps, recompress with ffmpeg for long reels. ~0.44 s/frame at 1080x1920 on CPU.
