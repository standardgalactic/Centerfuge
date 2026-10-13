"""Does running a scene script twice in one session leave the same file as running it once?

Run with Blender's Python module (pip install bpy) or inside Blender:
    python3 idempotence_check.py /path/to/tetraorthodrome.py
The script under test is executed unchanged. The check counts datablocks, not just objects.
"""
import runpy
import sys

import bpy


def census(tag):
    mats = bpy.data.materials
    print(f"{tag:26s} objects={len(bpy.data.objects):2d} meshes={len(bpy.data.meshes):3d} "
          f"materials={len(mats):3d} orphan materials={sum(m.users == 0 for m in mats):3d}")
    return len(bpy.data.objects), len(bpy.data.meshes), len(mats)


def purge_orphans():
    """Remove meshes and then materials that nothing uses. Order matters: a mesh holds a
    user count on each of its materials, so the materials become orphans only after the
    meshes are gone."""
    for coll in (bpy.data.meshes, bpy.data.materials):
        for block in list(coll):
            if block.users == 0:
                coll.remove(block)


def run_once(path, repair):
    if repair:
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        purge_orphans()
    runpy.run_path(path)


if __name__ == '__main__':
    path = sys.argv[-1]
    for repair in (False, True):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        print('with purge before each run:' if repair else 'script unchanged:')
        history = []
        for k in range(1, 4):
            run_once(path, repair)
            history.append(census(f'  after run {k}'))
        print('  idempotent (counts equal after runs 1, 2, 3):', history[0] == history[1] == history[2])
