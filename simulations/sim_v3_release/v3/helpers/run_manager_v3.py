import bpy
import sys
import importlib.util
import os

"""Run Manager v3
-------------------
Usage pattern (from bash):

    blender -b --python helpers/storage_helper_v3.py \\
            --python helpers/run_manager_v3.py -- \\
            --script scripts/hydra_persona_field.py \\
            --output /path/to/output.blend

Responsibilities:
  - load target script provided by --script
  - execute it after helper has configured the scene
  - optionally save .blend (if --output provided)
"""


def run_script(path):
    name = os.path.splitext(os.path.basename(path))[0]
    print(f"[RunManager_v3] Loading script: {name}")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    print(f"[RunManager_v3] Finished executing: {name}")


def main(argv):
    script_path = None
    blend_out = None

    if "--script" in argv:
        i = argv.index("--script")
        if i + 1 < len(argv):
            script_path = argv[i + 1]

    if "--output" in argv:
        i = argv.index("--output")
        if i + 1 < len(argv):
            blend_out = argv[i + 1]

    if not script_path:
        print("[RunManager_v3] No --script provided, nothing to run.")
        return

    run_script(script_path)

    if blend_out:
        print(f"[RunManager_v3] Saving blend to: {blend_out}")
        bpy.ops.wm.save_mainfile(filepath=blend_out)


if __name__ == "__main__":
    # Blender passes its own args; look for separator '--'
    if "--" in sys.argv:
        idx = sys.argv.index("--")
        user_argv = sys.argv[idx + 1:]
    else:
        user_argv = []
    main(user_argv)
