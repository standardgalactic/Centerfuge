
# Scene 01 – Eloi Day (vector valley) — Flyxion
import bpy, sys, argparse, math, random, json
def parse():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--seed", type=int, default=42)
    return ap.parse_known_args(sys.argv[sys.argv.index("--")+1:])
def semantic_color(phi):
    table=[(1.0,(0.85,1.00,0.85,1.0)),(0.7,(0.45,0.90,0.65,1.0)),
           (0.5,(0.55,0.95,1.00,1.0)),(0.0,(0.25,0.35,0.45,1.0))]
    phi=max(0.0,min(1.0,phi))
    for (a,ca),(b,cb) in zip(table[:-1],table[1:]):
        if b<=phi<=a:
            t=(phi-b)/(a-b)
            return tuple((1-t)*ca[i]+t*cb[i] for i in range(4))
    return table[-1][1]
def mat_color(name, rgba):
    m=bpy.data.materials.new(name); m.use_nodes=True
    bsdf=m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value=rgba
    bsdf.inputs["Roughness"].default_value=0.2
    return m
def run(out,w,h,seed):
    random.seed(seed); bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene; sc.render.engine="BLENDER_EEVEE"
    sc.render.resolution_x=w; sc.render.resolution_y=h
    sc.view_layers["View Layer"].use_freestyle=True
    # World
    sc.world.use_nodes=True; nt=sc.world.node_tree; nt.nodes.clear()
    bg=nt.nodes.new("ShaderNodeBackground"); outw=nt.nodes.new("ShaderNodeOutputWorld")
    bg.inputs[0].default_value=(0.96,0.98,1.0,1); bg.inputs[1].default_value=1.0
    nt.links.new(bg.outputs[0], outw.inputs[0])
    # Terrain
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0,0,0))
    ground=bpy.context.active_object
    bpy.ops.object.modifier_add(type="SUBSURF"); ground.modifiers["Subdivision"].levels=6
    bpy.ops.object.modifier_add(type="DISPLACE"); tex=bpy.data.textures.new("terrain","CLOUDS")
    ground.modifiers["Displace"].texture=tex; ground.modifiers["Displace"].strength=4.0
    ground.location.z=-1.5; ground.data.materials.append(mat_color("EloiGround", semantic_color(0.85)))
    # Trees
    def add_tree(x,y,h=6,r=0.9):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=h*0.35, location=(x,y,h*0.175))
        trunk=bpy.context.active_object; trunk.data.materials.append(mat_color("Trunk",(0.35,0.2,0.15,1)))
        bpy.ops.mesh.primitive_cone_add(radius1=r, depth=h*0.65, location=(x,y,h*0.65))
        crown=bpy.context.active_object; crown.data.materials.append(mat_color("Canopy", semantic_color(0.75)))
    for _ in range(120):
        x,y=(random.uniform(-30,30), random.uniform(-30,30))
        if (x*x+y*y)**0.5<7: continue
        add_tree(x,y,h=random.uniform(4,8), r=random.uniform(0.6,1.2))
    # Light & camera
    bpy.ops.object.light_add(type="SUN", location=(12,-10,30))
    bpy.context.active_object.data.energy=3.0
    bpy.ops.object.camera_add(location=(22,-35,18), rotation=(math.radians(65),0,math.radians(25)))
    sc.camera=bpy.context.active_object
    sc.render.filepath=out; bpy.ops.render.render(write_still=True)
    with open(out.replace(".png",".json"),"w") as f: json.dump({"scene":"scene_01_eloi_day","seed":seed,"size":[w,h]}, f, indent=2)
if __name__=="__main__":
    a,_=parse(); run(a.out,a.width,a.height,a.seed)
