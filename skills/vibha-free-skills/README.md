# Vibha's free masterclass skills

Two free starter skills by [@vibha.in.progress](https://instagram.com/vibha.in.progress), from her guide at https://vibha-ramprakash.github.io/masterclass/ (repo: https://github.com/Vibha-Ramprakash/masterclass).

- **nate-herk-style-edit**: raw talking-head -> fast captioned 9:16 reel (cover title, face punch-ins, number cards, split screens, ALL-CAPS captions, soft SFX, -14 LUFS).
- **free-sfx-finder**: finds CC0 sound effects on Openverse and places them on every cut.

Plus her MIT-licensed public skills:
- **captions**: 7 caption styles (`/captions pop-sticker`, editorial-highlight, paper-plane, smoke-exit, explosive-breakup, rolodex-flip, retro-typer). Needs ffmpeg, Node 18+, Chrome; tested on the Einstein reel.
- **effects**: 51 starter video effects.

Her paid plugin "Hop Studio" (220+ effects, 47 caption styles) is sold on vibha.is and is not in the Claude plugin directory, so it can't be installed from here.

The masterclass skills are not copied into this repo (her masterclass repo has no licence file). Run `bash install.sh` to fetch them straight from her repo into `~/.claude/skills/`.
In the Claude app, `free-sfx-finder` is already saved as a personal skill (script inlined in its SKILL.md).
Note: the cloud workspace blocks api.openverse.org; run the finder on your own computer.
