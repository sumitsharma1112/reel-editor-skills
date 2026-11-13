---
name: earshot
description: Trim a too-long talking video under a target length: transcribe word for word, propose cuts (repeats, retakes, filler first), wait for OK, then save the trimmed video next to the original.
---

# Earshot: transcript-first trim

Use when Sumit says a video is too long, says "Earshot", or asks to cut a talking video down to a length (default: under 35 seconds).

## Rules
- Keep the hook (first sentence / first ~3 s of speech) untouched. Keep his own voice: no re-recording, no TTS, no speed-up.
- Cut order: repeats, retakes, filler (umm, matlab, toh, basically, long pauses), then the weakest whole sentence only if still too long.
- Never cut mid-word; cut in the silences between words. Render nothing until he says OK.

## Steps
1. Copy the video to the working folder (never edit the original).
2. `python3 -I scripts/whisper_words.py video.mp4 words.json model hi` (see the script header for building the model from npm when Hugging Face is blocked).
3. Show the transcript as numbered lines with start-end times (fix obvious mis-hearings in the text, keep Whisper's times).
4. Propose cuts as a table: # | time | exact words cut | why. End with original length -> new length.
5. Wait for OK; apply his changes to the list.
6. Render keep-segments with ffmpeg trim/atrim + concat, 30 ms audio fades at each joint, libx264 crf 18, AAC 192k, same resolution/fps.
7. Check duration, look at a frame after each joint, re-transcribe and compare with the kept text.
8. Save `<name>_trimmed.mp4` next to the original (write back to his computer if it came from there).
