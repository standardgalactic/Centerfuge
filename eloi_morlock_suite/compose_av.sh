
#!/usr/bin/env bash
set -euo pipefail
ROOTDIR="${1:-output}"
for d in "$ROOTDIR"/scene_*; do
  [ -d "$d" ] || continue
  v="$d/visuals.mp4"
  a=$(ls "$d"/*.wav 2>/dev/null || true)
  [ -f "$v" ] && [ -f "$a" ] && {
    o="$d/composite.mp4"
    ffmpeg -hide_banner -loglevel error -i "$v" -i "$a" -c:v copy -c:a aac -b:a 192k -shortest "$o"
  }
done
