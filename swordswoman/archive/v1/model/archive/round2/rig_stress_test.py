"""Rig stress test (edge-stretch + leg/skirt penetration), round 2.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P model/rig_stress_test.py [-- --out DIR]

For each test pose: max edge-length ratio vs rest (max(r, 1/r)) per mesh (Subsurf/Solidify off,
Armature on), and a penetration count: leg vertices that lie OUTSIDE the skirt_outer surface
while above the skirt hem at that azimuth would mean a poke-through (approximate test by ray).
Writes stress.json + stress_<pose>.png (3/4 view) to DIR (default renders/model_round_2/stress).
Same conventions as the TA's round-1 test (/tmp/ta/stress.py): FK tests switch leg/arm IK off.
"""
import bpy, json, math, os, sys
from mathutils import Vector as V, Quaternion, Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[argv.index("--out") + 1] if "--out" in argv else os.path.join(ROOT, "renders", "model_round_2", "stress")
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "character.blend"))
sc = bpy.context.scene
rig = bpy.data.objects["rig"]
cam = bpy.data.objects["cam"]
meshes = [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render]


def mods(on):
    for o in meshes:
        for m in o.modifiers:
            if m.type in ("SOLIDIFY", "SUBSURF"):
                m.show_viewport = on


def evcos(o):
    dg = bpy.context.evaluated_depsgraph_get()
    e = o.evaluated_get(dg)
    m = e.to_mesh()
    cos = [v.co.copy() for v in m.vertices]
    edges = [tuple(ed.vertices) for ed in m.edges]
    polys = [tuple(p.vertices) for p in m.polygons]
    e.to_mesh_clear()
    return cos, edges, polys


def reset():
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
    for k, v in {"ik_leg.L": 1, "ik_leg.R": 1, "ik_arm.L": 0, "ik_arm.R": 0, "two_hand": 0}.items():
        rig[k] = float(v)
    for k in list(rig.keys()):
        if k.startswith("expr_"):
            rig[k] = 0.0
    rig.update_tag()
    bpy.context.view_layer.update()


def action(name):
    reset()
    rig.animation_data.action = bpy.data.actions[f"pose_{name}"]
    sc.frame_set(1)
    bpy.context.view_layer.update()


def rot(b, axis, deg):
    pb = rig.pose.bones[b]
    pb.rotation_mode = "XYZ"
    e = [0, 0, 0]
    e["XYZ".index(axis)] = math.radians(deg)
    pb.rotation_euler = e


def fk():
    for k in ("ik_leg.L", "ik_leg.R", "ik_arm.L", "ik_arm.R"):
        rig[k] = 0.0
    rig.update_tag()


mods(False)
reset()
rest = {o.name: evcos(o) for o in meshes}


def penetration():
    """Leg vertices (thigh/knee region, z > hem) that are outside the deformed skirt_outer."""
    so = bpy.data.objects["skirt_outer"]
    cos, _, polys = evcos(so)
    bvh = BVHTree.FromPolygons(cos, polys)
    n = 0
    for side in ("L", "R"):
        lc, _, _ = evcos(bpy.data.objects[f"leg.{side}"])
        for p in lc[::3]:
            # cast from the hip axis outward through p: if the skirt is hit beyond p, p is inside
            c = V((0, 0, p.z)) if p.z > 0.55 else None
            if c is None:
                continue
            d = (p - c)
            if d.length < 1e-4:
                continue
            hit = bvh.ray_cast(c, d.normalized(), 3.0)
            if hit[0] is not None and (hit[0] - c).length + 0.005 < d.length:
                # skirt surface between axis and the leg vertex: leg is outside the skirt there
                # only counts if the vertex is above the local hem (i.e. it should be covered)
                n += 1
    return n


