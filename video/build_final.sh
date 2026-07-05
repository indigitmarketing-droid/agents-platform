#!/usr/bin/env bash
# Build the final easyDent edit end-to-end.
#
#   1. Remotion renders the video treatment + clean original audio.
#   2. tools/mute_scatti.py silences the moments the client flagged as "scatti",
#      applied on the final render (OffthreadVideo adds a ~1-frame audio offset,
#      so muting in the render's own timeline lands sample-accurate).
#
# Usage:  bash build_final.sh
set -euo pipefail
cd "$(dirname "$0")"

# Headless Chromium shipped in this environment (Remotion won't download its own).
HS="${REMOTION_CHROME:-/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell}"

# Muted ranges in the FINAL timeline (seconds). Edit here to adjust.
MUTES=(6.78-7.15 7.39-7.44)

npx remotion render EasyDentEdit out/render_clean.mp4 --browser-executable="$HS"
python3 tools/mute_scatti.py out/render_clean.mp4 out/easyDent_edited.mp4 "${MUTES[@]}"
echo "Done -> out/easyDent_edited.mp4"
