# build_mesh.py (skinned rig, R): Blender -b --factory-startup -P build_mesh.py -- OUT.npz [voxel]
# Builds ONE connected watertight body mesh for the swordswoman in the H2 frame (units: figure 2.0 tall, front -Y, her left +X, z up):
#   * head / bow / bun = rig H2 parts (calibrated to the m96 masters; hair, face and eyes as vertex colours)
#   * torso (no waist cinch), wide obi band, straight A-line skirt down to the master hem, kimono bell sleeves hanging (arms down ~26 deg),
#     mitten hands, legs with thigh-high stockings (+ red top band), boots, side hair locks, bow ribbon tails  = procedural lofts fitted to
#     the m96 masters (EC0_S/E/SE_96) via the game-camera projection row = 120 - 52.608 (0.866 z + 0.5 y)  (S view)
#   * all parts unioned by a voxel remesh -> one manifold surface; per-face material + per-vertex source part from the nearest part surface.
import bpy, bmesh, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; VOX = float(a[1]) if len(a) > 1 else 0.006
H2 = "/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/hy3d/rigs/H2/parts"
bpy.ops.wm.read_factory_settings(use_empty=True)
MATS = {'hair': (61, 50, 53), 'dress': (192, 59, 61), 'skin': (248, 218, 194), 'sleeve': (142, 34, 44), 'socks': (38, 42, 71),
        'boots': (42, 34, 42), 'bow': (232, 96, 79), 'obi': (69, 56, 73), 'eyes': (85, 128, 162)}
MN = list(MATS)
# ------------------------------------------------------------------ H2 head parts (same normalisation as rig_lib: all H2 parts -> 2.0 tall, feet z=0)
imp = {}
for n in ["head", "bow", "bun", "torso", "skirt", "arm_L", "arm_R", "leg_L", "leg_R"]:
    bpy.ops.import_scene.gltf(filepath=os.path.join(H2, n + ".glb"))
    ms = [o for o in bpy.context.selected_objects if o.type == "MESH"]; o = ms[0]
    o.data.transform(o.matrix_world); o.parent = None; o.matrix_world = Matrix.Identity(4); imp[n] = o
for o in list(bpy.context.scene.objects):
    if o.type != "MESH": bpy.data.objects.remove(o)
V = np.concatenate([np.array([v.co[:] for v in o.data.vertices]) for o in imp.values()])
zlo = V[:, 2].min(); S = 2.0 / (V[:, 2].max() - zlo)
T = Matrix.Scale(S, 4) @ Matrix.Translation(Vector((0, 0, -zlo)))
for n in list(imp):
    if n in ("head", "bow", "bun"): imp[n].data.transform(T); imp[n].name = n
    else: bpy.data.objects.remove(imp.pop(n))
def vcol_mat(o):
    """per-vertex material name from the H2 vertex colours (nearest MATS colour)"""
    me = o.data; ca = me.color_attributes[0]; c = np.zeros((len(me.vertices), 3))
    if ca.domain == "CORNER":
        for l in me.loops: c[l.vertex_index] = ca.data[l.index].color_srgb[:3]
    else: c = np.array([d.color_srgb[:3] for d in ca.data])
    c = c * 255; MC = np.array([MATS[k] for k in MN], float)
    return np.array(MN)[((c[:, None] - MC[None]) ** 2).sum(-1).argmin(1)]
# ------------------------------------------------------------------ loft helper
def ring_pts(c, t, ref, ra, rb, n, p=2.0, oa=0.0, ob=0.0, ra2=None, rb2=None, bdir=None):
    """superellipse ring about centre c in the plane perpendicular to t; a-axis = ref projected; ra2/rb2 = radii on the negative side"""
    t = t / np.linalg.norm(t); A = ref - (ref @ t) * t; A /= np.linalg.norm(A); B = np.cross(t, A)
    if bdir is not None and B @ bdir < 0: B = -B  # mirror-safe: B always toward bdir (e.g. her back) on both sides
    th = np.linspace(0, 2 * np.pi, n, endpoint=False); ct, st = np.cos(th), np.sin(th)
    ea = np.sign(ct) * np.abs(ct) ** (2 / p); eb = np.sign(st) * np.abs(st) ** (2 / p)
    RA = np.where(ct >= 0, ra, ra if ra2 is None else ra2); RB = np.where(st >= 0, rb, rb if rb2 is None else rb2)
    return c + (oa * A + ob * B) + (RA * ea)[:, None] * A + (RB * eb)[:, None] * B
