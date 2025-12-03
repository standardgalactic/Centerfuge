#!/usr/bin/env bash
set -e

BLENDER=${BLENDER:-blender}
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="${ROOT_DIR}/scripts"
HELPERS_DIR="${ROOT_DIR}/helpers"
OUTPUT_DIR="${ROOT_DIR}/output_v3_3"
LOG_DIR="${ROOT_DIR}/logs_v3_3"

mkdir -p "$OUTPUT_DIR" "$LOG_DIR"

echo "[v3.3] ROOT_DIR = $ROOT_DIR"
echo "[v3.3] Using blender: $(which "$BLENDER" || echo "$BLENDER")"

for script in "$SCRIPTS_DIR"/*.py; do
    name=$(basename "$script" .py)
    blend_out="${OUTPUT_DIR}/${name}.blend"
    png_out="${OUTPUT_DIR}/${name}.png"
    log="${LOG_DIR}/${name}.log"

    echo "[v3.3] Running script: $script"
    "$BLENDER" -b             --python "${HELPERS_DIR}/storage_helper_v3_3.py"             --python "${HELPERS_DIR}/run_manager_v3_3.py" --             --script "$script"             --output "$blend_out"             > "$log" 2>&1

    echo "[v3.3] Rendering still for ${name}"
    abs_prefix="$(realpath "${OUTPUT_DIR}")/${name}_"

    "$BLENDER" -b "$blend_out"             -o "$abs_prefix"             -f 1             >> "$log" 2>&1

    if [ -f "${OUTPUT_DIR}/${name}_0001.png" ]; then
        mv "${OUTPUT_DIR}/${name}_0001.png" "$png_out"
    fi

    echo "[v3.3] Done: ${png_out}"
done

echo "[v3.3] All stills rendered."
