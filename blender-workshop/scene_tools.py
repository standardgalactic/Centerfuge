"""Chapter 20: inspect a scene and keep generated content in one removable collection."""
import bpy

GEN = 'Generated'


def inventory():
    """Counts of data-blocks by type, with how many have no users (orphans)."""
    out = {}
    for attr in ('objects', 'meshes', 'materials', 'collections', 'cameras', 'lights', 'images', 'node_groups'):
        blocks = getattr(bpy.data, attr)
        out[attr] = (len(blocks), sum(1 for b in blocks if b.users == 0))
    return out


def generated_collection(scene):
    """The one collection that scripts may fill and clear; created on first use and linked to the scene."""
    coll = bpy.data.collections.get(GEN)
    if coll is None:
        coll = bpy.data.collections.new(GEN)
        scene.collection.children.link(coll)
    return coll


def clear_generated(scene):
    """Remove only the objects in the generated collection, and the meshes that only they used."""
    coll = generated_collection(scene)
    meshes = {o.data for o in coll.objects if o.type == 'MESH'}
    for o in list(coll.objects):
        bpy.data.objects.remove(o)
    for me in meshes:
        if me.users == 0:
            bpy.data.meshes.remove(me)
