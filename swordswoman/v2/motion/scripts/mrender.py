# mrender.py (MOTION strand): Blender -b --factory-startup -P mrender.py -- PARTS_DIR JOBS.json OUT_DIR
# Rig = throw/scripts/rig_lib.py (exec'd as a library, as render_jobs.py) + SECONDARY rig: hair_side.L/R, hair_back (head mesh armature-deformed),
# skirt hem bones hem0..5 (skirt armature-deformed), ribbon tails (new strips, bow colour, 2-bone chains under the bow), bow + bun springs.
# Motion: key states captured from rig_lib.pose(); dense 120 Hz cubic-Hermite interpolation (quaternions); head / forearm lag (overlap);
# damped-spring particle chains (inertia, travel drag, gravity relative to rest, head/skirt collision) -> secondary bone angles per frame.
# JOBS.json {"jobs": [{"id", "view", "loop", "travel" (units/s, her forward), "seq": [{"pose", "ms", "name", "smear", "arc", "cw", "plane", "drag"}]}]}
# Out per frame: <id>_fNN_{guide,shade}.png (4x), <id>.json (pts + head transform + secondary states).
import bpy, sys, os, json, math
a0 = sys.argv[sys.argv.index("--") + 1:]
pdir_, jobp, outd_ = a0[:3]
LIB = "/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/throw/scripts/rig_lib.py"
src = open(LIB).read(); src = src[:src.index('if os.environ.get("RIG_LIB") == "1"')]
os.environ.setdefault("CHEAT", "0"); os.environ.setdefault("HEADV_E_TURN", "-18"); os.environ["MOCAP"] = "1"; os.environ.setdefault("ELBOW", "1")
sys.argv = [sys.argv[0], "--", pdir_, os.path.join(pdir_, "skel.txt"), os.path.join(os.path.dirname(LIB), "empty_keys.json"), outd_]
exec(compile(src, "rig_lib.py", "exec"))
import numpy as np
from mathutils import Vector, Matrix, Quaternion
from bpy_extras.object_utils import world_to_camera_view
CELL1 = int(os.environ.get("CELL1", "192")); PIV1 = tuple(int(x) for x in os.environ.get("PIV1", "96,152").split(","))
cam.data.shift_x = 0.5 - PIV1[0] / CELL1; cam.data.shift_y = (PIV1[1] / CELL1) - 0.5
sc.render.resolution_x = sc.render.resolution_y = CELL1 * SC
PPU1 = float(os.environ.get("PPU_FIX", "52.608")); cam.data.ortho_scale = CELL1 / PPU1
SECOND = os.environ.get("SECOND", "1") == "1"  # 0 = old rigid rig (A/B)
# ============================================================== secondary rig
HAIR = (61, 50, 53); BOWC = (232, 96, 79)
def vcols(o):
    me = o.data; ca = me.color_attributes["Color"]
    if ca.domain == "CORNER":
        c = np.zeros((len(me.vertices), 3))
        for l in me.loops: c[l.vertex_index] = ca.data[l.index].color_srgb[:3]
        return np.round(c * 255)
    return np.round(np.array([d.color_srgb[:3] for d in ca.data]) * 255)
