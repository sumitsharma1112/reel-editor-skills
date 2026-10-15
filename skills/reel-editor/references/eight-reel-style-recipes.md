# Eight reference-led reel recipes

Use for requests to recreate the eight illustrated/romantic reference styles studied on 2026-10-15. Choose one recipe before generating art. Do not apply the same caption pop, glow or transition to every style.

## Contents
- Evidence and inspection
- Eight style recipes
- Motion implementation and audio alignment
- Asset prompting and delivery checks

## Evidence and inspection

The IDs below are filename prefixes, not upload order. All eight files were decoded into twelve broadly spaced frames each, then inspected in twelve-frame windows spaced 0.15 seconds apart. Values labelled **starting settings** are implementation suggestions, not measured original settings. Exact fonts, editing applications, generation models, easing curves and soundtrack beat alignment are unverified. Visible caption timing is not verified vocal timing. Do not call a style viral based on these files alone.

| ID / filename prefix | Duration | Native dimensions | Visual recipe |
|---|---:|---:|---|
| R1 AQMVxm17 | 27.53 s | 902×512 | Devotional double exposure |
| R2 AQMgn_Fs | 22.15 s | 844×512 | Moonlit illustration with rising lyric column |
| R3 AQN60UN | 13.70 s | 512×910 | Burgundy romance, curved text then typing |
| R4 AQNVdit | 49.03 s | 910×512 | Illustrated scrapbook with literal lyric props |
| R5 AQNlqBp | 9.10 s | 892×512 | Surreal luminous montage |
| R6 AQNnWc | 17.62 s | 682×512 | Shared-earphone drawing with stacked lyric assembly |
| R7 AQO5w3 | 17.13 s | 908×512 | Anime reverse angles and foreground parallax |
| R8 AQOVQNb | 15.33 s | 512×910 | Red memory silhouette with elderly couple |

Inspect new references with:

```bash
python scripts/inspect_reference.py reference.mp4 --out /tmp/reference-wide
python scripts/inspect_reference.py reference.mp4 --start 4.9 --end 5.5 --step .1 --out /tmp/reference-cut
```

Read the broad sheets, choose changing regions, then sample densely around those events. For precise cut boundaries inspect adjacent frames at the source FPS. Dense stills show direction and ordering; they do not prove exact easing or audible synchronization. Never upload reference media, extracted frames or source audio to git.

## R1 — Devotional double exposure

**Observed:** A softly visible deity image persists beneath moving silhouettes, raised hands and birds. Beige/grey haze, dark silhouettes, blue-violet deity accents. Small pale handwritten Roman lyrics sit near the image's horizontal centre. At 1.0–2.65 s several foreground compositions replace one another while the deity layer remains visible. The sequence reuses visual motifs later.

**Build:** Separate deity plate, moving foreground clips, atmosphere and captions. Use opacity compositing; try normal alpha before screen/lighten, since screen can erase dark silhouettes. Cut or briefly dissolve foreground clips while retaining the background. Keep lyrics stationary while footage changes.

**Starting settings:** foreground opacity 0.35–0.6, 0.15–0.3 s dissolves where needed, soft low-contrast grade, 2–4% plate drift across a phrase. Cream #E8DECA; bundled Dancing Script or Parisienne as substitutes, not confirmed source fonts. Avoid a heavy caption outline or huge title treatment.

**9:16:** Generate a portrait deity plate and independently frame silhouettes; reserve a calm middle region. Do not stretch the landscape composite.

## R2 — Moonlit rising lyric column

**Observed:** Back-view couple occupies the left; moon and foliage occupy the right/top. The composition stays stable while a narrow, subdued lyric column grows upward on the right. Later samples show more lines, not a sequence of full-screen replacement cards. The 5.0–6.65 s window shows incremental column progression.

**Build:** One illustration, optional independent leaf layer, clipped text viewport and an accumulating line list. Animate the column's vertical translation when a line is added; use a top/bottom opacity mask. Keep the couple stationary or apply only restrained camera drift.

**Starting settings:** midnight #111923, foliage #384137, moon #F1E6CC, muted text #B9AF96. Cormorant Garamond regular as a serif substitute. Line height 1.25–1.4; smooth 0.25–0.5 s scroll. Do not make every word spring into view.

**9:16:** Recompose the couple toward lower-left and lyrics in an open upper-right region inside the safe area. Enlarge the reference's tiny text for phone readability without turning it into a dominant headline.

## R3 — Burgundy romance with curved lyric and typing

**Observed:** Woman and man by stairs, deep burgundy clothes/background and warm cream skin/clothing. Small gold text curves above the woman's head. Between 5.15 and 5.30 s the picture cuts to a hands/anklet detail. Flat gold text then progressively types across the upper detail shot; 5.30–6.35 s includes partial words. Later phrases reset and type again. This is a clean shot change, not a page flip.

