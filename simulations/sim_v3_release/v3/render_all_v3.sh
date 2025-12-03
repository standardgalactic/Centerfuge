#!/usr/bin/env bash
# Batch-render all .blend files in ./output_v3 to PNG and MP4 using ffmpeg.

BLENDER="/usr/bin/blender"
OUT_DIR="./output_v3"
RENDER_DIR="${OUT_DIR}/renders"
VIDEO_DIR="${OUT_DIR}/videos"

mkdir -p "$RENDER_DIR" "$VIDEO_DIR"

for blend in "$OUT_DIR"/*.blend; do
    [ -e "$blend" ] || continue
    name=$(basename "$blend" .blend)
    frame_path="${RENDER_DIR}/${name}_####"
    echo "[v3] Rendering ${blend}..."
    "$BLENDER" -b "$blend" -E BLENDER_EEVEE -o "$frame_path" -a

    echo "[v3] Encoding video for ${name}..."
    ffmpeg -framerate 24 -i "${RENDER_DIR}/${name}_%04d.png"                -c:v libx264 -pix_fmt yuv420p "${VIDEO_DIR}/${name}.mp4"
done
