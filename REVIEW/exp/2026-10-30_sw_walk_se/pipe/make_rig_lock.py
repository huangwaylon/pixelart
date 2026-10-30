"""make_rig_lock.py  (Blender, step 1a): rig r13 COPY -> pipe/rig_lock.blend with the DESIGN_LOCK silhouette changes.
  <blender> -b <skinned>/rig/rig.blend -P pipe/make_rig_lock.py -- pipe/rig_lock.blend pipe/face_calib.json
Bones, weights and the skeleton are unchanged (motion files stay valid); only rest vertex positions and attributes change.
 1. Sleeves (lock 4): every sleeve-material vertex on an arm is pulled radially toward the arm axis (upper arm -> forearm line) by
    SLEEVE_S(T) (T = 0 shoulder .. 1 elbow .. 2 wrist), so the bell sleeve becomes a slim tube with a small cuff flare; cuff
    vertices past CUFF_T are pulled back along the axis, so the hand reads outside the sleeve.
 2. Waist (lock 4): dress/obi vertices in the obi band are scaled toward the torso axis by up to WAIST_IN -> a clear inward step
    at the obi (waist break), the skirt below keeps its flare.
 3. PARTID colour attribute (one flat colour per body part: leg.L leg.R arm.L arm.R torso head; 0/255 channels so the 8-bit
    render is exact) for the interior-line pass; hands/neck/face/hair/bow are told apart by material in the pixel step.
 4. Face = flat skin: the illustration-classified r13 head labels the drawn eyes/mouth/blush as hair/bow; faces inside the
    S face-feature mask (eye dome row and below) are reset to skin (the eyes/brows come from the stamp in step 4 of the build).
 4b. Bow vs hair cleaned by a voxel majority vote (solid bow, no red specks in the hair).
 4c. Where the SE illustration projection saw the head, bow vs hair follows the illustration colour (red = bow).
 5. Eye tracking vertices (step 4, facesys b'): nearest face-skin rest vertex to each calibrated surface eye point
    (face_calib.json) -> armature prop 'lock_eye_verts'. The renderer reports their deformed screen position + depth.
    Sock/boot tones are a palette decision (lock_chain.py RAMP), not geometry."""
import bpy, sys, os, json, numpy as np
SK_RIG = "/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned/rig"
argv = sys.argv[sys.argv.index("--") + 1:]
OUT, CAL = argv[0], argv[1]
ao = bpy.data.objects["rig"]; body = bpy.data.objects["body"]; me = body.data
MAT = list(ao["mat_names"]) if not isinstance(ao["mat_names"], str) else eval(ao["mat_names"])  # [hair dress skin sleeve socks boots bow obi eyes]
mi = {n: i for i, n in enumerate(MAT)}
names = [g.name for g in body.vertex_groups]
co = np.array([v.co for v in me.vertices]); n = len(co)
fm = np.zeros(len(me.polygons), int); me.attributes["mat"].data.foreach_get("value", fm); fm_orig = fm.copy()
vm = np.full(n, -1)
for p in me.polygons: vm[list(p.vertices)] = fm[p.index]
dom = np.array([names[max(v.groups, key=lambda e: e.weight).group] if v.groups else "root" for v in me.vertices])
B = ao.data.bones
H = lambda b: np.array(B[b].head_local)

# ---- 1. sleeves
SLEEVE_T = [0.0, 0.5, 1.0, 1.4, 1.8, 2.3]
SLEEVE_S = [1.0, 0.95, 0.82, 0.66, 0.58, 0.58]
CUFF_T, CUFF_K = 1.85, 0.35
moved = 0
for s, sg in (("L", -1), ("R", 1)):
    P0, P1, P2 = H("upper_arm." + s), H("forearm." + s), H("hand." + s)
    sel = np.where((vm == mi["sleeve"]) & (np.sign(co[:, 0]) == sg) & np.array([not d.startswith(("chest", "spine", "pelvis", "neck")) for d in dom]))[0]
    p = co[sel]
    def seg(a, b, lo, hi):
        ab = b - a; t = np.clip(((p - a) @ ab) / (ab @ ab), lo, hi); q = a + t[:, None] * ab
        return np.linalg.norm(p - q, axis=1), t, q
    d0, t0, q0 = seg(P0, P1, 0, 1); d1, t1, q1 = seg(P1, P2, 0, 1.5)
    use1 = d1 < d0; T = np.where(use1, 1 + t1, t0); q = np.where(use1[:, None], q1, q0)
    off = p - q; k = np.interp(T, SLEEVE_T, SLEEVE_S)
    Tn = np.where(T > CUFF_T, CUFF_T + CUFF_K * (T - CUFF_T), T)
    qn = np.where((Tn >= 1)[:, None], P1 + (Tn - 1)[:, None] * (P2 - P1), P0 + Tn[:, None] * (P1 - P0))
    co[sel] = qn + off * k[:, None]; moved += len(sel)
