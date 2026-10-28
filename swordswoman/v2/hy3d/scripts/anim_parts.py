# Blender -b --factory-startup -P anim_parts.py -- PARTS_DIR SKEL.txt KEYS.json ANIM.json OUT_DIR [actions|all] [dirs=SE,E] [sizes=C,A] [modes=matid,shade]
# Round 4: per-frame 3D guides. Re-uses the rigid parts rig (rig_parts.py, exec'd as a library) and builds every frame of every action
# from anim.json (frame = key name | mix of two keys | overrides, with ms), adds secondary motion (bow/bun/skirt lag 1 frame, driven by
# the head/hip motion of the previous frame), the SE/NE stride+blade cheat (CHEAT deg), renders matid/shade + 1-bit silhouette at 4x
# for figure heights 48 px (C) and 40 px (A), and writes per-frame JSON (ms, pivot, blade pommel/tip, head) -> OUT/<action>_<dir>/.
import bpy, sys, os, json, math
here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else None
a0 = sys.argv[sys.argv.index("--") + 1:]
pdir_, skp_, keyp_, animp, outd_ = a0[:5]
acts_ = a0[5] if len(a0) > 5 else "all"; dirs_ = (a0[6] if len(a0) > 6 else "SE,E").split(",")
sizes_ = (a0[7] if len(a0) > 7 else "s48").split(",")  # s48 primary (style strand final: 44-48 px in a 64 cell); s32 optional
modes_ = (a0[8] if len(a0) > 8 else "matid,shade").split(",")
os.environ.setdefault("CHEAT", "28"); os.environ.setdefault("HEADV_E_TURN", "-18")
src = open(os.path.join(os.path.dirname(animp), "..", "scripts", "rig_parts.py")).read()
src = src[:src.index('if os.environ.get("RIG_LIB") == "1"')]
sys.argv = [sys.argv[0], "--", pdir_, skp_, keyp_, outd_]
exec(compile(src, "rig_parts.py", "exec"))
import numpy as np
from mathutils import Vector, Matrix, Euler
from bpy_extras.object_utils import world_to_camera_view
AN = json.load(open(animp)); KEYS = json.load(open(keyp_))
FIG = {"s32": 32, "s48": 48}; CELLS = {"s32": (64, (32, 56)), "s48": (96, (48, 84))}  # 1x guide cell + feet pivot per figure size
CELL1, PIV1 = 96, (48, 84)
def set_size(sz):
    global CELL1, PIV1
    CELL1, PIV1 = CELLS[sz]
    cam.data.shift_x = 0.5 - PIV1[0] / CELL1; cam.data.shift_y = (PIV1[1] / CELL1) - 0.5
    sc.render.resolution_x = sc.render.resolution_y = CELL1 * SC; cam.data.ortho_scale = CELL1 / PPUS.get(sz, PPU)
PPUS = {}
set_size("s48")
def keyget(name):
    for act, d in KEYS.items():
        if act != "_doc" and name in d: return d[name]
    raise KeyError(name)
MIRROR_ARM_BIAS = 0.0
def mirror(kd):  # swap R/L legs + off-arm swing for the second half of cycles (sword arm R kept)
    o = {}
    for k, v in kd.items():
        if k.startswith(("thigh.", "shin.", "foot.")):
            s = k[-1]; k2 = k[:-1] + ("L" if s == "R" else "R"); o[k2] = [v[0], -v[1], -v[2]]
        elif k in ("spine", "chest", "head", "hips"): o[k] = [v[0], -v[1], -v[2]]
        elif k == "upper_arm.L": o[k] = [-v[0] + MIRROR_ARM_BIAS, v[1], v[2]]
        else: o[k] = v
    return o
def mix(A, B, t):
    o = {}
    for k in set(A) | set(B):
        va, vb = A.get(k), B.get(k)
        if isinstance(va, list) or isinstance(vb, list):
            va = va or [0, 0, 0]; vb = vb or [0, 0, 0]; o[k] = [va[i] + (vb[i] - va[i]) * t for i in range(3)]
        elif k == "katana": o[k] = va if va is not None else vb
        else:
            va = 0 if va is None else va; vb = 0 if vb is None else vb; o[k] = va + (vb - va) * t
    return o