**Build:** Two matching paintings. Place a shaped text path above the head in shot one; use a fixed-width, centred text container for shot two and reveal grapheme clusters. Reset only at phrase changes. Keep hands and jewelry out of text bounds.

**Starting settings:** background #350408, accent #D8BB64, cream #E8C89F. Montserrat 500/700 as a Roman substitute. SVG textPath for curved Latin text. Reveal from actual word/character cue data; use a full-phrase layout so progressive text does not re-centre every letter. Preserve complete grapheme clusters for Indic scripts.

## R4 — Illustrated scrapbook with moving metaphor props

**Observed:** Consistent illustrated woman in green sari and man in red. Bookshop, green textured wall, window, bed and train shots. Photographic-style globe, sunflower, heart, planet, book and flowers overlap the drawings. Small cream Devanagari captions sit along the bottom. At 9.15–9.30 s the shop cuts to the green portrait; at 9.60–10.65 s sunflower/record elements move around the face, with a brief blurred movement around 10.05 s. Multiple props can coexist; this is not just one flattened image sliding.

**Build:** Background plates + separate character poses + individual transparent props + captions. Introduce objects on meaningful lyric cues. Use layer ordering to move a prop behind a character and another in front. Make each character pose/setting a distinct asset; a single sprite cannot recreate all scenes. Existing `scrapbook_collage.py` is a starting point, but its paper-card framing is optional: this reference fills the landscape frame.

**Starting settings:** 0.18–0.35 s prop entrances; scale 0.7→1.06→1; rotation ±8°; 6–14 px idle float at 1080 width. Cream captions #F3E6C8, restrained shadow; bundled Gotu or a readable Devanagari font as substitutes. Use blur during fast movement, then restore sharpness. Do not blur the full shot continuously.

**9:16:** Generate portrait settings and keep props within x=100–900. Place captions above the bottom interface region, not at the source's extreme bottom edge.

## R5 — Surreal luminous emotional montage

**Observed:** Brief black opening; eyes overlaid with a tiny figure, luminous pink/blue flowers, a CRT showing a glowing couple, blue-lit road, ghostlike couple, celestial silhouettes and a bright forest doorway. Shots change quickly; eye image is still present at 1.30 s and flowers appear at 1.45 s. Flowers pull back through 2.65 s. CRT and luminous-couple motifs recur. No prominent lyric typography in inspected frames.

**Build:** Generate separate cinematic moving clips for each motif with a consistent palette. Sequence them with clean cuts, occasional short dark dips and recurring hero imagery. Reserve glow for luminous subjects. Use background darkness to preserve silhouettes and facial features. Do not describe a slideshow plus bloom as equivalent to generated subject motion.

**Starting settings:** near-black/navy #060C1C, electric blue #54BFFF, pink #F18FD4. Bloom from a duplicate bright-pass layer, blur 12–30 px, opacity 0.2–0.45. Begin with roughly 0.6–1.5 s shots and adjust to actual soundtrack events; no BPM was measured. Add lyrics only if requested.

### R5 pacing correction from a recreated edit

When the user says fast surreal cuts are not visible, measure the delivered cut list before changing colour or adding more glow. An initial 19.78-second edit with 11 shot slots averaged about 1.8 seconds per shot and felt too slow. Rebuild the rhythm with roughly 0.4–0.8-second shots, a few 1.0–1.2-second emotional holds, and brief returns to earlier eye/flower/CRT/celestial imagery. A 35-shot revision averages about 0.57 seconds per shot. Treat this as a tested assembly target, not measured reference BPM or proof of vocal sync.

Use small 3-frame zoom-blur accents on selected cuts, followed by sharp settled pictures; do not make every transition a dissolve. Keep lyric phrase cards on their independent absolute timeline so rapid visual cuts do not repeatedly erase or restart the same caption. Insert generated metaphor art only where existing footage lacks a reference motif; animate stills modestly and distinguish them from live subject motion. Check motion in a short playback or dense frame sequence, not a sparse contact sheet alone.

## R6 — Shared-earphone illustration and stacked lyrics

**Observed:** Cropped shoulders of two illustrated people share white earphone cables. White background, mauve/rust and grey-green clothes. Pale yellow Devanagari lyric clusters build near the centre, with different word sizes and short stacked lines. In 1.0–2.65 s a short two-line cluster holds, then additional words assemble beneath/beside it; later groups replace it. Artwork remains visually stable.

**Build:** Use a clean illustration with deliberate open space between bodies. Keep earphone cable on a separate layer if it crosses captions. Lay out each complete phrase first, reveal words individually, then replace the group. Use 2–4 short lines and a consistent shared centre. Do not introduce upside-down outgoing text.

