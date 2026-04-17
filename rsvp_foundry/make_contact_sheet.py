#!/usr/bin/env python3
"""
make_contact_sheet.py — composite a grid of seed PNGs into a contact sheet.

Reads PNG files from a batch output directory and arranges them into an NxN
grid image. No Blender required — uses only stdlib + optional Pillow.

If Pillow is not available, falls back to writing an HTML contact sheet
that any browser can display.

Usage:
    python make_contact_sheet.py [--input-dir DIR] [--output FILE]
                                  [--cols N] [--thumb-size PX]
                                  [--generator NAME]

Examples:
    python make_contact_sheet.py --input-dir ./rsvp_output --cols 4
    python make_contact_sheet.py --input-dir ./rsvp_output/tree --generator tree --cols 3
"""

from __future__ import annotations
import argparse
import glob
import json
import os
import sys
from pathlib import Path


def find_pngs(input_dir: str, generator: str | None) -> list[Path]:
    pattern = f"{input_dir}/**/*.png"
    all_pngs = sorted(Path(p) for p in glob.glob(pattern, recursive=True))
    if generator:
        all_pngs = [p for p in all_pngs if generator in p.stem]
    return all_pngs


def make_pillow_sheet(pngs: list[Path], args: argparse.Namespace) -> None:
    from PIL import Image, ImageDraw, ImageFont

    thumb = args.thumb_size
    cols = args.cols
    rows = (len(pngs) + cols - 1) // cols
    label_h = 24
    pad = 4

    W = cols * (thumb + pad) + pad
    H = rows * (thumb + label_h + pad) + pad

    sheet = Image.new("RGB", (W, H), (18, 18, 18))
    draw = ImageDraw.Draw(sheet)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
    except OSError:
        font = ImageFont.load_default()

    for i, png in enumerate(pngs):
        col = i % cols
        row = i // cols
        x = pad + col * (thumb + pad)
        y = pad + row * (thumb + label_h + pad)

        try:
            img = Image.open(png).convert("RGB")
            img.thumbnail((thumb, thumb), Image.LANCZOS)
            # Centre in cell if not square
            ix = x + (thumb - img.width) // 2
            iy = y + (thumb - img.height) // 2
            sheet.paste(img, (ix, iy))
        except Exception as e:
            draw.rectangle([x, y, x + thumb, y + thumb], outline=(80, 40, 40))
            draw.text((x + 4, y + 4), str(e)[:20], fill=(180, 60, 60), font=font)

        label = png.stem[:28]
        draw.text((x, y + thumb + 2), label, fill=(160, 160, 160), font=font)

    out = Path(args.output)
    sheet.save(out)
    print(f"[contact_sheet] {out}  ({cols}×{rows}  {len(pngs)} images  {W}×{H}px)")


def make_html_sheet(pngs: list[Path], args: argparse.Namespace) -> None:
    """Fallback: write an HTML file with inline <img> tags."""
    thumb = args.thumb_size
    cols = args.cols

    out = Path(args.output).with_suffix(".html")
    base = out.parent

    rows_html = []
    for i in range(0, len(pngs), cols):
        batch = pngs[i : i + cols]
        cells = "".join(
            f'<td style="padding:4px;background:#111;vertical-align:top">'
            f'<img src="{os.path.relpath(p, base)}" '
            f'style="max-width:{thumb}px;max-height:{thumb}px;display:block">'
            f'<div style="color:#888;font-size:10px;font-family:monospace;'
            f'word-break:break-all">{p.stem}</div></td>'
            for p in batch
        )
        rows_html.append(f"<tr>{cells}</tr>")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>RSVP Contact Sheet</title>
<style>
  body {{ background: #0a0a0a; margin: 16px; }}
  table {{ border-collapse: collapse; }}
</style>
</head>
<body>
<h2 style="color:#666;font-family:monospace">RSVP Contact Sheet — {len(pngs)} images</h2>
<table>{''.join(rows_html)}</table>
</body>
</html>"""

    out.write_text(html)
    print(f"[contact_sheet] {out}  (HTML fallback  {len(pngs)} images)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Make an rsvp contact sheet")
    parser.add_argument("--input-dir", default="./rsvp_output",
                        help="Directory to scan for PNGs")
    parser.add_argument("--output", default="contact_sheet.png",
                        help="Output image path (.png or .html for fallback)")
    parser.add_argument("--cols", type=int, default=4, help="Grid columns")
    parser.add_argument("--thumb-size", type=int, default=256, help="Thumbnail px")
    parser.add_argument("--generator", default=None,
                        help="Filter PNGs by generator name substring")
    parser.add_argument("--limit", type=int, default=64,
                        help="Max images to include")
    args = parser.parse_args()

    pngs = find_pngs(args.input_dir, args.generator)
    if not pngs:
        print(f"[contact_sheet] No PNGs found in {args.input_dir}", file=sys.stderr)
        sys.exit(1)

    if len(pngs) > args.limit:
        print(f"[contact_sheet] limiting to {args.limit} of {len(pngs)} images")
        pngs = pngs[: args.limit]

    print(f"[contact_sheet] found {len(pngs)} PNGs")

    try:
        import PIL  # noqa: F401
        make_pillow_sheet(pngs, args)
    except ImportError:
        print("[contact_sheet] Pillow not available — writing HTML fallback")
        make_html_sheet(pngs, args)


if __name__ == "__main__":
    main()
