---
name: "remotion-setup"
description: "Install Remotion's official agent skills into the sandbox when the user asks for Remotion, motion graphics, kinetic text or animated titles/outros for his reels."
---

# Remotion setup

Remotion's official Agent Skills (remotion-dev/skills) teach React-based motion graphics: compositions, text animation, timing, fonts, effects, audio, captions, maps and rendering.

## Install (each new session — the sandbox is ephemeral)

```bash
cd /home/claude && npx -y skills add remotion-dev/skills --yes
```

This installs 12 skills into `/home/claude/.agents/skills/` (symlinked for Claude Code): remotion-best-practices (router), remotion-create, remotion-markup, remotion-studio, remotion-render, remotion-captions, remotion-maps, remotion-multimedia, remotion-interactivity, remotion-docs, remotion-saas, remotion-upgrade. After install they appear in the Skill list; start with `remotion-best-practices`.

## When to use which

- Remotion: designed motion graphics — kinetic typography, animated outros/CTAs, title cards, promo text over footage.
- Python/ffmpeg pipeline (existing): real-footage edits — beat-sync cuts, strobe edits, colour grades, rembg cutouts, head-back text.
- Combine: render Remotion overlay/segment, then composite or concat with ffmpeg.

## Notes

- Chromium is preinstalled at /opt/pw-browsers; if Remotion tries to download a browser, point it at that executable.
- CDN access may be blocked; rely on npm packages, not CDN scripts.
- Output 1080x1920, 30fps for reels; keep text inside the Instagram safe zone.
- Remotion is free for individuals and small teams; companies need a licence.