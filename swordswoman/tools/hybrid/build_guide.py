"""Build the hidden GUIDE rig hybrid/guide/guide.blend from a COPY of model/character.blend
(model/ is never written).  Re-proportions the round-9 procedural character toward
concept/chibi_iso_v5 + chibi_turnaround_v6 (the look target) and adds rig features for expressive
animation.  Deterministic; re-run after editing the PARAMS block.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/hybrid/build_guide.py

Edits (all in rest space, mesh + bones transformed together so the skin weights stay valid):
  1. head group (head, face, hair, bun, bow, ears, colliders) scaled about the chin  (HEAD_SCALE)
  2. NEW hair shell 'hair_bob': the concept's big bob -- full dome, heavy fringe down to the brow,
     side locks to the jaw, ear window, pulled-up nape.  Replaces the round-9 bangs / strands
     (hidden, kept in the file).  Side locks ride new bones hair_lock.L/R (secondary motion)
  3. face decals: eye line lowered (rotated down over the face, re-snapped to the skin), eyes
     squashed to the concept's almond height; blush / mouth follow
  4. bow: loops wider and lower (concept), loops on new bones bow_loop.L/R (secondary motion)
  5. collar: flared wider at the top
  6. skirt: side / back tails lengthened toward the floor and flared (front panel stays short)
  7. sleeves: new cuff bones sleeve_cuff.L/R (secondary motion of the bell cuffs)
  8. smear helpers smear_blade / smear_trail (hidden; render_guides rebuilds them per frame)
  9. rig['landmarks'] (bone-relative points for the joints pass) + rig['guide_meta']
"""
import bpy
import bmesh
import json
import math
import os
from mathutils import Vector as V, Matrix
from mathutils.bvhtree import BVHTree

ROOT = "/Users/waylonhuang/Documents/other/pixelart/swordswoman"
SRC = os.path.join(ROOT, "model", "character.blend")
OUT = os.path.join(ROOT, "hybrid", "guide", "guide.blend")

# ------------------------------------------------------------------ PARAMS
P = dict(
    HEAD_SCALE=1.03, HEAD_PIVOT=(0.0, 0.0, 1.80),          # chin pivot (build_character HEAD_PIVOT)
    CHIN_Z=1.80,
    SHELL_C=(0.0, 0.0, 2.32), SHELL_RX=0.645, SHELL_RY_FRONT=0.50, SHELL_RY_BACK=0.58, SHELL_TOP=2.98,
    BROW_Z=2.235, BANG_TIP=0.035, BANG_N=9, JAW_Z=1.93, NAPE_Z=1.98, LOCK_TIP=0.06,
    FRONT_DEG=60.0, LOCK_DEG=88.0, EAR_DEG=108.0, SHELL_TUCK=0.16, LOCK_FLARE=0.05, LOCK_Y=-0.14, NAPE_TUCK=0.22, SHELL_MARGIN=0.022, SHELL_THICK=0.022,
    EYE_Z=2.12, EYE_SQUASH=0.62, BLUSH_K=0.80, MOUTH_K=1.0,
    BOW_SX=1.0, BOW_SZ=0.95, BOW_SPREAD_DEG=16.0, BOW_FAT=1.2, BOW_LEN=0.92,
    BUN_MOVE=(0.0, 0.03, -0.12), BUN_SCALE=0.92, BOW_MOVE=(0.0, -0.02, 0.20), BOW_SCALE=1.06,
    COLLAR_FLARE=0.32,
    LEG_Z0=0.25, LEG_Z1=0.92, LEG_K=0.87,           # legs: compress 0.25..0.92 (shin+thigh) by LEG_K
    SKIRT_Z0=0.75, SKIRT_STRETCH=0.26, SKIRT_FLARE=0.18,
    ISO_ORTHO=6.8,
)
HEAD_GROUP = ("head", "ears", "face_decals", "hair_cap", "hair_sheen", "bangs", "hair_strands", "hair_streaks", "bun",
              "bun_crease", "bun_sheen", "bow", "hair_proxy", "head_collider")
