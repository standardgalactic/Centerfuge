# Centerfuge headless Blender models

This suite turns the repository's central mechanisms into reproducible Blender
scenes. Each script starts from an empty file, uses a deterministic random seed,
and writes both a `.blend` file and a still PNG. The default renderer is Eevee so
the complete suite is practical on a headless machine; pass `--engine CYCLES`
for final-quality output.

The seven scenes are complementary rather than alternate skins:

- `intake_geometry.py` — the presentation/quarantine chamber and its
  four-way admission decision (ADMIT/DIVERT/AUDIT/REFUSE).
- `centerfuge_cutaway.py` — the domestic machine's rotor stack, an actual
  cutaway through an open-wedge housing.
- `material_sorting_vortex.py` — classification and radial routing.
- `internal_routing.py` — gated ducts carrying labeled fractions out of the
  separation core, also a real cutaway.
- `hyperbolation_cognet.py` — the layered yarn-ball packaging of a single
  material packet, an exploded view.
- `maintenance_access.py` — the USER/TRAINED/PROTECTED_REPLACE_ONLY service
  boundary, read directly from `safety/service-maintenance.json`.
- `house_distribution.py` — the Centerfuge as the material metabolism of a
  dwelling.

Run one scene from the repository root:

```bash
blender -b --python-exit-code 1 -P headless_blender/centerfuge_cutaway.py -- \
  --output output/headless --resolution 1280x1280 --seed 42
```

Render everything and admit the result:

```bash
bash headless_blender/render_all.sh output/headless
```

`render_all.sh` requires Blender and regenerates every scene; it is the only
step that does. Checking whether a previously rendered output directory is
complete and passing does **not** require Blender at all:

```bash
python3 headless_blender/check_manifest.py output/headless
```

This is the supported check for CI or deployment: it reads
`output/headless/manifest.json` and the file listing only, and fails loudly
if a scene is missing, an expected output file is absent, or a required
verification result was never recorded. It never shells out to `blender` or
installs anything, so routine checks never carry the cost of a full Blender
setup; only an explicit `render_all.sh` (or a direct `blender -P` invocation)
does that.

## Provenance and verification

Every scene's `finish()` call writes a provenance record to
`<output>/manifest.json` — the exact generator, git commit, render
parameters, output paths, and verification results — before printing success.
Two verifications run automatically:

- **Fail-loud (`common.verify_image_not_degenerate`)**: the rendered PNG must
  exist and have pixel variance above a threshold, so a scene that silently
  renders a blank frame (dead lighting, wrong camera, transparent scene)
  still fails the build instead of reporting success.
- **Non-occlusion (`common.verify_visibility`)**: scenes that claim a
  "cutaway" or interior view (`centerfuge_cutaway.py`, `internal_routing.py`)
  ray-cast from the camera to their tagged interior objects and fail if too
  few are actually reachable through the housing's structural opening — this
  is what distinguishes a real cutaway from an opaque shell that merely
  isn't in the way of one camera angle. Tag roles with `common.tag_role` and
  build the open shell with `common.open_cylindrical_housing` if you add
  another interior-claiming scene, and add it to
  `check_manifest.py`'s `REQUIRES_VISIBILITY_CHECK`.

## Style presets

All scenes read colors from the module-level `PALETTE` dict in `common.py`,
which `begin()` populates from `common.STYLE_PRESETS[args.style]` (default
`"original"`, the palette this suite has always used). Add a new named entry
to `STYLE_PRESETS` before wiring up a `--style` value other than `original`;
this keeps images rendered under `"original"` comparable across later
stylistic changes instead of drifting with whatever `PALETTE` currently
contains.

All scripts accept `--output`, `--resolution WIDTHxHEIGHT`, `--samples`, `--seed`,
`--engine AUTO|BLENDER_EEVEE|BLENDER_EEVEE_NEXT|CYCLES`, `--style`, and
`--no-render`. `AUTO` selects the Eevee identifier supplied by the installed
Blender version. `--no-render` creates the `.blend` scene without rendering a
PNG (and skips the image verification, since there is no image to check).
Additional arguments after Blender's `--` separator belong to the scene script.

The scripts target Blender 4.0 or newer and use no external assets or add-ons.
