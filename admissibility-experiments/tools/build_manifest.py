#!/usr/bin/env python3
"""Build a deterministic manifest from sidecars without changing their status."""
import hashlib, json, os
from pathlib import Path
ROOT = Path(os.environ.get("ADMISSIBILITY_ROOT", Path(__file__).resolve().parents[1]))
OUT = Path(os.environ.get("ADMISSIBILITY_OUTPUT", ROOT / "output"))
entries = []
for path in sorted(OUT.glob("*.json")):
    data = json.loads(path.read_text(encoding="utf-8"))
    outputs = []
    for rel in data.get("outputs", []):
        target = ROOT / rel
        outputs.append({"path": rel, "sha256": hashlib.sha256(target.read_bytes()).hexdigest()
                        if target.is_file() else None})
    entries.append({"scene_id": data.get("scene_id"), "status": data.get("status"),
                    "generator": data.get("generator"), "outputs": outputs})
(OUT / "manifest.json").write_text(json.dumps({"schema_version": 1, "entries": entries}, indent=2), encoding="utf-8")
print(OUT / "manifest.json")