HIDE_IN_GUIDE = ("bangs", "hair_strands", "hair_sheen", "hair_streaks", "hair_cap")


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


bpy.ops.wm.open_mainfile(filepath=SRC)
sc = bpy.context.scene
rig = bpy.data.objects["rig"]
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.location = (0, 0, 0)
    pb.rotation_quaternion = (1, 0, 0, 0)
    pb.rotation_euler = (0, 0, 0)
    pb.scale = (1, 1, 1)
rig.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()
OBJ = bpy.data.objects


def verts_apply(ob, fn, shape_keys=True):
    """fn(world_point, index) -> new world point; applied to the mesh and every shape key."""
    me = ob.data
    if me.shape_keys and shape_keys:
        basis = [V(v.co) for v in me.vertices]
        new_basis = [fn(V(c), i) for i, c in enumerate(basis)]
        for kb in me.shape_keys.key_blocks:
            for i, d in enumerate(kb.data):
                delta = V(d.co) - basis[i]
                d.co = new_basis[i] + delta
        for i, v in enumerate(me.vertices):
            v.co = new_basis[i]
    else:
        for i, v in enumerate(me.vertices):
            v.co = fn(V(v.co), i)
    me.update()


def edit_bones(fn):
    bpy.context.view_layer.objects.active = rig
    for o in bpy.context.view_layer.objects:
        o.select_set(o == rig)
    bpy.ops.object.mode_set(mode="EDIT")
    fn(rig.data.edit_bones)
    bpy.ops.object.mode_set(mode="OBJECT")


# ------------------------------------------------------------------ 1. head scale
piv = V(P["HEAD_PIVOT"])
S = P["HEAD_SCALE"]
M_head = Matrix.Translation(piv) @ Matrix.Scale(S, 4) @ Matrix.Translation(-piv)
for n in HEAD_GROUP:
    ob = OBJ.get(n)
    if ob is None:
        continue
    ob.data.transform(M_head, shape_keys=True)
    ob.data.update()
    for md in ob.modifiers:
        if md.type == "SOLIDIFY" and md.name != "Outline":
            md.thickness *= S


def _head_bones(eb):
    eb["head"].tail = M_head @ eb["head"].tail
    for n in ("bun", "bow"):
        b = eb[n]
        h, t = M_head @ b.head, M_head @ b.tail
        b.head, b.tail = h, t


edit_bones(_head_bones)
bpy.context.view_layer.update()


def bvh_of(names):
    bm = bmesh.new()
    for n in names:
        ob = OBJ[n]
        tmp = bmesh.new()
        tmp.from_mesh(ob.data)
        tmp.transform(ob.matrix_world)
        me = bpy.data.meshes.new("_tmp")
        tmp.to_mesh(me)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        tmp.free()
    bm.normal_update()
    t = BVHTree.FromBMesh(bm)
    return t, bm


BUN_OBJS = ("bun", "bun_crease", "bun_sheen", "bow")
bc = V(rig.data.bones["bun"].head_local)
M_bun = Matrix.Translation(V(P["BUN_MOVE"])) @ Matrix.Translation(bc) @ Matrix.Scale(P["BUN_SCALE"], 4) @ Matrix.Translation(-bc)
for n in BUN_OBJS:
    OBJ[n].data.transform(M_bun)
    OBJ[n].data.update()


def _bun_bones(eb):
    for n in ("bun", "bow"):
        b = eb[n]
        h, t = M_bun @ b.head, M_bun @ b.tail
        b.head, b.tail = h, t


edit_bones(_bun_bones)
bk = V(rig.data.bones["bow"].head_local)
M_bow = Matrix.Translation(V(P["BOW_MOVE"])) @ Matrix.Translation(bk) @ Matrix.Scale(P["BOW_SCALE"], 4) @ Matrix.Translation(-bk)
OBJ["bow"].data.transform(M_bow)
OBJ["bow"].data.update()
for md in OBJ["bow"].modifiers:
    if md.type == "SOLIDIFY" and md.name != "Outline":
        md.thickness *= P["BOW_SCALE"]


