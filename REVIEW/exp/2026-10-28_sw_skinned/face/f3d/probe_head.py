# probe_head.py (F round 5): front map of the rest head in the head-bone frame -> face/f3d/probe.json + probe.png
# For a grid over head-local (x lateral, y along the bone), ray-cast along -Z_head (from her front) onto the rest body:
# material colour (matid 'Color'), hit z (head-local), normal.  Used to place the face texture art on the real skin area.
import bpy, json, os, sys
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
ao = bpy.data.objects["rig"]; body = bpy.data.objects["body"]
for p in ao.pose.bones: p.rotation_mode = "QUATERNION"; p.rotation_quaternion = (1, 0, 0, 0); p.location = (0, 0, 0)
ao.rotation_euler = (0, 0, 0); bpy.context.view_layer.update()
H = ao.matrix_world @ ao.data.bones["head"].matrix_local; Hi = H.inverted(); R3 = H.to_3x3()
dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
ev = body.evaluated_get(dg); me = ev.data; col = me.color_attributes.get("Color")
S = 128; X0, X1, Y0, Y1 = -0.16, 0.16, -0.10, 0.30
mats = []; zs = []
for j in range(S):
    row = []; zr = []
    for i in range(S):
        x = X0 + (X1 - X0) * (i + .5) / S; y = Y1 - (Y1 - Y0) * (j + .5) / S
        o = H @ Vector((x, y, 0.5)); d = (R3 @ Vector((0, 0, -1))).normalized()
        hit, p, n, fi, ob, _ = sc.ray_cast(dg, o, d)
        if not hit or ob is None or ob.name != "body": row.append(None); zr.append(None); continue
        ph = Hi @ p; poly = ev.data.polygons[fi]
        c = col.data[poly.loop_indices[0]].color if col.domain == "CORNER" else col.data[poly.vertices[0]].color
        lin = lambda u: u * 12.92 if u <= 0.0031308 else 1.055 * u ** (1 / 2.4) - 0.055
        row.append([int(round(lin(c[k]) * 255)) for k in range(3)]); zr.append(round(ph.z, 4))
    mats.append(row); zs.append(zr)
fa = json.load(open(os.path.join(os.path.dirname(os.path.dirname(HERE)), "rig", "face_anchors.json")))["anchors"]
anc = {k: [round(c, 4) for c in (Hi @ Vector(v["surf"]))] for k, v in fa.items()}
json.dump({"box": [X0, X1, Y0, Y1], "S": S, "mat": mats, "z": zs, "anchors_head_local": anc, "head_matrix": [list(r) for r in H]}, open(os.path.join(HERE, "probe.json"), "w"))
print("PROBE_DONE", anc, col.domain)
