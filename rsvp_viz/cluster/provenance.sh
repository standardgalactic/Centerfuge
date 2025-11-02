#!/usr/bin/env bash
set -euo pipefail
out="$1"; shift
artifact_rel="${out#${PWD}/}"
sha256=$(sha256sum "$out" | awk '{print $1}')
size=$(stat -c%s "$out")
git_rev=$(git rev-parse --short=12 HEAD 2>/dev/null || echo "nogit")
host=$(hostname)
ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat <<JSON
{"timestamp":"${ts}","run_id":"${RUN_ID}","seed":"${SEED}","host":"${host}","git_commit":"${git_rev}","path":"${artifact_rel}","sha256":"${sha256}","bytes":${size}}
JSON
