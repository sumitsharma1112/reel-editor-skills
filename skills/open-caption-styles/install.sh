#!/usr/bin/env bash
# Free, open-source caption styles from other creators (no Vibha paywall).
# 1) HeyGen HyperFrames caption blocks (Apache-2.0): 18 styles incl. text BEHIND the speaker.
# 2) HyperFrames agent skills (captions doctrine, text-behind-speaker rules).
# 3) remotion-captioneer (MIT, 14 styles) + remotion-subtitle (MIT, 14 templates) for Remotion projects.
set -e
DIR=${1:-$HOME/caption-styles}
mkdir -p "$DIR"
npx -y hyperframes@latest add caption-style mk-callout-highlight inline-highlight --dir "$DIR" --no-clipboard
npx -y skills add heygen-com/hyperframes -y || echo "skills CLI not available; HyperFrames skills skipped"
echo "Caption blocks are in $DIR/compositions/components/"
echo "For Remotion projects:  npm i remotion-captioneer remotion-subtitle"
