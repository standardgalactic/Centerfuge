#!/usr/bin/env bash
set -euo pipefail

repo="standardgalactic/Centerfuge"
apply=false

usage() {
    printf 'Usage: %s [--apply] [--repo OWNER/REPO]\n' "${0##*/}"
    printf 'Preview is the default. Use --apply to create the issues.\n'
}

while (($#)); do
    case "$1" in
        --apply) apply=true; shift ;;
        --repo)
            [[ $# -ge 2 ]] || { printf 'Missing value after --repo\n' >&2; exit 2; }
            repo="$2"
            shift 2
            ;;
        -h|--help) usage; exit 0 ;;
        *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
    esac
done

existing_titles=""
if $apply; then
    command -v gh >/dev/null 2>&1 || {
        printf 'GitHub CLI (gh) is required.\n' >&2
        exit 1
    }
    gh auth status >/dev/null
    existing_titles="$(
        gh issue list --repo "$repo" --state all --limit 1000 \
            --json title --jq '.[].title'
    )"
fi

create_issue() {
    local title="$1"
    local body
    body="$(cat)"

    if ! $apply; then
        printf '\n[%s]\n%s\n' "$title" "$body"
        return
    fi

    if grep -Fqx -- "$title" <<<"$existing_titles"; then
        printf 'Skipping existing issue: %s\n' "$title"
        return
    fi

    gh issue create --repo "$repo" --title "$title" --body "$body"
    existing_titles+="${existing_titles:+$'\n'}$title"
}

create_issue "Formalize the Centerfuge operating model and system boundaries" <<'EOF'
## Objective

Turn the Centerfuge concept into an explicit systems model. The documentation should distinguish the physical appliance, the household material streams it accepts, the transformations it performs, and the outputs or residues it produces.

## Work

- [ ] Define the system boundary and the admissible input classes.
- [ ] Specify the stages from intake through rotation, separation, routing, and labeled output.
- [ ] Add mass, energy, angular-momentum, and residence-time balances.
- [ ] Derive the centrifugal and drag regimes used by the proposed sorting mechanism.
- [ ] Identify which separations are geometric, density-based, aerodynamic, magnetic, optical, or chemical.
- [ ] State failure conditions for mixed, wet, hazardous, fragile, or compositionally ambiguous inputs.
- [ ] Distinguish the conceptual architecture from mechanisms already demonstrated experimentally.
- [ ] Add a glossary and a common notation table.

## Completion criterion

A reader can reconstruct the operating sequence, identify every physical assumption, and determine where empirical measurements are still required.
EOF

create_issue "Build a reproducible headless Blender experiment suite" <<'EOF'
## Objective

Expand the current visual experiments into a reproducible suite of scene generators that test and explain distinct parts of Centerfuge rather than serving only as illustrations.

## Work

- [ ] Keep every scene buildable from a checked-in Python script without manual Blender editing.
- [ ] Add experiments for intake geometry, vortex formation, material sorting, internal routing, maintenance access, and household integration.
- [ ] Record camera, lighting, render engine, resolution, samples, random seed, and Blender version.
- [ ] Give each output a manifest entry linking the PNG to its generator and parameters.
- [ ] Add cutaway and exploded-view variants where internal topology matters.
- [ ] Make labels legible at desktop and phone widths without obscuring the apparatus.
- [ ] Add a batch renderer that fails when a scene or expected output is missing.
- [ ] Preserve an original-look preset so later stylistic changes remain comparable.

## Completion criterion

A clean checkout can regenerate the complete image set with one documented command and produce an output manifest with no orphaned images or scripts.
EOF

create_issue "Add parameter sweeps and measurable sorting experiments" <<'EOF'
## Objective

Convert the qualitative material-sorting proposal into a set of falsifiable benchtop experiments and parameter sweeps.

## Work

- [ ] Define representative test materials with measured density, size, shape, moisture, and surface properties.
- [ ] Select measurable outputs such as purity, recovery, throughput, energy per kilogram, breakage, and contamination.
- [ ] Sweep angular velocity, airflow, feed rate, particle-size distribution, geometry, and residence time.
- [ ] Include negative controls and deliberately difficult mixtures.
- [ ] Model uncertainty and repeatability rather than reporting only best runs.
- [ ] Compare Centerfuge separation with gravity, screens, cyclones, magnets, and manual sorting baselines.
- [ ] Store parameters and results in machine-readable files.
- [ ] Define stop conditions for unsafe vibration, imbalance, dust, heat, or containment failure.

## Completion criterion

The repository contains a test plan capable of disproving an ineffective configuration and of comparing successful configurations on common metrics.
EOF

create_issue "Document safety, maintenance, and domestic failure modes" <<'EOF'
## Objective

Treat Centerfuge as a domestic appliance whose usefulness depends on containment, cleanability, repairability, and safe behavior under misuse.

## Work

- [ ] Create a failure-mode inventory covering imbalance, jams, overspeed, bearing failure, dust, aerosols, heat, noise, leaks, and incompatible materials.
- [ ] Define interlocks, emergency shutdown behavior, and safe access states.
- [ ] Show how internal surfaces, ducts, bins, and filters are inspected and cleaned.
- [ ] Separate user-serviceable components from protected high-energy components.
- [ ] Estimate maintenance intervals and consumable requirements.
- [ ] Add accessibility considerations for loading, unloading, controls, and status reporting.
- [ ] State clearly which hazardous waste classes must never enter the device.
- [ ] Connect each safety claim to either a standard, calculation, experiment, or explicit open question.

## Completion criterion

The design documentation explains how ordinary misuse and component failure are contained, detected, and repaired without relying on an ideal operator.
EOF

if ! $apply; then
    printf '\nPreview only. Run %s --apply to create these issues in %s.\n' "${0##*/}" "$repo"
fi
