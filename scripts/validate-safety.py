#!/usr/bin/env python3
"""Validate Centerfuge safety records without third-party dependencies.

This is a fail-closed project validator, not a general JSON Schema engine and
not a safety certification tool. The JSON Schemas remain canonical for record
shape; these checks enforce repository invariants and readiness semantics.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
HAZARDS = ROOT / "safety" / "hazards.json"
MANIFEST_DIR = ROOT / "safety" / "manifests"
SCHEMA_DIR = ROOT / "safety" / "schemas"

EVIDENCE = {"V", "M", "S", "D", "Q"}
STATES = {
    "OFF", "QUARANTINE", "READY", "RUN", "CONTROLLED_REFUSAL",
    "COOLDOWN_CLEARING", "USER_ACCESS", "SERVICE_LOCKOUT", "FAULT_LATCHED",
}
CATEGORIES = {
    "mechanical", "air_pressure", "thermal", "electrical", "material",
    "stop_behavior", "access_service", "installation",
}
DATUM_STATES = {"unknown", "provisional", "verified", "not_applicable"}
ITEM_STATES = {"missing", "installed", "verified", "not_applicable"}
HAZARD_ID = re.compile(r"^HZ-[0-9]{3}$")
CONTROL_ID = re.compile(r"^CTRL-[0-9]{3}$")
TRACE_ID = re.compile(r"^TR-[0-9]{3}$")
DATUM_ID = re.compile(r"^DAT-[A-Z]+-[0-9]{3}$")
SAFETY_ITEM_ID = re.compile(r"^(SNS|INT)-[0-9]{3}$")


class Problems:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.notes: list[str] = []

    def require(self, condition: bool, location: str, message: str) -> None:
        if not condition:
            self.errors.append(f"{location}: {message}")


def read_json(path: Path, problems: Problems) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        problems.errors.append(f"{path.relative_to(ROOT)}: {exc}")
        return None


def nonempty_strings(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, str) and bool(item.strip()) for item in value
    )


def unique_id(identifier: Any, pattern: re.Pattern[str], seen: set[str],
              location: str, problems: Problems) -> None:
    problems.require(isinstance(identifier, str) and bool(pattern.fullmatch(identifier)),
                     location, "identifier has the wrong form")
    if isinstance(identifier, str):
        problems.require(identifier not in seen, location, "identifier is duplicated")
        seen.add(identifier)


def validate_hazards(path: Path, problems: Problems) -> None:
    data = read_json(path, problems)
    if not isinstance(data, dict):
        return
    problems.require(data.get("schema_version") == "1.0.0", str(path), "unsupported schema_version")
    problems.require(data.get("evidence_status") in EVIDENCE, str(path), "invalid evidence_status")
    hazards = data.get("hazards")
    problems.require(isinstance(hazards, list) and bool(hazards), str(path), "hazards must be nonempty")
    if not isinstance(hazards, list):
        return

    seen_hazards: set[str] = set()
    seen_controls: set[str] = set()
    seen_traces: set[str] = set()
    required = {
        "id", "title", "subsystems", "operating_states", "initiating_events",
        "consequences", "severity", "likelihood_basis", "detection", "controls",
        "response", "verification", "evidence_status", "residual_risk", "open_questions",
    }
    for index, hazard in enumerate(hazards):
        loc = f"{path.relative_to(ROOT)}:hazards[{index}]"
        if not isinstance(hazard, dict):
            problems.errors.append(f"{loc}: hazard must be an object")
            continue
        missing = required - hazard.keys()
        problems.require(not missing, loc, f"missing fields: {', '.join(sorted(missing))}")
        unique_id(hazard.get("id"), HAZARD_ID, seen_hazards, loc, problems)
        problems.require(nonempty_strings(hazard.get("subsystems")), loc, "subsystems must be nonempty")
        states = hazard.get("operating_states")
        problems.require(nonempty_strings(states) and set(states) <= STATES, loc, "invalid operating_states")
        for field in ("initiating_events", "consequences", "detection", "response"):
            problems.require(nonempty_strings(hazard.get(field)), loc, f"{field} must be nonempty")
        problems.require(hazard.get("severity") in {"minor", "serious", "critical", "catastrophic"},
                         loc, "invalid severity")
        problems.require(hazard.get("evidence_status") in EVIDENCE, loc, "invalid evidence_status")
        controls = hazard.get("controls")
        problems.require(isinstance(controls, list) and bool(controls), loc, "controls must be nonempty")
        for control in controls if isinstance(controls, list) else []:
            cloc = f"{loc}:control"
            if not isinstance(control, dict):
                problems.errors.append(f"{cloc}: control must be an object")
                continue
            unique_id(control.get("id"), CONTROL_ID, seen_controls, cloc, problems)
            problems.require(control.get("type") in {
                "inherent", "passive", "mechanical", "electrical",
                "electronic", "software", "procedural",
            }, cloc, "invalid control type")
            problems.require(isinstance(control.get("required"), bool), cloc, "required must be boolean")
            problems.require(bool(str(control.get("verification", "")).strip()), cloc,
                             "control requires a verification statement")
        traces = hazard.get("verification")
        problems.require(isinstance(traces, list) and bool(traces), loc, "verification must be nonempty")
        for trace in traces if isinstance(traces, list) else []:
            tloc = f"{loc}:trace"
            if not isinstance(trace, dict):
                problems.errors.append(f"{tloc}: trace must be an object")
                continue
            unique_id(trace.get("id"), TRACE_ID, seen_traces, tloc, problems)
            problems.require(trace.get("kind") in {
                "requirement", "standard", "calculation", "inspection",
                "test", "demonstration", "open_question",
            }, tloc, "invalid trace kind")
            problems.require(trace.get("status") in {
                "planned", "open", "passing", "failing", "not_applicable",
            }, tloc, "invalid trace status")
            problems.require(bool(str(trace.get("reference", "")).strip()), tloc,
                             "trace reference must be nonempty")


def manifest_readiness(data: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    for name, category in data.get("categories", {}).items():
        if not isinstance(category, dict) or not category.get("applicable"):
            continue
        entries = category.get("data", [])
        if not entries:
            blockers.append(f"{name}: applicable category has no data")
        for datum in entries:
            if not isinstance(datum, dict):
                continue
            if datum.get("status") != "verified":
                blockers.append(f"{datum.get('id', name)}: status is not verified")
            for field in ("value", "provenance", "verified_at", "evidence"):
                if datum.get(field) is None or datum.get(field) == "":
                    blockers.append(f"{datum.get('id', name)}: {field} is missing")
    for collection in ("required_sensors", "required_interlocks"):
        for item in data.get(collection, []):
            if item.get("required") and item.get("status") != "verified":
                blockers.append(f"{item.get('id', collection)}: required item is not verified")
            if item.get("required") and not item.get("verification"):
                blockers.append(f"{item.get('id', collection)}: verification reference is missing")
    blockers.extend(str(item) for item in data.get("blockers", []))
    return blockers


def validate_manifest(path: Path, problems: Problems, require_runnable: bool) -> None:
    data = read_json(path, problems)
    if not isinstance(data, dict):
        return
    loc = str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)
    required = {
        "schema_version", "manifest_version", "apparatus_id", "configuration_id",
        "intended_process", "evidence_status", "approved_for_run", "categories",
        "required_sensors", "required_interlocks", "blockers",
    }
    problems.require(not (required - data.keys()), loc,
                     f"missing fields: {', '.join(sorted(required - data.keys()))}")
    problems.require(data.get("schema_version") == "1.0.0", loc, "unsupported schema_version")
    problems.require(data.get("evidence_status") in EVIDENCE, loc, "invalid evidence_status")
    problems.require(isinstance(data.get("approved_for_run"), bool), loc, "approved_for_run must be boolean")
    categories = data.get("categories")
    problems.require(isinstance(categories, dict), loc, "categories must be an object")
    if isinstance(categories, dict):
        problems.require(set(categories) == CATEGORIES, loc,
                         "categories must contain exactly the required category set")
        seen_data: set[str] = set()
        for name, category in categories.items():
            cloc = f"{loc}:categories.{name}"
            problems.require(isinstance(category, dict), cloc, "category must be an object")
            if not isinstance(category, dict):
                continue
            problems.require(isinstance(category.get("applicable"), bool), cloc, "applicable must be boolean")
            entries = category.get("data")
            problems.require(isinstance(entries, list), cloc, "data must be an array")
            if category.get("applicable"):
                problems.require(bool(entries), cloc, "applicable category requires data")
            for datum in entries if isinstance(entries, list) else []:
                dloc = f"{cloc}:datum"
                if not isinstance(datum, dict):
                    problems.errors.append(f"{dloc}: datum must be an object")
                    continue
                unique_id(datum.get("id"), DATUM_ID, seen_data, dloc, problems)
                status = datum.get("status")
                problems.require(status in DATUM_STATES, dloc, "invalid status")
                if status == "verified":
                    for field in ("value", "provenance", "verified_at", "evidence"):
                        problems.require(datum.get(field) not in (None, ""), dloc,
                                         f"verified datum requires {field}")
                if status == "unknown":
                    problems.require(datum.get("value") is None, dloc,
                                     "unknown datum must not carry a value")
        seen_items: set[str] = set()
        for collection in ("required_sensors", "required_interlocks"):
            items = data.get(collection)
            problems.require(isinstance(items, list), loc, f"{collection} must be an array")
            for item in items if isinstance(items, list) else []:
                iloc = f"{loc}:{collection}"
                if not isinstance(item, dict):
                    problems.errors.append(f"{iloc}: item must be an object")
                    continue
                unique_id(item.get("id"), SAFETY_ITEM_ID, seen_items, iloc, problems)
                problems.require(item.get("status") in ITEM_STATES, iloc, "invalid status")
                problems.require(isinstance(item.get("required"), bool), iloc, "required must be boolean")
                if item.get("status") == "verified":
                    problems.require(bool(item.get("verification")), iloc,
                                     "verified item requires verification reference")

    readiness = manifest_readiness(data)
    approved = data.get("approved_for_run") is True
    problems.require(not approved or not readiness, loc,
                     "approved_for_run is true while readiness blockers remain")
    if require_runnable:
        problems.require(approved and not readiness, loc,
                         "manifest is structurally valid but not admitted for RUN")
    elif readiness:
        problems.notes.append(f"{loc}: BLOCKED ({len(readiness)} readiness findings)")
    else:
        problems.notes.append(f"{loc}: RUNNABLE")


def manifest_paths(arguments: Iterable[str]) -> list[Path]:
    given = list(arguments)
    if not given:
        return sorted(MANIFEST_DIR.glob("*.json"))
    return [Path(item).resolve() for item in given]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-runnable", action="store_true",
                        help="fail unless every selected manifest is explicitly ready for RUN")
    parser.add_argument("manifests", nargs="*", help="manifest paths; defaults to safety/manifests/*.json")
    args = parser.parse_args(argv)

    problems = Problems()
    for schema in sorted(SCHEMA_DIR.glob("*.json")):
        read_json(schema, problems)
    validate_hazards(HAZARDS, problems)
    paths = manifest_paths(args.manifests)
    problems.require(bool(paths), "safety/manifests", "no manifests found")
    for path in paths:
        validate_manifest(path, problems, args.require_runnable)

    for note in problems.notes:
        print(note)
    if problems.errors:
        for error in problems.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Safety validation failed with {len(problems.errors)} error(s).", file=sys.stderr)
        return 1
    print(f"Safety validation passed for {len(paths)} manifest(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
