---
name: creator-templates
description: Four creator-style reel templates learned from @vibha.in.progress's Nov 2026 reels (own code) - RAW vs EDITED compare board, stats proof card with headline and speaker, chat app mock where a /command is typed and the result goes full screen, and a newspaper page with a highlighter sweep. Driven by a plan JSON.
---

# Creator templates

Use when Sumit asks for "raw vs edited", "before/after", "proof / insights wala hook", "chat me command type hoti hai" or "newspaper highlight" scenes, or says "Vibha jaisa template".

## Templates (scene `template` value)
| name | what it is | keys |
|---|---|---|
| `compare` | dark textured board, 2-line title, two rounded video cards with RAW / EDITED pills, typewriter strip | `title[2]`, `labels[2]`, `strip`, clips `raw`, `edited` |
| `proof` | pastel gradient, dark dashboard card with 4 counting stats (one glowing), headline + accent pill, speaker card, one-word side captions | `stats[[label,value]x4]`, `hot`, `headline[2]`, `words[[t0,t1,word]]`, clip `speaker` |
| `chatcmd` | chat app mock: greeting, command typed key by key on a keyboard, sent bubble, "working...", result card grows to full screen | `app`, `greeting`, `command`, `working`, `type_end`, `result_at`, clip `result` |
| `news` | newspaper page, headline, body text; a highlighter sweeps the key sentence, slow push-in | `paper`, `dateline`, `headline`, `body`, `highlight`, `hl_at`, `hl_dur`, clip `photo` |

## Steps
1. Write a plan JSON like `example_plan.json`: `{"audio": "vo.wav", "scenes": [{"template": ..., "dur": seconds, "clips": {...}, ...}]}`. Clips can be videos or stills; paths are relative to the plan.
2. `python3 scripts/creator_templates.py plan.json out.mp4` (fonts folder via `REEL_FONTS`, default the effects fonts).
3. Pull check frames with ffmpeg and look at them before sending.

## Rules
- Use Sumit's real numbers in `proof` (his own Insights screenshots). Never invent stats.
- On-screen text in Roman Hinglish. Voice only, no SFX, unless he asks.
- Keep text inside the Instagram safe zone (nothing above y=250 or below y=1700 on a 1920 frame).
- These are scene builders: mix them with `cutout-story` or `collage-explainer` scenes by concatenating outputs.

## Other latest formats seen on her page (not coded here)
- Paper-collage explainer with numbered cards: already in `skills/collage-explainer`.
- 20 effects in 20 seconds: `skills/effects` + `fx_pack20.py`.
- Education animations (3D map route, ink painting, white ball running a phone UI, 3D landing-page fly-by): to build next.