def add(A, B):
    o = dict(A)
    for k, v in B.items():
        if k.startswith("+"):  # additive
            k = k[1:]; c = o.get(k, [0, 0, 0] if isinstance(v, list) else 0)
            o[k] = [c[i] + v[i] for i in range(3)] if isinstance(v, list) else c + v
        else: o[k] = v
    return o
def frame_pose(fr):
    if "mix" in fr: a_, b_, t = fr["mix"]; kd = mix(keyget(a_.lstrip("~")) if not a_.startswith("~") else mirror(keyget(a_[1:])),
                                                   keyget(b_.lstrip("~")) if not b_.startswith("~") else mirror(keyget(b_[1:])), t)
    else:
        k = fr["key"]; kd = mirror(keyget(k[1:])) if k.startswith("~") else dict(keyget(k))
    return add(kd, fr.get("set", {}))
# ---------------- measurement helpers
def head_pos():
    return ao.matrix_world @ pbs["head"].head, ao.matrix_world @ pbs["head"].tail
def hip_pos(): return ao.matrix_world @ pbs["hips"].head
def blade_pts():
    M = blade.matrix_world; vs = [M @ v.co for v in blade.data.vertices]
    hm = hilt.matrix_world; hs = [hm @ v.co for v in hilt.data.vertices]
    c = sum(vs, Vector()) / len(vs); ax = (vs[0] - c)
    # tip = blade vertex farthest from hilt centre, pommel = hilt vertex farthest from blade centre
    hc = sum(hs, Vector()) / len(hs)
    tip = max(vs, key=lambda v: (v - hc).length); pom = max(hs, key=lambda v: (v - c).length)
    tipc = sum(sorted(vs, key=lambda v: -(v - hc).length)[:4], Vector()) / 4; pomc = sum(sorted(hs, key=lambda v: -(v - c).length)[:4], Vector()) / 4
    return pomc, tipc
def to_px(p, ppu):
    co = world_to_camera_view(sc, cam, p); return [round(co.x * CELL1, 2), round((1 - co.y) * CELL1, 2)]
def fig_height_px():
    pts = [o.matrix_world @ v.co for o in BIND for v in o.data.vertices]
    ys = [world_to_camera_view(sc, cam, p).y for p in pts]
    return (max(ys) - min(ys)) * CELL1
# calibrate px/unit per size on the rest pose, SE view (same scale for every direction)
set_view("SE"); pose({}); cam.data.ortho_scale = CELL1 / PPU; bpy.context.view_layer.update()
h26 = fig_height_px(); PPUS.update({s: PPU * FIG[s] / h26 for s in FIG})
print("calib: rest SE height at PPU 26 =", round(h26, 2), "px ->", {k: round(v, 3) for k, v in PPUS.items()}, flush=True)
# ---------------- secondary motion
SEC = AN.get("_secondary", {"bow_vel": 120, "bow_rot": 0.6, "bow_sz": 1.2, "skirt_vel": 90, "skirt_len": 1.4, "skirt_flare": 1.0, "drag": 0})
def secondary(kd, prev, cur, drag):
    # prev/cur = (head pos, hip pos, head quat, hip quat) world. Bow/bun keep the PREVIOUS frame's head orientation (1-frame lag, x gain overshoot)
    g = SEC.get("lag_gain", 1.3); vz = cur[0].z - prev[0].z; vh = cur[1].z - prev[1].z
    dq = cur[2].inverted() @ prev[2]; e = dq.to_euler("XYZ")
    bx = math.degrees(e.x) * g - SEC["bow_vel"] * vz - SEC["bow_vel"] * drag; by = math.degrees(e.y) * g; bz = math.degrees(e.z) * g
    bx = max(-40, min(40, bx)); by = max(-30, min(30, by)); bz = max(-30, min(30, bz))
    mv = (cur[0] - prev[0]).length + abs(math.degrees(e.x)) / 200 + abs(math.degrees(e.z)) / 200
    MINB = SEC.get("bow_min", 8.0)
    if mv > 0.004 and abs(bx) < MINB: bx = MINB if (bx > 0 or (bx == 0 and vz < 0)) else -MINB  # visible lag even on small moves
    s = max(0.82, min(1.2, 1 - SEC["bow_sz"] * vz))
    kd = dict(kd)
    b0 = kd.get("bow", [0, 0, 0]); kd["bow"] = [b0[0] + bx, b0[1] + by, b0[2] + bz]; kd["bow_s"] = [1 / math.sqrt(s), 1 / math.sqrt(s), s]
    bg_ = SEC.get("bun_gain", 0.6); nb = bg_ * bx
    if abs(vz) > 0.03 and abs(nb) < 10: nb = 10 if vz < 0 else -10   # bun visibly lags sharp vertical changes
    n0 = kd.get("bun", [0, 0, 0]); kd["bun"] = [n0[0] + nb, n0[1] + bg_ * by, n0[2] + bg_ * bz]
    dqh = cur[3].inverted() @ prev[3]; eh = dqh.to_euler("XYZ")
    kd["skirt_len"] = max(0.85, min(1.15, 1 + SEC["skirt_len"] * vh)); kd["skirt_flare"] = max(0.9, min(1.18, 1 - SEC["skirt_flare"] * vh))
    sa = kd.get("skirt_add", [0, 0, 0])
    kd["skirt_add"] = [sa[0] + max(-18, min(18, math.degrees(eh.x) * g + SEC["skirt_vel"] * drag)), sa[1] + max(-12, min(12, math.degrees(eh.y) * g)), sa[2]]
    return kd
