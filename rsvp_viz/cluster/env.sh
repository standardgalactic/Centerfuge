#!/usr/bin/env bash
export RSVP_IMAGE="${RSVP_IMAGE:-rsvp-blender:latest}"
export OUT_DIR="${OUT_DIR:-$PWD/output}"
export LOG_DIR="${LOG_DIR:-$PWD/output/logs}"
export SEED="${SEED:-42}"
export RUN_ID="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
mkdir -p "$OUT_DIR" "$LOG_DIR"
