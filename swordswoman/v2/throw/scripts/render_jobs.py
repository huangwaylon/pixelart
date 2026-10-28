# Blender -b --factory-startup -P render_jobs.py -- PARTS_DIR SKEL.txt JOBS.json OUT_DIR
# POSE strand renderer. Execs rig_lib.py (copy of hy3d rig_parts.py + yaw / roll / cheat / headv / blade_scr pose keys) as a library.
# JOBS.json: {"jobs": [{"id": str, "view": "SE", "pose": {...}} | {"id": str, "view": "SE", "seq": [{"pose": {...}, "ms": int, "smear": 0|1}], "loop": bool}]}
# Per frame writes OUT/<id>[_fNN]_{matid,part,core,blade}.png (4x of a 96 cell, 1x pivot (48,78) -> 64 cell = crop x16..80, y16..80, pivot (32,62))
# and OUT/<id>.json with screen points (1x px of the 96 cell).
import bpy, sys, os, json, math
a0 = sys.argv[sys.argv.index("--") + 1:]
pdir_, skp_, jobp, outd_ = a0[:4]
here = os.path.dirname(os.path.abspath(jobp))
LIB = os.environ.get("RIG_LIB_PATH")
src = open(LIB).read(); src = src[:src.index('if os.environ.get("RIG_LIB") == "1"')]
os.environ.setdefault("CHEAT", "0"); os.environ.setdefault("HEADV_E_TURN", "-18")
sys.argv = [sys.argv[0], "--", pdir_, skp_, os.path.join(os.path.dirname(LIB), "empty_keys.json"), outd_]
exec(compile(src, "rig_lib.py", "exec"))
import numpy as np
from mathutils import Vector, Matrix, Quaternion
from bpy_extras.object_utils import world_to_camera_view
CELL1, PIV1 = 96, (48, 76)
if os.environ.get("CELL1"): CELL1 = int(os.environ["CELL1"]); PIV1 = tuple(int(x) for x in os.environ.get("PIV1", f"{CELL1 // 2},{int(CELL1 * 76 / 96)}").split(","))  # G96: s96 guides (192 cell, pivot 96,152)
cam.data.shift_x = 0.5 - PIV1[0] / CELL1; cam.data.shift_y = (PIV1[1] / CELL1) - 0.5
sc.render.resolution_x = sc.render.resolution_y = CELL1 * SC
def fig_h():
    ex_ = [x for x in os.environ.get("FIG_EXCL", "").split(",") if x]  # THROW: e.g. bow,bun -> 48 px = hair crown to sole (prop/blockout convention)
    pts = [o.matrix_world @ v.co for o in BIND if o.name not in ex_ for v in list(o.data.vertices)[::3]]
    ys = [world_to_camera_view(sc, cam, p).y for p in pts]; return (max(ys) - min(ys)) * CELL1
set_view("SE"); pose({}); cam.data.ortho_scale = CELL1 / PPU; bpy.context.view_layer.update()
PPU1 = PPU * float(os.environ.get("FIG_PX", "48")) / fig_h()
if os.environ.get("PPU_FIX"): PPU1 = float(os.environ["PPU_FIX"])  # G96: fixed camera scale (1x px per unit) from the rig H calibration
cam.data.ortho_scale = CELL1 / PPU1
for o_ in BIND:
    if o_.name in os.environ.get("HIDE", "").split(","): o_.hide_render = True  # THROW: measurement passes (e.g. HIDE=bun)
print("calib PPU", round(PPU1, 3), flush=True)
# part groups (object colour pass)
GRP = {}
for o, bn in BIND.items():
    n = o.name
    if n in ("head", "bow", "bun"): g = 1
    elif n == "torso": g = 2
    elif n == "skirt": g = 3
    elif n == "arm_R" or n.startswith(("uarm_R", "farm_R", "elbow_R")): g = 4
    elif n == "arm_L" or n.startswith(("uarm_L", "farm_L", "elbow_L")): g = 5
    elif bn.endswith(".R"): g = 6
    elif bn.endswith(".L"): g = 7
    else: g = 2
    GRP[o] = g
