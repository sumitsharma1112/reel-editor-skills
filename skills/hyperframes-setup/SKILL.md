---
name: "hyperframes-setup"
description: "Install HeyGen's HyperFrames video skills and CLI into the sandbox when the user asks to use HyperFrames, or before building an HTML-to-video composition with it."
---

# HyperFrames setup (sandbox)

HyperFrames (github.com/heygen-com/hyperframes) renders MP4 video from HTML compositions. Its skills ship with many reference files, so install the full set into the session at the start of each session instead of relying on a single SKILL.md.

## Steps

1. Clone the repo and copy its skills into the session skills folder:
```bash
cd /home/claude && [ -d hyperframes ] || git clone --depth 1 https://github.com/heygen-com/hyperframes.git
mkdir -p /root/.claude/skills && cp -r /home/claude/hyperframes/skills/* /root/.claude/skills/
```
2. Point the CLI at the preinstalled headless Chromium (`npx hyperframes browser ensure` download is blocked here):
```bash
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell
export HYPERFRAMES_SKIP_SKILLS=1
echo "export HYPERFRAMES_BROWSER_PATH=$HYPERFRAMES_BROWSER_PATH" >> ~/.bashrc
```
   If that path is missing, find it with `find /opt/pw-browsers -name headless_shell -type f`.
3. Verify: `npx -y hyperframes doctor` should show Chrome and FFmpeg as OK.
4. CDNs (cdn.jsdelivr.net) are blocked by the sandbox proxy. After `npx hyperframes init <name> --non-interactive --resolution portrait`, install GSAP locally (`npm i gsap@3.14.2`) and replace the CDN `<script src>` in every composition HTML with `node_modules/gsap/dist/gsap.min.js`. Do the same for any other CDN library a block uses.
5. Render with `npx hyperframes render -o out.mp4`. Rendering uses software screenshot capture here, so it is slower than on a desktop.

## Then

Load the `hyperframes` skill (the router) and follow it for the actual video work. For the user's Instagram reels use portrait 1080x1920 (or 1080x1350 for carousels), Roman Hinglish text, readable not-too-fast text, and keep any SFX library the user provides in ./sfx.

Optional extras not installed by default: whisper-cpp (transcription), kokoro-onnx (local TTS), MusicGen (local music).