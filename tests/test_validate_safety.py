import importlib.util
import json
import tempfile
import unittest
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_safety", ROOT / "scripts" / "validate-safety.py"
)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class SafetyValidatorTests(unittest.TestCase):
    def test_domestic_boundaries_and_generated_index_are_current(self):
        problems = validator.Problems()
        validator.validate_domestic_boundaries(
            ROOT / "safety" / "domestic-boundaries.json", problems
        )
        self.assertEqual([], problems.errors)
        result = subprocess.run(
            ["python3", str(ROOT / "scripts" / "render-safety.py"), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_operating_stop_and_service_records_are_valid(self):
        problems = validator.Problems()
        validator.validate_operating_states(
            ROOT / "safety" / "operating-states.json", problems
        )
        hazards = validator.hazard_ids(ROOT / "safety" / "hazards.json", problems)
        validator.validate_stop_recovery(
            ROOT / "safety" / "stop-recovery.json", hazards, problems
        )
        validator.validate_service_maintenance(
            ROOT / "safety" / "service-maintenance.json", problems
        )
        self.assertEqual([], problems.errors)

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

    def test_required_experiment_datum_cannot_be_omitted(self):
        source = json.loads(
            (ROOT / "safety" / "manifests" / "experiment-001.json").read_text()
        )
        source["categories"]["mechanical"]["data"] = [
            datum for datum in source["categories"]["mechanical"]["data"]
            if datum["id"] != "DAT-MECH-007"
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "omitted.json"
            path.write_text(json.dumps(source), encoding="utf-8")
            problems = validator.Problems()
            validator.validate_manifest(path, problems, require_runnable=False)
        self.assertTrue(any("DAT-MECH-007" in error and "omits required" in error
                            for error in problems.errors))

    def test_sensor_record_requires_calibration_fields(self):
        source = json.loads(
            (ROOT / "safety" / "manifests" / "experiment-001.json").read_text()
        )
        del source["required_sensors"][0]["calibration_due_at"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing-calibration-field.json"
            path.write_text(json.dumps(source), encoding="utf-8")
            problems = validator.Problems()
            validator.validate_manifest(path, problems, require_runnable=False)
        self.assertTrue(any("sensor record requires calibration_due_at" in error
                            for error in problems.errors))

    def test_stale_calibration_is_a_readiness_blocker(self):
        source = json.loads(
            (ROOT / "safety" / "manifests" / "experiment-001.json").read_text()
        )
        sensor = source["required_sensors"][0]
        sensor.update({
            "status": "verified",
            "verification": "tests/evidence/sns-001.json",
            "instrument_id": "tachometer-example",
            "location": "drive shaft",
            "range": "0 to 100 rad/s",
            "accuracy": "+/- 1 rad/s",
            "sample_rate_hz": 100,
            "calibrated_at": "2020-01-01T00:00:00Z",
            "calibration_due_at": "2020-02-01T00:00:00Z",
            "calibration_record": "tests/evidence/calibration-example.json",
            "plausibility_test": "tests/evidence/plausibility-example.json",
            "availability_test": "tests/evidence/availability-example.json",
        })
        blockers = validator.manifest_readiness(source)
        self.assertIn("SNS-001: calibration is stale", blockers)


if __name__ == "__main__":
    unittest.main()
