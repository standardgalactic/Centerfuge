import bpy

# Storage Helper v3.1
# - Clears default scene
# - Adds one camera, three lights, and a ground plane
# - Static setup for still renders

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def setup_camera():
    cam_data = bpy.data.cameras.new("FlyxionCam_v3_1")
    cam = bpy.data.objects.new("FlyxionCam_v3_1", cam_data)
    cam.location = (14.0, -14.0, 10.0)
    cam.rotation_euler = (1.1, 0.0, 0.8)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam

def add_light(name, energy, loc):
    light_data = bpy.data.lights.new(name=name, type='AREA')
    light_data.energy = energy
    light_obj = bpy.data.objects.new(name, light_data)
    light_obj.location = loc
    bpy.context.scene.collection.objects.link(light_obj)
    return light_obj

def setup_lights():
    add_light("KeyLight_v3_1", 2000.0, (10.0, -8.0, 12.0))
    add_light("FillLight_v3_1", 900.0, (-8.0, -6.0, 8.0))
    add_light("RimLight_v3_1", 1600.0, (0.0, 10.0, 10.0))

def add_ground():
    bpy.ops.mesh.primitive_plane_add(size=80.0, location=(0.0, 0.0, -2.0))
    plane = bpy.context.active_object
    plane.name = "GroundPlane_v3_1"
    mat = bpy.data.materials.new("GroundMat_v3_1")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.03, 0.03, 0.03, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.95
    plane.data.materials.append(mat)

def configure_render():
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = 32
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.frame_start = 1
    scene.frame_end = 1
    scene.render.film_transparent = False

def main():
    clear_scene()
    setup_camera()
    setup_lights()
    add_ground()
    configure_render()
    print("[Helper_v3.1] Scene initialized.")

if __name__ == "__main__":
    main()
