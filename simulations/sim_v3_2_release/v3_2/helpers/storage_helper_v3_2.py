import bpy

# Storage Helper v3.2
# Static camera/lights/ground for still renders

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def setup_camera():
    cam_data = bpy.data.cameras.new("FlyxionCam_v3_2")
    cam = bpy.data.objects.new("FlyxionCam_v3_2", cam_data)
    cam.location = (16.0, -16.0, 11.0)
    cam.rotation_euler = (1.15, 0.0, 0.85)
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
    add_light("KeyLight_v3_2", 2600.0, (12.0, -9.0, 14.0))
    add_light("FillLight_v3_2", 1100.0, (-10.0, -7.0, 9.0))
    add_light("RimLight_v3_2", 1900.0, (0.0, 12.0, 11.0))

def add_ground():
    bpy.ops.mesh.primitive_plane_add(size=90.0, location=(0.0, 0.0, -2.5))
    plane = bpy.context.active_object
    plane.name = "GroundPlane_v3_2"
    mat = bpy.data.materials.new("GroundMat_v3_2")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.03, 0.03, 0.04, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.96
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
    print("[Helper_v3.2] Scene initialized.")

if __name__ == "__main__":
    main()