def make_smear(pt_prev, pt_cur):
    # solid arc guide between the previous and current blade (pommel-centred fan), smear ID colour
    if pt_prev is None or pt_cur is None: return None
    pom, tip = blade_pts(); L = (tip - pom).length
    d0 = (pt_prev[1] - pom).normalized(); d1 = (tip - pom).normalized()
    q = d0.rotation_difference(d1); N = 12; verts = []; faces = []
    from mathutils import Quaternion
    for k in range(N + 1):
        qk = Quaternion().slerp(q, k / N); dk = qk @ d0
        verts += [pom + dk * L * 0.70, pom + dk * L * 1.02]
    for k in range(N): faces.append((2 * k, 2 * k + 1, 2 * k + 3, 2 * k + 2))
    me_ = bpy.data.meshes.new("smear"); me_.from_pydata(verts, [], faces); o = bpy.data.objects.new("smear", me_); sc.collection.objects.link(o)
    sol = o.modifiers.new("th", "SOLIDIFY"); sol.thickness = 0.03
    ca = me_.color_attributes.new("Color", "BYTE_COLOR", "POINT")
    for d in ca.data: d.color_srgb = (0.94, 0.95, 1.0, 1)
    me_.materials.append(TM); me_.materials.append(OM)
    so = o.modifiers.new("outline", "SOLIDIFY"); so.thickness = 0.01; so.offset = 1; so.use_flip_normals = True; so.material_offset = 1; so.show_render = False
    ALL.append(o); return o
def make_lines(n):
    # VFX guide: n thin bars trailing behind the body along the (cheated) travel axis, at hip..chest heights
    out = []
    if not n: return out
    gm = math.radians(CHEAT.get(VIEW['dn'], 0.0)); back = Matrix.Rotation(gm, 3, "Z") @ Vector((0, 1, 0))
    hp_ = hip_pos(); hd = head_pos()[0]
    for k in range(n):
        z = hp_.z + (hd.z - hp_.z) * (0.15 + 0.7 * k / max(1, n - 1)); L_ = 0.55 - 0.12 * k
        c = Vector((hp_.x, hp_.y, z)) + back * (0.35 + L_ / 2)
        bpy.ops.mesh.primitive_cube_add(size=1, location=c); o = bpy.context.object; o.scale = (0.03, L_, 0.03)
        o.rotation_euler = (0, 0, gm); bpy.ops.object.transform_apply(scale=True, rotation=True)
        ca = o.data.color_attributes.new("Color", "BYTE_COLOR", "POINT")
        for d in ca.data: d.color_srgb = (0.94, 0.95, 1.0, 1)
        o.data.materials.append(TM); o.data.materials.append(OM)
        so = o.modifiers.new("outline", "SOLIDIFY"); so.thickness = 0.008; so.offset = 1; so.use_flip_normals = True; so.material_offset = 1; so.show_render = False
        ALL.append(o); out.append(o)
    return out
def render_to(path, mode):
    render(path, mode)
