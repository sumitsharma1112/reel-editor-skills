# Story-first Hindi moral reels

Use for everyday allegories followed by a social or festival message. Preserve the user's approved wording and ending.

## Story and delivery

- Build hook → ordinary character's problem → repeated action → revealing dialogue → short connection to the topic → callback. Keep the allegory's characters separate from the festival protagonist. Use the dishonest grocer/inspection or faulty toy mold as structural examples; write a different story for a new subject.
- Show actions, props and reactions before the lesson. Avoid a lecture illustrated with generic pictures. Do not promise virality.
- Keep food choices nonjudgmental when the message concerns conduct. Do not imply that screens, loneliness or one parent's behavior inevitably cause substance addiction.
- Supply clean Hindi narration and separate delivery instructions for TTS. Do not claim arbitrary `<emotion>` tags are supported by a provider. Keep production cues out of spoken text unless that specific TTS input format supports them.

## Recording completeness: before rendering

1. Read the entire approved script and listen to the entire supplied recording, especially its final 20–30 seconds. Match every paragraph, dialogue turn and the closing sentence. Duration and silence detection alone cannot establish completeness or word timing.
2. If a take ends mid-sentence, tell the user exactly which ending is missing and request the missing audio. Continue independent artwork/timing work. Do not silently substitute a shortened on-screen ending or call the reel complete. Make a provisional text-only ending only if the user authorizes it.
3. For an added ending, cut the unfinished first take at a quiet boundary before its partial sentence; append the complete new sentence once. Preserve speech speed and intentional pauses, listen across the join, then align each new caption to actual speech.
4. Retain the approved full script in the project. Use ASR to assist alignment, not to rewrite it: Hindi ASR may return Urdu script or wrong proper nouns. Forced word timestamps and silence boundaries still need listening checks.

## Reference-specific layout

Measure the actual supplied video, not the Instagram profile or a thumbnail. In the studied 360×640 reference, square artwork occupied y=140–500 with black bands. At 1080×1920 this maps to 1080×1080 art at x=0,y=420, with 420-pixel bands above and below. This is a reference-specific layout, not a universal Reel requirement.

- Start with headline near (505,304), two lines in white/yellow, about 74–86 px. Set Hindi phrase captions near (505,1600), about 61 px, white with a yellow second line. Set a small handle near (505,1462) inside the artwork.
- These observed placements can overlap Instagram UI/feed crops. When the user explicitly requests this exact reference layout, retain it and inspect a phone preview; otherwise move critical words into the safe zone. Adjust type to measured glyph bounds rather than shrinking all text blindly.
- Use one or two caption lines, strong contrast and phrase holds that fit speech. Render Devanagari with libass or Pillow RAQM and a verified Indic font. Use the bundled Noto Sans Devanagari Bold default, verified with libass. A font filename or fontconfig listing alone does not establish usable Hindi rendering: inspect a rendered frame for missing-glyph boxes.

## Artwork and editing

Generate each distinct scene separately with Imagegen. Use square art without baked-in text, consistent cast/clothing/props, warm illustrated outlines and varied wide shots, reactions, hands and object close-ups. Inspect every result. Reference prompts must specify whether to preserve only the visual style or also the cast/setting; explicitly exclude prior characters when moving to a new everyday scene. Do not let an old workshop appear in a new home scene accidentally.

Use clean cuts and modest 3–9% camera pushes/pulls; hold the revelation and closing callback. Camera movement over stills is not character animation or lip sync. Put the strongest visual problem in the opening. Keep music quiet under narration and lower it under the reveal; never add an unrelated reference soundtrack.

## Reusable renderer

Run `python scripts/story_reel.py story.json --out reel.mp4`, or `--validate-only` before rendering. Requires Python 3.10+, FFmpeg/ffprobe with libass, and the bundled font. Resolve all media paths relative to the JSON file. Provide a ready narration/mix; the renderer normalizes it and adds no music. Join approved narration takes before passing `audio`.

```json
{
  "duration": 4.0,
  "audio": "narration.wav",
  "approved_script": "approved.txt",
  "title": ["पहली पंक्ति…", "दूसरी पंक्ति!"],
  "handle": "@aitricksbysumit",
  "scenes": [
    {"start": 0, "end": 2, "image": "01.png", "motion": "pull"},
    {"start": 2, "end": 4, "image": "02.png", "motion": "push"}
  ],
  "captions": [
    {"start": 0.1, "end": 1.9, "text": "पहला वाक्य।"},
    {"start": 2.1, "end": 3.9, "text": "आखिरी|पूरा वाक्य।"}
  ]
}
```

Require `approved.txt` to contain exactly the spoken script; caption text must match it after ignoring punctuation/spacing, including the ending. Use `|` for a caption line break. Optional `font` (path) and `font_family` must refer to the same font; optional `max_end_hold` defaults to 1 second. Scene coverage must be contiguous, output duration must lie on the 30 fps grid, and narration must fit without truncation. These checks detect manifest errors; they do not prove the recording speaks the script or that text fits visually.

## Export and QA

- Encode 1080×1920, H.264 yuv420p, 30 fps, AAC stereo 48 kHz/192k, faststart. Use readable gain with no clipping; about −14 LUFS and −1.7 dBTP is a starting target. Inspect narration/music balance by listening.
- Compute shot frame counts as `round(end*fps)-round(start*fps)` to avoid cumulative drift. Use numeric filter durations such as `d=0.3`, not `d=.3` on FFmpeg versions that reject the latter.
- Treat FFmpeg exit code alone as insufficient. Probe every intermediate for its expected video frames, and verify final video dimensions, duration, audio stream and total frames. A concat job can otherwise leave a short video under full-length audio.
- Decode the whole export with `ffmpeg -v error -xerror -i reel.mp4 -f null -`. Render into temporary files and replace a previous final only after all checks pass. The reusable renderer applies these structural checks; inspect audio loudness separately.
- Inspect a contact sheet sampled across every shot, not just the first 30 frames. Read every closing caption at full size; check faces, missing props, clipping, continuity, UI placement and the complete last spoken sentence. Listen to the beginning, every join and the ending.
- Package only useful editable inputs: approved script, scene prompts, art, timing JSON, captions, font/license, source audio and renderer. Do not commit user art/audio/video or downloaded references to this repository. Keep renderer examples generic.
