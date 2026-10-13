"""Probe what the headless suite's two checks establish. Uses the suite's own functions unchanged."""
import sys, math
sys.path.insert(0,'/home/claude/standardgalactic/centerfuge/headless_blender')
import bpy, numpy as np
from mathutils import Vector
import common

def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene

def cam_at(loc, target=(0,0,0)):
    c=common.add_camera(loc, target, 50); bpy.context.view_layer.update(); return c

def vis(cam, objs, thr=0.0):
    return common.verify_visibility(cam, objs, min_fraction=thr)['objects']

# A. one sphere, nothing else: self-hits count as visible, so far-side vertices pass
sc=fresh(); s=common.sphere('S',1.0,(0,0,0),common.material('m',common.PALETTE['cyan']))
cam=cam_at((0,-6,0)); bpy.context.view_layer.update()
r=vis(cam,[s])['S']; 
cosines=[ (Vector(v.co)@Vector((0,-1,0))) for v in s.data.vertices]
print('A. lone sphere: fraction counted visible =', round(r['fraction'],2),
      '| fraction of ALL vertices facing the camera =', round(np.mean([c>0 for c in cosines]),2))

# B. object behind the camera
sc=fresh(); t=common.sphere('T',0.5,(0,-12,0),common.material('m',common.PALETTE['cyan']))
cam=cam_at((0,-6,0),(0,0,0)); bpy.context.view_layer.update()
print('B. sphere behind the camera: fraction counted visible =', round(vis(cam,[t])['T']['fraction'],2))

# C. an opaque wall with the target hidden behind it -> fails; wall with hide_render=True still blocks
sc=fresh(); m=common.material('m',common.PALETTE['cyan'])
tgt=common.sphere('Target',0.5,(0,0,0),m)
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,-3,0)); wall=bpy.context.object; wall.scale=(4,0.2,4); wall.name='Wall'
cam=cam_at((0,-8,0)); bpy.context.view_layer.update()
print('C1. target behind opaque wall: fraction =', round(vis(cam,[tgt])['Target']['fraction'],2))
wall.hide_render=True; bpy.context.view_layer.update()
print('C2. same wall with hide_render=True (absent from the render): fraction =', round(vis(cam,[tgt])['Target']['fraction'],2))
wall.hide_render=False
wall.data.materials.append(common.material('glass',(1,1,1,1),alpha=0.05)); bpy.context.view_layer.update()
print('C3. same wall given a nearly transparent material: fraction =', round(vis(cam,[tgt])['Target']['fraction'],2))

# D. the spoke case from the cutaway: endpoints lie inside neighbouring objects
sc=fresh(); m=common.material('m',common.PALETTE['cyan'])
ring=common.torus('Ring',2.0,0.09,(0,0,0),m); spindle=common.cylinder('Spindle',0.34,5.0,(0,0,0),m)
spoke=common.curve('Spoke',((0,0,0),(2.0,0,0)),m,0.035)
cam=cam_at((8,-8,3)); bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get()
for label,p in (('inner end',Vector((0,0,0))),('outer end',Vector((2,0,0))),('midpoint',Vector((1,0,0)))):
    o=cam.matrix_world.translation.copy(); d=(p-o); dist=d.length; d.normalize()
    ok,loc,n,i,hit,mat=sc.ray_cast(dg,o+d*1e-4,d,distance=dist*0.999)
    print(f'D. spoke {label:9s}: first object along the ray = {hit.name if ok else None}')
print('D. fraction reported for the spoke (endpoints only):', vis(cam,[spoke])['Spoke'])

# E. image check on synthetic images, using the suite's own function
from PIL import Image
def img_test(name, arr):
    path=f'/tmp/claude-0/-home-claude/927989f5-bbd5-524c-a738-cde2187a9709/scratchpad/hb/{name}.png'
    Image.fromarray(arr.astype(np.uint8),'RGB').save(path)
    try:
        r=common.verify_image_not_degenerate(path); return f"pass (stddev {r['stddev']:.1f})"
    except RuntimeError as e: return 'FAIL ('+str(e).split('(stddev=')[1].split(')')[0]+')' if 'stddev=' in str(e) else 'FAIL'
H=W=256
yy,xx=np.mgrid[0:H,0:W]
rng=np.random.default_rng(0)
noise=rng.integers(0,256,(H,W,3))
stripes=np.zeros((H,W,3)); stripes[...,1]=np.where((xx//16)%2==0,255,0)  # green stripes only
red_stripes=np.zeros((H,W,3)); red_stripes[...,0]=np.where((xx//16)%2==0,255,0)
blank=np.full((H,W,3),30)
cyan_on_dark=np.zeros((H,W,3)); cyan_on_dark[...]=[8,10,15]; cyan_on_dark[96:160,96:160]=[8,191,255]
print('E1. uniform dark frame           :', img_test('blank',blank))
print('E2. random noise (no scene at all):', img_test('noise',noise))
print('E3. strong green stripes, R=0     :', img_test('gstripes',stripes))
print('E4. same stripes in the red channel:', img_test('rstripes',red_stripes))
print('E5. cyan square on near-black     :', img_test('cyan',cyan_on_dark))