def loft(name, keys, ref, n=48, step=0.008, cap0="flat", cap1="flat", p=2.0, bdir=None):
    """keys: list of dicts {c:[x,y,z], ra, rb, (ra2, rb2, oa, ob)} along a path; resampled every ~step; caps flat|round"""
    C = np.array([k["c"] for k in keys], float); L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]
    m = max(2, int(L[-1] / step) + 1); s = np.linspace(0, L[-1], m)
    def I(f): return np.interp(s, L, [k.get(f, k.get(f[:-1], 0.0) if f.endswith("2") else 0.0) for k in keys])
    cc = np.stack([np.interp(s, L, C[:, i]) for i in range(3)], 1)
    ra, rb, ra2, rb2, oa, ob = I("ra"), I("rb"), I("ra2"), I("rb2"), I("oa"), I("ob")
    tg = np.gradient(cc, axis=0); rings = []
    for i in range(m):
        rings.append(ring_pts(cc[i], tg[i], np.array(ref, float), ra[i], rb[i], n, p, oa[i], ob[i], ra2[i], rb2[i], None if bdir is None else np.array(bdir, float)))
    def capring(i, sgn):
        out = []; t = tg[i] / np.linalg.norm(tg[i]); cen = rings[i].mean(0)
        for k in (0.35, 0.65, 0.88, 0.97):
            ang = k * np.pi / 2; r = rings[i] - cen; hgt = (ra[i] + rb[i]) / 2 * 0.8
            out.append(cen + r * math.cos(ang) + sgn * t * hgt * math.sin(ang))
        return out
    if cap0 == "round": rings = capring(0, -1)[::-1] + rings
    if cap1 == "round": rings = rings + capring(m - 1, 1)
    P = np.concatenate(rings); F = []; nr = len(rings)
    for i in range(nr - 1):
        for j in range(n):
            F.append((i * n + j, i * n + (j + 1) % n, (i + 1) * n + (j + 1) % n, (i + 1) * n + j))
    c0 = len(P); P = np.vstack([P, rings[0].mean(0), rings[-1].mean(0)])
    for j in range(n):
        F.append((c0, (j + 1) % n, j)); F.append((c0 + 1, (nr - 1) * n + j, (nr - 1) * n + (j + 1) % n))
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in P], [], F); me.validate()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    return o
G = {}  # geometry spec (also used by build_rig.py: joint positions)
# master-fit (qa/v0 vs EC0 masters): the H2 head/obi rows match the masters absolutely but the legs were ~3 rows short -> legs lengthened and
# everything above the knees lifted by DZ so the soles stay on z=0 (the pixel chain aligns soles to the master bottom row, as hires3d did)
DZ = 0.044
# ROUND 2: the head is the visual hull of the m96 master head stamps (rig/head_hull.py, already in the rig's master-aligned frame);
# bow, bun and ribbon tails are part of the hull (master silhouettes) -> the H2 head/bun/bow parts are retired.
for n_ in ("head", "bun", "bow"): bpy.data.objects.remove(imp.pop(n_))
_hh = np.load(os.path.join(os.path.dirname(os.path.abspath(OUT)), "head_hull.npz"), allow_pickle=True)
_me = bpy.data.meshes.new("head"); _me.from_pydata([tuple(v) for v in _hh["V"]], [], [tuple(int(i) for i in f) for f in _hh["F"]]); _me.validate()
_ca = _me.color_attributes.new("Color", "BYTE_COLOR", "POINT")
for i, m_ in enumerate(_hh["mat"]): _ca.data[i].color_srgb = [x / 255 for x in MATS[str(m_)]] + [1]
_bm = bmesh.new(); _bm.from_mesh(_me); bmesh.ops.recalc_face_normals(_bm, faces=_bm.faces); _bm.to_mesh(_me); _bm.free()
imp["head"] = bpy.data.objects.new("head", _me); bpy.context.scene.collection.objects.link(imp["head"])
HMAT = np.array([str(m_) for m_ in _hh["mat"]])
HV = np.array([v.co[:] for v in imp["head"].data.vertices])
def back_y(x0, z0, w=0.03):
    m = (np.abs(HV[:, 0] - x0) < w) & (np.abs(HV[:, 2] - z0) < 0.015); return float(HV[m, 1].max()) if m.any() else 0.2
def side_x(sx, y0, z0, w=0.03):
    m = (np.abs(HV[:, 1] - y0) < w) & (np.abs(HV[:, 2] - z0) < 0.015); return float((sx * HV[m, 0]).max()) if m.any() else 0.25