def wverts(o): M = o.matrix_world; return np.array([(M @ v.co)[:] for v in o.data.vertices])
def sstep(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
CH = {}  # chain name -> {"bones": [..], "parent": bone, "w": omega rad/s, "z": damping ratio, "cd": air drag, "gw": gravity weight, "max": deg, "col": (centre bone, min radius) or None}
if SECOND:
    head_o = [o for o in BIND if o.name == "head"][0]; skirt_o = [o for o in BIND if o.name == "skirt"][0]; bow_o = [o for o in BIND if o.name == "bow"][0]
    HV = wverts(head_o); HC = vcols(head_o); SV = wverts(skirt_o); BV = wverts(bow_o)
    hb = arm.bones["head"]; hx, hy = hb.head_local.x, hb.head_local.y
    ishair = np.abs(HC - np.array(HAIR)).sum(1) < 30
    ztop, zbot = HV[:, 2].max(), HV[:, 2].min(); ZH = zbot + 0.50 * (ztop - zbot)  # hinge ~ mid head (temple)
    phi = np.degrees(np.arctan2(HV[:, 0] - hx, -(HV[:, 1] - hy)))  # 0 = her front, +90 = her left (+x)
    HREG = {"hair_side.L": 80.0, "hair_side.R": -80.0, "hair_back": 180.0}
    def angk(p, c): d = np.radians(p - c); return np.maximum(0, np.cos(d)) ** 3
    wz = sstep((ZH - HV[:, 2]) / (ZH - zbot - 0.02)) * ishair
    wf = sstep((np.abs(phi) - 35) / 30.0)  # fringe (front) stays rigid
    K = {n: angk(phi, c) for n, c in HREG.items()}; Ks = sum(K.values()) + 1e-9
    HW = {n: wz * wf * K[n] / Ks for n in HREG}
    sk = arm.bones["skirt"]; sx, sy_ = sk.head_local.x, sk.head_local.y
    stop, sbot = SV[:, 2].max(), SV[:, 2].min(); sphi = np.degrees(np.arctan2(SV[:, 0] - sx, -(SV[:, 1] - sy_)))
    NH = 6; HEMA = [i * 360.0 / NH for i in range(NH)]
    def angd(p, c): d = (p - c + 180) % 360 - 180; return np.maximum(0, np.cos(np.radians(d) * NH / 4)) ** 2
    wsh = sstep((stop - 0.025 - SV[:, 2]) / (stop - 0.025 - sbot))
    SK = [angd(sphi, c) for c in HEMA]; SKs = sum(SK) + 1e-9
    SW = {f"hem{i}": wsh * SK[i] / SKs for i in range(NH)}
    bpy.context.view_layer.objects.active = ao; bpy.ops.object.mode_set(mode="EDIT"); E = arm.edit_bones
    def nb(name, h, t, par):
        b = E.new(name); b.head = Vector(h); b.tail = Vector(t); b.parent = E[par]; b.use_connect = False; return b
    for n in HREG:
        w = HW[n]; m = w > 0.5
        if m.sum() < 5: m = w > 0.2
        P_ = HV[m]; tip = P_[P_[:, 2] < np.percentile(P_[:, 2], 25)].mean(0); top = P_[P_[:, 2] > np.percentile(P_[:, 2], 85)].mean(0)
        hinge = np.array([top[0], top[1], ZH]); nb(n, hinge, tip, "head")
        CH[n] = {"bones": [n], "parent": "head"}
    for i, c in enumerate(HEMA):
        m = (SK[i] / SKs > 0.6) & (SV[:, 2] < sbot + 0.04); tip = SV[m].mean(0)
        nb(f"hem{i}", (sx, sy_, stop - 0.02), tip, "skirt"); CH[f"hem{i}"] = {"bones": [f"hem{i}"], "parent": "skirt"}
    # ribbon tails: hang from the bow knot (centre-back of the bow), slightly outward, ~0.30 long
    kn = Vector((float(BV[:, 0].mean()), float(np.percentile(BV[:, 1], 60)), float(np.percentile(BV[:, 2], 40))))
    RL = float(os.environ.get("RIB_LEN", "0.32")); TAILS = {}
    for s, sg in (("L", 1), ("R", -1)):
        p0 = kn + Vector((0.035 * sg, 0.05, 0)); p2 = p0 + Vector((0.10 * sg, 0.10, -RL)); p1 = p0 + (p2 - p0) * 0.5 + Vector((0.01 * sg, 0.01, 0))
        nb(f"rib{s}1", p0, p1, "bow"); nb(f"rib{s}2", p1, p2, f"rib{s}1"); CH["rib" + s] = {"bones": [f"rib{s}1", f"rib{s}2"], "parent": "bow"}; TAILS[s] = (p0, p1, p2)
    bpy.ops.object.mode_set(mode="OBJECT")
    CH = {"bow": {"bones": ["bow"], "parent": "head"}, "bun": {"bones": ["bun"], "parent": "head"}, **CH}  # bow first (ribbon chains hang from it)
    # spring parameters (natural frequency Hz, damping ratio, air drag 1/s, gravity weight, max deg, collide)
    SP = json.loads(os.environ.get("SPRING", "{}"))
    DEF = {"hair_side": (2.5, 0.26, 1.0, 0.35, 30, "head"), "hair_back": (2.1, 0.25, 1.4, 0.40, 30, "head"), "hem": (2.4, 0.26, 1.4, 0.30, 24, "skirt"),
           "rib": (1.5, 0.24, 3.0, 0.30, 45, "head"), "bow": (4.0, 0.30, 0.4, 0.10, 14, None), "bun": (4.5, 0.35, 0.2, 0.05, 9, None)}
    GAIN = {"hair_side": 2.4, "hair_back": 2.2, "hem": 2.0, "rib": 1.0, "bow": 1.5, "bun": 1.2}; GAIN.update(json.loads(os.environ.get("GAIN", "{}")))
    HANG = {"rib": 0.75}; HANG.update(json.loads(os.environ.get("HANG", "{}")))
    for n, c in CH.items():
        key = n.split(".")[0].rstrip("0123456789").rstrip("LR") if not n.startswith("hem") else "hem"
        key = "rib" if n.startswith("rib") else "hair_side" if n.startswith("hair_side") else key
        f, z, cd, gw, mx, col = SP.get(key, DEF[key]); c.update(w=2 * math.pi * f, z=z, cd=cd, gw=gw, max=mx, col=col, gain=GAIN.get(key, 1.0), hang=HANG.get(key, 0.0))
    # deforming objects: bake to armature space, parent to the armature, armature modifier with weights (rest = current, no pose applied yet)
    def deform(o, groups, base):
        mw = o.matrix_world.copy(); o.parent = None; o.data.transform(mw); o.matrix_world = Matrix.Identity(4)
        o.parent = ao; o.parent_type = "OBJECT"; o.matrix_parent_inverse = Matrix.Identity(4)
        tot = sum(groups.values()); vg = o.vertex_groups.new(name=base)
        for i, w in enumerate(1 - tot): vg.add([i], float(max(0.0, w)), "REPLACE")
        for n, w in groups.items():
            g = o.vertex_groups.new(name=n)
            for i in np.nonzero(w > 1e-3)[0]: g.add([int(i)], float(w[i]), "REPLACE")
        md = o.modifiers.new("arm", "ARMATURE"); md.object = ao; md.use_vertex_groups = True
        while o.modifiers[0].name != "arm": o.modifiers.move(len(o.modifiers) - 1, 0)
    deform(head_o, HW, "head"); deform(skirt_o, SW, "skirt")
    # ribbon tail meshes (flat strips, width tapers 0.055 -> 0.045, V-cut end), bow vertex colour, same toon/outline setup as the parts
    for s, (p0, p1, p2) in TAILS.items():
        vv, ff, ww = [], [], []; N = 8
        pts = [p0 + (p1 - p0) * (k / (N / 2)) if k <= N / 2 else p1 + (p2 - p1) * ((k - N / 2) / (N / 2)) for k in range(N + 1)]
        for k, p in enumerate(pts):
            hw = 0.042 - 0.010 * k / N; side = Vector((1, 0, 0)); dz = 0.03 if k == N else 0.0
            vv += [p + side * hw + Vector((0, 0.008, 0)), p - side * hw + Vector((0, 0.008, 0 + dz * 0)), p + side * hw - Vector((0, 0.008, 0)), p - side * hw - Vector((0, 0.008, 0))]
            u = k / N; ww += [u] * 4
        vv[-4].z += 0.03; vv[-2].z += 0.03  # V notch: outer corners lower than the middle -> lift one side
        for k in range(N):
            a_ = 4 * k; b_ = 4 * (k + 1)
            ff += [(a_, a_ + 1, b_ + 1, b_), (a_ + 2, b_ + 2, b_ + 3, a_ + 3), (a_, b_, b_ + 2, a_ + 2), (a_ + 1, a_ + 3, b_ + 3, b_ + 1)]
        ff += [(0, 2, 3, 1), (4 * N, 4 * N + 1, 4 * N + 3, 4 * N + 2)]
        me_ = bpy.data.meshes.new("rib_" + s); me_.from_pydata([v[:] for v in vv], [], ff); o = bpy.data.objects.new("rib_" + s, me_); sc.collection.objects.link(o)
        ca_ = me_.color_attributes.new("Color", "BYTE_COLOR", "POINT")
        for d in ca_.data: d.color_srgb = (*[x / 255 for x in BOWC], 1)
        o.parent = ao; o.parent_type = "OBJECT"; o.matrix_parent_inverse = Matrix.Identity(4)
        g0 = o.vertex_groups.new(name="bow"); g1 = o.vertex_groups.new(name=f"rib{s}1"); g2 = o.vertex_groups.new(name=f"rib{s}2")
        for i, u in enumerate(ww):
            if u <= 0.08: g0.add([i], 1.0, "REPLACE")
            elif u <= 0.5: g1.add([i], 1.0, "REPLACE")
            else: g2.add([i], 1.0, "REPLACE")
        md = o.modifiers.new("arm", "ARMATURE"); md.object = ao
        o.data.materials.append(TM); o.data.materials.append(OM); so = o.modifiers.new("outline", "SOLIDIFY"); so.thickness = 0.012; so.offset = 1; so.use_flip_normals = True; so.material_offset = 1; so.show_render = False
        BIND[o] = "bow"; ALL.append(o)
    for p in pbs: p.rotation_mode = "QUATERNION"
    bpy.context.view_layer.update()
# ============================================================== render helpers (as render_jobs.py)
GRP = {}
for o, bn in BIND.items():
    n = o.name
    if n in ("head", "bow", "bun") or n.startswith("rib_"): g = 1
    elif n == "torso": g = 2
    elif n == "skirt": g = 3
    elif n.startswith(("uarm_R", "farm_R", "elbow_R")): g = 4
    elif n.startswith(("uarm_L", "farm_L", "elbow_L")): g = 5
    elif bn.endswith(".R"): g = 6
    elif bn.endswith(".L"): g = 7
    else: g = 2
    GRP[o] = g
def px(p):
    co = world_to_camera_view(sc, cam, p); return [round(co.x * CELL1, 2), round((1 - co.y) * CELL1, 2)]
def bpts():
    M = blade.matrix_world; vs = [M @ v.co for v in blade.data.vertices]; hm = hilt.matrix_world; hs = [hm @ v.co for v in hilt.data.vertices]
    c = sum(vs, Vector()) / len(vs); hc = sum(hs, Vector()) / len(hs)
    tip = sum(sorted(vs, key=lambda v: -(v - hc).length)[:4], Vector()) / 4; pom = sum(sorted(hs, key=lambda v: -(v - c).length)[:4], Vector()) / 4
    return pom, tip
def rpass(path, kind):
    if kind == "shade":
        sc.render.engine = "BLENDER_EEVEE"; sc.eevee.taa_render_samples = 8
        for o in ALL: o.modifiers["outline"].show_render = True
        sc.render.filepath = path; bpy.ops.render.render(write_still=True); return
    sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "FLAT"
    sh.color_type = "VERTEX"; sh.show_object_outline = False; sh.show_cavity = False; sc.display.render_aa = "OFF"
    for o in ALL: o.modifiers["outline"].show_render = False
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)
W = lambda pb, attr: ao.matrix_world @ getattr(pb, attr)
def pts_meta():
    hp, ht = W(pbs["head"], "head"), W(pbs["head"], "tail")
    m = {"head_top": px(ht), "head": px((hp + ht) / 2), "neck": px(hp), "chest": px(W(pbs["chest"], "head")), "hips": px(W(pbs["hips"], "head"))}
    for s in "RL":
        m["foot." + s] = px(W(pbs["foot." + s], "tail")); m["knee." + s] = px(W(pbs["shin." + s], "head"))
        m["hand." + s] = px(W(pbs["hand." + s], "head")); m["hand_tip." + s] = px(W(pbs["hand." + s], "tail")); m["elbow." + s] = px(W(pbs["forearm." + s], "head"))
        m["shoulder." + s] = px(W(pbs["upper_arm." + s], "head"))
    hb_ = pbs["hips"].head; m["throw_ahead"] = px(ao.matrix_world @ (hb_ + Vector((0, -1.0, 0.25)))); m["throw_hips"] = px(ao.matrix_world @ hb_)
    return m
