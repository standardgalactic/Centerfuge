import bpy
import mathutils
import math
import random

"""HYDRA Persona Field
---------------------------------
Builds on an existing RSVP lattice collection (e.g. 'RSVP_Lattice_v2' or v3)
and instantiates multiple 'personas' as agent fields that read/write custom
properties on the lattice nodes.
Each persona has:
  - a color
  - a preferred direction in Φ, v, S space
  - a simple update rule projected onto the scene as trails.

Workflow:
  1. Run your lattice generator first (e.g. rsvp_lattice_fields_v2/v3).
  2. Run this script to inject HYDRA agents and keyframe a short animation.
"""

SCENE = bpy.context.scene
LATTICE_COLLECTION_NAME = SCENE.get("RSVP_collection", "RSVP_Lattice_v2")
FRAMES = 120
DT = 0.1

# Persona configuration
PERSONA_CONFIG = [
    {"name": "Seer",      "color": (0.6, 0.9, 1.0, 1.0), "phi_bias": +1.0, "entropy_bias": -0.3},
    {"name": "Engineer",  "color": (0.7, 1.0, 0.6, 1.0), "phi_bias": +0.3, "entropy_bias": +0.1},
    {"name": "Archivist", "color": (1.0, 0.8, 0.5, 1.0), "phi_bias": -0.2, "entropy_bias": +0.6},
    {"name": "Trickster", "color": (1.0, 0.3, 0.6, 1.0), "phi_bias":  0.0, "entropy_bias": +1.0},
]


def get_lattice_collection():
    coll = bpy.data.collections.get(LATTICE_COLLECTION_NAME)
    if coll is None:
        raise RuntimeError(f"Lattice collection '{LATTICE_COLLECTION_NAME}' not found.")
    return coll


def sample_node_objects(coll):
    # only nodes tagged as RSVP nodes, or fallback to all mesh objects
    nodes = [obj for obj in coll.objects if obj.type == 'MESH' and obj.get("is_rsvp_node", False)]
    if not nodes:
        nodes = [obj for obj in coll.objects if obj.type == 'MESH']
    if not nodes:
        raise RuntimeError("No mesh nodes found in lattice collection.")
    return nodes


def ensure_persona_collection():
    name = "HYDRA_Personas"
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def create_persona_object(cfg, origin):
    name = f"HYDRA_{cfg['name']}"
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, location=origin)
    obj = bpy.context.active_object
    obj.name = name
    obj["persona_name"] = cfg["name"]
    obj["phi_bias"] = cfg["phi_bias"]
    obj["entropy_bias"] = cfg["entropy_bias"]

    mat = bpy.data.materials.new(f"Mat_{name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Emission"].default_value = cfg["color"]
    bsdf.inputs["Emission Strength"].default_value = 8.0
    obj.data.materials.append(mat)
    return obj


def pick_random_node(nodes):
    return random.choice(nodes)


def persona_step(persona, node):
    """Move persona slightly towards nodes satisfying its bias:
    - high or low phi depending on phi_bias
    - high entropy depending on entropy_bias
    Also draw a small trail segment representing its trajectory.
    """
    phi = float(node.get("phi", 0.0))
    S = float(node.get("entropy", 0.0))
    weight = phi * persona["phi_bias"] + S * persona["entropy_bias"]

    node_loc = node.location
    agent = persona["object"]
    direction = (node_loc - agent.location)
    if direction.length > 0:
        direction.normalize()

    step_size = 0.08 + 0.03 * max(0.0, weight)
    agent.location += direction * step_size * DT

    # optional: subtle vertical jitter to visualize exploration
    agent.location.z += 0.01 * math.sin(weight)

    # keyframe
    agent.keyframe_insert(data_path="location")

    # trail
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.06, location=agent.location)
    trail = bpy.context.active_object
    trail.name = f"HYDRA_trail_{persona['cfg']['name']}"
    trail_mat = agent.data.materials[0]
    trail.data.materials.append(trail_mat)


def run():
    lattice = get_lattice_collection()
    nodes = sample_node_objects(lattice)
    personas_coll = ensure_persona_collection()

    # seed persona positions near center of lattice
    center = mathutils.Vector((0.0, 0.0, 0.0))
    personas = []
    for cfg in PERSONA_CONFIG:
        obj = create_persona_object(cfg, center)
        for c in obj.users_collection:
            c.objects.unlink(obj)
        personas_coll.objects.link(obj)
        personas.append({"cfg": cfg, "object": obj})

    # animate
    for frame in range(1, FRAMES + 1):
        bpy.context.scene.frame_set(frame)
        for persona in personas:
            node = pick_random_node(nodes)
            persona_step(persona, node)

    print("[HYDRA] Persona field animation complete.")


if __name__ == "__main__":
    run()
