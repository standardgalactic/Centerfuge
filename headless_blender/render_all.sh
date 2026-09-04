#!/usr/bin/env bash
# Regenerate every headless_blender scene and then admit the result.
#
# `set -euo pipefail` plus each scene's `--python-exit-code 1` makes a raised
# RuntimeError inside common.py (non-occlusion failure, degenerate-image
# failure) an immediate, loud pipeline failure -- but that alone only proves
# the *generation process* did not crash. The final check_manifest.py call is
# what actually re-verifies, from the written manifest.json and the files on
# disk, that every expected scene produced and recorded a passing result; a
# scene that Blender silently skipped (e.g. a typo removed it from the loop)
# would still leave this script's exit code 0 without that separate check.
set -euo pipefail

output_dir="${1:-output/headless}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$script_dir${PYTHONPATH:+:$PYTHONPATH}"

for scene in centerfuge_cutaway material_sorting_vortex hyperbolation_cognet house_distribution intake_geometry internal_routing maintenance_access; do
    blender -b --python-exit-code 1 -P "$script_dir/$scene.py" -- --output "$output_dir"
done

printf 'Centerfuge renders written to %s\n' "$output_dir"

python3 "$script_dir/check_manifest.py" "$output_dir"