def head_xf(rest):
    """head transform in screen terms vs the rest pose of this view: offset px of the head centre (vs rest, after removing the body pivot), tilt deg
    (screen roll of the head up axis, + = top leans screen-right), turn deg (yaw about world up vs rest, + = face turns toward screen-right), nod deg (+ = chin down)"""
    M = (ao.matrix_world @ pbs["head"].matrix).to_3x3(); up = (M @ Vector((0, 1, 0))).normalized()  # bone Y = up the head
    hp = W(pbs["head"], "head"); a = px(hp); b = px(hp + up * 0.3); tilt = math.degrees(math.atan2(b[0] - a[0], a[1] - b[1]))
    R0 = rest["Mh"]; Rr = M @ R0.inverted()  # rotation from rest head to current (world)
    v0 = Vector((0, -1, 0)); v1 = Rr @ v0; nod = math.degrees(math.asin(max(-1, min(1, -v1.z)))); v1h = Vector((v1.x, v1.y, 0)).normalized()
    yaw = math.degrees(math.atan2(v0.cross(v1h).z, v0.dot(v1h))); cmr = cam.matrix_world.to_3x3().col[0]
    turn = abs(yaw) * (1 if (v1h - v0).dot(cmr) >= 0 else -1)
    hc = px((hp + W(pbs["head"], "tail")) / 2)
    return {"centre_px": hc, "offset_px": [round(hc[0] - rest["hc"][0], 2), round(hc[1] - rest["hc"][1], 2)], "tilt_deg": round(tilt - rest["tilt"], 1),
            "turn_deg": round(turn, 1), "nod_deg": round(nod, 1)}
