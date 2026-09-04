#!/usr/bin/env python3
"""Build static dashboard data from an Admissibility Experiments output tree."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DIST = HERE / "dist"
RENDERS = DIST / "renders"


def relative_or_absolute(path_text: str, suite: Path) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else suite / path


def safe_render_name(scene_id: str, source: Path, ordinal: int) -> str:
    digest = hashlib.sha256(str(source).encode("utf-8")).hexdigest()[:8]
    suffix = source.suffix.lower() if source.suffix else ".png"
    return f"{scene_id}-{ordinal:02d}-{digest}{suffix}"


def normalized_check(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        return {"name": "Malformed check", "expected": None, "observed": item, "passed": False}
    return {
        "name": str(item.get("name", "Unnamed check")),
        "expected": item.get("expected"),
        "observed": item.get("observed"),
        "passed": item.get("passed") is True,
        "tolerance": item.get("tolerance"),
        "reversible": item.get("reversible"),
        "case": item.get("case"),
    }


def load_scene(sidecar: Path, suite: Path) -> dict[str, Any]:
    try:
        raw = json.loads(sidecar.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "scene_id": sidecar.stem, "framework": "unreadable", "primitive": "unknown",
            "status": "error", "checks": [], "parameters": {}, "evidence": {}, "render": {},
            "generator": "", "images": [], "source_sidecar": sidecar.name,
            "load_error": str(exc),
        }

    scene_id = str(raw.get("scene_id") or sidecar.stem)
    images = []
    missing = []
    for ordinal, output_text in enumerate(raw.get("outputs", []), start=1):
        source = relative_or_absolute(str(output_text), suite)
        if source.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            continue
        if source.is_file():
            target_name = safe_render_name(scene_id, source, ordinal)
            shutil.copy2(source, RENDERS / target_name)
            images.append({"src": f"renders/{target_name}", "label": source.name})
        else:
            missing.append(str(output_text))

    checks = [normalized_check(item) for item in raw.get("checks", [])]
    reported_status = raw.get("status") if raw.get("status") in {"pass", "fail"} else "error"
    computed_status = "pass" if checks and all(item["passed"] for item in checks) else "fail"
    status_consistent = reported_status == computed_status
    return {
        "scene_id": scene_id,
        "framework": str(raw.get("framework", "unclassified")),
        "primitive": str(raw.get("primitive", "unspecified")),
        "status": reported_status,
        "computed_status": computed_status,
        "status_consistent": status_consistent,
        "generator": str(raw.get("generator", "")),
        "checks": checks,
        "parameters": raw.get("parameters") if isinstance(raw.get("parameters"), dict) else {},
        "evidence": raw.get("evidence") if isinstance(raw.get("evidence"), dict) else {},
        "render": raw.get("render") if isinstance(raw.get("render"), dict) else {},
        "images": images,
        "missing_images": missing,
        "source_sidecar": sidecar.name,
        "load_error": None,
    }


def main() -> int:
    global DIST, RENDERS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", type=Path, help="Path to the admissibility-experiments root")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="Destination directory; defaults to this package's dist directory")
    args = parser.parse_args()
    suite = args.suite.expanduser().resolve()
    output = (args.output_dir.expanduser().resolve() if args.output_dir else DIST)
    DIST, RENDERS = output, output / "renders"
    source_output = suite / "output"
    if not suite.is_dir():
        parser.error(f"suite directory does not exist: {suite}")
    DIST.mkdir(parents=True, exist_ok=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    for asset in ("index.html", "dashboard.css", "dashboard.js"):
        shutil.copy2(HERE / "src" / asset, DIST / asset)

    scenes = [load_scene(path, suite) for path in sorted(source_output.glob("*.json"))
              if path.name != "manifest.json"] if source_output.is_dir() else []
    frameworks = sorted({item["framework"] for item in scenes})
    totals = {
        "scenes": len(scenes),
        "pass": sum(item["status"] == "pass" for item in scenes),
        "fail": sum(item["status"] == "fail" for item in scenes),
        "error": sum(item["status"] == "error" for item in scenes),
        "checks": sum(len(item["checks"]) for item in scenes),
        "checks_passed": sum(check["passed"] for item in scenes for check in item["checks"]),
        "missing_images": sum(len(item["missing_images"]) for item in scenes),
    }
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "suite_name": suite.name,
        "source_output": str(source_output),
        "totals": totals,
        "frameworks": frameworks,
        "scenes": scenes,
    }
    (DIST / "data.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Built {DIST / 'index.html'} from {len(scenes)} sidecar(s)")
    if not scenes:
        print(f"No sidecars found in {source_output}; the dashboard will show its empty state.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
