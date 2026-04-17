#!/usr/bin/env bash
# rsvp_expand.sh — meta-layer orchestrator
#
# Generates generators, then runs the batch pipeline on them.
# This is the self-expansion loop: field algebra → generators → worlds.
#
# Usage:
#   ./rsvp_expand.sh [OPTIONS]
#
# Options:
#   -c, --count N         Number of auto generators to compose (default: 6)
#   -s, --master-seed N   Master composition seed (default: 0)
#   -o, --output DIR      Root output directory (default: ./rsvp_expand_output)
#   -b, --blender PATH    Blender executable (default: blender)
#   -r, --render          Render PNG previews
#   -j, --jobs N          Parallel batch jobs (default: 1)
#   --seeds RANGE         Seed range for each generator, e.g. "0:4" (default: 0:3)
#   --dry-run             Compose and print plans without running Blender
#   -h, --help            Show this help

set -euo pipefail

COUNT=6
MASTER_SEED=0
OUTPUT_DIR="./rsvp_expand_output"
BLENDER="blender"
DO_RENDER=false
JOBS=1
SEEDS="0:3"
DRY_RUN=false

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

while [[ $# -gt 0 ]]; do
    case "$1" in
        -c|--count)       COUNT="$2"; shift 2 ;;
        -s|--master-seed) MASTER_SEED="$2"; shift 2 ;;
        -o|--output)      OUTPUT_DIR="$2"; shift 2 ;;
        -b|--blender)     BLENDER="$2"; shift 2 ;;
        -r|--render)      DO_RENDER=true; shift ;;
        -j|--jobs)        JOBS="$2"; shift 2 ;;
        --seeds)          SEEDS="$2"; shift 2 ;;
        --dry-run)        DRY_RUN=true; shift ;;
        -h|--help)
            sed -n '2,/^[^#]/p' "$0" | grep '^#' | sed 's/^# \?//'
            exit 0 ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

GEN_DIR="${OUTPUT_DIR}/generators"
BATCH_DIR="${OUTPUT_DIR}/assets"

mkdir -p "$GEN_DIR" "$BATCH_DIR"

echo "[rsvp_expand] count=${COUNT}  master_seed=${MASTER_SEED}  render=${DO_RENDER}"
echo "[rsvp_expand] generators → ${GEN_DIR}"
echo "[rsvp_expand] assets     → ${BATCH_DIR}"

# ---------------------------------------------------------------------------
# Step 1: Compose generators
# ---------------------------------------------------------------------------
echo ""
echo "=== STEP 1: composing ${COUNT} generators ==="

python3 "${SCRIPT_DIR}/compose_generator.py" \
    --count "$COUNT" \
    --seed  "$MASTER_SEED" \
    --output-dir "$GEN_DIR" \
    $( $DRY_RUN && echo "--dry-run" || echo "" )

if $DRY_RUN; then
    echo "[rsvp_expand] dry-run: stopping after composition plan"
    exit 0
fi

# ---------------------------------------------------------------------------
# Step 2: Batch render each composed generator
# ---------------------------------------------------------------------------
echo ""
echo "=== STEP 2: batch rendering ==="

RENDER_FLAG=""
$DO_RENDER && RENDER_FLAG="-r"

for gen_script in "${GEN_DIR}"/generate_auto_*.py; do
    gen_name="$(basename "$gen_script" .py)"
    gen_name="${gen_name#generate_}"   # strip "generate_" prefix
    gen_out="${BATCH_DIR}/${gen_name}"
    mkdir -p "$gen_out"

    echo "[rsvp_expand] running batch: generator=${gen_name}  seeds=${SEEDS}"

    # Temporarily copy generator to SCRIPT_DIR so rsvp package is on path
    tmp_script="${SCRIPT_DIR}/generate_${gen_name}.py"
    cp "$gen_script" "$tmp_script"

    bash "${SCRIPT_DIR}/rsvp_batch.sh" \
        -g "$gen_name" \
        -s "$SEEDS" \
        -o "$gen_out" \
        -b "$BLENDER" \
        -j "$JOBS" \
        $RENDER_FLAG || true   # don't abort batch on single generator failure

    rm -f "$tmp_script"
done

# ---------------------------------------------------------------------------
# Step 3: Aggregate manifests
# ---------------------------------------------------------------------------
echo ""
echo "=== STEP 3: aggregating manifests ==="

python3 - "$BATCH_DIR" "$OUTPUT_DIR/expand_manifest.json" <<'PYEOF'
import sys, json, glob, os

batch_dir, out_path = sys.argv[1:]
all_entries = []

for manifest in sorted(glob.glob(os.path.join(batch_dir, "**", "manifest.json"), recursive=True)):
    with open(manifest) as f:
        try:
            m = json.load(f)
            for e in m.get("entries", []):
                e["_generator"] = m.get("generator", "unknown")
                e["_manifest"] = manifest
                all_entries.append(e)
        except json.JSONDecodeError:
            pass

ok = sum(1 for e in all_entries if e.get("status") == "ok")
summary = {
    "schema": "rsvp-expand-manifest-v1",
    "total": len(all_entries),
    "ok": ok,
    "error": len(all_entries) - ok,
    "entries": all_entries,
}
with open(out_path, "w") as f:
    json.dump(summary, f, indent=2)
    f.write("\n")

print(f"[rsvp_expand] expand manifest → {out_path}  ({ok}/{len(all_entries)} ok)")
PYEOF

echo ""
echo "[rsvp_expand] done. Output in ${OUTPUT_DIR}"
echo "  generators:      ${GEN_DIR}"
echo "  assets:          ${BATCH_DIR}"
echo "  expand manifest: ${OUTPUT_DIR}/expand_manifest.json"
echo ""
echo "Next step — bias toward interesting regions:"
echo "  python manifest_to_generators.py ${OUTPUT_DIR}/expand_manifest.json \\"
echo "      --metric slow --count 6 --output-dir ${OUTPUT_DIR}/next_batch --run"
