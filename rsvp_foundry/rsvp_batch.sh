#!/usr/bin/env bash
# rsvp_batch.sh — batch headless Blender renderer for the rsvp asset foundry
#
# Usage:
#   ./rsvp_batch.sh [OPTIONS]
#
# Options:
#   -g, --generator NAME      Generator script name: tree | landscape (default: tree)
#   -s, --seeds "0 1 2 ..."   Space-separated seed list, or a range like "0:8"
#   -o, --output DIR          Output directory (default: ./rsvp_output)
#   -b, --blender PATH        Path to Blender executable (default: blender)
#   -r, --render              Also render a PNG preview from each .blend
#   -j, --jobs N              Parallel jobs (default: 1)
#   -p, --params "..."        Extra params forwarded verbatim to the generator script
#   -h, --help                Show this help
#
# Examples:
#   # Generate tree seeds 0-7 with PNG previews, 4 parallel jobs
#   ./rsvp_batch.sh -g tree -s "0:8" -r -j 4
#
#   # Landscape batch with seam and water, seeds 10 20 30
#   ./rsvp_batch.sh -g landscape -s "10 20 30" -r \
#       -p "--seam-axis x --add-water --resolution 128"
#
#   # Custom blender path
#   ./rsvp_batch.sh -g tree -s "0:4" -b /opt/blender-4.1/blender -r

set -euo pipefail

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
GENERATOR="tree"
SEEDS_RAW="0:4"
OUTPUT_DIR="./rsvp_output"
BLENDER="blender"
DO_RENDER=false
JOBS=1
EXTRA_PARAMS=""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        -g|--generator) GENERATOR="$2"; shift 2 ;;
        -s|--seeds)     SEEDS_RAW="$2"; shift 2 ;;
        -o|--output)    OUTPUT_DIR="$2"; shift 2 ;;
        -b|--blender)   BLENDER="$2"; shift 2 ;;
        -r|--render)    DO_RENDER=true; shift ;;
        -j|--jobs)      JOBS="$2"; shift 2 ;;
        -p|--params)    EXTRA_PARAMS="$2"; shift 2 ;;
        -h|--help)
            sed -n '2,/^[^#]/p' "$0" | grep '^#' | sed 's/^# \?//'
            exit 0 ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

# ---------------------------------------------------------------------------
# Resolve generator script
# ---------------------------------------------------------------------------
GENERATOR_SCRIPT="${SCRIPT_DIR}/generate_${GENERATOR}.py"
if [[ ! -f "$GENERATOR_SCRIPT" ]]; then
    echo "[rsvp_batch] ERROR: generator script not found: $GENERATOR_SCRIPT" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Expand seed range "A:B" → "A A+1 ... B-1"
# ---------------------------------------------------------------------------
expand_seeds() {
    local raw="$1"
    if [[ "$raw" =~ ^([0-9]+):([0-9]+)$ ]]; then
        local start="${BASH_REMATCH[1]}"
        local end="${BASH_REMATCH[2]}"
        seq "$start" $((end - 1))
    else
        echo "$raw" | tr ' ' '\n'
    fi
}

mapfile -t SEEDS < <(expand_seeds "$SEEDS_RAW")
echo "[rsvp_batch] generator=${GENERATOR}  seeds=${SEEDS[*]}  jobs=${JOBS}  render=${DO_RENDER}"

mkdir -p "$OUTPUT_DIR"

# ---------------------------------------------------------------------------
# Per-seed worker function
# ---------------------------------------------------------------------------
run_seed() {
    local seed="$1"
    local blend_out="${OUTPUT_DIR}/${GENERATOR}_seed${seed}.blend"
    local png_out="${OUTPUT_DIR}/${GENERATOR}_seed${seed}.png"
    local meta_out="${OUTPUT_DIR}/${GENERATOR}_seed${seed}.json"
    local log_out="${OUTPUT_DIR}/${GENERATOR}_seed${seed}.log"
    local ts
    ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

    echo "[rsvp_batch] seed=${seed} → ${blend_out}"

    # Run the generator
    # shellcheck disable=SC2086
    "$BLENDER" --background --python "$GENERATOR_SCRIPT" -- \
        --output "$blend_out" \
        --seed "$seed" \
        $EXTRA_PARAMS \
        >"$log_out" 2>&1

    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        echo "[rsvp_batch] ERROR seed=${seed} exit=${exit_code}  see ${log_out}" >&2
        write_meta "$meta_out" "$seed" "$ts" "error" "" ""
        return $exit_code
    fi

    # Optional PNG render via render_still.py (auto-framing camera)
    local render_time=""
    if $DO_RENDER; then
        local t0 t1
        t0=$(date +%s%N)
        "$BLENDER" --background "$blend_out" \
            --python "${SCRIPT_DIR}/render_still.py" -- \
            --output "$png_out" \
            --resolution 1024 \
            --samples 32 \
            >>"$log_out" 2>&1
        t1=$(date +%s%N)
        render_time=$(echo "scale=2; ($t1 - $t0) / 1000000000" | bc)
    fi

    write_meta "$meta_out" "$seed" "$ts" "ok" "$png_out" "$render_time"
    echo "[rsvp_batch] done  seed=${seed}"
}