print("LOCK sleeves: moved", moved, "verts")

# ---- 2. waist break
WAIST_Z = (0.785, 0.872); WAIST_FALL = 0.025; WAIST_IN = 0.07
tor = np.isin(vm, [mi["dress"], mi["obi"]]) & np.array([d in ("pelvis", "spine", "chest") or d.startswith("skirt") for d in dom])
yc = float(co[(vm == mi["obi"]), 1].mean())
z = co[:, 2]; w = np.clip(np.minimum(z - (WAIST_Z[0] - WAIST_FALL), (WAIST_Z[1] + WAIST_FALL) - z) / WAIST_FALL, 0, 1)
w = w * w * (3 - 2 * w); f = 1 - WAIST_IN * w * tor
co[:, 0] *= f; co[:, 1] = yc + (co[:, 1] - yc) * f
print("LOCK waist: verts", int((w * tor > 0).sum()), "yc", round(yc, 4))
me.vertices.foreach_set("co", co.ravel()); me.update()

# ---- 3. part IDs
PARTC = {"leg.L": (1, 0, 0), "leg.R": (0, 1, 0), "arm.L": (0, 0, 1), "arm.R": (1, 1, 0), "torso": (1, 0, 1), "head": (0, 1, 1)}
def part_of(g):
    for s in "LR":
        if g in (f"thigh.{s}", f"shin.{s}", f"foot.{s}", f"toe.{s}"): return "leg." + s
        if g in (f"shoulder.{s}", f"upper_arm.{s}", f"forearm.{s}", f"hand.{s}") or g.startswith(f"sleeve.{s}"): return "arm." + s
    if g.startswith("skirt") or g in ("root", "pelvis", "spine", "chest", "neck"): return "torso"  # neck = torso: chin|neck is a part edge
    return "head"
vp = np.array([part_of(d) for d in dom])
vp[np.char.startswith(vp, "leg") & np.isin(vm, [mi["dress"], mi["sleeve"], mi["obi"]])] = "torso"  # skirt cloth on the thighs
if me.color_attributes.get("PARTID"): me.color_attributes.remove(me.color_attributes["PARTID"])
ca = me.color_attributes.new("PARTID", "BYTE_COLOR", "CORNER")
cols = []
for poly in me.polygons:
    vs = [vp[i] for i in poly.vertices]; c = PARTC[max(sorted(set(vs)), key=vs.count)]
    for l in poly.loop_indices: cols.extend((*c, 1.0))
ca.data.foreach_set("color", cols)
json_parts = {k: list(v) for k, v in PARTC.items()}
ao["lock_parts"] = json.dumps(json_parts)

