"""Chapter 28: the review stages applied to meshes after a round trip through Blender (float32 storage, loops and polygons).

    python3 review_blender.py check
"""
import numpy as np
import bpy
import review as R


def readback(V, F):
    me = bpy.data.meshes.new('m'); me.from_pydata([tuple(v) for v in V], [], F); me.update()
    co = np.empty(len(me.vertices) * 3, dtype=np.float32); me.vertices.foreach_get('co', co)
    V2 = [tuple(float(c) for c in r) for r in co.reshape(-1, 3)]
    F2 = [tuple(p.vertices) for p in me.polygons]
    bpy.data.meshes.remove(me); return V2, F2


def check():
    same = 0; diffs = []
    for d in R.DEFECTS:
        V, F, p = R.delegate(R.SPEC, None if d == 'none' else d)
        a = R.run(V, F, p, R.STAGES[:6])[0]
        try:
            V2, F2 = readback(V, F); b = R.run(V2, F2, p, R.STAGES[:6])[0]
        except Exception as e:
            b = 'blender refused: ' + type(e).__name__
        h = R.run(*readback(V, F), p, R.STAGES[:7])[0] if b != 'format' and 'refused' not in str(b) else b
        print(f'{d:36s} python first failure: {str(a):10s} after Blender: {str(b):10s} hash stage after Blender: {h}')
        same += (a == b)
    print(f'{same} of {len(R.DEFECTS)} defects give the same first failure before and after the round trip')


if __name__ == '__main__':
    check()