# ============================================================== state capture / interpolation
BN = [p.name for p in pbs]
def cap():
    return {"q": {n: np.array(pbs[n].rotation_quaternion[:]) for n in BN}, "l": {n: np.array(pbs[n].location[:]) for n in BN}, "s": {n: np.array(pbs[n].scale[:]) for n in BN},
            "aq": np.array(ao.matrix_world.to_quaternion()[:]), "al": np.array(ao.matrix_world.translation[:]), "as": np.array(ao.matrix_world.to_scale()[:])}
def hermite(P, T, t, loop, period):
    """cubic Hermite through arrays P[i] at times T[i] (finite-difference tangents); loop wraps with period"""
    n = len(T)
    if loop:
        t = t % period; Te = list(T) + [T[0] + period]; Pe = list(P) + [P[0]]
        i = max(k for k in range(n) if Te[k] <= t + 1e-9)
        def tan(k):
            kp, km = (k + 1) % n, (k - 1) % n; tp = T[kp] + (period if kp <= k else 0); tm = T[km] - (period if km >= k else 0)
            return (P[kp] - P[km]) / (tp - tm)
        p0, p1, t0, t1 = Pe[i], Pe[i + 1], Te[i], Te[i + 1]; m0, m1 = tan(i % n), tan((i + 1) % n)
    else:
        t = min(max(t, T[0]), T[-1]); i = min(max(k for k in range(n) if T[k] <= t + 1e-9), n - 2) if n > 1 else 0
        if n == 1: return P[0]
        def tan(k):
            km, kp = max(0, k - 1), min(n - 1, k + 1); return (P[kp] - P[km]) / (T[kp] - T[km])
        p0, p1, t0, t1 = P[i], P[i + 1], T[i], T[i + 1]; m0, m1 = tan(i), tan(i + 1)
    h = t1 - t0; u = (t - t0) / h if h > 0 else 0.0
    h00 = 2 * u ** 3 - 3 * u ** 2 + 1; h10 = u ** 3 - 2 * u ** 2 + u; h01 = -2 * u ** 3 + 3 * u ** 2; h11 = u ** 3 - u ** 2
    return h00 * p0 + h10 * h * m0 + h01 * p1 + h11 * h * m1
