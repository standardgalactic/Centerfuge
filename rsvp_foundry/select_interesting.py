#!/usr/bin/env python3
"""
select_interesting.py — score and rank registry entries, emit generation targets.

Usage:
    python select_interesting.py [--registry FILE] [--metric METRIC] [--top N]
                                 [--generator NAME] [--emit-batch]

Metrics:
    render_seconds    prefer fast (simple) renders
    slow              prefer slow (complex) renders
    random            uniform random baseline

With --emit-batch, writes a ready-to-run rsvp_batch.sh invocation to stdout.
"""

from __future__ import annotations
import argparse
import json
import random
import sys
from pathlib import Path


METRICS = ["render_seconds", "slow", "random"]


def load_registry(path: str) -> list[dict]:
    with open(path) as f:
        reg = json.load(f)
    return [e for e in reg.get("entries", []) if e.get("status") == "ok"]


def score(entry: dict, metric: str, rng: random.Random) -> float:
    rt = entry.get("render_seconds") or 0.0
    if metric == "render_seconds":
        return -rt          # lower render time = higher score
    if metric == "slow":
        return rt
    return rng.random()     # random baseline


def main() -> None:
    parser = argparse.ArgumentParser(description="Select interesting registry entries")
    parser.add_argument("--registry", default="registry.json")
    parser.add_argument("--metric", default="random", choices=METRICS)
    parser.add_argument("--top", type=int, default=10, help="How many to select")
    parser.add_argument("--generator", default=None,
                        help="Filter to a specific generator name")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--emit-batch", action="store_true",
                        help="Print a rsvp_batch.sh command for the selected seeds")
    args = parser.parse_args()

    if not Path(args.registry).exists():
        print(f"[select] ERROR: {args.registry} not found. Run build_registry.py first.",
              file=sys.stderr)
        sys.exit(1)

    entries = load_registry(args.registry)

    if args.generator:
        entries = [e for e in entries if e.get("generator") == args.generator]

    if not entries:
        print("[select] No matching entries.", file=sys.stderr)
        sys.exit(1)

    rng = random.Random(args.seed)
    scored = sorted(entries, key=lambda e: score(e, args.metric, rng), reverse=True)
    selected = scored[: args.top]

    print(f"[select] metric={args.metric}  total={len(entries)}  selected={len(selected)}")
    print()

    for i, e in enumerate(selected):
        rt = e.get("render_seconds")
        rt_str = f"{rt:.1f}s" if rt else "n/a"
        gen = e.get("generator", "?")
        seed = e.get("seed", "?")
        print(f"  [{i:2d}]  {gen:20s}  seed={seed:4}  render={rt_str}")

    if args.emit_batch:
        # Group by generator
        by_gen: dict[str, list[int]] = {}
        for e in selected:
            g = e.get("generator", "unknown")
            s = e.get("seed")
            if s is not None:
                by_gen.setdefault(g, []).append(s)

        print()
        print("# --- batch commands ---")
        for gen, seeds in by_gen.items():
            seed_str = " ".join(str(s) for s in seeds)
            print(f'./rsvp_batch.sh -g {gen} -s "{seed_str}" -r')


if __name__ == "__main__":
    main()
