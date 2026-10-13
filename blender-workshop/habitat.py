"""The Chapter 3 habitat as data: platform, four walls with a gap in the south wall, and a plinth.

    python3 habitat.py       (Blender's Python module; builds both entrance variants and checks the construction)

Dimensions are those of Chapter 3. The platform top is at z = 0 and spans [-3, 3] in x and y; walls are 0.2 thick
and 2.5 high; the north wall is 6 long, the east and west walls 5.6 long, and the south wall is two blocks that
leave a gap [g0, g1] in x. The roof is absent. The plinth is 0.8 x 0.8 x 0.5.
"""
import bpy
from mathutils import Vector

ENTRANCES = {'centre': (-0.6, 0.6), 'east': (1.6, 2.8)}
PLINTH = {'xy': (-1.0, 1.0), 'size': (0.8, 0.8, 0.5)}
T, H = 0.2, 2.5


def box(name, centre, dims, coll):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=centre)
    o = bpy.context.active_object
    o.name = name
    o.scale = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for c in o.users_collection:
        c.objects.unlink(o)
    coll.objects.link(o)
    return o


def build(entrance='centre', scene=None):
    scene = scene or bpy.context.scene
    coll = bpy.data.collections.new('Habitat')
    scene.collection.children.link(coll)
    g0, g1 = ENTRANCES[entrance]
    box('Platform', (0, 0, -0.2), (6.0, 6.0, 0.4), coll)
    box('Wall_North', (0, 2.9, H / 2), (6.0, T, H), coll)
    box('Wall_East', (2.9, 0, H / 2), (T, 5.6, H), coll)
    box('Wall_West', (-2.9, 0, H / 2), (T, 5.6, H), coll)
    box('Wall_South_West', ((-3.0 + g0) / 2, -2.9, H / 2), (g0 + 3.0, T, H), coll)
    box('Wall_South_East', ((g1 + 3.0) / 2, -2.9, H / 2), (3.0 - g1, T, H), coll)
    px, py = PLINTH['xy']
    sx, sy, sz = PLINTH['size']
    box('Plinth', (px, py, sz / 2), (sx, sy, sz), coll)
    bpy.context.view_layer.update()
    return coll, (g0, g1)


def check():
    for ent in ENTRANCES:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        coll, (g0, g1) = build(ent)
        objs = {o.name: o for o in coll.objects}
        def bounds(o):
            vs = [o.matrix_world @ v.co for v in o.data.vertices]
            return [(min(v[i] for v in vs), max(v[i] for v in vs)) for i in range(3)]
        top = max(bounds(o)[2][1] for n, o in objs.items() if n == 'Platform')
        wall_zs = {n: bounds(o)[2] for n, o in objs.items() if n.startswith('Wall')}
        gap = bounds(objs['Wall_South_East'])[0][0] - bounds(objs['Wall_South_West'])[0][1]
        print(f'{ent:6s}: objects {len(objs)}, platform top z {top:.3f}, walls z-range {sorted(set((round(a,3), round(b,3)) for a, b in wall_zs.values()))}, '
              f'south gap {gap:.3f} (intended {g1 - g0:.3f}), east wall x {bounds(objs["Wall_East"])[0]}, '
              f'east/west length {bounds(objs["Wall_East"])[1][1] - bounds(objs["Wall_East"])[1][0]:.2f}')
        # the walls close the room: the inner faces meet without overlap or gap
        n, s = bounds(objs['Wall_North'])[1][0], bounds(objs['Wall_South_West'])[1][1]
        e = bounds(objs['Wall_East'])[1]
        print(f'        east wall y-range {e[0]:.2f}..{e[1]:.2f}; north wall inner face y {n:.2f}; south wall inner face y {s:.2f}')


if __name__ == '__main__':
    check()
