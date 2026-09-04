#!/usr/bin/env python3
"""Check headless_blender/manifest.json without launching or installing Blender.

Record vs Admit (see docs/operating-model.md's ledger vocabulary): common.py's
finish() only *records* each scene's generation parameters and verification
results into manifest.json from inside a running Blender process. This script
performs the separate *Admit* decision -- deciding whether the recorded state
is good enough to treat the render output as usable -- entirely outside
Blender, from the manifest file and the output directory's file listing alone.

This is deliberately the only supported way to validate render output in CI or
during deployment. It must never shell out to `blender`, `pip install bpy`, or
any other Blender acquisition step: a missing or stale manifest is reported as
a failure, not silently repaired by re-rendering. Regenerating outputs (which
does require Blender) is a separate, explicitly opt-in action performed with
render_all.sh, never an implicit side effect of running this checker.

Usage:
    python3 headless_blender/check_manifest.py [output_dir]

Exit code is 0 only if every scene named in EXPECTED_SCENES has a manifest
entry with the outputs it claims to have produced actually present on disk,
and any verification recorded for that scene is non-empty (i.e. finish()
completed without raising RuntimeError for that scene, since a raised
RuntimeError prevents write_manifest_entry from ever executing).
"""

import json
import sys
from pathlib import Path

EXPECTED_SCENES = (
    "centerfuge_cutaway",
    "material_sorting_vortex",
    "hyperbolation_cognet",
    "house_distribution",
    "intake_geometry",
    "internal_routing",
    "maintenance_access",
)

# Scenes whose name/label claims an interior view and therefore must carry a
# recorded "visibility" verification result (see common.verify_visibility).
# Adding a scene here without wiring `interior_objects` into its finish() call
# would make check_manifest.py fail it for a missing key, which is the
# intended admissibility gate rather than an accidental one.
REQUIRES_VISIBILITY_CHECK = ("centerfuge_cutaway", "internal_routing")


def check(output_dir):
    """Return (ok, findings) for the manifest at output_dir/manifest.json.

    `ok` is False if the manifest is missing, unreadable, missing an expected
    scene, missing a claimed output file, or missing a verification result
    that the scene's own generator is supposed to have recorded. Each finding
    is a human-readable string naming exactly which admissibility condition
    failed, not a generic "invalid manifest" message.
    """
    findings = []
    manifest_path = Path(output_dir) / "manifest.json"
    if not manifest_path.exists():
        return False, [
            f"{manifest_path} does not exist. Render the suite first with "
            "`bash headless_blender/render_all.sh <output_dir>` (requires Blender), "
            "or point --output at a directory that already has a manifest."
        ]

    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as exc:
        return False, [f"{manifest_path} is not valid JSON: {exc}"]

    scenes = manifest.get("scenes", {})
    for name in EXPECTED_SCENES:
        entry = scenes.get(name)
        if entry is None:
            findings.append(f"scene '{name}' has no manifest entry (never completed finish()).")
            continue

        outputs = entry.get("outputs", {})
        blend_path = outputs.get("blend")
        if not blend_path or not Path(blend_path).exists():
            findings.append(f"scene '{name}' claims blend output {blend_path!r} but it is missing.")

        image_path = outputs.get("image")
        rendered = entry.get("parameters", {}).get("rendered", True)
        if rendered and (not image_path or not Path(image_path).exists()):
            findings.append(f"scene '{name}' claims image output {image_path!r} but it is missing.")

        verification = entry.get("verification", {})
        if rendered and not verification.get("image"):
            findings.append(
                f"scene '{name}' has no recorded image verification; "
                "either it was never rendered through finish() or that check did not run."
            )
        if name in REQUIRES_VISIBILITY_CHECK and not verification.get("visibility"):
            findings.append(
                f"scene '{name}' claims an interior/cutaway view but has no recorded "
                "non-occlusion (visibility) verification; see common.verify_visibility."
            )

    orphaned = sorted(set(scenes) - set(EXPECTED_SCENES))
    if orphaned:
        findings.append(
            "manifest records scene(s) not in EXPECTED_SCENES (update this script's list if "
            f"they are intentional, additive scenes): {orphaned}"
        )

    return (len(findings) == 0), findings


def main(argv):
    output_dir = argv[1] if len(argv) > 1 else "output/headless"
    ok, findings = check(output_dir)
    if ok:
        print(f"OK: all {len(EXPECTED_SCENES)} expected scenes are present and verified in {output_dir}.")
        return 0
    print(f"FAILED manifest check for {output_dir}:", file=sys.stderr)
    for finding in findings:
        print(f"  - {finding}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
