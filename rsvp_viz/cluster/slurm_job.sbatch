#!/usr/bin/env bash
#SBATCH -J tetraorthodrome
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err
#SBATCH -p gpu
#SBATCH --gpus=1
#SBATCH -c 8
#SBATCH --mem=16G
#SBATCH -t 01:00:00
set -euo pipefail
source "$(dirname "$0")/env.sh"
INPUT="${INPUT:-data/lamphrodyne.yaml}"
BASE=$(basename "$INPUT" .yaml)
OUT_SCN="${OUT_DIR}/${BASE}"
mkdir -p "$OUT_SCN"
docker run --rm --gpus all -v "$PWD":/workspace -w /workspace -e SEED -e RUN_ID \
  "$RSVP_IMAGE" ./run_field_pipeline.sh "$INPUT"
MANIFEST="${OUT_SCN}/MANIFEST.jsonl"
for f in "${OUT_SCN}"/*; do
  "$(dirname "$0")/provenance.sh" "$f" >> "$MANIFEST"
done