def qalign(Q):
    out = [Q[0]]
    for q in Q[1:]: out.append(q if np.dot(q, out[-1]) >= 0 else -q)
    return out
LAG = json.loads(os.environ.get("LAG", '{"forearm.R": 0.035, "forearm.L": 0.035, "head": 0.03}'))
def state_at(ST, T, t, loop, period):
    def I(get, qn=False, tt=t):
        P = [get(s) for s in ST]
        if qn: P = qalign(P)
        v = hermite(P, T, tt, loop, period); return v / np.linalg.norm(v) if qn else v
    s = {"q": {}, "l": {}, "s": {}}
    for n in BN:
        tt = t - LAG.get(n, 0.0)
        s["q"][n] = I(lambda S: S["q"][n], True, tt); s["l"][n] = I(lambda S: S["l"][n], False, tt); s["s"][n] = I(lambda S: S["s"][n], False, tt)
    s["aq"] = I(lambda S: S["aq"], True); s["al"] = I(lambda S: S["al"]); s["as"] = I(lambda S: S["as"])
    return s
def apply(s):
    for n in BN:
        pbs[n].rotation_quaternion = Quaternion(s["q"][n]); pbs[n].location = Vector(s["l"][n]); pbs[n].scale = Vector(s["s"][n])
    ao.matrix_world = Matrix.LocRotScale(Vector(s["al"]), Quaternion(s["aq"]), Vector(s["as"])); bpy.context.view_layer.update()
