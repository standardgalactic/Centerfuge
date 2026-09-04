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
OPERATING_STATES = ROOT / "safety" / "operating-states.json"
STOP_RECOVERY = ROOT / "safety" / "stop-recovery.json"
SERVICE_MAINTENANCE = ROOT / "safety" / "service-maintenance.json"
DOMESTIC_BOUNDARIES = ROOT / "safety" / "domestic-boundaries.json"
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
TRANSITION_ID = re.compile(r"^TX-[0-9]{3}$")
EVENT_ID = re.compile(r"^EV-[0-9]{3}$")
SERVICE_ID = re.compile(r"^SVC-[0-9]{3}$")
DOMESTIC_ID = re.compile(r"^(CLN|ACC|INST)-[0-9]{3}$")


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


def validate_operating_states(path: Path, problems: Problems) -> None:
    data = read_json(path, problems)
    if not isinstance(data, dict):
        return
    loc = str(path.relative_to(ROOT))
    states = data.get("states")
    problems.require(isinstance(states, list), loc, "states must be an array")
    state_ids = {
        item.get("id") for item in states if isinstance(item, dict)
    } if isinstance(states, list) else set()
    problems.require(state_ids == STATES, loc, "state set must exactly match the normative vocabulary")
    for index, state in enumerate(states if isinstance(states, list) else []):
        sloc = f"{loc}:states[{index}]"
        problems.require(isinstance(state, dict), sloc, "state must be an object")
        if isinstance(state, dict):
            problems.require(bool(str(state.get("invariant", "")).strip()), sloc, "invariant is required")
            problems.require(bool(str(state.get("access", "")).strip()), sloc, "access rule is required")
    transitions = data.get("transitions")
    problems.require(isinstance(transitions, list) and bool(transitions), loc, "transitions must be nonempty")
    seen: set[str] = set()
    coverage: set[str] = set()
    for index, transition in enumerate(transitions if isinstance(transitions, list) else []):
        tloc = f"{loc}:transitions[{index}]"
        if not isinstance(transition, dict):
            problems.errors.append(f"{tloc}: transition must be an object")
            continue
        unique_id(transition.get("id"), TRANSITION_ID, seen, tloc, problems)
        source, target = transition.get("from"), transition.get("to")
        problems.require(source in STATES or source == "*", tloc, "unknown source state")
        problems.require(target in STATES, tloc, "unknown target state")
        if source in STATES:
            coverage.add(source)
        for field in ("guards", "actions", "completion_evidence", "ledger"):
            problems.require(nonempty_strings(transition.get(field)), tloc, f"{field} must be nonempty")
        problems.require(transition.get("timeout_fallback") in STATES, tloc, "invalid timeout fallback")
        problems.require(transition.get("reset_authority") in {
            "automatic", "user", "trained_service", "protected_service",
        }, tloc, "invalid reset authority")
    problems.require("RUN" in coverage and "FAULT_LATCHED" in coverage, loc,
                     "RUN and FAULT_LATCHED require explicit outgoing recovery transitions")


def hazard_ids(path: Path, problems: Problems) -> set[str]:
    data = read_json(path, problems)
    if not isinstance(data, dict) or not isinstance(data.get("hazards"), list):
        return set()
    return {item.get("id") for item in data["hazards"] if isinstance(item, dict)}


def validate_stop_recovery(path: Path, known_hazards: set[str], problems: Problems) -> None:
    data = read_json(path, problems)
    if not isinstance(data, dict):
        return
    loc = str(path.relative_to(ROOT))
    events = data.get("events")
    problems.require(isinstance(events, list) and bool(events), loc, "events must be nonempty")
    seen: set[str] = set()
    covered: set[str] = set()
    for index, event in enumerate(events if isinstance(events, list) else []):
        eloc = f"{loc}:events[{index}]"
        if not isinstance(event, dict):
            problems.errors.append(f"{eloc}: event must be an object")
            continue
        unique_id(event.get("id"), EVENT_ID, seen, eloc, problems)
        refs = event.get("hazards")
        problems.require(nonempty_strings(refs), eloc, "hazards must be nonempty")
        if isinstance(refs, list):
            problems.require(set(refs) <= known_hazards, eloc, "event references an unknown hazard")
            covered.update(refs)
        actions = event.get("actions")
        required_actions = {"feed", "drive", "brake", "extraction", "cooling", "gates", "alarm", "latch"}
        problems.require(isinstance(actions, dict) and set(actions) == required_actions,
                         eloc, "actions must contain the complete action vocabulary")
        problems.require(nonempty_strings(event.get("access_release")), eloc,
                         "access_release must be nonempty")
        problems.require(event.get("status") in {"modeled", "apparatus_specific_open", "verified"},
                         eloc, "invalid status")
        if event.get("status") == "verified":
            problems.require(not event.get("open_questions"), eloc,
                             "verified event may not retain open questions")
    problems.require({"HZ-001", "HZ-002", "HZ-004", "HZ-005", "HZ-006", "HZ-007",
                      "HZ-008", "HZ-010", "HZ-011", "HZ-012", "HZ-013", "HZ-014",
                      "HZ-017"} <= covered, loc,
                     "stop matrix does not cover every hazard requiring an active response")


