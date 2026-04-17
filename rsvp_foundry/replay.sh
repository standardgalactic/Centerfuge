#!/usr/bin/env bash
# replay.sh — recompile a specific generator+seed by identity.
#
# Every asset is reproducible. This script is the proof of that.
#
# Usage:
#   ./replay.sh GENERATOR SEED [--render] [--output DIR] [--blender PATH]
#
# Examples:
#   ./replay.sh tree 42
#   ./replay.sh landscape 7 --render
#   ./replay.sh auto_003 0 --render --output /tmp/replay

set -euo pipefail

GENERATOR="${1:?Usage: replay.sh GENERATOR SEED [--render] [--output DIR]}"
SEED="${2:?Usage: replay.sh GENERATOR SEED [--render] [--output DIR]}"
shift 2

DO_RENDER=false
OUTPUT_DIR="./rsvp_output/replay"
BLENDER="blender"
EXTRA_PARAMS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --render)       DO_RENDER=true; shift ;;
        --output)       OUTPUT_DIR="$2"; shift 2 ;;
        --blender)      BLENDER="$2"; shift 2 ;;
        -p|--params)    EXTRA_PARAMS="$2"; shift 2 ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$OUTPUT_DIR"

BLEND="${OUTPUT_DIR}/${GENERATOR}_seed${SEED}.blend"
PNG="${OUTPUT_DIR}/${GENERATOR}_seed${SEED}.png"
GENERATOR_SCRIPT="${SCRIPT_DIR}/generate_${GENERATOR}.py"

if [[ ! -f "$GENERATOR_SCRIPT" ]]; then
    echo "[replay] ERROR: generator not found: $GENERATOR_SCRIPT" >&2
    exit 1
fi

echo "[replay] ${GENERATOR} seed=${SEED} → ${BLEND}"

# shellcheck disable=SC2086
"$BLENDER" --background --python "$GENERATOR_SCRIPT" -- \
    --output "$BLEND" \
    --seed "$SEED" \
    $EXTRA_PARAMS

if $DO_RENDER; then
    echo "[replay] rendering → ${PNG}"
    "$BLENDER" --background "$BLEND" \
        --python "${SCRIPT_DIR}/render_still.py" -- \
        --output "$PNG" \
        --resolution 1024 \
        --samples 64
    echo "[replay] done → ${PNG}"
else
    echo "[replay] done → ${BLEND}"
fi