# ============================================================== spring chains
def chain_rigid(c):
    """world points p0 (root), p1..pn (rigid tips) + parent world rotation"""
    bs = c["bones"]; pts = [W(pbs[bs[0]], "head")] + [W(pbs[b], "tail") for b in bs]
    return [np.array(p[:]) for p in pts], np.array((ao.matrix_world @ pbs[c["parent"]].matrix).to_3x3())
def amp_(c, root, tg, p):
    """exaggerate each segment's angular deviation from its target direction by c['gain'] (clamped to max): reads at 1x"""
    g = c.get("gain", 1.0)
    if g == 1.0: return p
    out = []; b = root; bt = root
    for k in range(len(p)):
        L = np.linalg.norm(p[k] - (p[k - 1] if k else root)); rd = tg[k] - bt; rd = rd / max(np.linalg.norm(rd), 1e-9)
        d = p[k] - (p[k - 1] if k else root); d = d / max(np.linalg.norm(d), 1e-9)
        ang = math.acos(max(-1, min(1, float(d @ rd))))
        if ang > 1e-5:
            ax = np.cross(rd, d); ax /= max(np.linalg.norm(ax), 1e-9); th = min(ang * g, math.radians(c["max"]))
            d = rd * math.cos(th) + np.cross(ax, rd) * math.sin(th)
        b = b + d * L; bt = tg[k]; out.append(b)
    return out
