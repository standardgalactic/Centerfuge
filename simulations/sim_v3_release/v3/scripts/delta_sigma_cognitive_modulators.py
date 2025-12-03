import bpy
import math
import random

"""Delta–Sigma Cognitive Modulators
------------------------------------
Attaches a simple 1-bit delta–sigma modulator to each CLIO edge object
(as created by clio_feedback_graph.py). The modulator state is stored in
custom properties, and edge emission is toggled according to the bitstream.

This is not a full circuit sim; it's a visual metaphor mapping prediction
error into oversampling and noise-shaped binary pulses.
"""

SCENE = bpy.context.scene
FRAMES = 180
EDGE_PREFIX = "Edge_"


def find_clio_edges():
    edges = []
    for obj in SCENE.objects:
        if obj.name.startswith(EDGE_PREFIX) and obj.type == 'CURVE':
            edges.append(obj)
    return edges


def init_modulator(edge):
    if "ds_acc" not in edge:
        edge["ds_acc"] = 0.0
    if "ds_out" not in edge:
        edge["ds_out"] = 0.0
    if "ds_error_drive" not in edge:
        # treat prediction error as random field for now
        edge["ds_error_drive"] = random.uniform(-1.0, 1.0)


def ds_update(edge):
    """First-order delta–sigma loop:

        acc[n+1] = acc[n] + input - y[n]
        y[n]     = sign(acc[n+1])

    Here input is ds_error_drive scaled; y is +/-1, stored as ds_out.
    """
    acc = float(edge["ds_acc"])
    inp = float(edge["ds_error_drive"]) * 0.3
    out = float(edge["ds_out"])

    acc_next = acc + inp - out
    if acc_next >= 0:
        y_next = 1.0
    else:
        y_next = -1.0

    edge["ds_acc"] = acc_next
    edge["ds_out"] = y_next

    # use y_next to modulate brightness of the edge
    mat = edge.active_material
    if mat and mat.use_nodes:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            intensity = 2.0 + 3.0 * max(0.0, y_next)
            bsdf.inputs["Emission Strength"].default_value = intensity

    return y_next


def run():
    edges = find_clio_edges()
    if not edges:
        raise RuntimeError("No CLIO edges found. Run clio_feedback_graph.py first.")

    for e in edges:
        init_modulator(e)

    for frame in range(1, FRAMES + 1):
        SCENE.frame_set(frame)
        for e in edges:
            y = ds_update(e)
            e.keyframe_insert(data_path='data.bevel_factor_end')  # optional channel
        # can be expanded to affect camera, nodes, etc.

    print("[DeltaSigma] Cognitive modulators animated over CLIO edges.")


if __name__ == "__main__":
    run()