# ---- 4. face = flat skin. r13 has no eye/mouth matids, but its illustration-classified head labels the drawn eyes, mouth and blush
# as 'hair'/'bow' (dark/red colour classes). Head faces in front (y > FACE_Y) whose rest (x, z) falls in the S face-feature mask
# (rig/tex/face_mask_S.png, rows >= FACE_ROW0 = eye dome and below, so the bangs/brow band is untouched; +1 px) are reset to skin,
# in both the 'mat' attribute and the guide colour. Chart = facesys common.to_chart (S-master px from rest x, z).
CX0, CXS, CY0, CZ0, CZS = 63.95, 0.01473, 52.0, 1.2249, 0.01706
FACE_Y, FACE_ROW0 = 0.05, 46
img = bpy.data.images.load("/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned/rig/tex/face_mask_S.png")
mk = np.array(img.pixels[:]).reshape(img.size[1], img.size[0], 4)[::-1, :, 0] > 0.5
mk[:FACE_ROW0] = False
mkd = mk.copy(); mkd[1:] |= mk[:-1]; mkd[:-1] |= mk[1:]; mkd[:, 1:] |= mk[:, :-1]; mkd[:, :-1] |= mk[:, 1:]
fc = np.array([p.center for p in me.polygons]); fdom = np.array([max(sorted(set(dom[list(p.vertices)].tolist())), key=list(dom[list(p.vertices)]).count) for p in me.polygons])
u = np.floor(CX0 - fc[:, 0] / CXS).astype(int); w = np.floor(CY0 - (fc[:, 2] - CZ0) / CZS).astype(int)
inb = (u >= 0) & (u < 128) & (w >= 0) & (w < 128)
hit = np.zeros(len(fc), bool); hit[inb] = mkd[w[inb], u[inb]]
reset = hit & (fc[:, 1] > FACE_Y) & (fdom == "head") & (fm != mi["skin"])
gc = me.color_attributes["Color"]; skin_f = int(np.where(fm == mi["skin"])[0][0])
skin_col = tuple(gc.data[me.polygons[skin_f].loop_indices[0]].color)
for fi in np.where(reset)[0]:
    for l in me.polygons[fi].loop_indices: gc.data[l].color = skin_col
fm[reset] = mi["skin"]; me.attributes["mat"].data.foreach_set("value", fm)
for p in me.polygons:
    if reset[p.index]: vm[list(p.vertices)] = mi["skin"]
print("LOCK face: faces reset to flat skin:", int(reset.sum()), "(by mat:", np.bincount(np.array(fm_orig)[reset], minlength=9).tolist(), ")")

# ---- 4b. bow vs hair: the illustration classification scatters 'bow' flecks through the hair and leaves holes in the bow.
# Majority vote on a BOW_VOX voxel grid (3x3x3 box) over head hair/bow faces -> solid bow shapes, no red specks in the hair.
BOW_VOX, BOW_T = 0.012, 0.45
hb = np.isin(fm, [mi["hair"], mi["bow"]]) & (fc[:, 2] > 1.0) & ~reset
vi = np.floor(fc[hb] / BOW_VOX).astype(int); vi -= vi.min(0); dims = vi.max(0) + 3
cnt = np.zeros(dims); bow = np.zeros(dims); isb = (fm[hb] == mi["bow"]).astype(float)
np.add.at(cnt, tuple((vi + 1).T), 1.0); np.add.at(bow, tuple((vi + 1).T), isb)
def box3(a):
    o = np.zeros_like(a)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1): o += np.roll(np.roll(np.roll(a, dx, 0), dy, 1), dz, 2)
    return o
frac = box3(bow) / np.maximum(box3(cnt), 1e-9); newb = frac[tuple((vi + 1).T)] > BOW_T
idx = np.where(hb)[0]; chg = idx[newb != (fm[hb] == mi["bow"])]
bow_f = int(np.where(fm == mi["bow"])[0][0]); hair_f = int(np.where(fm == mi["hair"])[0][0])
bcol = tuple(gc.data[me.polygons[bow_f].loop_indices[0]].color); hcol = tuple(gc.data[me.polygons[hair_f].loop_indices[0]].color)
for fi in chg:
    tob = fm[fi] == mi["hair"]; fm[fi] = mi["bow"] if tob else mi["hair"]
    for l in me.polygons[fi].loop_indices: gc.data[l].color = bcol if tob else hcol
me.attributes["mat"].data.foreach_set("value", fm)
print("LOCK bow/hair majority: faces changed", len(chg), "-> bow faces", int((fm == mi["bow"]).sum()))

