#!/usr/bin/env bash
# Wall-text, liquid-glass and text-behind-head styles from other creators' public GitHub repos.
# Cloned from source (not copied here) so each keeps its own licence.
set -e
S=~/.claude/skills; mkdir -p $S; T=$(mktemp -d)
get(){ rm -rf "$S/$2"; GIT_LFS_SKIP_SMUDGE=1 git clone -q --depth 1 "https://github.com/$1" "$S/$2"; rm -rf "$S/$2/.git"; echo "ok $2"; }
get mjcamelobrito-ux/claude-text-effects text-effects-40      # 40 HyperFrames text styles incl. 2 WALL styles
get rogelioserrano11/effectswithclaude    effectswithclaude    # MIT, 18 fx: glass-widgets, giant word behind, kinetic captions
get aaksa/facecammaxxing                  facecammaxxing       # MIT, Remotion+GSAP+Three.js over RobustVideoMatting cut-out
get adamgodigital/claude-reel-effects     reel-effects-55      # MIT, 55 fx + 4 caption styles, liquid-glass-graph
get AlanECE/liquid-glass-motion-intro     liquid-glass-motion-intro  # MIT, liquid-glass intro + kinetic subtitles
GIT_LFS_SKIP_SMUDGE=1 git clone -q --depth 1 https://github.com/hoodini/ai-agents-skills "$T/h" && rm -rf "$S/yuv-viral-video" && cp -r "$T/h/skills/yuv-viral-video" "$S/" && echo "ok yuv-viral-video"
rm -rf "$T"; echo READY
