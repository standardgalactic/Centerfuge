#!/usr/bin/env bash
set -euo pipefail

output_dir="${1:-output/headless}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$script_dir${PYTHONPATH:+:$PYTHONPATH}"

for scene in centerfuge_cutaway material_sorting_vortex hyperbolation_cognet house_distribution; do
    blender -b --python-exit-code 1 -P "$script_dir/$scene.py" -- --output "$output_dir"
done

printf 'Centerfuge renders written to %s\n' "$output_dir"
