Xylomorphic Architecture Blender Generator
==========================================

This package includes a Python tool to generate Blender scene scripts inspired by the
Xylomorphic Architecture project — biomimetic urban forms integrating cellulose spires,
pulp conduits, canopy roofs, and luminous cityscapes.

Usage
-----
1. Extract the ZIP.
2. Run from terminal:
       python xylomorphic_blender_gen.py --outdir out --scenes all --render
   (Add --engine CYCLES or --res 1920x1080 as needed.)

3. Output directories:
       out/scripts/*.py   - generated Blender Python files
       out/blends/*.blend - Blender project files
       out/renders/*.png  - rendered still images

Example:
   python xylomorphic_blender_gen.py --outdir output --scenes xylomorphic_cityscape --render

Requirements
------------
- Blender 3.6+ installed and accessible as "blender" in PATH
- Python 3.8+
