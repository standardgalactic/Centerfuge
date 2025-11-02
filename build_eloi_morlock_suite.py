#!/usr/bin/env python3
"""
Flyxion – Eloi–Morlock Vector Simulation Suite Builder (Full Geometry)
Creates a reproducible project directory with 10 full Blender .py scenes,
shell runners, Dockerfile, docs, and a zip archive.
"""

import os, json, zipfile, textwrap

ROOT = "eloi_morlock_suite"
SCRIPTS = f"{ROOT}/scripts/eloi_morlock"
DOCS = f"{ROOT}/docs"

def ensure_dirs():
    os.makedirs(SCRIPTS, exist_ok=True)
    os.makedirs(DOCS, exist_ok=True)

def write(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(content).rstrip() + "\n")

def zip_dir(path: str, outname: str):
    with zipfile.ZipFile(outname, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(path):
            for file in files:
                full = os.path.join(root, file)
                rel = os.path.relpath(full, os.path.dirname(path))
                z.write(full, rel)

def build_manifest():
    write(f"{ROOT}/MANIFEST_SCHEMA.json", json.dumps({
        "scene": "string",
        "timestamp": "ISO8601 UTC",
        "sha256": "hex",
        "seed": "int",
        "frames": "int",
        "audio_file": "string",
        "entropy_band": "string",
        "size": [1920, 1080]
    }, indent=2))

def build_dockerfile():
    write(f"{ROOT}/Dockerfile", """
    FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04
    RUN apt-get update && \\
        apt-get install -y blender ffmpeg python3-pip zip && \\
        rm -rf /var/lib/apt/lists/*
    WORKDIR /workspace
    COPY scripts/ scripts/
    COPY run_eloi_morlock_stills.sh run_eloi_morlock_stills.sh
    RUN chmod +x run_eloi_morlock_stills.sh
    ENTRYPOINT ["/bin/bash"]
    """)

def build_runner_scripts():
    write(f"{ROOT}/run_eloi_morlock_stills.sh", """
    #!/usr/bin/env bash
    set -euo pipefail
    OUT="output_stills_$(date -u +%Y%m%dT%H%M%SZ)"
    mkdir -p "$OUT"
    pushd "$(dirname "$0")" >/dev/null
    cd scripts/eloi_morlock
    SCRIPTS=(
      scene_01_eloi_day.py
      scene_02_ruins_twilight.py
      scene_03_morlock_caves.py
      scene_04_forest_scatter.py
      scene_05_ridge_overlook.py
      scene_06_valley_to_cave_threshold.py
      scene_07_relics_wireframe.py
      scene_08_biolume_grotto_closeup.py
      scene_09_split_montage_cards.py
      scene_10_manifest_card.py
    )
    for s in "${SCRIPTS[@]}"; do
      base="${s%.py}"
      echo "[RUN] $s"
      blender -b -P "$s" -- --out "../../$OUT/${base}.png" --width 1920 --height 1080 --seed 42
    done
    popd >/dev/null
    echo "[OK] Stills saved in $OUT"
    """)
    os.chmod(f"{ROOT}/run_eloi_morlock_stills.sh", 0o755)

    write(f"{ROOT}/compose_av.sh", """
    #!/usr/bin/env bash
    set -euo pipefail
    ROOTDIR="${1:-output}"
    for d in "$ROOTDIR"/scene_*; do
      [ -d "$d" ] || continue
      v="$d/visuals.mp4"
      a=$(ls "$d"/*.wav 2>/dev/null || true)
      [ -f "$v" ] && [ -f "$a" ] && {
        o="$d/composite.mp4"
        ffmpeg -hide_banner -loglevel error -i "$v" -i "$a" -c:v copy -c:a aac -b:a 192k -shortest "$o"
      }
    done
    """)
    os.chmod(f"{ROOT}/compose_av.sh", 0o755)

def build_docs():
    write(f"{DOCS}/eloi_morlock.md", """
    # Eloi vs. Morlocks — Vector Simulation Suite (Flyxion)
    Vector-aesthetic stills rendered headlessly in Blender, encoding RSVP
    semantics: Eloi (diffusive, open equilibrium) vs Morlocks (confined,
    negentropic). See Appendices for color grammar and reproducibility notes.

    **Render all stills**
    ```bash
    bash run_eloi_morlock_stills.sh
    ```
    """)

    write(f"{DOCS}/appendix_D_visual_notes.md", """
    # Appendix D — Numerical & Visual Implementation Notes
    Engine: Eevee; Freestyle outlines on; solid-color worlds (no HDRI).
    Determinism: fixed seeds; analytic camera/lights; no physics solvers.
    Geometry: planes, grids, cones, cylinders; Displace (Clouds/Musgrave/Voronoi).
    Lighting: day Sun≈3.0; twilight Area≈2000; cave Points≈60–100 (cyan).
    """)

    write(f"{DOCS}/appendix_E_cluster_provenance.md", """
    # Appendix E — Deployment & Provenance
    Dockerfile included (Ubuntu + Blender). Each still writes a JSON sidecar
    with scene name, seed, size. For clusters: run the shell runner per job.
    """)

    write(f"{DOCS}/appendix_F_color_grammar.md", """
    # Appendix F — Semantic Color Grammar (SCG)
    Eloi Zenith (+1.0)  (0.85,1.00,0.85)
    Eloi Canopy (+0.7)  (0.45,0.90,0.65)
    Eloi Sky (+0.5)     (0.55,0.95,1.00)
    Transition (0.0)    (0.25,0.35,0.45)
    Ruin Stone (-0.2)   (0.35,0.35,0.40)
    Morlock Vein (-0.5) (0.18,0.14,0.35)
    Morlock Core (-0.8) (0.10,0.05,0.20)
    Biolume (-0.9)      (0.10,1.00,0.90)
    """)

    write(f"{DOCS}/appendix_G_sound_mapping.md", """
    # Appendix G — Sound Mapping
    Pitch f(phi)=220*2^phi, amplitude=0.5(1+phi). Eloi=Lydian; Morlocks=Phrygian.
    """)

    write(f"{DOCS}/appendix_H_av_sync.md", """
    # Appendix H — AV Sync
    ffmpeg -framerate 24 -pattern_type glob -i "frames_*.png" -crf 18 -vcodec libx264 visuals.mp4
    ffmpeg -i visuals.mp4 -i scene_audio.wav -c:v copy -c:a aac -b:a 192k -shortest composite.mp4
    """)

# --- Full-geometry scene files (10) ---

SCENE_01 = r"""
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
"""

SCENE_02 = r"""
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
"""

SCENE_03 = r"""
# Scene 03 – Morlock Caves — Flyxion
import bpy, sys, argparse, math, random, json
def parse():
    ap=argparse.ArgumentParser(); ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--seed", type=int, default=13); return ap.parse_known_args(sys.argv[sys.argv.index("--")+1:])
def mc(rgba):
    m=bpy.data.materials.new("M"); m.use_nodes=True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=rgba; return m
def run(out,w,h,seed):
    random.seed(seed); bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene; sc.render.engine="BLENDER_EEVEE"
    sc.render.resolution_x=w; sc.render.resolution_y=h; sc.view_layers["View Layer"].use_freestyle=True
    sc.world.use_nodes=True; wn=sc.world.node_tree; wn.nodes.clear()
    bg=wn.nodes.new("ShaderNodeBackground"); outw=wn.nodes.new("ShaderNodeOutputWorld")
    bg.inputs[0].default_value=(0.02,0.02,0.03,1); bg.inputs[1].default_value=1.0; wn.links.new(bg.outputs[0], outw.inputs[0])
    # cave shell
    bpy.ops.mesh.primitive_uv_sphere_add(radius=20, location=(0,0,6)); shell=bpy.context.active_object
    bpy.ops.object.modifier_add(type="DISPLACE"); tx=bpy.data.textures.new("rock","NOISE")
    shell.modifiers["Displace"].texture=tx; shell.modifiers["Displace"].strength=3.0
    shell.data.materials.append(mc((0.1,0.1,0.12,1)))
    # floor
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0,0,-2)); floor=bpy.context.active_object
    floor.data.materials.append(mc((0.08,0.08,0.09,1)))
    # biolum lights
    for _ in range(80):
        bpy.ops.object.light_add(type="POINT", location=(random.uniform(-10,10),random.uniform(-10,10),random.uniform(0,10)))
        lp=bpy.context.active_object; lp.data.energy=80; lp.data.color=(0.2,0.8,1.0)
    # camera
    bpy.ops.object.camera_add(location=(12,-16,4), rotation=(math.radians(75),0,math.radians(35))); sc.camera=bpy.context.active_object
    sc.render.filepath=out; bpy.ops.render.render(write_still=True)
    with open(out.replace(".png",".json"),"w") as f: json.dump({"scene":"scene_03_morlock_caves","seed":seed,"size":[w,h]}, f, indent=2)
if __name__=="__main__":
    a,_=parse(); run(a.out,a.width,a.height,a.seed)
"""

SCENE_04 = r"""
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
"""

SCENE_05 = r"""
# Scene 05 – Ridge Overlook — Flyxion
import bpy, sys, argparse, math, random, json
def parse():
    ap=argparse.ArgumentParser(); ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--seed", type=int, default=33); return ap.parse_known_args(sys.argv[sys.argv.index("--")+1:])
def mc(rgba): m=bpy.data.materials.new("M"); m.use_nodes=True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=rgba; return m
def run(out,w,h,seed):
    random.seed(seed); bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene; sc.render.engine="BLENDER_EEVEE"; sc.view_layers["View Layer"].use_freestyle=True
    sc.render.resolution_x=w; sc.render.resolution_y=h
    sc.world.use_nodes=True; wn=sc.world.node_tree; wn.nodes.clear()
    bg=wn.nodes.new("ShaderNodeBackground"); outw=wn.nodes.new("ShaderNodeOutputWorld")
    bg.inputs[0].default_value=(0.90,0.98,1.0,1); bg.inputs[1].default_value=1.0; wn.links.new(bg.outputs[0], outw.inputs[0])
    bpy.ops.mesh.primitive_grid_add(size=100, x_subdivisions=200, y_subdivisions=200); t=bpy.context.active_object
    bpy.ops.object.modifier_add(type="DISPLACE"); tx=bpy.data.textures.new("ridge","MUSGRAVE")
    tx.noise_scale=8.0; t.modifiers["Displace"].texture=tx; t.modifiers["Displace"].strength=10.0
    t.data.materials.append(mc((0.78,0.98,0.85,1)))
    bpy.ops.object.light_add(type="SUN", location=(15,-25,50)); bpy.context.active_object.data.energy=2.5
    bpy.ops.object.camera_add(location=(-30,-50,40), rotation=(math.radians(60),0,math.radians(-10))); sc.camera=bpy.context.active_object
    sc.render.filepath=out; bpy.ops.render.render(write_still=True)
    with open(out.replace(".png",".json"),"w") as f: json.dump({"scene":"scene_05_ridge_overlook","seed":seed,"size":[w,h]}, f, indent=2)
if __name__=="__main__":
    a,_=parse(); run(a.out,a.width,a.height,a.seed)
"""

SCENE_06 = r"""
# Scene 06 – Valley→Cave Threshold — Flyxion
import bpy, sys, argparse, math, random, json
def parse():
    ap=argparse.ArgumentParser(); ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--seed", type=int, default=19); return ap.parse_known_args(sys.argv[sys.argv.index("--")+1:])
def mc(rgba): m=bpy.data.materials.new("M"); m.use_nodes=True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=rgba; return m
def run(out,w,h,seed):
    random.seed(seed); bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene; sc.render.engine="BLENDER_EEVEE"; sc.view_layers["View Layer"].use_freestyle=True
    sc.render.resolution_x=w; sc.render.resolution_y=h
    bpy.ops.mesh.primitive_plane_add(size=100, location=(0,0,-1.5)); valley=bpy.context.active_object
    valley.data.materials.append(mc((0.85,1.0,0.85,1)))
    bpy.ops.mesh.primitive_plane_add(size=100, location=(0,0,-1.6)); cave=bpy.context.active_object
    cave.data.materials.append(mc((0.08,0.09,0.1,1)))
    bpy.ops.mesh.primitive_torus_add(major_radius=12, minor_radius=2, location=(0,8,0), rotation=(math.pi/2,0,0))
    ring=bpy.context.active_object; ring.data.materials.append(mc((0.2,0.25,0.3,1)))
    bpy.ops.object.light_add(type="SUN", location=(20,-20,30)); bpy.context.active_object.data.energy=2.5
    bpy.ops.object.light_add(type="POINT", location=(0,5,5)); bpy.context.active_object.data.energy=250.0
    bpy.ops.object.camera_add(location=(-18,-30,14), rotation=(math.radians(60),0,math.radians(15))); sc.camera=bpy.context.active_object
    sc.render.filepath=out; bpy.ops.render.render(write_still=True)
    with open(out.replace(".png",".json"),"w") as f: json.dump({"scene":"scene_06_valley_to_cave_threshold","seed":seed,"size":[w,h]}, f, indent=2)
if __name__=="__main__":
    a,_=parse(); run(a.out,a.width,a.height,a.seed)
"""

SCENE_07 = r"""
# Scene 07 – City Relics Wireframe — Flyxion
import bpy, sys, argparse, math, random, json
def parse():
    ap=argparse.ArgumentParser(); ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--seed", type=int, default=5); return ap.parse_known_args(sys.argv[sys.argv.index("--")+1:])
def mc(rgba): m=bpy.data.materials.new("M"); m.use_nodes=True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=rgba; return m
def run(out,w,h,seed):
    random.seed(seed); bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene; sc.render.engine="BLENDER_EEVEE"; sc.view_layers["View Layer"].use_freestyle=True
    sc.render.resolution_x=w; sc.render.resolution_y=h
    base=mc((0.82,0.82,0.86,1))
    for i in range(32):
        x=random.uniform(-40,40); y=random.uniform(-40,40); z=random.uniform(0.2,3.0)
        bpy.ops.mesh.primitive_cube_add(size=random.uniform(2,6), location=(x,y,z/2))
        o=bpy.context.active_object; o.data.materials.append(base)
        mod=o.modifiers.new("Wire","WIREFRAME"); mod.thickness=0.03
    bpy.ops.object.camera_add(location=(0,-55,28), rotation=(math.radians(65),0,0)); sc.camera=bpy.context.active_object
    sc.render.filepath=out; bpy.ops.render.render(write_still=True)
    with open(out.replace(".png",".json"),"w") as f: json.dump({"scene":"scene_07_relics_wireframe","seed":seed,"size":[w,h]}, f, indent=2)
if __name__=="__main__":
    a,_=parse(); run(a.out,a.width,a.height,a.seed)
"""

SCENE_08 = r"""
# Scene 08 – Bioluminescent Grotto (close-up) — Flyxion
import bpy, sys, argparse, math, random, json
def parse():
    ap=argparse.ArgumentParser(); ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--seed", type=int, default=11); return ap.parse_known_args(sys.argv[sys.argv.index("--")+1:])
def emissive(name, rgba, strength=3.0):
    m=bpy.data.materials.new(name); m.use_nodes=True
    e=m.node_tree.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value=rgba; e.inputs[1].default_value=strength
    m.node_tree.links.new(e.outputs[0], m.node_tree.nodes["Material Output"].inputs[0])
    return m
def run(out,w,h,seed):
    random.seed(seed); bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene; sc.render.engine="BLENDER_EEVEE"; sc.view_layers["View Layer"].use_freestyle=True
    sc.render.resolution_x=w; sc.render.resolution_y=h
    sc.world.use_nodes=True; wn=sc.world.node_tree; wn.nodes.clear()
    bg=wn.nodes.new("ShaderNodeBackground"); outw=wn.nodes.new("ShaderNodeOutputWorld")
    bg.inputs[0].default_value=(0.01,0.01,0.015,1); bg.inputs[1].default_value=1.0; wn.links.new(bg.outputs[0], outw.inputs[0])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=14, location=(0,0,3)); shell=bpy.context.active_object
    bpy.ops.object.modifier_add(type="DISPLACE"); tx=bpy.data.textures.new("t","VORONOI")
    shell.modifiers["Displace"].texture=tx; shell.modifiers["Displace"].strength=2.0
    mwall=bpy.data.materials.new("Wall"); mwall.use_nodes=True
    mwall.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(0.08,0.08,0.09,1); shell.data.materials.append(mwall)
    glow=emissive("Glow",(0.1,1.0,0.9,1), strength=3.0)
    for _ in range(140):
        x,y,z=(random.uniform(-6,6),random.uniform(-6,6),random.uniform(-1,6))
        bpy.ops.mesh.primitive_cone_add(radius1=0.25, depth=0.6, location=(x,y,z))
        bpy.context.active_object.data.materials.append(glow)
    bpy.ops.object.camera_add(location=(7,-8,4), rotation=(math.radians(75),0,math.radians(35))); sc.camera=bpy.context.active_object
    sc.render.filepath=out; bpy.ops.render.render(write_still=True)
    with open(out.replace(".png",".json"),"w") as f: json.dump({"scene":"scene_08_biolume_grotto_closeup","seed":seed,"size":[w,h]}, f, indent=2)
if __name__=="__main__":
    a,_=parse(); run(a.out,a.width,a.height,a.seed)
"""

SCENE_09 = r"""
# Scene 09 – Split Montage Cards — Flyxion
import bpy, sys, argparse, json
def parse():
    ap=argparse.ArgumentParser(); ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080)
    return ap.parse_known_args(sys.argv[sys.argv.index("--")+1:])
def mc(rgba): m=bpy.data.materials.new("M"); m.use_nodes=True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=rgba; return m
def run(out,w,h):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene; sc.render.engine="BLENDER_EEVEE"; sc.view_layers["View Layer"].use_freestyle=True
    sc.render.resolution_x=w; sc.render.resolution_y=h
    def card(x, col):
        bpy.ops.mesh.primitive_plane_add(size=10, location=(x,0,0))
        p=bpy.context.active_object; p.data.materials.append(mc(col))
    card(-6,(0.85,1.0,0.9,1))
    card( 6,(0.07,0.1,0.12,1))
    bpy.ops.object.camera_add(location=(0,-18,0), rotation=(1.5708,0,0)); sc.camera=bpy.context.active_object
    sc.render.filepath=out; bpy.ops.render.render(write_still=True)
    with open(out.replace(".png",".json"),"w") as f: json.dump({"scene":"scene_09_split_montage_cards","size":[w,h]}, f, indent=2)
if __name__=="__main__":
    a,_=parse(); run(a.out,a.width,a.height)
"""

SCENE_10 = r"""
# Scene 10 – Manifest Card — Flyxion
import bpy, sys, argparse, json
def parse():
    ap=argparse.ArgumentParser(); ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080)
    return ap.parse_known_args(sys.argv[sys.argv.index("--")+1:])
def mc(rgba): m=bpy.data.materials.new("M"); m.use_nodes=True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=rgba; return m
def run(out,w,h):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene; sc.render.engine="BLENDER_EEVEE"; sc.view_layers["View Layer"].use_freestyle=True
    sc.render.resolution_x=w; sc.render.resolution_y=h
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0,0,0)); bpy.context.active_object.data.materials.append(mc((0.95,0.95,0.98,1)))
    bpy.ops.object.camera_add(location=(0,-12,0), rotation=(1.5708,0,0)); sc.camera=bpy.context.active_object
    sc.render.filepath=out; bpy.ops.render.render(write_still=True)
    with open(out.replace(".png",".json"),"w") as f: json.dump({"scene":"scene_10_manifest_card","size":[w,h]}, f, indent=2)
if __name__=="__main__":
    a,_=parse(); run(a.out,a.width,a.height)
"""

def build_scenes():
    write(f"{SCRIPTS}/scene_01_eloi_day.py", SCENE_01)
    write(f"{SCRIPTS}/scene_02_ruins_twilight.py", SCENE_02)
    write(f"{SCRIPTS}/scene_03_morlock_caves.py", SCENE_03)
    write(f"{SCRIPTS}/scene_04_forest_scatter.py", SCENE_04)
    write(f"{SCRIPTS}/scene_05_ridge_overlook.py", SCENE_05)
    write(f"{SCRIPTS}/scene_06_valley_to_cave_threshold.py", SCENE_06)
    write(f"{SCRIPTS}/scene_07_relics_wireframe.py", SCENE_07)
    write(f"{SCRIPTS}/scene_08_biolume_grotto_closeup.py", SCENE_08)
    write(f"{SCRIPTS}/scene_09_split_montage_cards.py", SCENE_09)
    write(f"{SCRIPTS}/scene_10_manifest_card.py", SCENE_10)

def main():
    ensure_dirs()
    build_manifest()
    build_dockerfile()
    build_runner_scripts()
    build_docs()
    build_scenes()
    zip_dir(ROOT, f"{ROOT}.zip")
    print(f"[Flyxion] Built full suite → {ROOT}.zip")
    print(f"Render headless stills:\n  cd {ROOT} && bash run_eloi_morlock_stills.sh")

if __name__ == "__main__":
    main()