# ------------------------------------------------------------------ torso / neck / obi / skirt
tor = [(0.93, .135, .100, 0), (1.00, .140, .100, 0), (1.10, .146, .104, 0), (1.17, .156, .108, -.004), (1.215, .160, .104, -.004),
       (1.255, .146, .090, -.002), (1.285, .112, .076, 0), (1.305, .070, .060, .004)]
loft("torso", [{"c": [0, y, z + DZ], "ra": rx, "rb": ry} for z, rx, ry, y in tor], [1, 0, 0], n=64, p=2.4)
loft("neck", [{"c": [0, .006, 1.26 + DZ], "ra": .047, "rb": .045}, {"c": [0, .012, 1.47 + DZ], "ra": .046, "rb": .044}], [1, 0, 0], n=40)
G["obi"] = (0.957 + DZ, 1.052 + DZ)
loft("obi", [{"c": [0, 0, z], "ra": .150, "rb": .112} for z in G["obi"]], [1, 0, 0], n=64, p=2.6)
G["hem"] = 0.767
sk = [(0.975 + DZ, .141, .101, 0), (0.94 + DZ, .151, .110, .002), (0.88 + DZ, .170, .127, .004), (0.82 + DZ, .188, .146, .006), (G["hem"], .205, .163, .008)]  # r2: fuller hips
loft("skirt", [{"c": [0, y, z], "ra": rx, "rb": ry} for z, rx, ry, y in sk], [1, 0, 0], n=72, p=2.3)
# ------------------------------------------------------------------ arms (+ sleeves, hands), sx = +1 her left (+X)
ABD = math.radians(26.0); UA, FA, HL = 0.22, 0.215, 0.10
for side, sx in (("L", 1), ("R", -1)):
    Sh = np.array([sx * .158, 0.008, 1.188 + DZ]); d1 = np.array([sx * math.sin(ABD), -0.03, -math.cos(ABD)]); d1 /= np.linalg.norm(d1)
    d2 = np.array([sx * math.sin(ABD + math.radians(3)), -0.07, -math.cos(ABD + math.radians(3))]); d2 /= np.linalg.norm(d2)
    El = Sh + UA * d1; Wr = El + FA * d2; Ht = Wr + HL * d2
    G["arm." + side] = {"sh": Sh.tolist(), "el": El.tolist(), "wr": Wr.tolist(), "ht": Ht.tolist(), "d1": d1.tolist(), "d2": d2.tolist()}
    lat = np.array([sx * math.cos(ABD), 0, sx * math.sin(ABD)])  # frontal plane, perpendicular to the arm, pointing out/up
    loft("arm_" + side, [{"c": (Sh + 0.01 * d1).tolist(), "ra": .044, "rb": .044}, {"c": (Sh + 0.03 * d1).tolist(), "ra": .046, "rb": .046},
                         {"c": El.tolist(), "ra": .039, "rb": .040}, {"c": (Wr - 0.01 * d2).tolist(), "ra": .031, "rb": .033}], lat, n=32, cap0="round")
    # hands 1.3x the H2 size (Opus: 0.5-scale hands pixelize to 1-2 detached px; masters draw 3-4 px mitts)
    loft("hand_" + side, [{"c": (Wr - 0.02 * d2).tolist(), "ra": .034, "rb": .038}, {"c": (Wr + 0.03 * d2).tolist(), "ra": .043, "rb": .054},
                          {"c": (Wr + 0.07 * d2).tolist(), "ra": .039, "rb": .049}, {"c": Ht.tolist(), "ra": .027, "rb": .035}], lat, n=32, cap1="round")
    t_ = lambda s_: Sh + d1 * min(s_, UA) + d2 * max(0.0, s_ - UA)
    cuff = UA + FA + 0.012
    sl = [(-0.05, .056, .058, -.01, 0), (0.0, .064, .064, 0, 0), (0.08, .066, .068, .006, .004), (UA, .076, .080, .012, .014),
          (UA + 0.10, .106, .092, -.016, .022), (cuff, .124, .100, -.034, .028)]
    loft("sleeve_" + side, [{"c": t_(s_).tolist(), "ra": ra, "rb": rb, "oa": oa, "ob": ob} for s_, ra, rb, oa, ob in sl], lat, n=56, p=2.6, bdir=[0, 1, 0])
    G["sleeve." + side] = {"cuff_s": cuff, "lat": lat.tolist(), "rings": sl}