def test(label):
    bpy.context.view_layer.update()
    res, p99, stretch = {}, {}, {}
    for o in meshes:
        cos, edges, _ = evcos(o)
        rc, re, _ = rest[o.name]
        if len(cos) != len(rc):
            continue
        mx = 1.0
        st = 1.0
        allr = []
        for a, b in re:
            l0 = (rc[a] - rc[b]).length
            if l0 < 1e-5:
                continue
            r = (cos[a] - cos[b]).length / l0
            q = max(r, 1 / r if r > 0 else 99)
            mx = max(mx, q)
            st = max(st, r)
            allr.append(q)
        allr.sort()
        res[o.name] = round(mx, 2)
        p99[o.name] = round(allr[int(len(allr) * 0.99)] if allr else 1.0, 2)
        stretch[o.name] = round(st, 2)
    for d in (res, p99, stretch):
        d.pop("face_decals", None)      # shape-key decals collapse by design (lids) - not skinning
    worst = sorted(res.items(), key=lambda x: -x[1])[:5]
    pen = penetration()
    arm = lambda d: max(v for k, v in d.items() if k.split(".")[0] in ("arm", "sleeve", "hand"))
    print(f"{label:16s} pen={pen:3d} arm/sleeve max={arm(res)} p99={arm(p99)} stretch={arm(stretch)} | "
          + " ".join(f"{n}:{m}" for n, m in worst))
    return dict(worst_maxratio=worst, penetration_samples=pen, arms_sleeves_maxratio=arm(res),
                arms_sleeves_p99=arm(p99), arms_sleeves_max_stretch=arm(stretch),
                p99_all=sorted(p99.items(), key=lambda x: -x[1])[:5],
                max_stretch_all=sorted(stretch.items(), key=lambda x: -x[1])[:5])


R = {}
for nm in ("sword_ready", "walk_contact", "run_stride", "jump_apex", "overhead"):
    action(nm)
    R[nm] = test(nm)
    rig.animation_data.action = None
reset(); fk(); rot("thigh.L", "X", 60); rot("thigh.R", "X", -45); rot("shin.R", "X", 70); R["fk_run_stride"] = test("fk_run_stride")
reset(); fk(); rot("upper_arm.L", "X", 150); rot("upper_arm.R", "X", 150); R["fk_arms_overhead"] = test("fk_arms_overhead")
reset(); fk(); rot("upper_arm.L", "Z", 80); rot("upper_arm.R", "Z", -80); R["fk_arms_T"] = test("fk_arms_T")
reset(); fk(); rot("spine", "X", 30); rot("chest", "X", 20); rot("head", "X", -20); R["fk_bend_fwd"] = test("fk_bend_fwd")
reset(); fk(); rot("thigh.L", "X", 90); rot("thigh.R", "X", 90); rot("shin.L", "X", -100); rot("shin.R", "X", -100)
R["fk_jump_tuck"] = test("fk_jump_tuck")
json.dump(R, open(os.path.join(OUT, "stress.json"), "w"), indent=1)

# images of the FK stress poses (3/4 front-left, low)
mods(True)
for m in [mm for o in meshes for mm in o.modifiers if mm.name == "Outline"]:
    m.thickness = 0.006
el = math.radians(8)
cam.data.ortho_scale = 3.8
cam.rotation_euler = (math.pi / 2 - el, 0, math.radians(40))
d = V((math.sin(math.radians(40)) * math.cos(el), -math.cos(math.radians(40)) * math.cos(el), math.sin(el)))
cam.location = V((0, 0, 1.4)) + d * 20
sc.render.resolution_x = sc.render.resolution_y = 512
for label, setup in (
        ("fk_run_stride", lambda: (fk(), rot("thigh.L", "X", 60), rot("thigh.R", "X", -45), rot("shin.R", "X", 70))),
        ("fk_jump_tuck", lambda: (fk(), rot("thigh.L", "X", 90), rot("thigh.R", "X", 90), rot("shin.L", "X", -100),
                                  rot("shin.R", "X", -100))),
        ("fk_arms_overhead", lambda: (fk(), rot("upper_arm.L", "X", 150), rot("upper_arm.R", "X", 150))),
        ("fk_arms_T", lambda: (fk(), rot("upper_arm.L", "Z", 80), rot("upper_arm.R", "Z", -80)))):
    reset()
    setup()
    bpy.context.view_layer.update()
    sc.render.filepath = os.path.join(OUT, f"stress_{label}.png")
    bpy.ops.render.render(write_still=True)
print("[stress] wrote", OUT)
