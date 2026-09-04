import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_safety", ROOT / "scripts" / "validate-safety.py"
)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class SafetyValidatorTests(unittest.TestCase):
    def test_repository_records_are_structurally_valid_but_blocked(self):
        problems = validator.Problems()
        validator.validate_hazards(ROOT / "safety" / "hazards.json", problems)
        validator.validate_manifest(
            ROOT / "safety" / "manifests" / "experiment-001.json",
            problems,
            require_runnable=False,
        )
        self.assertEqual([], problems.errors)
        self.assertTrue(any("BLOCKED" in note for note in problems.notes))

    def test_unknown_datum_cannot_hide_a_value(self):
        source = json.loads(
            (ROOT / "safety" / "manifests" / "experiment-001.json").read_text()
        )
        source["categories"]["mechanical"]["data"][0]["value"] = 1000
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text(json.dumps(source), encoding="utf-8")
            problems = validator.Problems()
            validator.validate_manifest(path, problems, require_runnable=False)
        self.assertTrue(any("unknown datum must not carry a value" in error
                            for error in problems.errors))

    def test_draft_manifest_fails_runnable_gate(self):
        problems = validator.Problems()
        validator.validate_manifest(
            ROOT / "safety" / "manifests" / "experiment-001.json",
            problems,
            require_runnable=True,
        )
        self.assertTrue(any("not admitted for RUN" in error for error in problems.errors))


if __name__ == "__main__":
    unittest.main()