for o in kat: GRP[o] = 8 if o.name == "blade" else 9
GCOL = {g: (((g * 25 / 255) + 0.055) / 1.055) ** 2.4 for g in range(1, 11)}
GCOL = {g: (v, 0, 0, 1) for g, v in GCOL.items()}
for o, g in GRP.items(): o.color = GCOL[g]
SEC = {"bow_vel": 110, "bow_sz": 4.0, "skirt_vel": 120, "skirt_len": 2.4, "skirt_flare": 2.0, "lag_gain": 2.0, "bow_min": 18, "bun_gain": 1.0}
def secondary(kd, prev, cur, drag):
    g = SEC.get("lag_gain", 1.3); vz = cur[0].z - prev[0].z; vh = cur[1].z - prev[1].z
    dq = cur[2].inverted() @ prev[2]; e = dq.to_euler("XYZ")
    bx = math.degrees(e.x) * g - SEC["bow_vel"] * vz - SEC["bow_vel"] * drag; by = math.degrees(e.y) * g; bz = math.degrees(e.z) * g
    bx = max(-40, min(40, bx)); by = max(-30, min(30, by)); bz = max(-30, min(30, bz))
    mv = (cur[0] - prev[0]).length + abs(math.degrees(e.x)) / 200 + abs(math.degrees(e.z)) / 200
    MINB = SEC.get("bow_min", 8.0)
    if mv > 0.004 and abs(bx) < MINB: bx = MINB if (bx > 0 or (bx == 0 and vz < 0)) else -MINB
    s = max(0.82, min(1.2, 1 - SEC["bow_sz"] * vz))
    kd = dict(kd)
    b0 = kd.get("bow", [0, 0, 0]); kd["bow"] = [b0[0] + bx, b0[1] + by, b0[2] + bz]; kd["bow_s"] = [1 / math.sqrt(s), 1 / math.sqrt(s), s]
    nb = SEC.get("bun_gain", 0.6) * bx
    n0 = kd.get("bun", [0, 0, 0]); kd["bun"] = [n0[0] + nb, n0[1] + by, n0[2] + bz]
    dqh = cur[3].inverted() @ prev[3]; eh = dqh.to_euler("XYZ")
    kd["skirt_len"] = kd.get("skirt_len", 1.0) * max(0.85, min(1.15, 1 + SEC["skirt_len"] * vh))
    kd["skirt_flare"] = kd.get("skirt_flare", 1.0) * max(0.9, min(1.18, 1 - SEC["skirt_flare"] * vh))
    sa = kd.get("skirt_add", [0, 0, 0])
    kd["skirt_add"] = [sa[0] + max(-18, min(18, math.degrees(eh.x) * g + SEC["skirt_vel"] * drag)), sa[1] + max(-12, min(12, math.degrees(eh.y) * g)), sa[2]]
    return kd
def mot():
    return ((ao.matrix_world @ pbs["head"].head).copy(), (ao.matrix_world @ pbs["hips"].head).copy(),
            (ao.matrix_world @ pbs["head"].matrix).to_quaternion(), (ao.matrix_world @ pbs["hips"].matrix).to_quaternion())
def bpts():
    M = blade.matrix_world; vs = [M @ v.co for v in blade.data.vertices]; hm = hilt.matrix_world; hs = [hm @ v.co for v in hilt.data.vertices]
    c = sum(vs, Vector()) / len(vs); hc = sum(hs, Vector()) / len(hs)
    tip = sum(sorted(vs, key=lambda v: -(v - hc).length)[:4], Vector()) / 4; pom = sum(sorted(hs, key=lambda v: -(v - c).length)[:4], Vector()) / 4
    return pom, tip
def px(p):
    co = world_to_camera_view(sc, cam, p); return [round(co.x * CELL1, 2), round((1 - co.y) * CELL1, 2)]