# ---- 4c. where the SE illustration saw the face (pm_SE), the bow/hair split follows the illustration colour (red = bow): the SE
# bow keeps its drawn shape. Sampled once at the face's pj_SE uv from rig/tex_illus/SE.png (r10 projection, read-only).
ti = bpy.data.images.load(SK_RIG + "/tex_illus/SE.png"); TW, TH = ti.size
tx = np.array(ti.pixels[:]).reshape(TH, TW, 4)[..., :3]
pm = np.zeros(len(fm)); me.attributes["pm_SE"].data.foreach_get("value", pm)
uvl = me.uv_layers["pj_SE"].data; nl = len(uvl); uva = np.zeros(nl * 2); uvl.foreach_get("uv", uva); uva = uva.reshape(-1, 2)
ls_ = np.zeros(len(fm), int); me.polygons.foreach_get("loop_start", ls_); lt_ = np.zeros(len(fm), int); me.polygons.foreach_get("loop_total", lt_)
csum = np.vstack([np.zeros((1, 2)), np.cumsum(uva, 0)]); fuv = (csum[ls_ + lt_] - csum[ls_]) / lt_[:, None]
sel4 = np.where(np.isin(fm, [mi["hair"], mi["bow"]]) & (pm > 0.5) & (fc[:, 2] > 1.0))[0]
px_ = np.clip((fuv[sel4, 0] * TW).astype(int), 0, TW - 1); py_ = np.clip((fuv[sel4, 1] * TH).astype(int), 0, TH - 1)
cc = tx[py_, px_]; red = (cc[:, 0] > 0.25) & (cc[:, 0] > 2.2 * cc[:, 1]) & (cc[:, 0] > 1.8 * cc[:, 2])
n4c = 0
for fi, r_ in zip(sel4, red):
    want = mi["bow"] if r_ else mi["hair"]
    if fm[fi] != want:
        fm[fi] = want; n4c += 1
        for l in me.polygons[fi].loop_indices: gc.data[l].color = bcol if r_ else hcol
me.attributes["mat"].data.foreach_set("value", fm)
print("LOCK bow from SE illustration: faces changed", n4c, "-> bow faces", int((fm == mi["bow"]).sum()))

# ---- 5. eye tracking vertices (after the face reset, so the nearest vertex is face skin)
cal = json.load(open(CAL)); cand = np.where((vm == mi["skin"]) & (dom == "head"))[0]
ev = {}
for e in cal["eyes"]:
    P = np.array(e["rest_m"]); i = int(cand[np.argmin(((co[cand] - P) ** 2).sum(1))]); ev[e["key"]] = i
    print("LOCK eye", e["key"], "vertex", i, "dist mm", round(float(np.linalg.norm(co[i] - P)) * 1000, 2))
ao["lock_eye_verts"] = json.dumps(ev)
# ---- 6. Amendment 1: toward the master EC0_SE_96 proportions (after the eye vertices are picked; bones unchanged)
A1 = dict(HEAD_XY=1.10, HEAD_Z=1.0, NECK_Z=1.03, V_TOP=1.035, V_W0=0.012, V_K=0.75, V_Y=0.03, OBI_Z=(0.779, 0.876), OBI_Y=0.0,
          BOOT_TOP=0.26, BOOT_XY=1.0, LOCK_K=1.7, LOCK_Z0=1.20, LOCK_WAVE=0.006, LOCK_WL=0.075)
for _k in list(A1):  # tuning sweeps: env LOCKA1_<KEY> (scalars only)
    if os.environ.get("LOCKA1_" + _k) is not None: A1[_k] = float(os.environ["LOCKA1_" + _k])
def recolour(sel, mname):
    src = int(np.where(fm == mi[mname])[0][0]); col = tuple(gc.data[me.polygons[src].loop_indices[0]].color)
    for fi in np.where(sel)[0]:
        for l in me.polygons[fi].loop_indices: gc.data[l].color = col
    fm[sel] = mi[mname]
