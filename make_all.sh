#!/usr/bin/env bash
# ==============================================================
# make_all.sh — Rebuilds the complete Tetraorthodrome project.
# Blender 4.2.x, Cycles, 180 frames default.
# Generates scripts, tools, docs, Docker, SLURM, and zips it.
# ==============================================================

set -euo pipefail
ROOT="rsvp_viz"
FRAMES_DEFAULT=180

echo "[1/8] Creating directory tree..."
mkdir -p $ROOT/{scripts/tetraorthodrome,cluster,docs,tools,data,output}

# --------------------------------------------------------------
# run_field_pipeline.sh
# --------------------------------------------------------------
cat > $ROOT/run_field_pipeline.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
YAML_FILE=${1:? "Usage: ./run_field_pipeline.sh data/lamphrodyne.yaml"}
BASENAME=$(basename "$YAML_FILE" .yaml)
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="${ROOT_DIR}/output/${BASENAME}"
SCRIPTS="${ROOT_DIR}/scripts"
DOCS="${ROOT_DIR}/docs"
mkdir -p "$OUT" "$DOCS"

echo "[1/4] Build model with Geometry Nodes / VDB (if enabled)"
blender -b -E CYCLES -P "${SCRIPTS}/generate_field_model_nodes.py" -- \
  --config "$YAML_FILE" --out "$OUT/${BASENAME}.blend"

echo "[2/4] Render animation (Cycles, MP4)"
blender -b "$OUT/${BASENAME}.blend" -E CYCLES -P "${SCRIPTS}/render_field_animation.py" -- \
  --config "$YAML_FILE" --out "$OUT"

echo "[3/4] Snapshot (PNG)"
blender -b "$OUT/${BASENAME}.blend" -E CYCLES -P "${SCRIPTS}/export_snapshot.py" -- \
  --out "$OUT/${BASENAME}.png"