def _bow_bone(eb):
    b = eb["bow"]
    h, t = M_bow @ b.head, M_bow @ b.tail
    b.head, b.tail = h, t


edit_bones(_bow_bone)
bpy.context.view_layer.update()
HEAD_BVH, _hbm = bvh_of(["head"])
SHELL_BVH = HEAD_BVH   # the round-9 skull cap is hidden in the guide (the shell replaces it)


# ------------------------------------------------------------------ 3. face decals
fd = OBJ["face_decals"]
mats = [s.material.name if s.material else "" for s in fd.material_slots]
vcat = {}
for poly in fd.data.polygons:
    m = mats[poly.material_index]
    cat = "eye" if any(k in m for k in ("eye", "glint", "ink")) else ("mouth" if "mouth" in m else "blush")
    for vi in poly.vertices:
        vcat[vi] = cat
eye_vs = [i for i, c in vcat.items() if c == "eye"]
co = [V(v.co) for v in fd.data.vertices]
C = V(P["SHELL_C"])
eye_c = {s: sum((co[i] for i in eye_vs if (co[i].x > 0) == (s > 0)), V()) / max(1, sum(1 for i in eye_vs if (co[i].x > 0) == (s > 0)))
         for s in (1, -1)}
eye_z = (eye_c[1].z + eye_c[-1].z) / 2
Rf = 0.60
ang = math.asin(max(-1, min(1, (eye_z - C.z) / Rf))) - math.asin(max(-1, min(1, (P["EYE_Z"] - C.z) / Rf)))
R_face = Matrix.Translation(C) @ Matrix.Rotation(ang, 4, "X") @ Matrix.Translation(-C)
offs = {}


def _decal(p, i):
    cat = vcat.get(i, "blush")
    q = V(p)
    if cat == "eye":
        ec = eye_c[1 if p.x > 0 else -1]
        q.z = ec.z + (q.z - ec.z) * P["EYE_SQUASH"]
    else:
        k = P["BLUSH_K"] if cat == "blush" else P["MOUTH_K"]
        q.z = eye_z + (q.z - eye_z) * k
    q = R_face @ q
    if i not in offs:
        loc0, n0, _, _ = HEAD_BVH.find_nearest(p)
        off = (p - loc0).dot(n0) if loc0 is not None else 0.004
        loc1, n1, _, _ = HEAD_BVH.find_nearest(q)
        offs[i] = (loc1 + n1 * max(off, 0.002)) - q if loc1 is not None else V()
    return q + offs[i]


verts_apply(fd, _decal)

# ------------------------------------------------------------------ 2. hair shell
RX, RYF, RYB = P["SHELL_RX"], P["SHELL_RY_FRONT"], P["SHELL_RY_BACK"]
RZ = P["SHELL_TOP"] - C.z


def rho0(phi):
    ry = RYF if math.cos(phi) > 0 else RYB          # phi measured from the front (-Y)
    s, c = math.sin(phi), math.cos(phi)
    return 1.0 / math.sqrt((s / RX) ** 2 + (c / ry) ** 2)


ears = OBJ.get("ears")
EAR_TOP = max((ears.matrix_world @ v.co).z for v in ears.data.vertices) - 0.15 if ears else 2.2   # hem over the ear: only the lobe shows


def tri(x):
    f = x - math.floor(x)
    return 1 - abs(f - 0.5) * 2


def hem(phi):
    a = abs(math.degrees(phi))
    side = 1 if phi > 0 else -1                       # +phi = her left (+X)
    # fringe: pointed tips, swept to HER RIGHT (tips shifted toward -phi), longest right of centre
    bang = P["BROW_Z"] - P["BANG_TIP"] * tri(phi / math.radians(2 * P["FRONT_DEG"]) * P["BANG_N"] + 0.5 + 0.25) \
        - 0.02 * smoothstep(10, -30, math.degrees(phi)) + 0.015 * smoothstep(5, 35, math.degrees(phi))
    lock = P["JAW_Z"] - P["LOCK_TIP"] * tri((a - P["FRONT_DEG"]) / (P["LOCK_DEG"] - P["FRONT_DEG"]) * 2.0)
    ear = EAR_TOP
    nape = P["NAPE_Z"]
    w1 = smoothstep(P["FRONT_DEG"] - 6, P["FRONT_DEG"] + 6, a)
    w2 = smoothstep(P["LOCK_DEG"] - 5, P["LOCK_DEG"] + 5, a)
    w3 = smoothstep(P["EAR_DEG"] - 6, P["EAR_DEG"] + 10, a)
    z = lerp(bang, lock, w1)
    z = lerp(z, ear, w2)
    z = lerp(z, nape, w3)
    return z


