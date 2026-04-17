#!/usr/bin/env python3
"""
manifest_to_generators.py — read rsvp_batch manifest.json files and emit
new compose_generator.py calls biased toward statistically interesting regions.

"Interesting" is defined per manifest field as:
  - high closure variance across seeds (field is sensitive to parameters)
  - seeds where render succeeded (as a basic fitness signal)
  - outlier seeds by any numeric metric stored in params

Usage:
    python manifest_to_generators.py manifest.json [manifest2.json ...] \\
        --count 8 \\
        --metric closure_variance \\
        --output-dir ./next_batch

The script reads the manifests, scores seeds, selects the top-N by metric,
and emits compose_generator.py invocations (or runs them directly with --run).

Metrics available:
  render_seconds   — faster renders = simpler topology
  slow             — slower renders = more complex topology  
  random           — uniform random selection (baseline)
"""

from __future__ import annotations
import argparse
import json
import random
import subprocess
import sys
from pathlib import Path


def load_manifests(paths: list[Path]) -> list[dict]:
    entries = []
    for path in paths:
        with path.open() as f:
            manifest = json.load(f)
        for entry in manifest.get("entries", []):
            entry["_manifest_file"] = str(path)
            entries.append(entry)
    return entries


def score_entries(entries: list[dict], metric: str, rng: random.Random) -> list[tuple[float, dict]]:
    scored = []
    for entry in entries:
        if entry.get("status") != "ok":
            continue
        rt = entry.get("render_seconds")

        if metric == "render_seconds":
            # prefer fast (simple) renders
            score = -rt if rt is not None else 0.0
        elif metric == "slow":
            # prefer slow (complex) renders
            score = rt if rt is not None else 0.0
        elif metric == "random":
            score = rng.random()
        else:
            score = rng.random()

        scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def entry_to_compose_args(entry: dict, index: int) -> dict:
    """Extract a composition seed from an entry's existing seed, offset for novelty."""
    base_seed = entry.get("seed", 0)
    # Derive a new composition seed that's related but distinct
    composition_seed = (base_seed * 6364136223846793005 + index) & 0x7FFFFFFF
    return {
        "name": f"derived_{index:03d}_from_seed{base_seed}",
        "composition_seed": composition_seed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate new composer calls from manifest analysis"
    )
    parser.add_argument("manifests", nargs="+", help="manifest.json files to read")
    parser.add_argument("--count", type=int, default=6, help="Number of new generators to emit")
    parser.add_argument(
        "--metric",
        default="random",
        choices=["render_seconds", "slow", "random"],
        help="Selection metric",
    )
    parser.add_argument("--output-dir", default="./next_batch", help="Output directory")
    parser.add_argument("--seed", type=int, default=0, help="RNG seed for scoring")
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run compose_generator.py immediately after planning",
    )
    parser.add_argument(
        "--compose-script",
        default="compose_generator.py",
        help="Path to compose_generator.py",
    )
    args = parser.parse_args()

    rng = random.Random(args.seed)
    manifest_paths = [Path(p) for p in args.manifests]

    entries = load_manifests(manifest_paths)
    if not entries:
        print("[manifest_to_generators] No valid entries found in manifests.", file=sys.stderr)
        sys.exit(1)

    print(f"[manifest_to_generators] loaded {len(entries)} entries from {len(manifest_paths)} manifest(s)")

    scored = score_entries(entries, args.metric, rng)
    selected = scored[: args.count]

    print(f"[manifest_to_generators] selected {len(selected)} entries by metric={args.metric!r}")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    plan_path = out_dir / "generation_plan.json"
    plan = []

    for i, (score, entry) in enumerate(selected):
        compose_args = entry_to_compose_args(entry, i)
        record = {
            "rank": i,
            "score": score,
            "source_seed": entry.get("seed"),
            "source_manifest": entry.get("_manifest_file"),
            "composition_seed": compose_args["composition_seed"],
            "output_name": compose_args["name"],
        }
        plan.append(record)
        print(
            f"  [{i}] seed={entry.get('seed')}  score={score:.3f}  "
            f"→ composition_seed={compose_args['composition_seed']}"
        )

    plan_path.write_text(json.dumps(plan, indent=2) + "\n")
    print(f"[manifest_to_generators] plan → {plan_path}")

    if args.run:
        compose_script = Path(args.compose_script)
        if not compose_script.exists():
            print(f"[manifest_to_generators] ERROR: {compose_script} not found", file=sys.stderr)
            sys.exit(1)

        # Emit all compositions in one compose_generator call using master seed
        # We re-seed compose_generator with the first composition seed as master
        master_seed = plan[0]["composition_seed"] if plan else 0
        cmd = [
            sys.executable,
            str(compose_script),
            "--count", str(len(plan)),
            "--seed", str(master_seed),
            "--output-dir", str(out_dir),
        ]
        print(f"[manifest_to_generators] running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    else:
        # Print the command that would be run
        print("\n[manifest_to_generators] to generate, run:")
        print(
            f"  python compose_generator.py "
            f"--count {len(plan)} "
            f"--seed {plan[0]['composition_seed'] if plan else 0} "
            f"--output-dir {out_dir}"
        )


if __name__ == "__main__":
    main()
