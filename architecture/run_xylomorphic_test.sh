# morphic_test.sh
# ------------------------------------------------------------
# Generate and render all Xylomorphic Architecture scenes
# using Blender headless. Requires Blender on PATH.
# ============================================================

set -euo pipefail

OUTDIR="out_xylomorphic"
BLENDER="blender"             # change if you have a custom path
ENGINE="CYCLES"               # or BLENDER_EEVEE
SAMPLES=32                    # Cycles samples
RES="400x200"               # Resolution
SCENES="all"                  # or comma-separated subset

echo "[Xylomorphic] Generating and rendering scenes..."

python3 xylomorphic_blender_gen.py \
  --outdir "$OUTDIR" \
  --scenes "$SCENES" \
  --render \
  --blender "$BLENDER" \
  --engine "$ENGINE" \
  --samples "$SAMPLES" \
  --res "$RES"

echo "[Xylomorphic] Done."
echo "Results:"
echo "  Scripts → $OUTDIR/scripts/"
echo "  Blends  → $OUTDIR/blends/"
echo "  Renders → $OUTDIR/renders/"

