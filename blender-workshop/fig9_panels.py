"""Four presentations of one geometry (the habitat with the east entrance), for Figure 9.1."""
import math, bpy
from mathutils import Vector
from presentations import scene_setup, flat_material, assign, make_camera
from arrangement_scene import diffuse_material, emission_material


def lights(sc):
    """Ambient world light only, so that no hard shadow decides what a panel appears to show."""
    bg = sc.world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.9, 0.92, 1.0, 1)
    bg.inputs['Strength'].default_value = 0.75


def solid(sc, coll):
    mats = {'wall': diffuse_material('Wall', (200, 195, 185), 0.8), 'floor': diffuse_material('Floor', (150, 135, 110), 0.9),
            'plinth': diffuse_material('Plinth', (0, 114, 178), 0.5)}
    for o in coll.objects:
        assign(o, mats['floor'] if o.name == 'Platform' else mats['plinth'] if o.name == 'Plinth' else mats['wall'])


def render(sc, name, w=600, h=450, samples=32):
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.eevee.taa_render_samples = samples
    sc.view_settings.view_transform = 'Standard'
    sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = f'figs/fig9_{name}.png'
    bpy.ops.render.render(write_still=True)


def panel(which):
    sc, coll, (g0, g1) = scene_setup('east')
    lights(sc); solid(sc, coll)
    if which == 'plan':
        make_camera(sc, (0, 0, 12), (0, 0, 0), ortho=6.4); render(sc, 'plan', 450, 450)
    elif which == 'eye':
        make_camera(sc, ((g0 + g1) / 2, -2.9, 1.6), (math.pi / 2, 0, 0), lens=18); render(sc, 'eye')
    elif which == 'cut':
        cutter = bpy.data.objects.new('Cutter', bpy.data.meshes.new('Cutter'))
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(3.0, -3.0, 1.6)); c = bpy.context.active_object
        c.scale = (6.0, 6.0, 3.2); bpy.ops.object.transform_apply(scale=True)
        c.display_type = 'WIRE'; c.hide_render = True
        for o in coll.objects:
            if o.name.startswith('Wall'):
                m = o.modifiers.new('Cut', 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.object = c; m.solver = 'EXACT'
        cam = make_camera(sc, (8.0, -9.0, 8.0), (0, 0, 0)); cam.data.lens = 40
        cam.rotation_euler = (-cam.location).to_track_quat('-Z', 'Y').to_euler()
        render(sc, 'cut')
    elif which == 'wire':
        mat = emission_material('Wire', (230, 230, 230))
        for o in coll.objects:
            assign(o, mat)
            m = o.modifiers.new('W', 'WIREFRAME'); m.thickness = 0.03; m.use_replace = True
        cam = make_camera(sc, (7.0, -9.0, 6.0), (0, 0, 0)); cam.data.lens = 35
        cam.rotation_euler = (-cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.0
        render(sc, 'wire')


if __name__ == '__main__':
    import sys
    for w in sys.argv[1:]:
        panel(w)
