import bpy
import math

"""Storage Helper v3
----------------------
- Clears default scene
- Adds cinematic camera path (orbit)
- Three-point lighting
- Neutral ground plane
- Default render settings
"""

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()


def setup_camera_with_orbit():
    cam_data = bpy.data.cameras.new("FlyxionCam_v3")
    cam = bpy.data.objects.new("FlyxionCam_v3", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    cam.location = (8, -8, 6)
    cam.rotation_euler = (1.1, 0, 0.9)

    # orbit empty
    empty = bpy.data.objects.new("CamOrbit", None)
    empty.location = (0, 0, 0)
    bpy.context.scene.collection.objects.link(empty)

    cam.parent = empty

    # animate orbit
    frames = 180
    for f in range(1, frames + 1):
        bpy.context.scene.frame_set(f)
        angle = 2 * math.pi * (f - 1) / frames
        empty.rotation_euler[2] = angle
        empty.keyframe_insert(data_path="rotation_euler")

    return cam, empty


def add_light(name, energy, loc):
    light_data = bpy.data.lights.new(name=name, type='AREA')
    light_data.energy = energy
    light_obj = bpy.data.objects.new(name, light_data)
    light_obj.location = loc
    bpy.context.scene.collection.objects.link(light_obj)
    return light_obj


def setup_lights():
    add_light("KeyLight_v3", 2000, (6, -5, 7))
    add_light("FillLight_v3", 900, (-5, -3, 4))
    add_light("RimLight_v3", 1600, (-1, 7, 7))


def add_ground():
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -3))
    plane = bpy.context.active_object
    plane.name = "GroundPlane_v3"
    mat = bpy.data.materials.new("GroundMat_v3")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.03, 0.03, 0.03, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.95
    plane.data.materials.append(mat)


def configure_render():
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = 64
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.frame_start = 1
    scene.frame_end = 180
    scene.render.film_transparent = False


def main():
    clear_scene()
    setup_camera_with_orbit()
    setup_lights()
    add_ground()
    configure_render()
    print("[Helper_v3] Scene initialized.")


if __name__ == "__main__":
    main()