NU, NUP, NLO = 144, 18, 16
verts, faces, lockw = [], [], []
zmin_all = min(hem(2 * math.pi * i / NU - math.pi) for i in range(NU))
for i in range(NU):
    phi = 2 * math.pi * i / NU - math.pi
    r0 = rho0(phi)
    dx, dy = math.sin(phi), -math.cos(phi)
    col = []
    for j in range(NUP):                                     # dome: top -> equator
        el = math.pi / 2 * (1 - j / NUP)
        col.append(V((C.x + dx * r0 * math.cos(el), C.y + dy * r0 * math.cos(el), C.z + RZ * math.sin(el))))
    zh = hem(phi)
    for j in range(NLO + 1):                                 # bob sides: equator -> hem
        t = j / NLO
        z = lerp(C.z, zh, t)
        tt = (C.z - z) / max(1e-6, C.z - zmin_all)
        a_ = abs(math.degrees(phi))
        wl = smoothstep(P["FRONT_DEG"] - 8, P["FRONT_DEG"] + 8, a_)          # 0 fringe .. 1 locks
        wn = smoothstep(P["EAR_DEG"] - 10, P["EAR_DEG"] + 20, a_)           # nape
        tuck = lerp(lerp(P["SHELL_TUCK"], -P["LOCK_FLARE"], wl), P["NAPE_TUCK"], wn)
        r = r0 * (1 - tuck * tt * tt)
        q = V((C.x + dx * r, C.y + dy * r, z))
        # side locks hang BEHIND the face front (concept profile: the eye and cheek stay in front)
        wz = smoothstep(P["BROW_Z"] + 0.10, P["BROW_Z"] - 0.02, z) * wl
        if wz > 0 and q.y < P["LOCK_Y"]:
            q.y = lerp(q.y, P["LOCK_Y"], wz)
        col.append(q)
    # keep clear of the skin
    for k, p in enumerate(col):
        d = p - V((C.x, C.y, min(p.z, C.z) if k >= NUP else C.z))
        d = d.normalized() if d.length > 1e-6 else V((0, 0, 1))
        for _ in range(40):
            loc, nrm, _, dist = SHELL_BVH.find_nearest(p)
            if loc is None:
                break
            inside = (p - loc).dot(nrm) < 0
            if inside or dist < P["SHELL_MARGIN"]:
                p = p + d * 0.006
            else:
                break
        col[k] = p
    a = abs(math.degrees(phi))
    lw = smoothstep(P["FRONT_DEG"] - 4, P["FRONT_DEG"] + 8, a) * (1 - smoothstep(P["LOCK_DEG"] - 4, P["LOCK_DEG"] + 4, a))
    for k, p in enumerate(col):
        verts.append(p)
        zt = C.z - 0.05
        lockw.append((lw * smoothstep(zt, P["JAW_Z"] + 0.05, p.z) if p.z < zt else 0.0, 1 if phi > 0 else -1))
NV = NUP + NLO + 1
top = len(verts)
verts.append(V((C.x, C.y, C.z + RZ)))
lockw.append((0.0, 1))
for i in range(NU):
    i2 = (i + 1) % NU
    faces.append((top, i2 * NV, i * NV))
    for j in range(NV - 1):
        faces.append((i * NV + j, i2 * NV + j, i2 * NV + j + 1, i * NV + j + 1))