# ------------------------------------------------------------------ legs (lengthened), boots
for side, sx in (("L", 1), ("R", -1)):
    Hp = np.array([sx * .085, 0.0, 0.84 + DZ]); Kn = np.array([sx * .095, -0.004, 0.475]); An = np.array([sx * .100, 0.010, 0.088])
    Tt = np.array([sx * .100, -0.135, 0.03])
    G["leg." + side] = {"hip": Hp.tolist(), "knee": Kn.tolist(), "ankle": An.tolist(), "toe": Tt.tolist(), "ball": [sx * .1, -.07, .035]}
    # r4: thicker legs toward the chibi masters (S master: thigh ~8 px, sock ~6 px incl. outline), centres spread at the hem to keep a gap
    # round 2: fuller chibi thighs (r +8%), centres spread to keep a >= 3 cm gap below the hem (no inner-thigh fusion)
    lg = [(Hp + np.array([0, 0, .06]), .076, .076), (Hp, .084, .082), (np.array([sx * .097, -.002, .77]), .080, .079),
          (np.array([sx * .097, -.003, .65]), .072, .072), (np.array([sx * .096, -.004, .55]), .063, .064), (Kn, .057, .058),
          (np.array([sx * .097, .0, .35]), .059, .061), (np.array([sx * .099, .006, .22]), .051, .053), (An, .044, .046)]
    loft("leg_" + side, [{"c": c.tolist(), "ra": ra, "rb": rb} for c, ra, rb in lg], [1, 0, 0], n=40)
    loft("boot_" + side, [{"c": [sx * .099, .008, .196], "ra": .060, "rb": .062}, {"c": [sx * .100, .010, .12], "ra": .061, "rb": .064},
                          {"c": [sx * .100, .012, .05], "ra": .062, "rb": .066}], [1, 0, 0], n=40)
    loft("foot_" + side, [{"c": [sx * .100, .045, .046], "ra": .056, "rb": .046}, {"c": [sx * .100, -.04, .044], "ra": .058, "rb": .044},
                          {"c": [sx * .100, -.105, .037], "ra": .053, "rb": .037}], [1, 0, 0], n=40, cap0="round", cap1="round", p=2.6)
G["sock_top"] = 0.622; G["sock_band"] = 0.026; G["boot_top"] = 0.196
# ------------------------------------------------------------------ hair locks (front side locks to the shoulder), bow (knot + 2 lobes) + ribbon tails
for side, sx in (("L", 1), ("R", -1)):
    zs = [1.60, 1.47, 1.38, 1.30]; rr_ = [(.030, .034), (.026, .030), (.020, .024), (.010, .013)]
    xs = [0.5 * sum(max(side_x(q_, -0.095, 1.60 + DZ) - 0.035, 0.19) for q_ in (1, -1)), 0.226, 0.232, 0.232]  # mirror-symmetric (H2 head is not)
    lk = [([sx * x, -.10, z + DZ], ra, rb) for x, z, (ra, rb) in zip(xs, zs, rr_)]
    loft("lock_" + side, [{"c": c, "ra": ra, "rb": rb} for c, ra, rb in lk], [1, 0, 0], n=24, cap1="round")
    G["lock." + side] = [c for c, _, _ in lk]
