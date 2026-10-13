"""Chapter 20 measurements: operators versus data API, orphans, safe clearing.

    python3 ch20_probe.py ops|time|orphans|poll|clear|names
"""
import sys, time
import bpy
from scene_tools import inventory, generated_collection, clear_generated


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def ops():
    sc = fresh()
    print('before: active', bpy.context.view_layer.objects.active, 'selected', len(bpy.context.selected_objects), inv())
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(1, 2, 3))
    o = bpy.context.active_object
    print('after ops cube: active', o.name, 'selected', len(bpy.context.selected_objects), 'mesh', o.data.name, inv())
    me = bpy.data.meshes.new('Cube2'); me.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    ob = bpy.data.objects.new('Tri', me); generated_collection(sc).objects.link(ob)
    print('after data API triangle: active', bpy.context.view_layer.objects.active.name, 'selected', len(bpy.context.selected_objects), inv())
    print('collections of ops cube:', [c.name for c in o.users_collection], '; of data-API object:', [c.name for c in ob.users_collection])


def inv():
    return {k: v[0] for k, v in inventory().items() if k in ('objects', 'meshes')}


def timing():
    import statistics
    N = 300
    res = {}
    for label in ('ops', 'data'):
        ts = []
        for rep in range(5):
            sc = fresh(); coll = generated_collection(sc)
            t = time.perf_counter()
            if label == 'ops':
                for i in range(N):
                    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(i, 0, 0))
            else:
                me = bpy.data.meshes.new('Cube')
                h = 0.5
                me.from_pydata([(x, y, z) for x in (-h, h) for y in (-h, h) for z in (-h, h)], [],
                               [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
                for i in range(N):
                    o = bpy.data.objects.new('C', me); o.location = (i, 0, 0); coll.objects.link(o)
            ts.append(time.perf_counter() - t)
        res[label] = ts
        print(label, f'{N} cubes: median {statistics.median(ts)*1000:.1f} ms, min {min(ts)*1000:.1f}, max {max(ts)*1000:.1f}  per cube {statistics.median(ts)/N*1e6:.0f} us')
    print('ratio of medians', round(statistics.median(res['ops']) / statistics.median(res['data']), 1))


def orphans():
    sc = fresh(); coll = generated_collection(sc)
    me = bpy.data.meshes.new('M'); me.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    o = bpy.data.objects.new('O', me); coll.objects.link(o)
    print('with object:', inventory()['meshes'], 'mesh users', me.users)
    bpy.data.objects.remove(o)
    print('after removing the object:', inventory()['meshes'], 'mesh users', me.users, 'mesh still in bpy.data:', 'M' in bpy.data.meshes)
    print('orphans_purge available:', hasattr(bpy.data, 'orphans_purge'))
    n = bpy.data.orphans_purge(do_recursive=True)
    print('purged', n, '->', inventory()['meshes'])


def poll():
    sc = fresh()
    try:
        bpy.ops.object.mode_set(mode='EDIT')
        print('mode_set with no active object: ran')
    except RuntimeError as e:
        print('mode_set with no active object: RuntimeError:', str(e).strip().splitlines()[0][:110])
    bpy.ops.mesh.primitive_cube_add()
    bpy.ops.object.mode_set(mode='EDIT'); print('with an active object: mode', bpy.context.object.mode)
    bpy.ops.object.mode_set(mode='OBJECT')
    try:
        bpy.ops.object.delete()
        print('delete selected: ran, objects left', len(bpy.data.objects))
    except RuntimeError as e:
        print('delete:', str(e)[:100])


def clear():
    sc = fresh()
    # unrelated work the script must not touch
    me = bpy.data.meshes.new('Keep'); me.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    keep = bpy.data.objects.new('Mine', me); sc.collection.objects.link(keep)
    coll = generated_collection(sc)
    shared = bpy.data.meshes.new('Shared'); shared.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    for i in range(50):
        o = bpy.data.objects.new(f'G{i}', shared); coll.objects.link(o)
    print('before:', inventory()['objects'], inventory()['meshes'])
    clear_generated(sc)
    print('after clear_generated:', inventory()['objects'], inventory()['meshes'], '; Mine survives:', 'Mine' in bpy.data.objects and bpy.data.objects['Mine'].data.name == 'Keep')
    clear_generated(sc)
    print('second call is a no-op:', inventory()['objects'], inventory()['meshes'])
    # a generated object sharing a mesh with unrelated work must not take that mesh with it
    shared2 = bpy.data.meshes.new('Common'); shared2.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    a = bpy.data.objects.new('mine2', shared2); sc.collection.objects.link(a)
    b = bpy.data.objects.new('gen2', shared2); coll.objects.link(b)
    clear_generated(sc)
    print('shared-mesh case: Common kept', 'Common' in bpy.data.meshes, 'users', shared2.users)


def names():
    fresh()
    a = bpy.data.objects.new('Wall', None); b = bpy.data.objects.new('Wall', None); c = bpy.data.objects.new('Wall', None)
    print([a.name, b.name, c.name])
    bpy.data.objects.remove(a)
    d = bpy.data.objects.new('Wall', None)
    print('after removing the first and adding again:', d.name, '; existing:', sorted(o.name for o in bpy.data.objects))
    print('lookup by name returns', bpy.data.objects['Wall'].name == 'Wall' if 'Wall' in bpy.data.objects else 'no exact Wall')


if __name__ == '__main__':
    {'ops': ops, 'time': timing, 'orphans': orphans, 'poll': poll, 'clear': clear, 'names': names}[sys.argv[1]]()