me = bpy.data.meshes.new("hair_bob")
me.from_pydata([tuple(v) for v in verts], [], faces)
me.update()
hb = bpy.data.objects.new("hair_bob", me)
OBJ["hair_cap"].users_collection[0].objects.link(hb)
hb.parent = rig
hb.matrix_parent_inverse = rig.matrix_world.inverted()
hair_mat = OBJ["hair_cap"].material_slots[0].material   # (cap mesh kept, hidden)
me.materials.append(hair_mat)
for poly in me.polygons:
    poly.use_smooth = True
for n in HIDE_IN_GUIDE:
    if OBJ.get(n):
        OBJ[n].hide_render = True
        OBJ[n].hide_viewport = True


# ------------------------------------------------------------------ 4/5/6. bow, collar, skirt
bow_b = rig.data.bones["bow"]
K = V(bow_b.head_local)


def _bow(p, i):
    d = p - K
    if d.z > 0:
        s_ = 1 if d.x > 0 else -1
        ax = V((math.sin(math.radians(35)) * s_, 0, math.cos(math.radians(35))))   # build: ears 35 deg off vertical
        along = d.dot(ax)
        perp = V((d.x, 0, d.z)) - ax * along
        w = smoothstep(0.0, 0.08, abs(d.x)) if d.z > 0 else 0.0
        d2 = ax * along * P["BOW_LEN"] + perp * lerp(1.0, P["BOW_FAT"], w)
        d2 = Matrix.Rotation(math.radians(P["BOW_SPREAD_DEG"]) * s_ * w, 3, "Y") @ d2
        d = V((d2.x, d.y, d2.z))
        d.z *= P["BOW_SZ"]
    d.x *= P["BOW_SX"]
    return K + d


verts_apply(OBJ["bow"], _bow)


def _collar(p, i):
    f = 1 + P["COLLAR_FLARE"] * smoothstep(1.70, 2.00, p.z)
    q = V(p)
    q.x *= f
    q.y = 0.05 + (q.y - 0.05) * f
    return q


verts_apply(OBJ["collar"], _collar)


def skirt_warp(p):
    z0 = P["SKIRT_Z0"]
    if p.z >= z0:
        return V(p)
    d = V((p.x, p.y - 0.05, 0))
    ny = d.normalized().y if d.length > 1e-6 else 0.0           # -1 front .. +1 back
    k = 1 + P["SKIRT_STRETCH"] * smoothstep(-0.55, 0.15, ny)
    t = min(1.0, (z0 - p.z) / (z0 - 0.21))
    f = 1 + P["SKIRT_FLARE"] * t * smoothstep(-0.7, 0.0, ny)
    z = z0 - (z0 - p.z) * k
    return V((p.x * f, 0.05 + (p.y - 0.05) * f, max(0.03, z)))


for n in ("skirt_outer", "skirt_under"):
    verts_apply(OBJ[n], lambda p, i: skirt_warp(p))


def _skirt_bones(eb):
    for b in eb:
        if b.name.startswith("skirt"):
            b.head, b.tail = skirt_warp(V(b.head)), skirt_warp(V(b.tail))


edit_bones(_skirt_bones)


# ------------------------------------------------------------------ 6b. shorter legs
# z in [LEG_Z0, LEG_Z1] (shin + thigh) is compressed by LEG_K; everything above moves down rigidly by D.
# Leg / skirt / shorts / pelvis meshes get the remap; upper-body parts that hang below the hips (arms,
# hands, sleeves, scarf, katana) move rigidly so they keep their shape.
Z0, Z1, LK = P["LEG_Z0"], P["LEG_Z1"], P["LEG_K"]
DL = (Z1 - Z0) * (1 - LK)


def leg_f(z):
    if z <= Z0:
        return z
    if z <= Z1:
        return Z0 + (z - Z0) * LK
    return z - DL


REMAP_OBJS = ("leg.L", "leg.R", "foot.L", "foot.R", "shoe.L", "shoe.R", "shorts", "thigh_strap.L", "skirt_outer",
              "skirt_under", "body_torso", "corset", "corset_buckles", "corset_tabs", "belt_pouch", "bodice")