KG = {"hair_side": 1.0, "hair_back": 1.0, "rib": 1.3, "hem": 0.6, "bow": 0.4, "bun": 0.3}
def simulate(ST, T, loop, period, travel, dt=1 / 120.0, kicks=None):
    """returns {chain: [[p1..pn] world at each output time]} (positions in the un-travelled world frame)"""
    tout = list(T); G = np.array([0, 0, -12.6])  # gravity in units/s^2 (2 units ~ 1.55 m)
    t0 = -round(2 * period / dt) * dt if loop else T[0] - round(0.25 / dt) * dt; t1 = T[-1] + 1e-6 if not loop else period
    nsteps = int(round((t1 - t0) / dt)) + 1; dist = 0.0
    trav = (lambda t: travel) if not isinstance(travel, list) else (lambda t: float(np.interp(t % period if loop else t, T, travel)))
    samp = []
    for k in range(nsteps):
        t = t0 + k * dt; apply(state_at(ST, T, t, loop, period)); dist += trav(t) * (dt if k else 0.0); off = np.array([0, -dist, 0])
        samp.append((t, {n: chain_rigid(c) for n, c in CH.items()}, off))
    # rest pose of each chain (gravity reference in the parent frame) = first sample's parent-local rigid directions
    res = {n: [None] * len(tout) for n in CH}
    for n, c in CH.items():
        w, z, cd, gw = c["w"], c["z"], c["cd"], c["gw"]; npt = len(c["bones"])
        R0 = samp[0][1][n][1]; g_loc = R0.T @ G  # gravity direction as seen by the parent at the start (rest reference)
        p = [samp[0][1][n][0][k + 1] + samp[0][2] for k in range(npt)]; v = [np.zeros(3) for _ in range(npt)]
        prev_tg = None; Ls = [np.linalg.norm(samp[0][1][n][0][k + 1] - samp[0][1][n][0][k]) for k in range(npt)]
        for si, (t, rig, off) in enumerate(samp):
            pts, Rp = rig[n]; tg = [pts[k + 1] + off for k in range(npt)]; root = pts[0] + off
            if c["hang"]:
                b_ = root; tg2 = []
                for k in range(npt):
                    rd_ = tg[k] - (tg[k - 1] if k else root); L_ = np.linalg.norm(rd_); dn_ = rd_ / max(L_, 1e-9)
                    h_ = c["hang"] * (1.0 if k else 0.7); d_ = (1 - h_) * dn_ + h_ * np.array([0, 0, -1.0]); d_ /= max(np.linalg.norm(d_), 1e-9)
                    b_ = b_ + d_ * L_; tg2.append(b_)
                tg = tg2
            vt = [(tg[k] - prev_tg[k]) / dt if prev_tg is not None else np.array([0, -trav(t), 0.0]) for k in range(npt)]
            if si == 0: v = [x.copy() for x in vt]
            grel = gw * (G - Rp @ g_loc)  # extra gravity when the parent is rotated away from its rest orientation
            for k in range(npt):
                wk = w * ((0.45 if c["hang"] else 0.6) if k > 0 else 1.0)
                acc = wk * wk * (tg[k] - p[k]) - 2 * z * wk * (v[k] - vt[k]) - cd * v[k] + grel
                v[k] = v[k] + acc * dt; p[k] = p[k] + v[k] * dt
            # length constraints + collision + angle clamp (relative to the rigid direction)
            base = root
            for k in range(npt):
                rd = tg[k] - (tg[k - 1] if k else root); d = p[k] - base; L = Ls[k]
                if np.linalg.norm(d) < 1e-9: d = rd.copy()
                d = d / np.linalg.norm(d); rdn = rd / max(np.linalg.norm(rd), 1e-9)
                ang = math.degrees(math.acos(max(-1, min(1, float(d @ rdn))))); mx = c["max"]
                if ang > mx:
                    ax = np.cross(rdn, d); ax = ax / max(np.linalg.norm(ax), 1e-9); th = math.radians(mx)
                    d = rdn * math.cos(th) + np.cross(ax, rdn) * math.sin(th)
                if c["col"]:  # keep the tip at least at its rigid distance from the collider axis (head centre / skirt axis): no swinging into the face / legs
                    cb = pbs["head"] if c["col"] == "head" else pbs["skirt"]
                    cc = np.array(W(cb, "head")[:]) + off; ax_ = np.array((ao.matrix_world.to_3x3() @ (cb.tail - cb.head)).normalized()[:])
                    q = base + d * L; rr = q - cc; rr -= ax_ * (rr @ ax_); qr = tg[k] - cc; qr -= ax_ * (qr @ ax_)
                    r0 = np.linalg.norm(qr) * (0.97 if c["col"] == "head" else 0.92)
                    if np.linalg.norm(rr) < r0 and np.linalg.norm(rr) > 1e-6:
                        q = q + rr / np.linalg.norm(rr) * (r0 - np.linalg.norm(rr)); d = (q - base) / max(np.linalg.norm(q - base), 1e-9)
                newp = base + d * L; v[k] = v[k] + (newp - p[k]) / dt * 0.0; p[k] = newp; base = newp
            prev_tg = tg
            if kicks:
                for j, kk in enumerate(kicks):
                    if kk and abs((t % period if loop else t) - T[j]) < dt / 2 + 1e-9:
                        kg = KG.get(n.split(".")[0].rstrip("0123456789").rstrip("LR") if not n.startswith(("hem", "rib", "hair_side")) else "hem" if n.startswith("hem") else "rib" if n.startswith("rib") else "hair_side", 1.0)
                        fw = np.array((ao.matrix_world.to_3x3() @ Vector((0, -1, 0)))[:]); fw[2] = 0; fw /= max(np.linalg.norm(fw), 1e-9)
                        for k in range(npt): v[k] = v[k] + kg * (kk[0] * fw + np.array([0, 0, kk[1]]))
            for j, to in enumerate(tout):
                if abs(t - to) < dt / 2 + 1e-9 and (not loop or t >= 0 - 1e-9): res[n][j] = [x - off for x in amp_(c, root, tg, p)]
    return res
def set_chain(c, P):
    for k, b in enumerate(c["bones"]):
        pb = pbs[b]; Mw = ao.matrix_world @ pb.matrix; h = Mw.translation; cur = (W(pb, "tail") - W(pb, "head")).normalized()
        d = (Vector(P[k]) - h).normalized(); R = cur.rotation_difference(d).to_matrix().to_4x4()
        Mw2 = Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ Mw; pb.matrix = ao.matrix_world.inverted() @ Mw2; bpy.context.view_layer.update()