**Starting settings:** text #EBDC8D, muted purple #9A668D and grey-green #7D9390. Gotu/Devanagari serif alternative after glyph testing; no confirmed source font. 0.15–0.25 s opacity/scale settling; 1.0→0.98 group settle at most. Verify matras and conjuncts. This source is approximately 4:3, so create new portrait artwork rather than cropping both heads away by accident.

## R7 — Anime couple, reverse angles, foreground parallax

**Observed:** Bright white environment, woman with long brown hair and floral detail, man in lilac shirt, drifting pink petals. At 2.0 s the woman is facing camera; at 2.15 s the man replaces her. From 2.45 s a blurred back-view woman enters the foreground and slides across the sharp man. Later reverse angles put the man's blurred back in front of the sharp woman. Foreground coverage changes over time. No prominent caption block in sampled frames.

**Build:** Prepare at least four consistent poses: front woman/man and back woman/man. Composite sharp midground character, blurred foreground back-view cutout, and petals at several depths. Move foreground faster than midground. Use shot/reverse-shot cuts; do not horizontally mirror a front face to invent a back view. Keep the target eye/face visible long enough after each foreground sweep.

**Starting settings:** white #FBF9F8, lilac #B69CCD, petals #EDA5BA. Foreground blur 12–24 px at 1080 width, 10–20% width travel across 1–2 s; midground drift 1–3%. Petals vary in size/blur and move with seeded deterministic paths. Blur follows depth, not a global filter.

## R8 — Red memory silhouette and lifelong love

**Observed:** Vertical red vignette, dark dancing-young-couple silhouette in the middle, warm detailed elderly couple feeding one another below. Small cream Roman lyric near the upper fifth. Picture fades up from black during the opening, then persists while short phrases replace one another. The background silhouette is subordinate to the older couple; later samples retain the same layered arrangement.

**Build:** Red gradient/vignette → subdued silhouette → warm foreground couple → restrained lyric → own handle. Use a softly looped silhouette pose only if independent animation is available. Otherwise label the result a still-art animation. Keep foreground details sharp; use opacity to separate memory from present.

**Starting settings:** #390000 edges, #7C0909 centre, lyric #E5D8BF. Montserrat 500 as a substitute. Fade-in 0.5–0.8 s, 2–3% slow picture drift, phrase fade 0.12–0.2 s. Move the source's low creator credit into a safer location for @aitricksbysumit; never copy another creator's signature into a new render.

## Motion implementation and audio alignment

- Use one absolute timeline for audio, caption events, image cuts and prop cues. Remotion: convert seconds to integer frames once; use local frames within each Sequence. FFmpeg: construct a complete video timeline without repeatedly trimming transition duration from audio.
- Record cue data as `{start, end, text, style, assetIds, transition}`; validate start < end and that events remain within media duration. A phrase may span a picture cut (R1); a picture may span several phrases (R8).
- Use deterministic motion: `floatY=A*sin(2*pi*t/period + phase)` and seeded petals. Avoid random values generated anew per rendered frame.
- Animate blur on the moving layer only. For a blur settle: `blur=maxBlur*(1-ease(clamp(localTime/entrance)))`; hold zero blur after entrance.
- Handle Indic text with a shaping engine and grapheme-safe reveals. Never reveal individual UTF-16 code units of a conjunct.
- **Treat supplied estimated timestamps as provisional.** Match against actual speech using supported transcription/forced alignment or checked listening. Silence detection can suggest boundaries, but cannot identify dialogue. Do not infer verified sync from waveform correlation, matching duration or embedded captions alone.
- Check beginning, middle and final 20–30 seconds against actual dialogue. Keep continuous source audio when requested. Ensure both video stream and audio stream reach the intended ending; a long audio stream can hide a truncated video in container duration.

## Asset prompting and delivery checks

Prompt a consistent art bible: medium, palette, character clothes/hair/age, camera angle, light, negative space and aspect ratio. Request each new narrative scene separately with no baked-in lyrics. Request transparent props separately for collage/parallax recipes. A flattened generated image cannot supply independent depth motion without masks or additional layers.

Export 1080×1920 only when a portrait reel is requested. The references' native landscape formats are deliberate evidence, not corrupt uploads. Recompose backgrounds/subjects at portrait aspect; do not stretch or automatically add blurred sides. Keep vital content roughly x=80–900, y=300–1450 as a conservative working layout, then preview platform overlays; these are design margins, not a guaranteed permanent Instagram specification.

Before a full render, inspect a settled frame, a dense transition sequence and a representative short motion preview. Compare source/recreation text scale, anchor, line spacing, layer order, blur locality and motion direction. Exact fonts, timings and easing remain approximate until measured or independently verified. Report guides as guides; do not claim a production renderer or exact clone was tested when only inspection tooling was run.
