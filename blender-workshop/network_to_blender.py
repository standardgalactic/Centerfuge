import json
import bpy

PATH = bpy.path.abspath('//network_states.json')   # file saved next to the .blend
with open(PATH) as f:
    data = json.load(f)

R = data['radius']
states = data['states']
peak = max(max(row) for row in states)

coll = bpy.data.collections.new('Network_Nodes')
bpy.context.scene.collection.children.link(coll)

# One shared unit-cube mesh used as every node marker
h = 0.1
verts = [(x, y, z) for x in (-h, h) for y in (-h, h) for z in (-h, h)]
faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
         (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
mesh = bpy.data.meshes.new('Node_Marker_Mesh')
mesh.from_pydata(verts, [], faces)
mesh.update()

markers = []
for i, p in enumerate(data['pos']):
    obj = bpy.data.objects.new(f'Node_{i:02d}', mesh)
    obj.location = (R * p[0], R * p[1], R * p[2])
    obj['node_index'] = i
    coll.objects.link(obj)
    markers.append(obj)

# Marker volume proportional to stock: edge scale is the cube root of x / peak
for frame_index, row in enumerate(states):
    frame = 1 + frame_index
    for obj, x in zip(markers, row):
        s = max(x, 0.0) / peak
        s = s ** (1.0 / 3.0)
        obj.scale = (s, s, s)
        obj.keyframe_insert(data_path='scale', frame=frame)

bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = len(states)