for ob in OBJ:
    if ob.type != "MESH" or ob.name.startswith("smear"):
        continue
    if ob.name in REMAP_OBJS:
        verts_apply(ob, lambda p, i: V((p.x, p.y, leg_f(p.z))))
    else:
        verts_apply(ob, lambda p, i: V((p.x, p.y, p.z - DL)))
REMAP_BONES = ("thigh", "shin", "foot", "toe", "knee", "skirt", "root", "toe_pivot", "foot_ctrl", "foot_ik", "knee_pole")


def _leg_bones(eb):
    for b in eb:
        if b.name.startswith(REMAP_BONES):
            h, t = V(b.head), V(b.tail)
            b.head, b.tail = V((h.x, h.y, leg_f(h.z))), V((t.x, t.y, leg_f(t.z)))
        else:
            b.head, b.tail = V(b.head) - V((0, 0, DL)), V(b.tail) - V((0, 0, DL))


edit_bones(_leg_bones)
bpy.context.view_layer.update()
C = C - V((0, 0, DL))
K = V(rig.data.bones["bow"].head_local)
verts = [V(p) - V((0, 0, DL)) for p in verts]


# ------------------------------------------------------------------ 2b/4b/7. secondary bones + weights
def lock_tips():
    out = {}
    for s in (1, -1):
        cands = [(p, w) for p, (w, sd) in zip(verts, lockw) if sd == s and w > 0.5]
        lo = min(cands, key=lambda x: x[0].z)[0] if cands else V((0.55 * s, -0.3, 1.95))
        hi = V((lo.x * 0.97, lo.y, C.z - 0.05))
        out[s] = (hi, lo)
    return out


LT = lock_tips()
bow_tips = {}
bw = OBJ["bow"]
for s in (1, -1):
    pts = [bw.matrix_world @ v.co for v in bw.data.vertices if (v.co.x - K.x) * s > 0.05]
    bow_tips[s] = max(pts, key=lambda p: (p - K).length) if pts else K + V((0.3 * s, 0, 0.3))


def _new_bones(eb):
    for s, side in ((1, "L"), (-1, "R")):
        b = eb.new(f"hair_lock.{side}")
        b.head, b.tail = LT[s]
        b.parent = eb["head"]
        b.use_deform = True
        b = eb.new(f"bow_loop.{side}")
        b.head = K + (bow_tips[s] - K) * 0.12
        b.tail = bow_tips[s]
        b.parent = eb["bow"]
        b.use_deform = True
        sl = eb[f"sleeve.{side}"]
        b = eb.new(f"sleeve_cuff.{side}")
        b.head = sl.head.lerp(sl.tail, 0.5)
        b.tail = sl.tail + (sl.tail - sl.head) * 0.25
        b.roll = sl.roll
        b.parent = sl
        b.use_deform = True


edit_bones(_new_bones)

# hair_bob weights + armature
vg_h = hb.vertex_groups.new(name="head")
vg_l = {1: hb.vertex_groups.new(name="hair_lock.L"), -1: hb.vertex_groups.new(name="hair_lock.R")}
for i, (w, s) in enumerate(lockw):
    vg_h.add([i], 1.0 - w, "REPLACE")
    if w > 0:
        vg_l[s].add([i], w, "REPLACE")
am = hb.modifiers.new("Armature", "ARMATURE")
am.object = rig
ss = hb.modifiers.new("Subsurf", "SUBSURF")
ss.levels = 1
ss.render_levels = 1
so = hb.modifiers.new("Thickness", "SOLIDIFY")
so.thickness = P["SHELL_THICK"]
so.offset = -1

# bow loops
vgb = bw.vertex_groups["bow"]
vbl = {1: bw.vertex_groups.new(name="bow_loop.L"), -1: bw.vertex_groups.new(name="bow_loop.R")}
for v in bw.data.vertices:
    dx = v.co.x - K.x
    s = 1 if dx > 0 else -1
    w = smoothstep(0.03, 0.14, abs(dx)) * smoothstep(-0.02, 0.06, v.co.z - K.z)
    vgb.add([v.index], 1.0 - w, "REPLACE")
    if w > 0:
        vbl[s].add([v.index], w, "REPLACE")