# ---------------------------------------------------------------------------
# Write JSON metadata sidecar
# ---------------------------------------------------------------------------
write_meta() {
    local path="$1" seed="$2" ts="$3" status="$4" png="$5" rtime="$6"

    # Parse EXTRA_PARAMS into a JSON object of key→value strings
    # Handles --key value and --flag (boolean) patterns
    local params_json
    params_json=$(python3 - "$EXTRA_PARAMS" <<'PYEOF'
import sys, json, re

raw = sys.argv[1] if len(sys.argv) > 1 else ""
tokens = raw.split()
d = {}
i = 0
while i < len(tokens):
    tok = tokens[i]
    if tok.startswith("--"):
        key = tok.lstrip("-").replace("-", "_")
        if i + 1 < len(tokens) and not tokens[i+1].startswith("--"):
            d[key] = tokens[i+1]
            i += 2
        else:
            d[key] = True
            i += 1
    else:
        i += 1
print(json.dumps(d))
PYEOF
)

    python3 - "$path" "$seed" "$ts" "$status" "$png" "$rtime" \
              "$GENERATOR" "$GENERATOR_SCRIPT" "$params_json" <<'PYEOF'
import sys, json, os

path, seed, ts, status, png, rtime, gen, script, extra_json = sys.argv[1:]

meta = {
    "schema": "rsvp-meta-v1",
    "generator": gen,
    "script": script,
    "seed": int(seed),
    "timestamp": ts,
    "status": status,
    "outputs": {
        "blend": path.replace(".json", ".blend"),
        "log":   path.replace(".json", ".log"),
        "png":   png if png else None,
    },
    "render_seconds": float(rtime) if rtime else None,
    "params": json.loads(extra_json),
}

with open(path, "w") as f:
    json.dump(meta, f, indent=2)
    f.write("\n")
PYEOF
}

export -f run_seed write_meta
export BLENDER GENERATOR_SCRIPT OUTPUT_DIR DO_RENDER EXTRA_PARAMS GENERATOR

# ---------------------------------------------------------------------------
# Run — parallel or sequential
# ---------------------------------------------------------------------------
if command -v parallel &>/dev/null && [[ "$JOBS" -gt 1 ]]; then
    printf '%s\n' "${SEEDS[@]}" | parallel -j "$JOBS" run_seed {}
else
    if [[ "$JOBS" -gt 1 ]]; then
        echo "[rsvp_batch] WARNING: GNU parallel not found, falling back to sequential"
    fi
    for seed in "${SEEDS[@]}"; do
        run_seed "$seed"
    done
fi

# ---------------------------------------------------------------------------
# Summary manifest
# ---------------------------------------------------------------------------
MANIFEST="${OUTPUT_DIR}/manifest.json"
python3 - "$OUTPUT_DIR" "$GENERATOR" "$MANIFEST" <<'PYEOF'
import sys, json, os, glob

out_dir, gen, manifest_path = sys.argv[1:]
entries = []

for meta_file in sorted(glob.glob(os.path.join(out_dir, f"{gen}_seed*.json"))):
    with open(meta_file) as f:
        try:
            entries.append(json.load(f))
        except json.JSONDecodeError:
            pass

summary = {
    "schema": "rsvp-manifest-v1",
    "generator": gen,
    "count": len(entries),
    "ok": sum(1 for e in entries if e.get("status") == "ok"),
    "error": sum(1 for e in entries if e.get("status") == "error"),
    "entries": entries,
}

with open(manifest_path, "w") as f:
    json.dump(summary, f, indent=2)
    f.write("\n")

print(f"[rsvp_batch] manifest → {manifest_path}  ({summary['ok']}/{summary['count']} ok)")
PYEOF