def smear_obj(prev_tip, kd, cw=True, plane="s"):
    """crescent between the previous and current blade, swept in the SCREEN plane (clockwise by default = over the top, left -> right)"""
    pom, tip = bpts(); L = (tip - pom).length
    cm = cam.matrix_world.to_3x3(); r_, u_, v_ = cm.col[0], cm.col[1], -cm.col[2]
    def ang(d): return math.atan2(d.dot(u_), d.dot(r_))
    d0 = (prev_tip - pom).normalized(); d1 = (tip - pom).normalized()
    if plane == "h":  # horizontal swing seen from the side: sweep about world Z through the camera side (flat band)
        ax = Vector((0, 0, 1)); a0 = math.atan2(d0.y, d0.x); a1 = math.atan2(d1.y, d1.x); da = a1 - a0
        while da > math.pi: da -= 2 * math.pi
        while da < -math.pi: da += 2 * math.pi
        mid = (Matrix.Rotation(da / 2, 3, ax) @ d0)
        if mid.dot(-v_) < 0: da = da - 2 * math.pi if da > 0 else da + 2 * math.pi
        N = 16; vv = []; ff = []
        for k in range(N + 1):
            dk = (Matrix.Rotation(da * k / N, 3, ax) @ d0).normalized(); w = 0.80 - 0.08 * k / N
            vv += [pom + dk * L * w, pom + dk * L * 1.03]
        for k in range(N): ff.append((2 * k, 2 * k + 1, 2 * k + 3, 2 * k + 2))
        me_ = bpy.data.meshes.new("smear"); me_.from_pydata(vv, [], ff); o = bpy.data.objects.new("smear", me_); sc.collection.objects.link(o)
        o.modifiers.new("th", "SOLIDIFY").thickness = 0.03; o.color = (((250 / 255 + 0.055) / 1.055) ** 2.4, 0, 0, 1)
        ca = me_.color_attributes.new("Color", "BYTE_COLOR", "POINT")
        for d in ca.data: d.color_srgb = (0.94, 0.95, 1.0, 1)
        return o
    da = ang(d1) - ang(d0)
    if os.environ.get("SMEAR_SHORT", "1") == "1":  # MOCAP: sweep the short way between the two real blade positions
        while da > math.pi: da -= 2 * math.pi
        while da < -math.pi: da += 2 * math.pi
    elif cw:
        while da > 0: da -= 2 * math.pi
    else:
        while da < 0: da += 2 * math.pi
    N = 16; vv = []; ff = []
    for k in range(N + 1):
        R = Matrix.Rotation(da * k / N, 3, -v_); dk = (R @ d0).normalized(); w = 0.80 - 0.08 * k / N
        vv += [pom + dk * L * w, pom + dk * L * 1.03]
    for k in range(N): ff.append((2 * k, 2 * k + 1, 2 * k + 3, 2 * k + 2))
    me_ = bpy.data.meshes.new("smear"); me_.from_pydata(vv, [], ff); o = bpy.data.objects.new("smear", me_); sc.collection.objects.link(o)
    o.modifiers.new("th", "SOLIDIFY").thickness = 0.03
    ca = me_.color_attributes.new("Color", "BYTE_COLOR", "POINT")
    for d in ca.data: d.color_srgb = (0.94, 0.95, 1.0, 1)
    o.color = (((250 / 255 + 0.055) / 1.055) ** 2.4, 0, 0, 1); return o
