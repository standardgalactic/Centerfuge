#!/usr/bin/env bash
set -u

BLENDER_BIN="${BLENDER_BIN:-blender}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export ADMISSIBILITY_ROOT="$ROOT_DIR"
mkdir -p "${ADMISSIBILITY_OUTPUT:-$ROOT_DIR/output}"

scenes=(
  pop_refuse_bind_collapse record_admit_commit distinction_holonomy sheaf_gluing
  vertical_horizontal_repair rsvp_field persistence_cone_tidal_torque
  tartan_weave data_center_substrate fusion_reactor_comparison
  molecular_manufacturing aniara_whale_cutaway city_of_brutes_triad
  sproll_manipulatives fluid_flashcards render_ledger
)

engine_failures=0
for scene in "${scenes[@]}"; do
  echo "[render] $scene"
  if ! "$BLENDER_BIN" --background --python "$ROOT_DIR/scenes/$scene.py"; then
    echo "[engine-error] $scene" >&2
    engine_failures=$((engine_failures + 1))
  fi
done

if (( engine_failures > 0 )); then
  echo "$engine_failures scene process(es) crashed" >&2
  exit 2
fi

python3 "$ROOT_DIR/tools/verify_suite.py"

