#!/usr/bin/env bash
# Run all v3 simulation scripts through Blender headless.

BLENDER="/usr/bin/blender"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="${ROOT_DIR}/scripts"
HELPERS_DIR="${ROOT_DIR}/helpers"
OUTPUT_DIR="${ROOT_DIR}/output_v3"
LOG_DIR="${ROOT_DIR}/logs_v3"

mkdir -p "$OUTPUT_DIR" "$LOG_DIR"

for script in "$SCRIPTS_DIR"/*.py; do
    name=$(basename "$script" .py)
    out_blend="${OUTPUT_DIR}/${name}.blend"
    log_file="${LOG_DIR}/${name}.log"

    echo "[v3] Running ${name}..."
    "$BLENDER" -b             --python "${HELPERS_DIR}/storage_helper_v3.py"             --python "${HELPERS_DIR}/run_manager_v3.py" --             --script "$script"             --output "$out_blend"             > "$log_file" 2>&1

    echo "[v3] Completed ${name}, blend saved to ${out_blend}"
done