def validate_service_maintenance(path: Path, problems: Problems) -> None:
    data = read_json(path, problems)
    if not isinstance(data, dict):
        return
    loc = str(path.relative_to(ROOT))
    components = data.get("components")
    problems.require(isinstance(components, list) and bool(components), loc,
                     "components must be nonempty")
    seen: set[str] = set()
    classes: set[str] = set()
    for index, component in enumerate(components if isinstance(components, list) else []):
        cloc = f"{loc}:components[{index}]"
        if not isinstance(component, dict):
            problems.errors.append(f"{cloc}: component must be an object")
            continue
        unique_id(component.get("id"), SERVICE_ID, seen, cloc, problems)
        service_class = component.get("service_class")
        classes.add(service_class)
        problems.require(service_class in {"USER", "TRAINED", "PROTECTED_REPLACE_ONLY"},
                         cloc, "invalid service class")
        expected_access = "USER_ACCESS" if service_class == "USER" else "SERVICE_LOCKOUT"
        problems.require(component.get("access_state") == expected_access, cloc,
                         "access state is inconsistent with service class")
        for field in ("tasks", "interval_basis", "return_to_service"):
            problems.require(nonempty_strings(component.get(field)), cloc, f"{field} must be nonempty")
        problems.require(component.get("status") in {"modeled", "apparatus_specific_open", "verified"},
                         cloc, "invalid status")
        if component.get("status") == "verified":
            problems.require(not component.get("open_questions"), cloc,
                             "verified component may not retain open questions")
    problems.require(classes == {"USER", "TRAINED", "PROTECTED_REPLACE_ONLY"}, loc,
                     "register must exercise all service classes")


def validate_domestic_boundaries(path: Path, problems: Problems) -> None:
    data = read_json(path, problems)
    if not isinstance(data, dict):
        return
    loc = str(path.relative_to(ROOT))
    seen: set[str] = set()
    cleaning = data.get("cleaning_zones")
    problems.require(isinstance(cleaning, list) and bool(cleaning), loc,
                     "cleaning_zones must be nonempty")
    for index, zone in enumerate(cleaning if isinstance(cleaning, list) else []):
        zloc = f"{loc}:cleaning_zones[{index}]"
        if not isinstance(zone, dict):
            problems.errors.append(f"{zloc}: zone must be an object")
            continue
        unique_id(zone.get("id"), DOMESTIC_ID, seen, zloc, problems)
        problems.require(str(zone.get("id", "")).startswith("CLN-"), zloc, "cleaning ID must use CLN")
        problems.require(zone.get("service_class") in {"USER", "TRAINED", "PROTECTED_REPLACE_ONLY"},
                         zloc, "invalid service class")
        for field in ("soil_or_carryover", "method", "verification"):
            problems.require(nonempty_strings(zone.get(field)), zloc, f"{field} must be nonempty")
        problems.require(bool(str(zone.get("residue_custody", "")).strip()), zloc,
                         "residue custody is required")
        problems.require(zone.get("status") in {"modeled", "apparatus_specific_open", "verified"},
                         zloc, "invalid status")
    for collection, prefix in (
        ("accessibility_requirements", "ACC-"),
        ("installation_requirements", "INST-"),
    ):
        records = data.get(collection)
        problems.require(isinstance(records, list) and bool(records), loc,
                         f"{collection} must be nonempty")
        for index, record in enumerate(records if isinstance(records, list) else []):
            rloc = f"{loc}:{collection}[{index}]"
            if not isinstance(record, dict):
                problems.errors.append(f"{rloc}: requirement must be an object")
                continue
            unique_id(record.get("id"), DOMESTIC_ID, seen, rloc, problems)
            problems.require(str(record.get("id", "")).startswith(prefix), rloc,
                             f"identifier must use {prefix}")
            for field in ("subject", "requirement", "verification"):
                problems.require(bool(str(record.get(field, "")).strip()), rloc,
                                 f"{field} must be nonempty")
            problems.require(record.get("status") in {
                "modeled", "apparatus_specific_open", "verified",
            }, rloc, "invalid status")
            if record.get("status") == "verified":
                problems.require(not record.get("open_questions"), rloc,
                                 "verified requirement may not retain open questions")


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
    validate_operating_states(OPERATING_STATES, problems)
    known_hazards = hazard_ids(HAZARDS, problems)
    validate_stop_recovery(STOP_RECOVERY, known_hazards, problems)
    validate_service_maintenance(SERVICE_MAINTENANCE, problems)
    validate_domestic_boundaries(DOMESTIC_BOUNDARIES, problems)
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