def rpass(path, kind, extra=()):
    if kind == "shade":  # toon guide (as rig_lib.render shade): EEVEE + outline modifiers, smear visible
        sc.render.engine = "BLENDER_EEVEE"; sc.eevee.taa_render_samples = 8
        for o in ALL: o.modifiers["outline"].show_render = True
        for o in extra: o.hide_render = False; o.modifiers["outline"].show_render = False
        sc.render.filepath = path; bpy.ops.render.render(write_still=True); return
    if kind == "guide":  # matid incl. the smear-ID crescent (ff_redraw guide)
        kind = "matid"; extra_vis = True
    else: extra_vis = kind == "smear"
    sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "FLAT"
    sh.color_type = "VERTEX" if kind == "matid" else "OBJECT"; sh.show_object_outline = False; sh.show_cavity = False; sc.display.render_aa = "OFF"
    vis = {"matid": None, "part": None, "core": (1, 2, 3), "blade": (8, 9), "smear": ()}[kind]
    for o in ALL:
        o.modifiers["outline"].show_render = False
        if vis is not None and o in GRP: o.hide_render = o.hide_render or GRP[o] not in vis
    for o in extra: o.hide_render = not extra_vis
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)
def pts_meta(kd):
    hp, ht = ao.matrix_world @ pbs["head"].head, ao.matrix_world @ pbs["head"].tail
    m = {"head_top": px(ht), "head": px((hp + ht) / 2), "neck": px(hp), "chest": px(ao.matrix_world @ pbs["chest"].head), "hips": px(ao.matrix_world @ pbs["hips"].head)}
    for s in "RL":
        m["foot." + s] = px(ao.matrix_world @ pbs["foot." + s].tail); m["knee." + s] = px(ao.matrix_world @ pbs["shin." + s].head)
        m["hand." + s] = px(ao.matrix_world @ pbs["hand." + s].head); m["hand_tip." + s] = px(ao.matrix_world @ pbs["hand." + s].tail)
    zm = min((o.matrix_world @ o.data.vertices[i].co).z for o in BIND for i in range(0, len(o.data.vertices), 4))
    from mathutils import Vector as V_
    hb_ = pbs["hips"].head; m["throw_ahead"] = px(ao.matrix_world @ (hb_ + V_((0, -1.0, 0.25))))  # THROW: point 1 unit ahead (her -Y) + 0.25 up of the hips -> ball flight direction
    m["throw_hips"] = px(ao.matrix_world @ hb_)
    m["zmin_px"] = round(zm * PPU1 * math.cos(math.radians(30)), 2)
    if kd.get("katana", 0): pom, tip = bpts(); m["blade_pommel"] = px(pom); m["blade_tip"] = px(tip)
    return m
J = json.load(open(jobp)); os.makedirs(outd_, exist_ok=True)
for job in J["jobs"]:
    set_view(job["view"]); jid = job["id"]
    seq = job.get("seq") or [{"pose": job["pose"], "ms": 0}]
    for f in seq: f["pose"].setdefault("katana", 1)
    single = "seq" not in job; loop = job.get("loop", False); meta = {"id": jid, "view": job["view"], "cell_1x": CELL1, "pivot_1x": PIV1, "ppu": PPU1, "frames": []}
    M = []; T = []
    for f in seq: pose(f["pose"]); M.append(mot()); T.append(bpts()[1].copy())
    for i, f in enumerate(seq):
        kd = f["pose"]
        if not single and job.get("secondary", True):
            j = (i - 1) % len(seq) if loop else max(0, i - 1); kd = secondary(kd, M[j], M[i], f.get("drag", 0.0))
        pose(kd); ex = []
        if f.get("smear") and f.get("arc", 1) and (loop or i > 0): ex.append(smear_obj(T[(i - 1) % len(seq)], kd, f.get("cw", True), f.get("plane", "s"))); ALL.append(ex[-1]); ex[-1].modifiers.new("outline", "SOLIDIFY").show_render = False
        stem = jid if single else f"{jid}_f{i:02d}"
        hid0 = {o: o.hide_render for o in ALL}
        for kind in (("matid", "part", "core", "blade") + (("smear",) if ex else ()) + (("guide", "shade") if os.environ.get("GUIDES") == "1" else ())):
            rpass(os.path.join(outd_, f"{stem}_{kind}.png"), kind, ex)
            for o, h in hid0.items(): o.hide_render = h
        meta["frames"].append({"i": i, "ms": f.get("ms", 0), "name": f.get("name", ""), "air": bool(kd.get("absz", 0) or kd.get("lift", 0) > 0.06), "pts": pts_meta(kd)})
        for o in ex: ALL.remove(o); bpy.data.objects.remove(o)
    json.dump(meta, open(os.path.join(outd_, f"{jid}.json"), "w"))
print("ALLDONE", len(J["jobs"]), flush=True)
