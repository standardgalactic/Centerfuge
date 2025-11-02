#!/usr/bin/env bash
#SBATCH -J tetra-array
#SBATCH -o logs/%x-%A_%a.out
#SBATCH -e logs/%x-%A_%a.err
#SBATCH -p gpu
#SBATCH --gpus=1
#SBATCH -c 8
#SBATCH --mem=16G
#SBATCH -t 02:00:00
#SBATCH --array=0-9
set -euo pipefail
source "$(dirname "$0")/env.sh"
mapfile -t JOBS < <(ls -1 data/*.yaml | sort)
INPUT="${JOBS[$SLURM_ARRAY_TASK_ID]}"
BASE=$(basename "$INPUT" .yaml)
OUT_SCN="${OUT_DIR}/${BASE}"
mkdir -p "$OUT_SCN"
docker run --rm --gpus all -v "$PWD":/workspace -w /workspace -e SEED -e RUN_ID \
  "$RSVP_IMAGE" ./run_field_pipeline.sh "$INPUT"
MANIFEST="${OUT_SCN}/MANIFEST.jsonl"
> "$MANIFEST"
for f in "${OUT_SCN}"/*; do
  "$(dirname "$0")/provenance.sh" "$f" >> "$MANIFEST"
done
