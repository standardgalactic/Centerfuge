# Blender as an Experimental Workshop

LaTeX textbook with the code behind its measurements.

Build the book: `latexmk -xelatex main.tex` (needs XeLaTeX and Latin Modern fonts).

Run the experiments: Blender is used as the `bpy` Python module (5.2.2 for the reported numbers), headless, EEVEE only.
Each chapter's script says its commands in its first docstring, for example `python3 world_blender.py check`.
Scripts without `_blender` in the name use only Python and NumPy (some also SciPy).

| Part | Chapters | Files |
|---|---|---|
| Prologue | synestia | `prologue.tex`, `synestia.py`, `synestia_blender.py` |
| V experiments | 15 to 19 | `ch15`..`ch19`, `occupancy*`, `branching*`, `foam*`, `transport*`, `dla*` |
| VI constructors | 20 to 23 | `scene_tools.py`, `mesh_tools.py`, `stairs*.py`, `batch.py` |
| VII persistent worlds | 24 to 27 | `world*.py`, `glb_read.py`, `export_probe.py`, `identity.py`, `solver*.py`, `coupling*.py` |
| VIII orchestration | 28 to 30 | `alternatives*.py`, `review*.py`, `degrade.py`, `ledger*.py`, `ledger.jsonl`, `capstone*.py` |

Each chapter ends by stating what its checks do not show. Results come from one machine and have not been independently reproduced.
