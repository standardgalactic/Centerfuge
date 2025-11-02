
#!/usr/bin/env bash
set -euo pipefail
OUT="output_stills_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$OUT"
pushd "$(dirname "$0")" >/dev/null
cd scripts/eloi_morlock
SCRIPTS=(
  scene_01_eloi_day.py
  scene_02_ruins_twilight.py
  scene_03_morlock_caves.py
  scene_04_forest_scatter.py
  scene_05_ridge_overlook.py
  scene_06_valley_to_cave_threshold.py
  scene_07_relics_wireframe.py
  scene_08_biolume_grotto_closeup.py
  scene_09_split_montage_cards.py
  scene_10_manifest_card.py
)
for s in "${SCRIPTS[@]}"; do
  base="${s%.py}"
  echo "[RUN] $s"
  blender -b -P "$s" -- --out "../../$OUT/${base}.png" --width 1920 --height 1080 --seed 42
done
popd >/dev/null
echo "[OK] Stills saved in $OUT"