# sleeve cuffs
for side in ("L", "R"):
    ob = OBJ[f"sleeve.{side}"]
    b = rig.data.bones[f"sleeve.{side}"]
    h, t = V(b.head_local), V(b.tail_local)
    g_sl = ob.vertex_groups[f"sleeve.{side}"]
    g_cf = ob.vertex_groups.new(name=f"sleeve_cuff.{side}")
    gi = g_sl.index
    for v in ob.data.vertices:
        w = next((g.weight for g in v.groups if g.group == gi), 0.0)
        if w <= 0:
            continue
        tt = (v.co - h).dot(t - h) / (t - h).length_squared
        c = smoothstep(0.35, 0.85, tt)
        if c > 0:
            g_sl.add([v.index], w * (1 - c), "REPLACE")
            g_cf.add([v.index], w * c, "REPLACE")

# ------------------------------------------------------------------ 8. smear helpers
for n in ("smear_blade", "smear_trail"):
    me = bpy.data.meshes.new(n)
    ob = bpy.data.objects.new(n, me)
    sc.collection.objects.link(ob)
    ob.hide_render = True
    ob["guide_note"] = "rebuilt per frame by tools/hybrid/render_guides.py from the pose JSON 'smears' list"

# ------------------------------------------------------------------ 9. landmarks + meta
bpy.context.view_layer.update()


def centroid(pts):
    return sum(pts, V()) / max(1, len(pts))


fdw = [fd.matrix_world @ v.co for v in fd.data.vertices]
eyes = {s: centroid([fdw[i] for i in eye_vs if (fdw[i].x > 0) == (s > 0)]) for s in (1, -1)}
mouth = centroid([fdw[i] for i, c in vcat.items() if c == "mouth"])
hv = [hb.matrix_world @ V(p) for p in verts]
head_top = max(hv, key=lambda p: p.z)
headw = [OBJ["head"].matrix_world @ v.co for v in OBJ["head"].data.vertices]
chin = min([p for p in headw if p.y < -0.10 and abs(p.x) < 0.05] or headw, key=lambda p: p.z)
bunw = [OBJ["bun"].matrix_world @ v.co for v in OBJ["bun"].data.vertices]
kat = OBJ["katana"]
sb = rig.data.bones["sword"]
sh, sd = V(sb.head_local), (V(sb.tail_local) - V(sb.head_local)).normalized()
kw = [kat.matrix_world @ v.co for v in kat.data.vertices]
proj = [((p - sh).dot(sd), p) for p in kw]
tip = max(proj, key=lambda x: x[0])[1]
pommel = min(proj, key=lambda x: x[0])[1]


def perp(p):
    q = p - sh
    return (q - sd * q.dot(sd)).length


# guard = along-axis position of the widest cross-section (bar + kagi hook)
bins = {}
for a_, p in proj:
    k_ = round(a_ / 0.02)
    bins[k_] = max(bins.get(k_, 0.0), perp(p))
gk = max(bins, key=lambda k_: bins[k_])
guard = sh + sd * (gk * 0.02)
hook = max([p for a_, p in proj if abs(a_ - gk * 0.02) < 0.12], key=perp)
heels = {}
for s, side in ((1, "L"), (-1, "R")):
    sw = [OBJ[f"shoe.{side}"].matrix_world @ v.co for v in OBJ[f"shoe.{side}"].data.vertices]
    heels[s] = min([p for p in sw if p.z < 0.05] or sw, key=lambda p: -p.y)
