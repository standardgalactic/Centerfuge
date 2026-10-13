"""Write down what a render depends on, so that a later render can be compared with it.

    python3 render_record.py      (Blender's Python module; records the scene of arrangement_scene.build)
"""
import hashlib, json, math, bpy


def record(scene):
    cam = scene.camera
    d = cam.data
    return {
        'blender': bpy.app.version_string,
        'engine': scene.render.engine,
        'resolution': [scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage],
        'samples': scene.eevee.taa_render_samples,
        'view_transform': scene.view_settings.view_transform,
        'look': scene.view_settings.look,
        'exposure': scene.view_settings.exposure,
        'camera': {'type': d.type, 'lens_mm': d.lens, 'sensor_mm': d.sensor_width, 'ortho_scale': d.ortho_scale,
                   'location': [round(c, 6) for c in cam.location], 'rotation': [round(c, 6) for c in cam.rotation_euler]},
        'lights': {o.name: [o.data.type, round(o.data.energy, 3)] for o in scene.objects if o.type == 'LIGHT'},
    }


def digest(rec):
    return hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()[:12]


if __name__ == '__main__':
    from arrangement_scene import build
    sc, cam, markers, info = build('source')
    r1 = record(sc)
    print(json.dumps(r1, indent=1))
    d1 = digest(r1)
    sc.eevee.taa_render_samples = 16
    d2 = digest(record(sc))
    sc.eevee.taa_render_samples = 64
    print('digest', d1, '-> after changing samples to 16:', d2, '; a second reading of the unchanged scene agrees:', digest(record(sc)) == digest(record(sc)))
