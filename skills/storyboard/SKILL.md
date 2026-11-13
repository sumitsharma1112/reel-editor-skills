---
name: storyboard
description: Turn a reel edit into a one-page storyboard of numbered beat cards (still, spoken words, on-screen element, two alternative ideas, notes box), then apply only the noted beats on 'done, run my notes'.
---

# Storyboard

Use when Sumit says "storyboard", "show me the edit as cards", or wants to review an edit beat by beat before the final render.

## Build the storyboard
1. Work from the edit's own timeline (plan/script that rendered it), not guesses. If there is only a video, cut it into beats at scene cuts and sentence ends (Whisper word timings, see the earshot skill).
2. One beat = one shot, card, effect or caption change. Number beats in order.
3. For every beat collect:
   - a still frame from the middle of the beat (ffmpeg `-ss` grab, 360 px wide)
   - the exact words spoken in that beat (from the transcript, with start-end time)
   - what is on screen right then: caption text, card, effect name, transition
   - two alternative ideas for that beat, one short plain line each (a different effect, caption style, cut, B-roll or SFX)
4. Make it one page he can open: an HTML artifact (or an HTML file if artifacts are not available) with a grid of cards, stills embedded, and under each card a notes box (textarea) with quick buttons: "keep", "use idea 1", "use idea 2". Add a "Copy all notes" button that copies `#beat: note` lines.
5. Send it and stop. Do not render anything yet.

## "done, run my notes"
1. Read his notes (pasted text or the copied notes block). Beats with no note or "keep" stay exactly as they are.
2. Change only the noted beats. Re-render just those beats as stills and show them side by side old -> new.
3. Wait for his OK, then render the full video once.

## Rules
- Never change an un-noted beat, its timing or its audio.
- Keep his voice and hook as they are.
- On-screen captions in Hinglish Roman unless he asks otherwise; no ALL CAPS words in any TTS text.
