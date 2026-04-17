#!/usr/bin/env bash
# render_from_generator.sh — generate a .blend then render a still in one step.
#
# Usage:
#   ./render_from_generator.sh GENERATOR SEED [--output DIR] [--blender PATH]
#                               [--resolution PX] [--samples N]
#
# Examples:
#   ./render_from_generator.sh tree 42
#   ./render_from_generator.sh landscape 7 --resolution 2048

set -euo pipefail

GENERATOR="${1:?Usage: render_from_generator.sh GENERATOR SEED}"
SEED="${2:?Usage: render_from_generator.sh GENERATOR SEED}"
shift 2

OUTPUT_DIR="./rsvp_output/stills"
BLENDER="blender"
RESOLUTION=1024
SAMPLES=64
EXTRA_PARAMS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --output)     OUTPUT_DIR="$2"; shift 2 ;;
        --blender)    BLENDER="$2"; shift 2 ;;
        --resolution) RESOLUTION="$2"; shift 2 ;;
        --samples)    SAMPLES="$2"; shift 2 ;;
        -p|--params)  EXTRA_PARAMS="$2"; shift 2 ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$OUTPUT_DIR"

TMP_BLEND="/tmp/rsvp_${GENERATOR}_${SEED}.blend"
PNG="${OUTPUT_DIR}/${GENERATOR}_seed${SEED}.png"

echo "[render_from_generator] ${GENERATOR} seed=${SEED}"

# Step 1: generate .blend
# shellcheck disable=SC2086
"$BLENDER" --background \
    --python "${SCRIPT_DIR}/generate_${GENERATOR}.py" -- \
    --output "$TMP_BLEND" \
    --seed "$SEED" \
    $EXTRA_PARAMS

# Step 2: render still using universal renderer
"$BLENDER" --background "$TMP_BLEND" \
    --python "${SCRIPT_DIR}/render_still.py" -- \
    --output "$PNG" \
    --resolution "$RESOLUTION" \
    --samples "$SAMPLES"

echo "[render_from_generator] → ${PNG}"
