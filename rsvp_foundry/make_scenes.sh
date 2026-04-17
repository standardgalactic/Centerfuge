#!/usr/bin/env bash
# make_scenes.sh — batch scene composition across a seed range.
#
# Usage:
#   ./make_scenes.sh [--seeds RANGE] [--output DIR] [--render] [--blender PATH]
#
# Examples:
#   ./make_scenes.sh --seeds "0:6" --render
#   ./make_scenes.sh --seeds "0 3 7 12" --output ./scenes

set -euo pipefail

SEEDS="0:4"
OUTPUT_DIR="./rsvp_output/scenes"
DO_RENDER=false
BLENDER="blender"
TREE_COUNT=10
RESOLUTION=64
EXTRA_PARAMS=""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --seeds)       SEEDS="$2"; shift 2 ;;
        --output)      OUTPUT_DIR="$2"; shift 2 ;;
        --render)      DO_RENDER=true; shift ;;
        --blender)     BLENDER="$2"; shift 2 ;;
        --tree-count)  TREE_COUNT="$2"; shift 2 ;;
        --resolution)  RESOLUTION="$2"; shift 2 ;;
        -p|--params)   EXTRA_PARAMS="$2"; shift 2 ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

mkdir -p "$OUTPUT_DIR"

# Expand seed range
expand_seeds() {
    if [[ "$1" =~ ^([0-9]+):([0-9]+)$ ]]; then
        seq "${BASH_REMATCH[1]}" $(( BASH_REMATCH[2] - 1 ))
    else
        echo "$1" | tr ' ' '\n'
    fi
}

echo "[make_scenes] seeds=${SEEDS}  render=${DO_RENDER}"

while IFS= read -r seed; do
    BLEND="${OUTPUT_DIR}/scene_seed${seed}.blend"
    PNG="${OUTPUT_DIR}/scene_seed${seed}.png"

    echo "[make_scenes] seed=${seed} → ${BLEND}"

    # shellcheck disable=SC2086
    "$BLENDER" --background \
        --python "${SCRIPT_DIR}/generate_scene.py" -- \
        --output "$BLEND" \
        --seed "$seed" \
        --tree-count "$TREE_COUNT" \
        --resolution "$RESOLUTION" \
        $EXTRA_PARAMS

    if $DO_RENDER; then
        "$BLENDER" --background "$BLEND" \
            --python "${SCRIPT_DIR}/render_still.py" -- \
            --output "$PNG" \
            --resolution 1024 \
            --samples 64
        echo "[make_scenes] rendered → ${PNG}"
    fi

done < <(expand_seeds "$SEEDS")

echo "[make_scenes] done → ${OUTPUT_DIR}"
