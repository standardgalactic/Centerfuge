# Centerfuge headless Blender models

This suite turns the repository's central mechanisms into reproducible Blender
scenes. Each script starts from an empty file, uses a deterministic random seed,
and writes both a `.blend` file and a still PNG. The default renderer is Eevee so
the complete suite is practical on a headless machine; pass `--engine CYCLES`
for final-quality output.

The four scenes are complementary rather than alternate skins. `centerfuge_cutaway.py`
models the domestic machine, `material_sorting_vortex.py` visualizes classification
and radial routing, `hyperbolation_cognet.py` exposes the layered yarn-ball packaging
of a single material packet, and `house_distribution.py` shows the Centerfuge as the
material metabolism of a dwelling.

Run one scene from the repository root:

```bash
blender -b --python-exit-code 1 -P headless_blender/centerfuge_cutaway.py -- \
  --output output/headless --resolution 1280x1280 --seed 42
```

Render everything:

```bash
bash headless_blender/render_all.sh output/headless
```

All scripts accept `--output`, `--resolution WIDTHxHEIGHT`, `--samples`, `--seed`,
`--engine AUTO|BLENDER_EEVEE|BLENDER_EEVEE_NEXT|CYCLES`, and `--no-render`.
`AUTO` selects the Eevee identifier supplied by the installed Blender version.
The last option creates
the `.blend` scene without rendering a PNG. Additional arguments after Blender's
`--` separator belong to the scene script.

The scripts target Blender 4.0 or newer and use no external assets or add-ons.
