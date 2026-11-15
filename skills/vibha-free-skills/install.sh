#!/usr/bin/env bash
# Installs Vibha Ramprakash's two free masterclass skills from her public repo (not copied here: no licence file in that repo).
#   nate-herk-style-edit  -> ~/.claude/skills/nate-herk-style-edit
#   free-sfx-finder       -> ~/.claude/skills/free-sfx-finder
#   captions (7 caption styles, MIT) -> ~/.claude/skills/captions
#   effects (51 video effects, MIT)  -> ~/.claude/skills/effects
set -e
T=$(mktemp -d)
git clone --depth 1 https://github.com/Vibha-Ramprakash/masterclass "$T/mc"
mkdir -p ~/.claude/skills
unzip -o -q "$T/mc/nate-style-edit-skill.zip" -d ~/.claude/skills/
unzip -o -q "$T/mc/free-sfx-finder.zip" -d ~/.claude/skills/
rm -rf ~/.claude/skills/captions ~/.claude/skills/effects
git clone --depth 1 https://github.com/Vibha-Ramprakash/claude-caption-styles ~/.claude/skills/captions
git clone --depth 1 https://github.com/Vibha-Ramprakash/claude-video-effects ~/.claude/skills/effects
(cd ~/.claude/skills/captions && npm install --silent)
rm -rf "$T"
ls ~/.claude/skills/nate-herk-style-edit/SKILL.md ~/.claude/skills/free-sfx-finder/SKILL.md ~/.claude/skills/captions/SKILL.md ~/.claude/skills/effects/SKILL.md && echo READY
