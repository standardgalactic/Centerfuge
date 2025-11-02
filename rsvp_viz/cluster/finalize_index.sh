#!/usr/bin/env bash
set -euo pipefail
OUT="${1:-output}"
IDX="$OUT/INDEX.json"
git_rev=$(git rev-parse --short=12 HEAD 2>/dev/null || echo "nogit")
ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo '{ "timestamp": "'$ts'", "git_commit": "'$git_rev'", "runs": [' > "$IDX"
first=1
for MAN in $(find "$OUT" -name MANIFEST.jsonl | sort); do
  [ $first -eq 1 ] || echo ',' >> "$IDX"
  first=0
  SCN=$(basename "$(dirname "$MAN")")
  printf '  { "scene":"%s", "manifest":"%s" }' "$SCN" "${MAN#${PWD}/}" >> "$IDX"
done
echo -e '\n] }' >> "$IDX"