# bow (knot + lobes) and bun bone anchors from the hull's master-coloured regions
BW = HV[HMAT == "bow"]; BK = BW[BW[:, 1] > 0.08]  # the bow sits on the BACK of the head (N/NE/E masters); lobes spread sideways
zs_ = np.arange(1.82, 1.98, 0.02); wd_ = [np.abs(BK[np.abs(BK[:, 2] - z_) < 0.01, 0]).max() if (np.abs(BK[:, 2] - z_) < 0.01).sum() > 5 else 0 for z_ in zs_]
zw = float(zs_[int(np.argmax(wd_))]); band = BK[np.abs(BK[:, 2] - zw) < 0.08]
kq = band[np.abs(band[:, 0]) < 0.04]; kn = kq[np.argsort(-kq[:, 1])[: max(10, len(kq) // 4)]].mean(0); kn[0] = 0.0
G["bow_knot"] = kn.tolist(); G["bow"] = {}
for side, sx in (("L", 1), ("R", -1)):
    Q = band[sx * band[:, 0] > 0.06]
    far = Q[np.argsort(-np.abs(Q[:, 0]))[: max(5, len(Q) // 10)]].mean(0)
    p0 = kn + np.array([sx * 0.035, 0, 0]); p2 = far; p1 = (p0 + p2) / 2 + np.array([0, 0.01, 0])
    G["bow"][side] = [p0.tolist(), p1.tolist(), p2.tolist()]
G["bow_zcut"] = float(zw - 0.085)  # bow-coloured hull below this = ribbon tails
HR = HV[HMAT == "hair"]; zt = HR[:, 2].max(); cand = HR[(HR[:, 2] > zt - 0.12) & (HR[:, 1] > 0.04)]
bc = cand[np.argsort(-(cand[:, 1] * 0.6 + cand[:, 2]))[: max(20, len(cand) // 8)]].mean(0) if len(cand) else np.array([0, .15, zt - .05])
bc[0] = 0.0; G["bun"] = {"c": (bc - np.array([0, 0.03, 0.03])).tolist(), "r": 0.075}
G["DZ"] = DZ
# ------------------------------------------------------------------ union by voxel remesh
parts = {o.name: o for o in bpy.context.scene.objects if o.type == "MESH"}
for o in parts.values():
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.triangulate(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
src = {}
for n, o in parts.items():
    me = o.data; vv = [v.co.copy() for v in me.vertices]; pp = [tuple(p.vertices) for p in me.polygons]
    src[n] = (BVHTree.FromPolygons(vv, pp), np.array([v[:] for v in vv]), np.array(pp))
headmat = vcol_mat(imp["head"])
bpy.ops.object.select_all(action="DESELECT")
cp = []
for n, o in parts.items():
    c = o.copy(); c.data = o.data.copy(); bpy.context.scene.collection.objects.link(c); c.select_set(True); cp.append(c)
bpy.context.view_layer.objects.active = cp[0]; bpy.ops.object.join(); body = bpy.context.object; body.name = "body"
md = body.modifiers.new("rm", "REMESH"); md.mode = "VOXEL"; md.voxel_size = VOX; md.adaptivity = 0.0; md.use_smooth_shade = True
bpy.ops.object.modifier_apply(modifier="rm")
bm = bmesh.new(); bm.from_mesh(body.data)
# keep the largest shell only (voxel crumbs), smooth a little
shells = []; seen = set()
for v in bm.verts:
    if v.index in seen: continue
    st = [v]; comp = []; seen.add(v.index)
    while st:
        x = st.pop(); comp.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen: seen.add(y.index); st.append(y)
    shells.append(comp)
shells.sort(key=len, reverse=True); print("shells", [len(s) for s in shells[:6]])
for s in shells[1:]: bmesh.ops.delete(bm, geom=list(set(s)), context="VERTS")
bm.to_mesh(body.data); bm.free()
VB = np.array([v.co[:] for v in body.data.vertices]); FB = [tuple(p.vertices) for p in body.data.polygons]
def label(pts):
    best = np.full(len(pts), 9.0); lab = np.empty(len(pts), dtype=object); fid = np.zeros(len(pts), int)
    for n, (bvh, _, _) in src.items():
        for i, p in enumerate(pts):
            r = bvh.find_nearest(Vector(p))
            if r[0] is not None and r[3] < best[i] - 1e-9: best[i] = r[3]; lab[i] = n; fid[i] = r[2]
    return lab, fid, best
vlab, vfid, vd = label(VB)
FC = np.array([VB[list(f)].mean(0) for f in FB]); flab, ffid, _ = label(FC)
def mat_of(n, fi, p):
    x, y, z = p
    if n == "head": return headmat[src["head"][2][fi][0]]
    if n.startswith("lock"): return "hair"
    if n == "obi": return "obi"
    if n.startswith(("hand", "neck")): return "skin"
    if n.startswith(("boot", "foot")): return "boots"
    if n.startswith("sleeve"): return "sleeve"
    if n.startswith("arm"): return "sleeve"
    if n.startswith("leg"):
        if z > G["sock_top"]: return "skin"
        if z > G["sock_top"] - G["sock_band"]: return "dress"
        return "socks" if z > G["boot_top"] - 0.01 else "boots"
    if n == "torso":
        if G["obi"][0] <= z <= G["obi"][1]: return "obi"
        if y < 0 and z > 1.262 + G["DZ"] and abs(x) < 0.40 * (z - 1.255 - G["DZ"]): return "skin"  # small kimono V at the collar
        return "dress"
    return "dress"
fmat = [mat_of(flab[i], ffid[i], FC[i]) for i in range(len(FB))]
np.savez_compressed(OUT, V=VB, F=np.array(FB, dtype=object), fmat=np.array(fmat), vlab=vlab.astype(str), flab=flab.astype(str), G=json.dumps(G),
                    head_v=HV, head_mat=HMAT)
print("BODY", len(VB), len(FB), {m: fmat.count(m) for m in MN}, flush=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT.replace(".npz", "_parts.blend"))