echo "[4/4] Minimal Markdown doc"
cat > "${DOCS}/${BASENAME}.md" <<DOC
# ${BASENAME}
Generated from \`${YAML_FILE}\`.

Artifacts:
- Blend: \`${OUT}/${BASENAME}.blend\`
- Animation: \`${OUT}/animation.mp4\`
- Snapshot: \`${OUT}/${BASENAME}.png\`
DOC

echo "Done -> ${OUT}"
EOF
chmod +x $ROOT/run_field_pipeline.sh

# --------------------------------------------------------------
# Dockerfile (Blender 4.2.x headless, Py deps)
# --------------------------------------------------------------
cat > $ROOT/Dockerfile <<'EOF'
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04
ARG DEBIAN_FRONTEND=noninteractive
ARG BLENDER_VERSION=4.2.2
ARG BLENDER_MAJOR=4.2
RUN apt-get update && apt-get install -y --no-install-recommends \
  wget ca-certificates python3 python3-pip git ffmpeg parallel \
  libgl1 libx11-6 libxi6 libxxf86vm1 libxcursor1 libxrender1 libxrandr2 \
  && rm -rf /var/lib/apt/lists/*
WORKDIR /opt
RUN wget -q https://download.blender.org/release/Blender${BLENDER_MAJOR}/blender-${BLENDER_VERSION}-linux-x64.tar.xz && \
  tar -xf blender-${BLENDER_VERSION}-linux-x64.tar.xz && \
  ln -s /opt/blender-${BLENDER_VERSION}-linux-x64/blender /usr/local/bin/blender && \
  rm blender-${BLENDER_VERSION}-linux-x64.tar.xz
COPY tools/requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --no-cache-dir -r /tmp/requirements.txt
WORKDIR /workspace
COPY . .
RUN chmod +x run_field_pipeline.sh
ENTRYPOINT ["/bin/bash"]
EOF

# --------------------------------------------------------------
# tools/requirements.txt
# --------------------------------------------------------------
cat > $ROOT/tools/requirements.txt <<'EOF'
numpy
pyopenvdb==11.0.0 ; platform_system!="Windows"
EOF

# --------------------------------------------------------------
# cluster utilities
# --------------------------------------------------------------
cat > $ROOT/cluster/env.sh <<'EOF'
#!/usr/bin/env bash
export RSVP_IMAGE="${RSVP_IMAGE:-rsvp-blender:latest}"
export OUT_DIR="${OUT_DIR:-$PWD/output}"
export LOG_DIR="${LOG_DIR:-$PWD/output/logs}"
export SEED="${SEED:-42}"
export RUN_ID="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
mkdir -p "$OUT_DIR" "$LOG_DIR"
EOF
chmod +x $ROOT/cluster/env.sh

cat > $ROOT/cluster/provenance.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
out="$1"; shift
artifact_rel="${out#${PWD}/}"
sha256=$(sha256sum "$out" | awk '{print $1}')
size=$(stat -c%s "$out")
git_rev=$(git rev-parse --short=12 HEAD 2>/dev/null || echo "nogit")
host=$(hostname)
ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat <<JSON
{"timestamp":"${ts}","run_id":"${RUN_ID}","seed":"${SEED}","host":"${host}","git_commit":"${git_rev}","path":"${artifact_rel}","sha256":"${sha256}","bytes":${size}}
JSON
EOF
chmod +x $ROOT/cluster/provenance.sh

cat > $ROOT/cluster/slurm_job.sbatch <<'EOF'
#!/usr/bin/env bash
#SBATCH -J tetraorthodrome
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err
#SBATCH -p gpu
#SBATCH --gpus=1
#SBATCH -c 8
#SBATCH --mem=16G
#SBATCH -t 01:00:00
set -euo pipefail
source "$(dirname "$0")/env.sh"
INPUT="${INPUT:-data/lamphrodyne.yaml}"
BASE=$(basename "$INPUT" .yaml)
OUT_SCN="${OUT_DIR}/${BASE}"
mkdir -p "$OUT_SCN"
docker run --rm --gpus all -v "$PWD":/workspace -w /workspace -e SEED -e RUN_ID \
  "$RSVP_IMAGE" ./run_field_pipeline.sh "$INPUT"
MANIFEST="${OUT_SCN}/MANIFEST.jsonl"
for f in "${OUT_SCN}"/*; do
  "$(dirname "$0")/provenance.sh" "$f" >> "$MANIFEST"
done
EOF

cat > $ROOT/cluster/slurm_array.sbatch <<'EOF'
#!/usr/bin/env bash
#SBATCH -J tetra-array
#SBATCH -o logs/%x-%A_%a.out
#SBATCH -e logs/%x-%A_%a.err
#SBATCH -p gpu
#SBATCH --gpus=1
#SBATCH -c 8
#SBATCH --mem=16G
#SBATCH -t 02:00:00
#SBATCH --array=0-9
set -euo pipefail
source "$(dirname "$0")/env.sh"
mapfile -t JOBS < <(ls -1 data/*.yaml | sort)
INPUT="${JOBS[$SLURM_ARRAY_TASK_ID]}"
BASE=$(basename "$INPUT" .yaml)
OUT_SCN="${OUT_DIR}/${BASE}"
mkdir -p "$OUT_SCN"
docker run --rm --gpus all -v "$PWD":/workspace -w /workspace -e SEED -e RUN_ID \
  "$RSVP_IMAGE" ./run_field_pipeline.sh "$INPUT"
MANIFEST="${OUT_SCN}/MANIFEST.jsonl"
> "$MANIFEST"
for f in "${OUT_SCN}"/*; do
  "$(dirname "$0")/provenance.sh" "$f" >> "$MANIFEST"
done
EOF

cat > $ROOT/cluster/finalize_index.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
OUT="${1:-output}"
IDX="$OUT/INDEX.json"
git_rev=$(git rev-parse --short=12 HEAD 2>/dev/null || echo "nogit")
ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo '{ "timestamp": "'$ts'", "git_commit": "'$git_rev'", "runs": [' > "$IDX"
first=1
for MAN in $(find "$OUT" -name MANIFEST.jsonl | sort); do
  [ $first -eq 1 ] || echo ',' >> "$IDX"
  first=0
  SCN=$(basename "$(dirname "$MAN")")
  printf '  { "scene":"%s", "manifest":"%s" }' "$SCN" "${MAN#${PWD}/}" >> "$IDX"
done
echo -e '\n] }' >> "$IDX"
EOF
chmod +x $ROOT/cluster/finalize_index.sh

# --------------------------------------------------------------
# scripts: core generator, renderer, snapshot
# (Generator includes curl-noise + VDB mode)
# --------------------------------------------------------------
cat > $ROOT/scripts/generate_field_model_nodes.py <<'EOF'
# scripts/generate_field_model_nodes.py
import bpy, argparse, sys, math, os, random, yaml
from math import sin, cos, pi, exp, sqrt

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    return ap.parse_known_args(sys.argv[sys.argv.index("--")+1:])[0]

# -------- Perlin for curl-noise --------
class Perlin3D:
    def __init__(self, seed=0):
        random.seed(seed)
        self.p = list(range(256))
        random.shuffle(self.p)
        self.p = self.p*2
    @staticmethod
    def fade(t): return t*t*t*(t*(t*6-15)+10)
    @staticmethod
    def lerp(a,b,t): return a+t*(b-a)
    @staticmethod
    def grad(h,x,y,z):
        h &= 15
        u = x if h<8 else y
        v = y if h<4 else (x if h in (12,14) else z)
        return ((u if (h&1)==0 else -u) + (v if (h&2)==0 else -v))
    def noise(self,x,y,z,freq=1.0):
        x*=freq; y*=freq; z*=freq
        X=int(math.floor(x))&255; Y=int(math.floor(y))&255; Z=int(math.floor(z))&255
        x-=math.floor(x); y-=math.floor(y); z-=math.floor(z)
        u,v,w=self.fade(x),self.fade(y),self.fade(z)
        p=self.p
        A=p[X]+Y; AA=p[A]+Z; AB=p[A+1]+Z
        B=p[X+1]+Y; BA=p[B]+Z; BB=p[B+1]+Z
        return self.lerp(
            self.lerp(
              self.lerp(self.grad(p[AA],x,y,z), self.grad(p[BA],x-1,y,z), u),
              self.lerp(self.grad(p[AB],x,y-1,z), self.grad(p[BB],x-1,y-1,z), u), v),
            self.lerp(
              self.lerp(self.grad(p[AA+1],x,y,z-1), self.grad(p[BA+1],x-1,y,z-1), u),
              self.lerp(self.grad(p[AB+1],x,y-1,z-1), self.grad(p[BB+1],x-1,y-1,z-1), u), v),
            w)

def curl_noise_at(perlin, p, freq=1.0, eps=1e-3):
    x,y,z = p
    def N1(pt): return perlin.noise(pt[0],pt[1],pt[2],freq=freq)
    def N2(pt): return perlin.noise(pt[0]+31.7,pt[1]-12.3,pt[2]+7.1,freq=freq)
    def N3(pt): return perlin.noise(pt[0]-19.4,pt[1]+24.6,pt[2]-3.3,freq=freq)
    def dxf(f): return (f((x+eps,y,z))-f((x-eps,y,z)))/(2*eps)
    def dyf(f): return (f((x,y+eps,z))-f((x,y-eps,z)))/(2*eps)
    def dzf(f): return (f((x,y,z+eps))-f((x,y,z-eps)))/(2*eps)
    cx = dzf(N2)-dyf(N3)
    cy = dxf(N3)-dzf(N1)
    cz = dyf(N1)-dxf(N2)
    return (cx,cy,cz)

# -------- RSVP field evaluators --------
def eval_phi(pt, spec):
    t = spec.get("type","gaussian")
    if t=="gaussian":
        A=spec.get("amplitude",1.0); sigma=spec.get("sigma",0.6)
        cx,cy,cz = spec.get("center",[0,0,0])
        dx,dy,dz = pt[0]-cx, pt[1]-cy, pt[2]-cz
        return A*math.exp(-(dx*dx+dy*dy+dz*dz)/(2*sigma*sigma))
    if t=="radial":
        scale=spec.get("scale",1.0); r=sqrt(pt[0]**2+pt[1]**2+pt[2]**2)
        return math.exp(-scale*r)
    return 0.0

def eval_v(pt, spec):
    t=spec.get("type","swirl"); s=spec.get("strength",1.0); ax=spec.get("axis","z")
    x,y,z=pt
    if t=="swirl":
        return {"z":(-s*y, s*x, 0), "x":(0,-s*z,s*y), "y":(s*z,0,-s*x)}.get(ax,(0,0,s))
    if t=="radial":
        r=sqrt(x*x+y*y+z*z)+1e-8; return (s*x/r,s*y/r,s*z/r)
    if t=="uniform":
        return {"x":(s,0,0),"y":(0,s,0),"z":(0,0,s)}.get(ax,(0,0,s))
    return (0,0,0)

def eval_S(pt, spec):
    t=spec.get("type","radial")
    if t=="constant": return spec.get("bias",0.0)
    if t=="radial":
        scale=spec.get("scale",1.0); bias=spec.get("bias",0.0)
        r=sqrt(pt[0]**2+pt[1]**2+pt[2]**2)
        return bias+(1.0-math.exp(-scale*r))
    return 0.0

# -------- Mesh / GN construction --------
def build_base_mesh(cfg):
    m=cfg.get("mesh",{})
    base=m.get("base","sphere"); res=int(m.get("resolution",64))
    radius=float(m.get("radius",1.0))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if base=="sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=res, ring_count=max(res//2,8), radius=radius)
    elif base=="torus":
        bpy.ops.mesh.primitive_torus_add(major_segments=res, minor_segments=max(res//2,8),
                                         major_radius=radius, minor_radius=radius*0.35)
    elif base=="grid":
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=res, y_subdivisions=res, size=2*radius)
    obj=bpy.context.active_object; obj.name=cfg.get("name","RSVP_Object")
    bpy.ops.object.shade_smooth()
    return obj

def add_geometry_nodes(obj, cfg):
    ng=bpy.data.node_groups.new("RSVP_GN","GeometryNodeTree")
    mod=obj.modifiers.new(name="RSVP_GN_MOD", type='NODES')
    mod.node_group=ng
    n=ng.nodes; l=ng.links; n.clear()
    gi=n.new("NodeGroupInput"); go=n.new("NodeGroupOutput")
    gi.location=(-800,0); go.location=(800,0)
    ng.inputs.new("NodeSocketGeometry","Geometry")
    ng.outputs.new("NodeSocketGeometry","Geometry")
    n_pos=n.new("GeometryNodeInputPosition"); n_pos.location=(-600,200)
    n_norm=n.new("GeometryNodeInputNormal");  n_norm.location=(-600,-50)
    names=cfg.get("nodes",{}).get("store_attributes",{}).get("names",{})
    name_phi=names.get("phi","phi"); name_S=names.get("entropy","entropy")
    a_phi=n.new("GeometryNodeInputNamedAttribute"); a_phi.location=(-400,200)
    a_phi.data_type='FLOAT'; a_phi.inputs["Name"].default_value=name_phi
    a_S=n.new("GeometryNodeInputNamedAttribute"); a_S.location=(-400,-250)
    a_S.data_type='FLOAT'; a_S.inputs["Name"].default_value=name_S
    chain=gi

    disp_cfg=cfg.get("nodes",{}).get("displace_from_phi",{"enabled":True,"scale":0.25})
    if disp_cfg.get("enabled",True):
        setp=n.new("GeometryNodeSetPosition"); setp.location=(0,100)
        scale=n.new("ShaderNodeMath"); scale.operation='MULTIPLY'; scale.location=(-150,200)
        scale.inputs[1].default_value=float(disp_cfg.get("scale",0.25))
        l.new(a_phi.outputs["Attribute"], scale.inputs[0])
        val_out=scale.outputs["Value"]
        clamp=disp_cfg.get("clamp",None)
        if clamp and isinstance(clamp,(list,tuple)) and len(clamp)==2:
            cl=n.new("ShaderNodeClamp"); cl.location=(-10,200)
            cl.inputs["Min"].default_value=float(clamp[0]); cl.inputs["Max"].default_value=float(clamp[1])
            l.new(val_out, cl.inputs["Value"]); val_out=cl.outputs["Result"]
        mul=n.new("ShaderNodeVectorMath"); mul.operation='MULTIPLY'; mul.location=(150,100)
        l.new(n_norm.outputs["Normal"], mul.inputs[0])
        l.new(val_out, mul.inputs[1])
        l.new(gi.outputs["Geometry"], setp.inputs["Geometry"])
        l.new(n_pos.outputs["Position"], setp.inputs["Position"])
        l.new(mul.outputs["Vector"], setp.inputs["Offset"])
        chain=setp

    tw_cfg=cfg.get("nodes",{}).get("twist_from_v",{"enabled":False})
    if tw_cfg.get("enabled",False):
        a_vmag=n.new("GeometryNodeInputNamedAttribute"); a_vmag.location=(-150,-280)
        a_vmag.data_type='FLOAT'; a_vmag.inputs["Name"].default_value="v_mag"
        axis=n.new("ShaderNodeCombineXYZ"); axis.location=(60,-220)
        axis_vec={'x':(1,0,0),'y':(0,1,0),'z':(0,0,1)}.get(cfg.get("fields",{}).get("vector_v",{}).get("axis","z"),(0,0,1))
        axis.inputs["X"].default_value,axis.inputs["Y"].default_value,axis.inputs["Z"].default_value=axis_vec
        s=n.new("ShaderNodeMath"); s.operation='MULTIPLY'; s.location=(60,-120)
        s.inputs[1].default_value=float(tw_cfg.get("angle_scale",1.0))
        l.new(a_vmag.outputs["Attribute"], s.inputs[0])
        rot=n.new("GeometryNodeRotateEuler"); rot.location=(240,-100)
        rot.inputs["Space"].default_value='AXIS_ANGLE'
        l.new(axis.outputs["Vector"], rot.inputs["Axis"])
        l.new(s.outputs["Value"], rot.inputs["Angle"])
        setp2=n.new("GeometryNodeSetPosition"); setp2.location=(600,-100)
        l.new(chain.outputs["Geometry"], setp2.inputs["Geometry"])
        l.new(rot.outputs["Rotation"], setp2.inputs["Position"])
        chain=setp2

    l.new(chain.outputs["Geometry"], go.inputs["Geometry"])
    return mod, name_phi, name_S

def make_material(cfg, entropy_attr):
    mat=bpy.data.materials.new("RSVP_Mat"); mat.use_nodes=True
    nt=mat.node_tree; n=nt.nodes; l=nt.links
    for node in list(n):
        if node.type!='OUTPUT_MATERIAL': n.remove(node)
    out=[x for x in n if x.type=='OUTPUT_MATERIAL'][0]
    bsdf=n.new("ShaderNodeBsdfPrincipled"); bsdf.location=(220,0)
    attr=n.new("ShaderNodeAttribute"); attr.location=(-600,0); attr.attribute_name=entropy_attr
    ramp=n.new("ShaderNodeValToRGB"); ramp.location=(-350,0)
    preset=(cfg.get("material",{}).get("color_ramp","inferno") or "inferno").lower()
    palette={
        "inferno":[(0.0,(0.001,0.0,0.013)),(0.25,(0.144,0.019,0.233)),(0.5,(0.543,0.060,0.321)),(0.75,(0.944,0.364,0.082)),(1.0,(0.988,0.998,0.645))],
        "magma":[(0.0,(0.001,0.0,0.015)),(0.5,(0.502,0.027,0.349)),(1.0,(0.987,0.889,0.745))],
        "plasma":[(0.0,(0.050,0.030,0.527)),(0.5,(0.461,0.470,0.020)),(1.0,(0.940,0.975,0.131))],
        "viridis":[(0.0,(0.267,0.005,0.329)),(0.5,(0.128,0.566,0.551)),(1.0,(0.993,0.906,0.145))],
        "gray":[(0.0,(0,0,0)),(1.0,(1,1,1))]
    }.get(preset)
    ramp.color_ramp.elements.clear()
    for i,(pos,col) in enumerate(palette):
        el = ramp.color_ramp.elements.new(pos) if i>0 else ramp.color_ramp.elements[0]
        el.position=pos; el.color=(*col,1.0)
    emis=n.new("ShaderNodeEmission"); emis.location=(220,-200)
    emis.inputs["Strength"].default_value=float(cfg.get("material",{}).get("emission_strength",3.0))
    mix=n.new("ShaderNodeAddShader"); mix.location=(460,-60)
    l.new(attr.outputs["Fac"], ramp.inputs["Fac"])
    l.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    l.new(ramp.outputs["Color"], emis.inputs["Color"])
    l.new(bsdf.outputs["BSDF"], mix.inputs[0])
    l.new(emis.outputs["Emission"], mix.inputs[1])
    l.new(mix.outputs["Shader"], out.inputs["Surface"])
    bsdf.inputs["Roughness"].default_value=float(cfg.get("material",{}).get("base_roughness",0.25))
    return mat

def bake_attributes(obj, cfg):
    me=obj.data
    def ensure_attr(name):
        if name not in me.attributes:
            me.attributes.new(name=name, type='FLOAT', domain='POINT')
        return me.attributes[name].data
    names=cfg.get("nodes",{}).get("store_attributes",{}).get("names",{})
    a_phi=ensure_attr(names.get("phi","phi"))
    a_S=ensure_attr(names.get("entropy","entropy"))
    a_vmag=ensure_attr("v_mag"); a_cx=ensure_attr("curl_x"); a_cy=ensure_attr("curl_y"); a_cz=ensure_attr("curl_z")

    phi_spec=cfg.get("fields",{}).get("scalar_phi",{})
    v_spec=cfg.get("fields",{}).get("vector_v",{})
    S_spec=cfg.get("fields",{}).get("entropy_S",{})

    curl_cfg=cfg.get("noise",{}).get("curl",{})
    perlin=Perlin3D(seed=int(curl_cfg.get("seed",0)))
    freq=float(curl_cfg.get("frequency",1.0))
    amp=float(curl_cfg.get("amplitude",0.0))
    curl_enabled=bool(curl_cfg.get("enabled",False))

    me.calc_normals()
    for i,v in enumerate(me.vertices):
        p=(v.co.x,v.co.y,v.co.z)
        phi=eval_phi(p,phi_spec)
        vx,vy,vz=eval_v(p,v_spec); vm=sqrt(vx*vx+vy*vy+vz*vz)
        S=eval_S(p,S_spec)
        a_phi[i].value=float(phi); a_S[i].value=float(S); a_vmag[i].value=float(vm)
        if curl_enabled:
            cx,cy,cz=curl_noise_at(perlin,p,freq=freq)
            a_cx[i].value=amp*cx; a_cy[i].value=amp*cy; a_cz[i].value=amp*cz
        else:
            a_cx[i].value=a_cy[i].value=a_cz[i].value=0.0
    me.update()

def apply_curl_offset(obj):
    ng=bpy.data.node_groups.new("RSVP_CURL_GN","GeometryNodeTree")
    mod=obj.modifiers.new(name="RSVP_CURL",type='NODES'); mod.node_group=ng
    n=ng.nodes; l=ng.links; n.clear()
    gi=n.new("NodeGroupInput"); go=n.new("NodeGroupOutput")
    gi.location=(-400,0); go.location=(400,0)
    ng.inputs.new("NodeSocketGeometry","Geometry"); ng.outputs.new("NodeSocketGeometry","Geometry")
    ax=n.new("GeometryNodeInputNamedAttribute"); ay=n.new("GeometryNodeInputNamedAttribute"); az=n.new("GeometryNodeInputNamedAttribute")
    ax.location=(-200,200); ay.location=(-200,50); az.location=(-200,-100)
    ax.data_type='FLOAT'; ay.data_type='FLOAT'; az.data_type='FLOAT'
    ax.inputs["Name"].default_value="curl_x"; ay.inputs["Name"].default_value="curl_y"; az.inputs["Name"].default_value="curl_z"
    comb=n.new("ShaderNodeCombineXYZ"); comb.location=(0,100)
    l.new(ax.outputs["Attribute"], comb.inputs["X"])
    l.new(ay.outputs["Attribute"], comb.inputs["Y"])
    l.new(az.outputs["Attribute"], comb.inputs["Z"])
    pos=n.new("GeometryNodeInputPosition"); pos.location=(-200,-150)
    setp=n.new("GeometryNodeSetPosition"); setp.location=(200,0)
    l.new(gi.outputs["Geometry"], setp.inputs["Geometry"])
    l.new(pos.outputs["Position"], setp.inputs["Position"])
    l.new(comb.outputs["Vector"], setp.inputs["Offset"])
    l.new(setp.outputs["Geometry"], go.inputs["Geometry"])

def build_volume_from_vdb(cfg):
    vinfo=cfg.get("volume",{})
    path=vinfo.get("vdb_path"); grid=vinfo.get("grid","density")
    if not path or not os.path.exists(path):
        raise FileNotFoundError(f"VDB not found: {path}")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.object.volume_import(filepath=path)
    vol=bpy.context.active_object
    vol.name=cfg.get("name","RSVP_Vol")+"_VOL"
    vol.data.grids.load()
    vol.data.display.density=float(vinfo.get("density_scale",1.0))
    # simple volume emission
    mat=bpy.data.materials.new("RSVP_Vol"); mat.use_nodes=True
    nt=mat.node_tree; n=nt.nodes; l=nt.links
    for node in list(n):
        if node.type!='OUTPUT_MATERIAL': n.remove(node)
    out=[x for x in n if x.type=='OUTPUT_MATERIAL'][0]
    v=n.new("ShaderNodeVolumePrincipled"); v.location=(0,0)
    v.inputs["Emission Strength"].default_value=float(cfg.get("material",{}).get("emission_strength",3.0))
    l.new(v.outputs["Volume"], out.inputs["Volume"])
    vol.data.materials.clear(); vol.data.materials.append(mat)
    return vol

def main():
    args=parse_args()
    with open(args.config,"r") as f: cfg=yaml.safe_load(f)

    if cfg.get("volume",{}).get("enabled",False):
        _=build_volume_from_vdb(cfg)
        bpy.ops.wm.save_as_mainfile(filepath=args.out)
        return

    obj=build_base_mesh(cfg)
    _,name_phi,name_S = add_geometry_nodes(obj,cfg)
    bake_attributes(obj,cfg)
    apply_curl_offset(obj)
    mat=make_material(cfg,name_S)
    if obj.data.materials: obj.data.materials[0]=mat
    else: obj.data.materials.append(mat)

    # Scene render defaults (Cycles)
    scene=bpy.context.scene
    scene.render.engine='CYCLES'
    scene.cycles.samples=64
    bpy.ops.wm.save_as_mainfile(filepath=args.out)

if __name__=="__main__":
    main()
EOF

cat > $ROOT/scripts/render_field_animation.py <<'EOF'
# scripts/render_field_animation.py
import bpy, argparse, sys, yaml, math

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    return ap.parse_known_args(sys.argv[sys.argv.index("--")+1:])[0]

def main():
    args=parse_args()
    with open(args.config,"r") as f: cfg=yaml.safe_load(f)
    scene=bpy.context.scene
    frames=int(cfg.get("animation",{}).get("frames",180))
    scene.frame_start=1; scene.frame_end=frames
    scene.render.engine='CYCLES'
    scene.cycles.samples=64
    scene.render.fps=24
    scene.render.image_settings.file_format='FFMPEG'
    scene.render.ffmpeg.format='MPEG4'
    scene.render.ffmpeg.codec='H264'
    scene.render.ffmpeg.constant_rate_factor='HIGH'
    scene.render.filepath=f"{args.out}/animation.mp4"

    cam_radius=float(cfg.get("animation",{}).get("camera_radius",3.0))
    if not any(o.type=='CAMERA' for o in bpy.context.scene.objects):
        bpy.ops.object.camera_add(location=(cam_radius,0,cam_radius*0.7))
    cam=[o for o in bpy.context.scene.objects if o.type=='CAMERA'][0]
    scene.camera=cam

    deg=float(cfg.get("animation",{}).get("camera_orbit_degrees",360))
    for f in range(scene.frame_start, frames+1):
        t=(f-scene.frame_start)/(frames-scene.frame_start+1)
        ang=math.radians(deg)*t
        cam.location.x=cam_radius*math.cos(ang)
        cam.location.y=cam_radius*math.sin(ang)
        cam.keyframe_insert(data_path="location", frame=f)

    bpy.ops.render.render(animation=True)

if __name__=="__main__":
    main()
EOF

cat > $ROOT/scripts/export_snapshot.py <<'EOF'
# scripts/export_snapshot.py
import bpy, argparse, sys, os

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    return ap.parse_known_args(sys.argv[sys.argv.index("--")+1:])[0]

def main():
    args=parse_args()
    scene=bpy.context.scene
    scene.render.engine='CYCLES'
    scene.cycles.samples=64
    scene.render.fps=24
    scene.render.image_settings.file_format='PNG'
    scene.render.filepath=args.out
    bpy.ops.render.render(write_still=True)

if __name__=="__main__":
    main()
EOF

# --------------------------------------------------------------
# tools: NPZ→VDB and NPZ→points
# --------------------------------------------------------------
cat > $ROOT/tools/npz_to_vdb.py <<'EOF'
# tools/npz_to_vdb.py
# Usage: python npz_to_vdb.py input_fields.npz out.vdb --grid density --from phi
import argparse, numpy as np
import pyopenvdb as vdb

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("npz"); ap.add_argument("out_vdb")
    ap.add_argument("--grid", default="density")
    ap.add_argument("--from", dest="src", default="phi")
    ap.add_argument("--voxel_size", type=float, default=1.0)
    ap.add_argument("--transpose", action="store_true", help="Use if NPZ is xyz; converts to zyx")
    args=ap.parse_args()
    data=np.load(args.npz)
    if args.src not in data: raise KeyError(f"{args.src} not in {list(data.keys())}")
    arr=np.asarray(data[args.src], dtype=np.float32)
    if args.transpose:
        arr=np.transpose(arr,(2,1,0))
    grid=vdb.FloatGrid(); grid.name=args.grid
    grid.transform=vdb.createLinearTransform(voxelSize=args.voxel_size)
    vdb.tools.copyFromArray(grid, arr)
    vdb.write(args.out_vdb, grids=[grid])
    print(f"Wrote {args.out_vdb} grid={grid.name} shape={arr.shape}")
if __name__=="__main__":
    main()
EOF

cat > $ROOT/tools/npz_to_points.py <<'EOF'
# tools/npz_to_points.py
# Usage: python npz_to_points.py input_fields.npz out.ply --from phi --th 0.2 --voxel 1.0
import argparse, numpy as np

def write_ply_xyz(path, pts):
    with open(path,"w") as f:
        f.write("ply\nformat ascii 1.0\n")
        f.write(f"element vertex {len(pts)}\nproperty float x\nproperty float y\nproperty float z\nend_header\n")
        for x,y,z in pts: f.write(f"{x} {y} {z}\n")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("npz"); ap.add_argument("out_ply")
    ap.add_argument("--from", dest="src", default="phi")
    ap.add_argument("--th", type=float, default=0.2)
    ap.add_argument("--voxel", type=float, default=1.0)
    ap.add_argument("--transpose", action="store_true")
    args=ap.parse_args()
    data=np.load(args.npz)
    arr=np.asarray(data[args.src], dtype=np.float32)
    if args.transpose: arr=np.transpose(arr,(2,1,0))
    idx=np.argwhere(arr>=args.th)
    pts=idx[:, ::-1].astype(np.float32)*args.voxel
    write_ply_xyz(args.out_ply, pts)
    print(f"Wrote {args.out_ply} with {len(pts)} points")
if __name__=="__main__":
    main()
EOF

# --------------------------------------------------------------
# Tetraorthodrome 10-step bpy scripts (full)
# --------------------------------------------------------------
echo "[2/8] Writing tetraorthodrome step scripts..."

cat > $ROOT/scripts/tetraorthodrome/step_01_base_tetra.py <<'EOF'
"""
STEP 01 — Base Tetrahedron
Constructs the canonical tetrahedron frame used for all subsequent rotations.
"""
import bpy, sys, argparse
from mathutils import Vector
parser = argparse.ArgumentParser()
parser.add_argument("--out", required=True)
args, _ = parser.parse_known_args(sys.argv[sys.argv.index("--")+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
verts = [
    Vector((1, 1, 1)),
    Vector((-1, -1, 1)),
    Vector((-1, 1, -1)),
    Vector((1, -1, -1))
]
faces = [(0,1,2), (0,1,3), (0,2,3), (1,2,3)]
mesh = bpy.data.meshes.new("Tetrahedron")
mesh.from_pydata(verts, [], faces)
obj = bpy.data.objects.new("Tetrahedron", mesh)
bpy.context.collection.objects.link(obj)
bpy.ops.object.shade_smooth()
mat = bpy.data.materials.new("TetraGlow")
mat.use_nodes = True
em = mat.node_tree.nodes.new("ShaderNodeEmission")
em.inputs[0].default_value = (0.2, 0.6, 1, 1)
mat.node_tree.links.new(em.outputs[0], mat.node_tree.nodes["Material Output"].inputs[0])
obj.data.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=args.out)
EOF

cat > $ROOT/scripts/tetraorthodrome/step_02_add_axes.py <<'EOF'
"""
STEP 02 — Add Orthogonal Axes
Adds four orthogonal empties representing X, Y, Z, and diagonal D axes.
"""
import bpy, sys, argparse
parser=argparse.ArgumentParser()
parser.add_argument("--out", required=True)
args,_=parser.parse_known_args(sys.argv[sys.argv.index("--")+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
axes = {
    "X": ((1,0,0),(1,0,0,1)),
    "Y": ((0,1,0),(0,1,0,1)),
    "Z": ((0,0,1),(0,0,1,1)),
    "D": ((1,1,1),(1,1,0,1))
}
for name,(vec,col) in axes.items():
    empty=bpy.data.objects.new(f"Axis_{name}",None)
    empty.empty_display_type='ARROWS'
    empty.location=tuple(1.5*v for v in vec)
    empty.color=col
    bpy.context.collection.objects.link(empty)
bpy.ops.wm.save_as_mainfile(filepath=args.out)
EOF

cat > $ROOT/scripts/tetraorthodrome/step_03_axis_colors.py <<'EOF'
"""
STEP 03 — Axis Coloring
Creates colored cylinders along each axis to make orientation visible.
"""
import bpy, sys, argparse, math
parser=argparse.ArgumentParser()
parser.add_argument("--out", required=True)
args,_=parser.parse_known_args(sys.argv[sys.argv.index("--")+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
axes = {
    "X": ((1,0,0),(1,0.2,0.2,1),(0,math.pi/2,0)),
    "Y": ((0,1,0),(0.2,1,0.2,1),(-math.pi/2,0,0)),
    "Z": ((0,0,1),(0.2,0.2,1,1),(0,0,0))
}
for name,(loc,col,rot) in axes.items():
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2, location=(0,0,0))
    cyl=bpy.context.active_object
    cyl.rotation_euler=rot
    mat=bpy.data.materials.new(f"Mat_{name}")
    mat.use_nodes=True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=col
    cyl.data.materials.append(mat)
    bpy.context.collection.objects.link(cyl)
bpy.ops.wm.save_as_mainfile(filepath=args.out)
EOF

cat > $ROOT/scripts/tetraorthodrome/step_04_first_rotation.py <<'EOF'
"""
STEP 04 — Single Axis Rotation
Rotates tetrahedron about X-axis over N frames.
"""
import bpy, sys, argparse, math
parser=argparse.ArgumentParser()
parser.add_argument("--out", required=True)
parser.add_argument("--frames", type=int, default=180)
args,_=parser.parse_known_args(sys.argv[sys.argv.index("--")+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1, depth=1.5)
obj=bpy.context.active_object
obj.rotation_mode='XYZ'
for f in range(1, args.frames+1, 5):
    obj.rotation_euler[0]=math.radians(2*f)
    obj.keyframe_insert(data_path="rotation_euler",frame=f)
bpy.ops.wm.save_as_mainfile(filepath=args.out)
EOF

cat > $ROOT/scripts/tetraorthodrome/step_05_dual_axis_spin.py <<'EOF'
"""
STEP 05 — Dual-Axis Spin
Simultaneous rotation around X and Y axes.
"""
import bpy, sys, argparse, math
parser=argparse.ArgumentParser()
parser.add_argument("--out", required=True)
parser.add_argument("--frames", type=int, default=180)
args,_=parser.parse_known_args(sys.argv[sys.argv.index("--")+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1, depth=1.5)
obj=bpy.context.active_object
obj.rotation_mode='XYZ'
for f in range(1, args.frames+1, 5):
    obj.rotation_euler[0]=math.radians(2*f)
    obj.rotation_euler[1]=math.radians(1.5*f)
    obj.keyframe_insert(data_path="rotation_euler",frame=f)
bpy.ops.wm.save_as_mainfile(filepath=args.out)
EOF

cat > $ROOT/scripts/tetraorthodrome/step_06_full_precession.py <<'EOF'
"""
STEP 06 — Full Precession
Illustrates compound rotation through changing Euler angles (Z–Y–X order).
"""
import bpy, sys, argparse, math
parser=argparse.ArgumentParser()
parser.add_argument("--out", required=True)
parser.add_argument("--frames", type=int, default=180)
args,_=parser.parse_known_args(sys.argv[sys.argv.index("--")+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1, depth=1.5)
obj=bpy.context.active_object
obj.rotation_mode='ZYX'
for f in range(1, args.frames+1, 5):
    t=f/args.frames
    obj.rotation_euler[0]=math.radians(360*t)                # Z
    obj.rotation_euler[1]=math.radians(180*t)                # Y
    obj.rotation_euler[2]=math.radians(90*math.sin(t*2*math.pi))  # X (modulated)
    obj.keyframe_insert(data_path="rotation_euler",frame=f)
bpy.ops.wm.save_as_mainfile(filepath=args.out)
EOF

cat > $ROOT/scripts/tetraorthodrome/step_07_project_shadow.py <<'EOF'
"""
STEP 07 — Shadow Projection
Adds a ground plane and a light to visualize the tetraorthodrome's shadow.
"""
import bpy, sys, argparse
parser=argparse.ArgumentParser()
parser.add_argument("--out", required=True)
args,_=parser.parse_known_args(sys.argv[sys.argv.index("--")+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1, depth=1.5)
obj=bpy.context.active_object
bpy.ops.mesh.primitive_plane_add(size=6, location=(0,0,-1))
light=bpy.data.lights.new(name="KeyLight",type='SUN')
light.energy=3.0
lightobj=bpy.data.objects.new("KeyLight",light)
lightobj.location=(4,-4,5)
bpy.context.collection.objects.link(lightobj)
bpy.ops.wm.save_as_mainfile(filepath=args.out)
EOF

cat > $ROOT/scripts/tetraorthodrome/step_08_entropy_color_map.py <<'EOF'
"""
STEP 08 — Entropy Color Map
Applies dynamic emission color keyed to a sinusoid over time.
"""
import bpy, sys, argparse, math
parser=argparse.ArgumentParser()
parser.add_argument("--out", required=True)
parser.add_argument("--frames", type=int, default=180)
args,_=parser.parse_known_args(sys.argv[sys.argv.index("--")+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1, depth=1.5)
obj=bpy.context.active_object
mat=bpy.data.materials.new("EntropyMat")
mat.use_nodes=True
em=mat.node_tree.nodes.new("ShaderNodeEmission")
mat.node_tree.links.new(em.outputs[0],mat.node_tree.nodes["Material Output"].inputs[0])
obj.data.materials.append(mat)
for f in range(1, args.frames+1, 5):
    t=f/args.frames
    hue=t
    color=(abs(math.sin(2*math.pi*hue)),abs(math.sin(4*math.pi*hue)),abs(math.sin(6*math.pi*hue)),1)
    em.inputs[0].default_value=color
    em.inputs[1].default_value=2.0
    em.keyframe_insert(data_path="inputs[0].default_value", frame=f)
bpy.ops.wm.save_as_mainfile(filepath=args.out)
EOF

cat > $ROOT/scripts/tetraorthodrome/step_09_field_overlay.py <<'EOF'
"""
STEP 09 — Field Overlay
Adds vector arrows around the tetrahedron to suggest flow (Φ, 𝒗, S).
"""
import bpy, sys, argparse, math, random
parser=argparse.ArgumentParser()
parser.add_argument("--out", required=True)
parser.add_argument("--count", type=int, default=80)
args,_=parser.parse_known_args(sys.argv[sys.argv.index("--")+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1, depth=1.5)
core=bpy.context.active_object
core.name="TetraCore"
random.seed(42)
for i in range(args.count):
    theta=2*math.pi*random.random()
    phi=math.acos(2*random.random()-1)
    r=1.5+random.random()
    x=r*math.sin(phi)*math.cos(theta)
    y=r*math.sin(phi)*math.sin(theta)
    z=r*math.cos(phi)
    bpy.ops.mesh.primitive_cone_add(radius1=0.05, depth=0.3, location=(x,y,z))
    arrow=bpy.context.active_object
    arrow.rotation_euler=(phi,0,theta)
    mat=bpy.data.materials.new(f"ArrowMat{i}")
    mat.use_nodes=True
    col=(random.random(),0.5*random.random(),1.0-random.random()/2,1)
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=col
    arrow.data.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=args.out)
EOF

cat > $ROOT/scripts/tetraorthodrome/step_10_summary_render.py <<'EOF'
"""
STEP 10 — Summary Render
Orbits camera around the tetraorthodrome, producing a complete animation.
"""
import bpy, sys, argparse, math
parser=argparse.ArgumentParser()
parser.add_argument("--out", required=True)
parser.add_argument("--frames", type=int, default=180)
args,_=parser.parse_known_args(sys.argv[sys.argv.index("--")+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1, depth=1.5)
obj=bpy.context.active_object
obj.rotation_mode='XYZ'
for f in range(1, args.frames+1, 5):
    t=f/args.frames
    obj.rotation_euler[0]=math.radians(360*t)
    obj.rotation_euler[1]=math.radians(180*t)
    obj.rotation_euler[2]=math.radians(90*math.sin(t*2*math.pi))
    obj.keyframe_insert(data_path="rotation_euler",frame=f)
bpy.ops.object.camera_add(location=(4,0,2))
cam=bpy.context.active_object
bpy.context.scene.camera=cam
for f in range(1, args.frames+1, 5):
    ang=2*math.pi*f/args.frames
    cam.location.x=4*math.cos(ang)
    cam.location.y=4*math.sin(ang)
    cam.keyframe_insert(data_path="location",frame=f)
# basic render setup
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=64
scene.render.fps=24
scene.render.image_settings.file_format='FFMPEG'
scene.render.ffmpeg.format='MPEG4'
scene.render.ffmpeg.codec='H264'
scene.render.filepath=f"{args.out[:-6]}.mp4"
bpy.ops.render.render(animation=True)
bpy.ops.wm.save_as_mainfile(filepath=args.out)
EOF

# --------------------------------------------------------------
# docs (stub; you can paste the full A–E text later)
# --------------------------------------------------------------
echo "[3/8] Writing documentation stub..."
cat > $ROOT/docs/tetraorthodrome.md <<'EOF'
# Tetraorthodrome Construction and Rotation

This repository contains:
- Ten Blender Python scripts illustrating tetraorthodrome construction and rotation (steps 01–10).
- A headless pipeline (Geometry Nodes/VDB → Animation → Snapshot).
- Tools to convert NPZ fields to VDB or point clouds.
- Docker & SLURM configs for deterministic cluster renders.

> Replace this stub with your full manuscript (Overview + Appendices A–E).
EOF

# --------------------------------------------------------------
# Minimal example data YAML
# --------------------------------------------------------------
cat > $ROOT/data/lamphrodyne.yaml <<EOF
name: lamphrodyne
mesh: { base: sphere, resolution: 64, radius: 1.0 }
fields:
  scalar_phi: { type: gaussian, amplitude: 1.0, sigma: 0.6, center: [0,0,0] }
  vector_v: { type: swirl, strength: 0.8, axis: z }
  entropy_S: { type: radial, scale: 1.3, bias: 0.1 }
noise:
  curl:
    enabled: true
    amplitude: 0.15
    frequency: 1.2
    seed: 42
nodes:
  displace_from_phi: {enabled: true, scale: 0.25, clamp: [-0.5, 0.5]}
  twist_from_v:      {enabled: false, angle_scale: 1.0}
  store_attributes:  {enabled: true, names: {phi: phi, entropy: entropy}}
material:
  color_ramp: inferno
  emission_strength: 3.0
  base_roughness: 0.25
animation:
  frames: ${FRAMES_DEFAULT}
  camera_orbit_degrees: 360
  camera_radius: 3.0
volume:
  enabled: false
  vdb_path: "data/phi_volume.vdb"
  grid: "density"
  density_scale: 1.0
EOF

# --------------------------------------------------------------
# Helpful echo + packaging
# --------------------------------------------------------------
echo "[4/8] Project tree prepared at $ROOT/"
echo "[5/8] Packaging zip..."
zip -qr ${ROOT}.zip ${ROOT}
echo "[6/8] Created ${ROOT}.zip"

cat <<TIP

[7/8] Quick start (local):
  ./run_field_pipeline.sh data/lamphrodyne.yaml

[8/8] Tetraorthodrome storyboard (examples):
  blender -b -P scripts/tetraorthodrome/step_01_base_tetra.py -- --out output/step01.blend
  blender -b -P scripts/tetraorthodrome/step_10_summary_render.py -- --out output/step10.blend -- --frames ${FRAMES_DEFAULT}

TIP
EOF