def chain_state(n, c, P, rigid):
    pts = rigid[0]; o = {}
    tip_r = Vector(pts[-1]); tip = Vector(P[-1]); a = px(tip_r); b = px(tip)
    d0 = Vector(pts[-1] - pts[0]).normalized(); d1 = (tip - Vector(pts[0])).normalized()
    return {"tip_px": b, "tip_offset_px": [round(b[0] - a[0], 2), round(b[1] - a[1], 2)], "deg": round(math.degrees(d0.angle(d1)) if (d0 - d1).length > 1e-6 else 0.0, 1)}
# ============================================================== jobs
J = json.load(open(jobp)); os.makedirs(outd_, exist_ok=True)
KINDS = os.environ.get("KINDS", "guide,shade").split(",")
for job in J["jobs"]:
    set_view(job["view"]); jid = job["id"]; seq = job["seq"]; loop = job.get("loop", False); travel = job.get("travel", 0.0); travel = [float(f.get("travel", travel)) for f in seq] if any("travel" in f for f in seq) else float(travel)
    pose({"katana": 0}); bpy.context.view_layer.update()
    rest = {"Mh": (ao.matrix_world @ pbs["head"].matrix).to_3x3(), "hc": px((W(pbs["head"], "head") + W(pbs["head"], "tail")) / 2)}
    up_ = (rest["Mh"] @ Vector((0, 1, 0))).normalized(); hp_ = W(pbs["head"], "head"); a_ = px(hp_); b_ = px(hp_ + up_ * 0.3); rest["tilt"] = math.degrees(math.atan2(b_[0] - a_[0], a_[1] - b_[1]))
    rest_hips = px(W(pbs["hips"], "head"))
    ST, T = [], []; tacc = 0.0
    KICK = [f["pose"].pop("_kick", None) for f in seq]
    for f in seq: f["pose"]["katana"] = 0; pose(f["pose"]); ST.append(cap()); T.append(tacc); tacc += f.get("ms", 100) / 1000.0
    period = tacc
    sim = simulate(ST, T, loop, period, travel, kicks=KICK) if (SECOND and CH and len(seq) > 1) else None
    meta = {"id": jid, "view": job["view"], "cell_1x": CELL1, "pivot_1x": PIV1, "ppu": PPU1, "second": SECOND, "frames": []}
    for i, f in enumerate(seq):
        st = state_at(ST, T, T[i], loop, period); apply(st)
        sec = {}
        if sim:
            rig = {n: chain_rigid(c) for n, c in CH.items()}
            for n, c in CH.items():
                if sim[n][i] is not None: sec[n] = chain_state(n, c, sim[n][i], rig[n]); set_chain(c, sim[n][i])
        for o in kat: o.hide_render = True
        if os.environ.get("DBG") and i == 0:
            dg = bpy.context.evaluated_depsgraph_get()
            for o in ALL:
                if o.name.startswith(("rib", "head", "skirt", "bow")):
                    oe = o.evaluated_get(dg); vs = [oe.matrix_world @ v.co for v in oe.data.vertices]
                    print("DBG", o.name, o.hide_render, len(vs), [round(min(v[k] for v in vs), 3) for k in range(3)], [round(max(v[k] for v in vs), 3) for k in range(3)], [m.type for m in o.modifiers])
        stem = f"{jid}_f{i:02d}"
        for kind in KINDS: rpass(os.path.join(outd_, f"{stem}_{kind}.png"), kind)
        kd = f["pose"]; P_ = pts_meta()
        meta["frames"].append({"i": i, "ms": f.get("ms", 0), "name": f.get("name", ""), "air": bool(kd.get("absz", 0) or kd.get("lift", 0) > 0.06), "pts": P_,
                               "head_xf": head_xf(rest), "secondary": sec, "body_offset_px": [round(P_["hips"][0] - rest_hips[0], 2), round(P_["hips"][1] - rest_hips[1], 2)]})
    json.dump(meta, open(os.path.join(outd_, f"{jid}.json"), "w"))
    print("JOB", jid, len(seq), flush=True)
print("ALLDONE", len(J["jobs"]), flush=True)
