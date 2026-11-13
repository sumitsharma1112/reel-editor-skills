#!/usr/bin/env bash
# Installs Vibha Ramprakash's two free masterclass skills from her public repo (not copied here: no licence file in that repo).
#   nate-herk-style-edit  -> ~/.claude/skills/nate-herk-style-edit
#   free-sfx-finder       -> ~/.claude/skills/free-sfx-finder
set -e
T=$(mktemp -d)
git clone --depth 1 https://github.com/Vibha-Ramprakash/masterclass "$T/mc"
mkdir -p ~/.claude/skills
unzip -o -q "$T/mc/nate-style-edit-skill.zip" -d ~/.claude/skills/
unzip -o -q "$T/mc/free-sfx-finder.zip" -d ~/.claude/skills/
rm -rf "$T"
ls ~/.claude/skills/nate-herk-style-edit/SKILL.md ~/.claude/skills/free-sfx-finder/SKILL.md && echo READY
