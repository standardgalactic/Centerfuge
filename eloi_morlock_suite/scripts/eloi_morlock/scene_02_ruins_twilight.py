
# Scene 02 – Ruins Twilight — Flyxion
import bpy, sys, argparse, math, random, json
def parse():
    ap=argparse.ArgumentParser(); ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--seed", type=int, default=7); return ap.parse_known_args(sys.argv[sys.argv.index("--")+1:])
def mc(rgba):
    m=bpy.data.materials.new("M"); m.use_nodes=True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=rgba; return m
def run(out,w,h,seed):
    random.seed(seed); bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene; sc.render.engine="BLENDER_EEVEE"
    sc.render.resolution_x=w; sc.render.resolution_y=h; sc.view_layers["View Layer"].use_freestyle=True
    sc.world.use_nodes=True; wn=sc.world.node_tree; wn.nodes.clear()
    bg=wn.nodes.new("ShaderNodeBackground"); outw=wn.nodes.new("ShaderNodeOutputWorld")
    bg.inputs[0].default_value=(0.25,0.28,0.35,1); bg.inputs[1].default_value=1.0; wn.links.new(bg.outputs[0], outw.inputs[0])
    # ground
    bpy.ops.mesh.primitive_plane_add(size=80); g=bpy.context.active_object
    bpy.ops.object.modifier_add(type="SUBSURF"); g.modifiers["Subdivision"].levels=5
    bpy.ops.object.modifier_add(type="DISPLACE"); tx=bpy.data.textures.new("d","MUSGRAVE")
    g.modifiers["Displace"].texture=tx; g.modifiers["Displace"].strength=4.0; g.location.z=-1.3
    g.data.materials.append(mc((0.2,0.25,0.22,1)))
    # arches & columns
    stone=mc((0.7,0.7,0.75,1))
    def arch(x,y,rot=0):
        bpy.ops.mesh.primitive_torus_add(major_radius=2.5, minor_radius=0.25, location=(x,y,3), rotation=(math.pi/2,0,rot))
        r=bpy.context.active_object; r.data.materials.append(stone)
        for dz in (0,1.5,3):
            bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=3, location=(x-2.4,y,1.5+dz)); bpy.context.active_object.data.materials.append(stone)
            bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=3, location=(x+2.4,y,1.5+dz)); bpy.context.active_object.data.materials.append(stone)
    for i in range(5):
        arch(-15+i*8, random.uniform(-10,10), rot=random.uniform(0,math.pi/3))
    # ferns
    fern=mc((0.0,0.7,0.4,1))
    for _ in range(140):
        bpy.ops.mesh.primitive_cone_add(radius1=0.8, depth=0.2, location=(random.uniform(-35,35),random.uniform(-35,35),0.05))
        bpy.context.active_object.data.materials.append(fern)
    # light & camera
    bpy.ops.object.light_add(type="AREA", location=(0,-10,12)); L=bpy.context.active_object; L.data.energy=2000; L.data.size=12
    bpy.ops.object.camera_add(location=(0,-28,10), rotation=(math.radians(65),0,0)); sc.camera=bpy.context.active_object
    sc.render.filepath=out; bpy.ops.render.render(write_still=True)
    with open(out.replace(".png",".json"),"w") as f: json.dump({"scene":"scene_02_ruins_twilight","seed":seed,"size":[w,h]}, f, indent=2)
if __name__=="__main__":
    a,_=parse(); run(a.out,a.width,a.height,a.seed)