fc = np.array([p.center for p in me.polygons])
fdom = np.array([max(sorted(set(dom[list(p.vertices)].tolist())), key=list(dom[list(p.vertices)]).count) for p in me.polygons])
# visible neck + collar V: dress faces on the neck / chest top become skin (the neck column above V_TOP, a V on the chest front)
neck = (fm == mi["dress"]) & np.isin(fdom, ["neck", "chest", "head"]) & (fc[:, 2] > A1["V_TOP"])
vee = (fm == mi["dress"]) & (fc[:, 1] > A1["V_Y"]) & (np.abs(fc[:, 0]) < A1["V_W0"] + A1["V_K"] * (fc[:, 2] - (A1["V_TOP"] - 0.075))) & (fc[:, 2] > A1["V_TOP"] - 0.075)
recolour(neck | vee, "skin"); print("LOCK A1 neck + collar V faces -> skin:", int((neck | vee).sum()))
# obi band: any dress face left inside r13's obi z band on the front becomes obi (a clean full-width band; the band height already
# matches the master's ~4-5 px at 1x, so it is not made taller)
ob = (fm == mi["dress"]) & np.isin(fdom, ["spine", "pelvis", "chest"]) & (fc[:, 2] > A1["OBI_Z"][0]) & (fc[:, 2] < A1["OBI_Z"][1]) & (fc[:, 1] > A1["OBI_Y"])
recolour(ob, "obi"); print("LOCK A1 obi band faces:", int(ob.sum()))
# taller, slightly bigger boots: sock faces below BOOT_TOP become boot; boot vertices widen around each leg's axis
bt = (fm == mi["socks"]) & (fc[:, 2] < A1["BOOT_TOP"]); recolour(bt, "boots"); print("LOCK A1 sock -> boot faces:", int(bt.sum()))
for p in me.polygons:
    if fm[p.index] == mi["boots"]: vm[list(p.vertices)] = mi["boots"]
for sg in (-1, 1):
    bv = (vm == mi["boots"]) & (np.sign(co[:, 0]) == sg)
    for z0 in np.arange(0, A1["BOOT_TOP"] + 0.02, 0.02):  # per 2 cm slice: scale about the slice centre (keeps the leg axis)
        sl = bv & (co[:, 2] >= z0) & (co[:, 2] < z0 + 0.02)
        if sl.sum() < 3: continue
        c = co[sl, :2].mean(0); co[sl, :2] = c + (co[sl, :2] - c) * A1["BOOT_XY"]
# longer, wavier side locks (master): vertices of the side-lock bones below LOCK_Z0 stretch down by LOCK_K and wave sideways
lk = np.char.startswith(dom.astype(str), "hair_side") & (co[:, 2] < A1["LOCK_Z0"])
dz = A1["LOCK_Z0"] - co[lk, 2]; co[lk, 2] = A1["LOCK_Z0"] - dz * A1["LOCK_K"]
co[lk, 0] += np.sign(co[lk, 0]) * A1["LOCK_WAVE"] * np.sin(2 * np.pi * dz * A1["LOCK_K"] / A1["LOCK_WL"])
print("LOCK A1 side-lock verts stretched:", int(lk.sum()), "new bottom z", round(float(co[lk, 2].min()), 3))
# head width: head-group vertices (head, hair, bun, bow) scale about the head bone's head (neck joint)
hd = np.isin(dom, ["head", "bun", "bow_knot"]) | np.char.startswith(dom.astype(str), "hair") | np.char.startswith(dom.astype(str), "bow.")
pv = H("head"); co[hd, :2] = pv[:2] + (co[hd, :2] - pv[:2]) * A1["HEAD_XY"]; co[hd, 2] = pv[2] + (co[hd, 2] - pv[2]) * A1["HEAD_Z"]
print("LOCK A1 head verts scaled:", int(hd.sum()))
me.attributes["mat"].data.foreach_set("value", fm); me.vertices.foreach_set("co", co.ravel()); me.update()
ao["lock_a1"] = json.dumps(A1)
# ---- 7. RPOS: rest position per vertex (float colour, fixed box) -> the renderer's 'rpos' pass = exact surface correspondence between
# frames (temporal contour hysteresis follows each surface point instead of a whole-part shift)
RLO, RHI = np.array([-0.45, -0.40, -0.02]), np.array([0.45, 0.40, 1.62])
if me.color_attributes.get("RPOS"): me.color_attributes.remove(me.color_attributes["RPOS"])
ra = me.color_attributes.new("RPOS", "FLOAT_COLOR", "POINT"); rn = (co - RLO) / (RHI - RLO)
ra.data.foreach_set("color", np.concatenate([rn, np.ones((n, 1))], 1).astype(np.float32).ravel())
ao["lock_rpos_box"] = json.dumps([RLO.tolist(), RHI.tolist()])
ao["lock"] = "pipe/make_rig_lock.py (DESIGN_LOCK 2026-10-30) on rig r13"
bpy.ops.wm.save_as_mainfile(filepath=OUT, copy=False)
print("LOCK_RIG_SAVED", OUT)
