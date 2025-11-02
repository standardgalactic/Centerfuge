#!/usr/bin/env bash
set -euo pipefail
YAML_FILE=${1:? "Usage: ./run_field_pipeline.sh data/lamphrodyne.yaml"}
BASENAME=$(basename "$YAML_FILE" .yaml)
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="${ROOT_DIR}/output/${BASENAME}"
SCRIPTS="${ROOT_DIR}/scripts"
DOCS="${ROOT_DIR}/docs"
mkdir -p "$OUT" "$DOCS"

echo "[1/4] Build model with Geometry Nodes / VDB (if enabled)"
blender -b -E CYCLES -P "${SCRIPTS}/generate_field_model_nodes.py" -- \
  --config "$YAML_FILE" --out "$OUT/${BASENAME}.blend"

echo "[2/4] Render animation (Cycles, MP4)"
blender -b "$OUT/${BASENAME}.blend" -E CYCLES -P "${SCRIPTS}/render_field_animation.py" -- \
  --config "$YAML_FILE" --out "$OUT"

echo "[3/4] Snapshot (PNG)"
blender -b "$OUT/${BASENAME}.blend" -E CYCLES -P "${SCRIPTS}/export_snapshot.py" -- \
  --out "$OUT/${BASENAME}.png"

echo "[4/4] Minimal Markdown doc"
cat > "${DOCS}/${BASENAME}.md" <<DOC
# ${BASENAME}
Generated from \`${YAML_FILE}\`.

Artifacts:
- Blend: \`${OUT}/${BASENAME}.blend\`
- Animation: \`${OUT}/animation.mp4\`
- Snapshot: \`${OUT}/${BASENAME}.png\`
DOC

echo "Done -> ${OUT}"
