# f_render.py (F, round 3) -- faceless head pass + per-frame 3D face anchors, without touching R's renderer.
#   <blender> -b rig/rig.blend -P face/f_render.py -- motion/<act>.json <view> <outdir> [--preview] [--frames=a:b] [--anchors-only]
# 1. swaps the in-memory pixels of R's projection texture rig/tex/tex_<V>.png for face/tex/tex_<V>_nf.png (the master with the face
#    features erased), then runs R's render/render_motion.py with KINDS=tex --no-post (or --preview -> pv), so the head pass carries the
#    master hair/skin but no baked face: <outdir>/<act>_<V>_fNN_tex.png (8x) or _pv.png (preview).
# 2. face anchors: every m96 anchor pixel (face/parts.json: eye.i iris centre, brow.i, mouth, cheek.i, nose) is ray-cast from the view
#    camera onto the REST head surface, stored in the head bone's rest frame, and per frame re-posed with the head bone matrix and
#    projected through the same camera -> <outdir>/<act>_<V>_face.json:
#    {view, yaw, align, anchors_rest:{name:[x,y]} (128-cell sprite px), frames:[{i, anchors:{name:{xy, depth, facing}}, head:{yaw, pitch, roll}}]}
#    xy = 128-cell sprite coords (x192 - 32 + align.dx), same frame as the pixel grid; depth = camera distance (m); facing = n . to_cam.
import bpy, sys, os, json, math
from mathutils import Vector, Matrix
argv = sys.argv[sys.argv.index("--") + 1:]
HERE = os.path.dirname(os.path.abspath(__file__)); EXP = os.path.dirname(HERE)
pos = [x for x in argv if not x.startswith("--")]; flags = [x for x in argv if x.startswith("--")]
MOT, VIEW, OUT = pos[:3]
PREVIEW = "--preview" in flags; AONLY = "--anchors-only" in flags
os.makedirs(OUT, exist_ok=True)
AL = json.load(open(os.path.join(EXP, "rig", "align.json")))
PARTS = json.load(open(os.path.join(HERE, "parts.json")))
_CJ = os.path.join(HERE, "calib.json")
CAL = json.load(open(_CJ)) if os.path.exists(_CJ) else {}
# ---- 1. faceless texture in memory (R's file on disk is untouched)
for v in ("S", "SE", "E", "NE", "N"):
    p = os.path.join(EXP, "rig", "tex", f"tex_{v}.png"); q = os.path.join(HERE, "tex", f"tex_{v}_nf.png")
    if v != VIEW or not os.path.exists(q): continue
    im = bpy.data.images.load(p, check_existing=True); nf = bpy.data.images.load(q)
    im.pixels[:] = nf.pixels[:]; im.update(); im.pack()
    bpy.data.images.remove(nf)
