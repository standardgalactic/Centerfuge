
# Scene 04 – Forest Scatter — Flyxion
import bpy, sys, argparse, math, random, json
def parse():
    ap=argparse.ArgumentParser(); ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--seed", type=int, default=21); ap.add_argument("--count", type=int, default=600)
    return ap.parse_known_args(sys.argv[sys.argv.index("--")+1:])
def mc(rgba): m=bpy.data.materials.new("M"); m.use_nodes=True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=rgba; return m
def run(out,w,h,seed,count):
    random.seed(seed); bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene; sc.render.engine="BLENDER_EEVEE"; sc.view_layers["View Layer"].use_freestyle=True
    sc.render.resolution_x=w; sc.render.resolution_y=h
    bpy.ops.mesh.primitive_plane_add(size=120); g=bpy.context.active_object
    bpy.ops.object.modifier_add(type="SUBSURF"); g.modifiers["Subdivision"].levels=5
    bpy.ops.object.modifier_add(type="DISPLACE"); tx=bpy.data.textures.new("h","MUSGRAVE")
    g.modifiers["Displace"].texture=tx; g.modifiers["Displace"].strength=8.0; g.location.z=-3
    g.data.materials.append(mc((0.82,0.98,0.85,1)))
    # prototype tree
    bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=1.6, location=(0,0,0.8)); trunk=bpy.context.active_object
    trunk.data.materials.append(mc((0.35,0.2,0.15,1)))
    bpy.ops.mesh.primitive_cone_add(radius1=0.9, depth=2.4, location=(0,0,2.0)); crown=bpy.context.active_object
    crown.data.materials.append(mc((0.0,0.9,0.4,1)))
    coll=bpy.data.collections.new("Trees"); bpy.context.scene.collection.children.link(coll)
    for _ in range(count):
        dx,dy=(random.uniform(-50,50),random.uniform(-50,50))
        t= bpy.data.objects.new("Trunk", trunk.data); c=bpy.data.objects.new("Crown", crown.data)
        s=random.uniform(0.6,1.3); t.location=(dx,dy,0.8); c.location=(dx,dy,2.0); t.scale=c.scale=(s,s,s)
        coll.objects.link(t); coll.objects.link(c)
    bpy.ops.object.camera_add(location=(28,-40,24), rotation=(math.radians(65),0,math.radians(25))); sc.camera=bpy.context.active_object
    sc.render.filepath=out; bpy.ops.render.render(write_still=True)
    with open(out.replace(".png",".json"),"w") as f: json.dump({"scene":"scene_04_forest_scatter","seed":seed,"count":count,"size":[w,h]}, f, indent=2)
if __name__=="__main__":
    a,_=parse(); run(a.out,a.width,a.height,a.seed,a.count)