LM = {
    "eye_L": ["head", list(eyes[1])], "eye_R": ["head", list(eyes[-1])], "mouth": ["head", list(mouth)],
    "face": ["head", list((eyes[1] + eyes[-1]) / 2 * 0.6 + mouth * 0.4)],
    "head_center": ["head", list(C)], "head_top": ["head", list(head_top)], "chin": ["head", list(chin)],
    "bun": ["bun", list(centroid(bunw))], "bow": ["bow", list(K)],
    "bow_loop_L": ["bow_loop.L", list(bow_tips[1])], "bow_loop_R": ["bow_loop.R", list(bow_tips[-1])],
    "sword_tip": ["sword", list(tip)], "sword_pommel": ["sword", list(pommel)], "sword_guard": ["sword", list(guard)],
    "sword_hook": ["sword", list(hook)],
    "heel_L": ["foot.L", list(heels[1])], "heel_R": ["foot.R", list(heels[-1])],
}
LM = {k_: [b, [round(c, 5) for c in p]] for k_, (b, p) in LM.items()}
rig["landmarks"] = json.dumps(LM)
rig["iso_ortho"] = P["ISO_ORTHO"]
allz = [p.z for o in OBJ if o.type == "MESH" and not o.hide_render and not o.name.startswith(("katana", "smear", "saya"))
        for p in [o.matrix_world @ v.co for v in o.data.vertices]]
H_new = head_top.z - chin.z
meta = {"source": "model/character.blend (round 9) re-proportioned by tools/hybrid/build_guide.py", "params": P,
        "note_params": "z-valued params are in pre-leg-compression space; everything above the hips was then lowered by leg_shift",
        "leg_shift": round(DL, 4),
        "H_world": round(H_new, 4), "crown_z": round(head_top.z, 4), "chin_z": round(chin.z, 4),
        "top_z_incl_bow": round(max(allz), 4),
        "sleeve_tip_L": "sleeve_cuff.L", "sleeve_tip_R": "sleeve_cuff.R",
        "secondary_chains": {"bun": ["bun"], "bow": ["bow", "bow_loop.L", "bow_loop.R"],
                             "ribbons": ["scarf.L.001-005", "scarf.R.001-005"],
                             "skirt": ["skirt.F, skirt.F.001", "skirt.L-.002", "skirt.R-.002", "skirt.B, skirt.tail.001-003"],
                             "sleeves": ["sleeve.L > sleeve_cuff.L", "sleeve.R > sleeve_cuff.R"],
                             "hair": ["hair_lock.L", "hair_lock.R"]},
        "squash_stretch": {"root": "whole body about the floor (feet stay planted)", "cog": "body above the feet incl. legs IK",
                           "spine": "upper body about the waist", "chest": "chest + head + arms", "head": "head about the neck",
                           "bun": "bun", "hips": "hips + legs (legs are IK; prefer cog / spine)"},
        "hidden_in_guide": list(HIDE_IN_GUIDE)}
rig["guide_meta"] = json.dumps(meta)
# rig reference for pose authors (bones, parents, rest points, which local axis is 'up')
def _vax(b):
    M = b.matrix_local.to_3x3()
    c = [abs(M.col[i].z) for i in range(3)]
    return "XYZ"[c.index(max(c))]


ref = {"note": "rest pose, armature space (= world at yaw 0): +X her LEFT, -Y her FRONT (S), +Z up, 1 unit = 1 old H; "
               "guide head height H' = %.3f" % H_new,
       "bones": {b.name: {"parent": b.parent.name if b.parent else None, "head": [round(c, 4) for c in b.head_local],
                          "tail": [round(c, 4) for c in b.tail_local], "deform": b.use_deform, "up_axis": _vax(b),
                          "local_axes_world": {a: [round(c, 3) for c in b.matrix_local.to_3x3().col[i]] for i, a in enumerate("XYZ")},
                          "constraints": [c.type + ":" + c.name for c in rig.pose.bones[b.name].constraints]}
                 for b in rig.data.bones},
       "props": {k_: (rig[k_] if isinstance(rig[k_], (int, float)) else "str") for k_ in rig.keys()
                 if k_ not in ("poses", "landmarks", "guide_meta", "cycles", "pose_names", "idle_sword_dir")},
       "actions": sorted(a.name for a in bpy.data.actions),
       "landmarks": LM}
json.dump(ref, open(os.path.join(os.path.dirname(OUT), "rig_reference.json"), "w"), indent=1)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True, copy=False)
print("[build_guide] saved", OUT)
print("GUIDE_META", json.dumps(meta))
print("LANDMARKS", json.dumps(LM))