def sil_from(matid_path, out_path):
    im = Image.open(matid_path).convert("RGBA"); al = np.asarray(im)[..., 3]
    S4 = al.shape[0]; n = S4 // CELL1
    s1 = al.reshape(CELL1, n, CELL1, n).mean((1, 3)) > 127
    Image.fromarray((np.kron(s1, np.ones((n, n))) * 255).astype(np.uint8), "L").convert("1").save(out_path)
    return int(s1.sum())
os.makedirs(outd_, exist_ok=True)
order = [k for k in AN if not k.startswith("_")] if acts_ == "all" else acts_.split(",")
for act in order:
    spec = AN[act]; frames = spec["frames"]; loop = spec.get("loop", False); drag0 = spec.get("drag", 0.0)
    for dn in dirs_:
        set_view(dn); od = os.path.join(outd_, f"{act}_{dn}"); os.makedirs(od, exist_ok=True)
        kds = [add(frame_pose(fr), fr.get("set_" + dn, {})) for fr in frames]  # set_<dir>: per-view overrides
        # pass 1: motion samples without secondary
        mot = []
        for kd in kds:
            pose(kd); mot.append((head_pos()[0].copy(), hip_pos().copy(), (ao.matrix_world @ pbs["head"].matrix).to_quaternion(), (ao.matrix_world @ pbs["hips"].matrix).to_quaternion()))
        tips = []
        for kd in kds:
            pose(kd); tips.append(blade_pts() if kd.get("katana") else None)
        metas = {sz: {"action": act, "dir": dn, "size": sz, "fig_px": FIG[sz], "loop": loop, "cell_1x": CELLS[sz][0], "scale": SC, "pivot_1x": list(CELLS[sz][1]),
                      "px_per_unit_1x": round(PPUS[sz], 4), "elev_deg": 30, "cheat_deg": CHEAT.get(dn, 0.0), "head_cheat": HEADV.get(dn),
                      "ids": ["skin", "hair", "dress", "obi", "boots", "eyes", "bow", "sleeve", "blade", "hilt", "smear"], "frames": []} for sz in sizes_}
        for sz in sizes_: os.makedirs(os.path.join(od, sz), exist_ok=True)
        for i, (fr, kd) in enumerate(zip(frames, kds)):
            j = (i - 1) % len(frames) if loop else max(0, i - 1)
            drag = fr.get("drag", drag0)
            kd2 = secondary(kd, mot[j], mot[i], drag)
            pose(kd2)
            sm = make_smear(tips[j], tips[i]) if fr.get("smear") and (loop or i > 0) else None
            sl = make_lines(fr.get("speedlines", 0))
            air = bool(kd2.get("absz", 0)) or kd2.get("lift", 0) > 0.06
            for sz in sizes_:
                set_size(sz); bpy.context.view_layer.update()
                hp, ht = head_pos(); pom, tip = blade_pts(); kat_ = bool(kd2.get("katana", 0))
                metas[sz]["frames"].append({"i": i, "name": fr.get("name", f"f{i}"), "ms": fr["ms"], "src": fr.get("key") or fr.get("mix"), "air": air,
                    "smear": sm is not None, "katana": kat_, "pivot": list(PIV1), "head_centre": to_px((hp + ht) / 2, 0), "head_top": to_px(ht, 0),
                    "hip": to_px(hip_pos(), 0), "blade_pommel": to_px(pom, 0) if kat_ else None, "blade_tip": to_px(tip, 0) if kat_ else None})
                for mode in modes_:
                    render_to(os.path.join(od, sz, f"f{i:02d}_{mode}.png"), mode)
            if sm is not None: ALL.remove(sm); bpy.data.objects.remove(sm)
            for o in sl: ALL.remove(o); bpy.data.objects.remove(o)
        for sz in sizes_:
            m_ = metas[sz]; m_["note"] = "px coords are 1x cell pixels (x right, y down); renders are 4x (fNN_matid/shade.png); fNN_sil.png = 1-bit 1x silhouette (alpha box>50%) at 4x nearest (written by post.py)."
            json.dump(m_, open(os.path.join(od, sz, "frames.json"), "w"), indent=1)
            json.dump({"action": act, "dir": dn, "keys": [f["name"] + ("_air" if f["air"] else "") for f in m_["frames"]], "ms": [f["ms"] for f in m_["frames"]]},
                      open(os.path.join(od, sz, "keys.json"), "w"), indent=1)
        print("DONE", act, dn, len(frames), flush=True)
