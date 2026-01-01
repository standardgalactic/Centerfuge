import bpy, math, sys, os
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import common

common.reset()
common.camera()

# Parameters (theory knobs)
a = b = c = 1.0
e1 = 0.35   # squareness (latitude)
e2 = 0.35   # squareness (longitude)

def sgn(x): return -1 if x < 0 else 1

def superquadric(theta, phi):
    ct, st = math.cos(theta), math.sin(theta)
    cp, sp = math.cos(phi), math.sin(phi)

    x = a * sgn(ct) * abs(ct)**e1 * sgn(cp) * abs(cp)**e2
    y = b * sgn(ct) * abs(ct)**e1 * sgn(sp) * abs(sp)**e2
    z = c * sgn(st) * abs(st)**e1
    return x,y,z

# Start with a UV sphere as a parameter lattice
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16)
obj = bpy.context.object

for v in obj.data.vertices:
    r = v.co.length
    theta = math.asin(v.co.z / r)
    phi = math.atan2(v.co.y, v.co.x)
    v.co[:] = superquadric(theta, phi)

# Normals
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.normals_make_consistent()
bpy.ops.object.mode_set(mode='OBJECT')

obj.data.materials.append(
    common.material("Superquadric", (0.85, 0.45, 0.25, 1))
)

out = Path(__file__).resolve().parent.parent / "out/superquadric"
common.finish(out)