src = open(os.path.join(EXP, "render", "render_motion.py")).read()
os.environ["KINDS"] = "tex"
rargs = [MOT, VIEW, OUT] + (["--preview"] if PREVIEW else []) + [f for f in flags if f.startswith("--frames=")] + ["--no-post"]
if AONLY: rargs += ["--frames=0:0"]
sys.argv = [sys.argv[0], "--"] + rargs
G = {"__name__": "__main__", "__file__": os.path.join(EXP, "render", "render_motion.py")}
exec(compile(src, G["__file__"], "exec"), G)
sc, cam, ao, pbs, apply, frames, CELL = G["sc"], G["cam"], G["ao"], G["pbs"], G["apply"], G["frames"], G["CELL"]
idxs = list(range(len(frames)))
fr_flag = next((f.split("=")[1] for f in flags if f.startswith("--frames=")), None)
if fr_flag: a_, b_ = fr_flag.split(":"); idxs = idxs[int(a_ or 0):int(b_) if b_ else None]
from bpy_extras.object_utils import world_to_camera_view
al = AL.get(VIEW, {"dx": 0, "dy": 0}); DX, DY = int(al["dx"]), int(al["dy"])
cam_dir = (cam.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized(); to_cam = -cam_dir


def proj(p):
    co = world_to_camera_view(sc, cam, p)
    return [co.x * CELL - 32 + DX, (1 - co.y) * CELL - 32 + DY], co.z


def ray_origin(x, y):
    u, v = (x + 32 - DX) / CELL, (y + 32 - DY) / CELL
    tr, br, bl, tl = cam.data.view_frame(scene=sc)
    X = tl + (tr - tl) * u + (bl - tl) * v
    return cam.matrix_world @ Vector((X.x, X.y, 0.0))


def head_m():
    return ao.matrix_world @ pbs["head"].matrix


apply({"bones": {}})
dg = bpy.context.evaluated_depsgraph_get()
H0 = head_m(); H0i = H0.inverted()
pview = PARTS.get(VIEW)
if pview is None:   # NE/N/W...: use the nearest drawn view's anchors (face hidden or partial)
    pview = PARTS["SE" if VIEW in ("NE",) else "S"]
loc = {}
cal = CAL.get(VIEW if VIEW in PARTS else ("SE" if VIEW == "NE" else "S"), {"dx": 0, "dy": 0})
TO = (cal["dx"], cal["dy"])   # rendered head vs master offset (face/calib.json)
for n, a in pview.items():
    x, y = a["xy"][0] + TO[0], a["xy"][1] + TO[1]; o = ray_origin(x, y)
    hit, p, nrm, fi, ob, _ = sc.ray_cast(dg, o, cam_dir)
    if not hit:   # rare hull holes: nearest hit within 1.5 px, else the eye's depth along the same ray
        for ddx, ddy in ((0.5, 0), (-0.5, 0), (0, 0.5), (0, -0.5), (1, 0), (-1, 0), (0, 1), (0, -1), (1.5, 0), (-1.5, 0)):
            hit, p2, nrm, fi, ob, _ = sc.ray_cast(dg, ray_origin(x + ddx, y + ddy), cam_dir)
            if hit:
                p = p2 + (o - ray_origin(x + ddx, y + ddy)); break
    if not hit:
        ref = next((loc[k] for k in ("eye.0", "eye.1") if k in loc), None)
        if ref is None: print("FACE_ANCHOR_MISS", n); continue
        t = (H0 @ ref["p"] - o).dot(cam_dir); p = o + cam_dir * t; nrm = H0.to_3x3() @ ref["n"]; ob = None
        print("FACE_ANCHOR_FALLBACK", n)
    back, _ = proj(p)
    loc[n] = {"p": H0i @ p, "n": (H0i.to_3x3() @ nrm).normalized(), "err": [back[0] - x, back[1] - y], "obj": ob.name if ob else None}
print("FACE_ANCHORS", {n: [round(c, 3) for c in l["p"]] for n, l in loc.items()}, flush=True)
fwd0 = H0.to_3x3() @ Vector((0, 0, 1)); up0 = H0.to_3x3() @ Vector((0, 1, 0))


def ang_h(v):
    return math.degrees(math.atan2(v.x, v.y))


out = {"view": VIEW, "yaw": G["YAW"], "align": {"dx": DX, "dy": DY}, "preview": PREVIEW, "scale": G["SC"],
       "tex_off": list(TO), "anchors_rest": {n: [pview[n]["xy"][0] + TO[0], pview[n]["xy"][1] + TO[1]] for n in loc}, "fit_err": {n: [round(e, 3) for e in l["err"]] for n, l in loc.items()},
       "anchors_head_local_m": {n: [round(c, 5) for c in l["p"]] for n, l in loc.items()}, "frames": []}
for i in (idxs if not AONLY else list(range(len(frames)))):
    apply(frames[i]); Hm = head_m(); R3 = Hm.to_3x3()
    A = {}
    for n, l in loc.items():
        p = Hm @ l["p"]; nn = (R3 @ l["n"]).normalized(); xy, z = proj(p)
        A[n] = {"xy": [round(xy[0], 3), round(xy[1], 3)], "depth": round(z, 4), "facing": round(nn.dot(to_cam), 4)}
    fwd = (R3 @ Vector((0, 0, 1))); up = (R3 @ Vector((0, 1, 0)))
    # head yaw relative to the camera (deg, + = turning toward the camera), pitch (+ = chin up), screen roll (+ = clockwise on screen)
    tc = Vector((to_cam.x, to_cam.y, 0)).normalized()
    def yaw_to_cam(f):
        fh = Vector((f.x, f.y, 0)).normalized(); return math.degrees(math.acos(max(-1, min(1, fh.dot(tc)))))
    a0, b0 = proj(Hm.translation)[0], proj(Hm.translation + up * 0.1)[0]
    roll = math.degrees(math.atan2(b0[0] - a0[0], -(b0[1] - a0[1])))
    head = {"yaw_cam": round(yaw_to_cam(fwd), 2), "dyaw": round(yaw_to_cam(fwd0) - yaw_to_cam(fwd), 2),
            "pitch": round(math.degrees(math.asin(max(-1, min(1, fwd.z)))) - math.degrees(math.asin(max(-1, min(1, fwd0.z)))), 2),
            "roll": round(roll, 2), "turn": round(ang_h(fwd) - ang_h(fwd0), 2)}
    out["frames"].append({"i": i, "key": frames[i].get("key"), "face": frames[i].get("face"), "blink": frames[i].get("blink"),
                          "anchors": A, "head": head})
act = G["act"]
json.dump(out, open(os.path.join(OUT, f"{act}_{VIEW}_face{'_pv' if PREVIEW else ''}.json"), "w"), indent=0)
print("FACE_DONE", OUT, flush=True)
