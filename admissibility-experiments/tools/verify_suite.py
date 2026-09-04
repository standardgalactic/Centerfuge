#!/usr/bin/env python3
"""Validate sidecars and return non-zero only at suite level."""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get("ADMISSIBILITY_ROOT", Path(__file__).resolve().parents[1]))
OUTPUT = Path(os.environ.get("ADMISSIBILITY_OUTPUT", ROOT / "output"))
EXPECTED = {
    "pop_refuse_bind_collapse", "record_admit_commit", "distinction_holonomy",
    "sheaf_gluing", "vertical_horizontal_repair", "rsvp_field",
    "persistence_cone_tidal_torque", "tartan_weave", "data_center_substrate",
    "fusion_reactor_comparison", "molecular_manufacturing", "aniara_whale_cutaway",
    "city_of_brutes_triad", "sproll_manipulatives", "fluid_flashcards", "render_ledger",
}
problems = []
seen = set()
for path in sorted(OUTPUT.glob("*.json")):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        problems.append(f"{path.name}: invalid JSON: {exc}")
        continue
    scene_id = data.get("scene_id")
    seen.add(scene_id)
    if data.get("status") != "pass":
        failed = [c.get("name") for c in data.get("checks", []) if not c.get("passed")]
        problems.append(f"{scene_id}: status={data.get('status')}; failed={failed}")
    generator = ROOT / str(data.get("generator", ""))
    if not generator.is_file(): problems.append(f"{scene_id}: missing generator {generator}")
    if os.environ.get("DRY_RUN", "0") != "1":
        for rel in data.get("outputs", []):
            if not (ROOT / rel).is_file(): problems.append(f"{scene_id}: missing output {rel}")
missing = EXPECTED - seen
if missing: problems.append("missing sidecars: " + ", ".join(sorted(missing)))
if problems:
    print("Suite inadmissible:", *problems, sep="\n  ", file=sys.stderr)
    raise SystemExit(1)
print(f"Suite admissible: {len(seen)} sidecars verified")
