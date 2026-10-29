# build_rig.py (skinned rig, R): Blender -b --factory-startup -P build_rig.py -- work/body.npz rig.blend rest_skeleton.json
# body.npz (build_mesh.py, H2 frame: 2.0 units tall, front -Y, her left +X) -> CONTRACT frame: metres (K = 0.775 m per H2 unit), front +Y,
# her left -X (Blender .L = character's left), Z up, soles on z=0.  Armature with the contract bone names + secondary chains, part-aware
# analytic skin weights (joint-plane partition of unity per body part, smooth windows for hair / skirt / sleeve / bow chains), Laplacian
# weight smoothing over the mesh graph, Armature modifier with Preserve Volume (dual quaternion).
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]
NPZ, BLEND, SKJ = a[:3]
K = 0.775
bpy.ops.wm.read_factory_settings(use_empty=True)
d = np.load(NPZ, allow_pickle=True); G = json.loads(str(d["G"])); DZ = G["DZ"]
V = d["V"].astype(float); FC = [tuple(f) for f in d["F"]]; fmat = d["fmat"]; vlab = d["vlab"]; HV = d["head_v"]
MATS = {'hair': (61, 50, 53), 'dress': (192, 59, 61), 'skin': (248, 218, 194), 'sleeve': (142, 34, 44), 'socks': (38, 42, 71),
        'boots': (42, 34, 42), 'bow': (232, 96, 79), 'obi': (69, 56, 73), 'eyes': (85, 128, 162)}
MN = list(MATS)
def Fw(p):  # H2 frame -> contract frame
    p = np.asarray(p, float); return np.stack([-K * p[..., 0], -K * p[..., 1], K * p[..., 2]], -1)
nv = len(V)
# majority filter on the H2 head's hair/skin/eye labels (the H2 vertex-colour boundary is ragged after the remesh): 3 passes face->vertex->face
flab = d["flab"]; fmat = fmat.astype(object)
FA_ = np.array([f[:3] for f in FC]); headf = np.nonzero(flab == "head")[0]; HM = ["hair", "skin", "eyes", "bow"]
for it in range(int(os.environ.get("HEADMAJ", "1"))):
    vv = np.zeros((nv, len(HM)))
    for j, m in enumerate(HM):
        sel = headf[fmat[headf] == m]
        for c in range(3): np.add.at(vv[:, j], FA_[sel, c], 1)
    fv = vv[FA_[headf]].sum(1); fv[:, 2] *= 1.6  # keep the eyes from eroding
    fmat[headf] = np.array(HM, dtype=object)[fv.argmax(1)]
# round 5: face zone on the skull (front-facing, z 1.38..1.80, |x| < 0.23) -> skin + face texture (forehead under the fringe included)
_P3 = V[np.array([f[:3] for f in FC])]; _nr = np.cross(_P3[:, 1] - _P3[:, 0], _P3[:, 2] - _P3[:, 0]); _nr /= np.linalg.norm(_nr, axis=1, keepdims=True) + 1e-12
_cz = _P3.mean(1); FZ = (flab == "head") & (_cz[:, 2] > 1.36) & (_cz[:, 2] < 1.80) & (np.abs(_cz[:, 0]) < 0.235) & (_nr[:, 1] < 0.35) & (_cz[:, 1] < 0.0 - float(G.get("head_fwd", 0.0)))  # F: all front skin + the cheek sides (profile views)
ILLUS = G.get("head_mode", "") == "illus"
if ILLUS: FZ[:] = False  # round 7: the illustration texture carries the face; keep the hull classification
fmat[FZ] = "skin"; fmat[(flab == "head") & ~FZ & (fmat == "skin") & ((_cz[:, 2] > 1.70) | (np.abs(_cz[:, 0]) > 0.215))] = "hair"  # scalp/temple outside the face = hair colour
# per-vertex material (majority of incident faces) -> used for hair masks
vm_votes = {}
vmat = np.empty(nv, dtype=object)
for fi, f in enumerate(FC):
    for v in f: vmat[v] = fmat[fi]  # last wins; refined below for hair
bowv = np.zeros(nv, bool)
for fi, f in enumerate(FC):
    if fmat[fi] == "bow" and flab[fi] in ("head", "hair_shell"): bowv[list(f)] = True
hairv = np.zeros(nv, bool)
for fi, f in enumerate(FC):
    if fmat[fi] == "hair":
        hairv[list(f)] = True
# ------------------------------------------------------------------ skeleton (H2 frame)
B = {}  # name -> (head, tail, parent, zaxis_hint in H2 frame)
FWD = np.array([0, -1.0, 0]); UP = np.array([0, 0, 1.0])
def bone(n, h, t, par, z=FWD): B[n] = (np.array(h, float), np.array(t, float), par, np.array(z, float))
bone("root", [0, 0, 0], [0, -0.2, 0], None, UP)
bone("pelvis", [0, 0, 0.90], [0, 0, 1.00], "root")
bone("spine", [0, 0, 1.00], [0, 0, 1.12], "pelvis")
bone("chest", [0, 0, 1.12], [0, 0, 1.30], "spine")
HF = float(G.get("head_fwd", 0.0))  # round 5: head forward over the neck (neck angles forward from the chest)
bone("neck", [0, .006, 1.30], [0, .006 - 0.8 * HF, 1.43], "chest")
bone("head", [0, .006 - 0.8 * HF, 1.43], [0, .006 - 1.2 * HF, 1.85], "neck")
for s, sx in (("L", 1), ("R", -1)):
    L_ = G["leg." + s]
    bone(f"thigh.{s}", L_["hip"], L_["knee"], "pelvis"); bone(f"shin.{s}", L_["knee"], L_["ankle"], f"thigh.{s}")
    bone(f"foot.{s}", L_["ankle"], L_["ball"], f"shin.{s}", UP); bone(f"toe.{s}", L_["ball"], L_["toe"], f"foot.{s}", UP)
    A_ = G["arm." + s]
    bone(f"shoulder.{s}", [sx * .03, 0, 1.275 + DZ - .04], A_["sh"], "chest")
    bone(f"upper_arm.{s}", A_["sh"], A_["el"], f"shoulder.{s}"); bone(f"forearm.{s}", A_["el"], A_["wr"], f"upper_arm.{s}")
    bone(f"hand.{s}", A_["wr"], A_["ht"], f"forearm.{s}")
# sleeve bag chain: elbow -> cuff ring centre -> cuff lower/back corner of the bag
SLV = {}
for s, sx in (("L", 1), ("R", -1)):
    A_ = G["arm." + s]; Sh, El, Wr = (np.array(A_[k]) for k in ("sh", "el", "wr")); d1, d2 = np.array(A_["d1"]), np.array(A_["d2"])
    lat = np.array(G["sleeve." + s]["lat"]); cuff = G["sleeve." + s]["cuff_s"]; UA = np.linalg.norm(El - Sh)
    t2 = d2; A2 = lat - (lat @ t2) * t2; A2 /= np.linalg.norm(A2); B2 = np.cross(t2, A2)
    if B2[1] < 0: B2 = -B2  # mirror-safe: B2 toward her back on both sides (as build_mesh bdir)
    cc = El + d2 * (cuff - UA) + (-.034) * A2 + .028 * B2  # cuff ring centre (as build_mesh sl[-1])
    mid = El + d2 * (0.5 * (cuff - UA)) + (-.012) * A2 + .02 * B2
    SLV[s] = dict(Sh=Sh, El=El, Wr=Wr, d1=d1, d2=d2, A2=A2, B2=B2, cuff=cuff, UA=UA)
    bone(f"sleeve.{s}.1", El + 0.02 * B2, mid + 0.03 * B2 - 0.02 * A2, f"forearm.{s}")
    bone(f"sleeve.{s}.2", mid + 0.03 * B2 - 0.02 * A2, cc + 0.06 * B2 - 0.06 * A2, f"sleeve.{s}.1")
# hair chains from the head mesh
HC = np.array([0, .01 - HF, 1.62 + DZ])
HMAT_ = d["head_mat"].astype(str) if "head_mat" in d else np.array(["hair"] * len(HV))
def col_pts(x0, cond, w=0.025):
    m = (np.abs(HV[:, 0] - x0) < w) & cond & (HMAT_ == "hair"); return HV[m]  # hair-coloured hull only (no bow ribbons / face)
FR = {}
for nm, x0 in (("L", .13), ("C", 0.0), ("R", -.13)):
    P_ = col_pts(x0, HV[:, 1] < -0.06 - HF)
    P_ = P_[P_[:, 2] > 1.60 + DZ]; zb = float(np.percentile(P_[:, 2], 2)); zt = 1.80 + DZ  # fringe ends at the brows (not the side hair)
    def yf(z):
        q = P_[np.abs(P_[:, 2] - z) < 0.015]; return float(q[:, 1].min()) + 0.03 if len(q) else -0.2
    p0 = [x0, yf(zt), zt]; p2 = [x0 * 1.05, yf(zb + .01), zb + 0.005]; p1 = [x0 * 1.02, yf((zt + zb) / 2), (zt + zb) / 2]
    bone(f"hair_front.{nm}.1", p0, p1, "head"); bone(f"hair_front.{nm}.2", p1, p2, f"hair_front.{nm}.1")
    FR[nm] = (zb, zt)
for s, sx in (("L", 1), ("R", -1)):
    lk = np.array(G["lock." + s]); lk[0, 2] += 0.02
    for i in range(3): bone(f"hair_side.{s}.{i+1}", lk[i], lk[i + 1], "head" if i == 0 else f"hair_side.{s}.{i}")
Pb = col_pts(0.0, HV[:, 1] > 0.08, 0.04)
zlow = max(float(np.percentile(Pb[:, 2], 1.5)), 1.47 + DZ); ztop = 1.78 + DZ
def yb(z):
    q = Pb[np.abs(Pb[:, 2] - z) < 0.015]; return float(q[:, 1].max()) - 0.035 if len(q) else 0.2
zz = np.linspace(ztop, zlow + 0.01, 4)
for i in range(3): bone(f"hair_back.{i+1}", [0, yb(zz[i]), zz[i]], [0, yb(zz[i + 1]), zz[i + 1]], "head" if i == 0 else f"hair_back.{i}")
bc = np.array(G["bun"]["c"]); bd = (bc - HC) / np.linalg.norm(bc - HC); br = float(G["bun"]["r"])
bone("bun", bc - bd * br * 0.9, bc + bd * br, "head")
kn = np.array(G["bow_knot"]); bone("bow_knot", kn, kn + [0, .06, 0], "head", UP)
for s in "LR":
    p0, p1, p2 = (np.array(p) for p in G["bow"][s])
    bone(f"bow.{s}.1", p0, p1, "bow_knot", UP); bone(f"bow.{s}.2", p1, p2, f"bow.{s}.1", UP)
SKA = {"F": 0, "FL": 45, "L": 90, "BL": 135, "B": 180, "BR": 225, "R": 270, "FR": 315}
ztopS = 0.975 + DZ; hem = G["hem"]
def skr(z):  # skirt ellipse radii at z (build_mesh sk)
    zs = [hem, .80 + DZ, .84 + DZ, .90 + DZ, .95 + DZ, .975 + DZ]; rx = [.180, .178, .176, .171, .160, .143]; ry = [.142, .139, .135, .128, .117, .103]
    return np.interp(z, zs, rx), np.interp(z, zs, ry)
for n, ph in SKA.items():
    dv = np.array([math.sin(math.radians(ph)), -math.cos(math.radians(ph))])
    def sp(z, inset):
        rx, ry = skr(z); r = 1 / math.sqrt((dv[0] / rx) ** 2 + (dv[1] / ry) ** 2); return [dv[0] * (r - inset), dv[1] * (r - inset) + .006, z]
    za, zb_, zc = ztopS - 0.01, 0.5 * (ztopS + hem) - 0.02, hem + 0.004
    rad = np.array([dv[0], dv[1], 0])
    bone(f"skirt.{n}.1", sp(za, .03), sp(zb_, .025), "pelvis", rad); bone(f"skirt.{n}.2", sp(zb_, .025), sp(zc, .02), f"skirt.{n}.1", rad)
# mirror-symmetrise every .L/.R pair about x=0 (average of the pair and its mirror): the H2 head mesh is slightly asymmetric
MIR = np.array([-1.0, 1, 1])
for n in list(B):
    if ".L" in n and n.replace(".L", ".R") in B:
        m = n.replace(".L", ".R"); hL, tL, pL, zL = B[n]; hR, tR, pR, zR = B[m]
        h = (hL + hR * MIR) / 2; tt = (tL + tR * MIR) / 2
        B[n] = (h, tt, pL, zL); B[m] = (h * MIR, tt * MIR, pR, zR * MIR if abs(zR[0]) > 0 else zR)
# ------------------------------------------------------------------ weights (H2 frame)
BN = list(B); BI = {n: i for i, n in enumerate(BN)}; W = np.zeros((nv, len(BN)), np.float32)
def ss(e0, e1, x): t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def chain_w(P, names, joints, bws):
    """joint-plane partition of unity: names[k] owns the slab between joints[k-1] and joints[k] (planes ⟂ the bisector of the adjacent bones)"""
    n = len(names); s = []
    for j, (J, nrm) in enumerate(joints):
        nrm = np.asarray(nrm, float); nrm = nrm / np.linalg.norm(nrm); s.append(ss(-bws[j], bws[j], (P - np.asarray(J)) @ nrm))
    out = []
    for k in range(n):
        w = np.ones(len(P))
        if k > 0: w = w * s[k - 1]
        if k < n - 1: w = w * (1 - s[k])
        out.append(w)
    return out
def addw(idx, names, ws, scale=None):
    for nm, w in zip(names, ws):
        W[idx, BI[nm]] += w if scale is None else w * scale
def unit(v): v = np.asarray(v, float); return v / np.linalg.norm(v)
L = vlab
for s, sx in (("L", 1), ("R", -1)):
    # legs, boots, feet
    idx = np.nonzero(np.isin(L, [f"leg_{s}", f"boot_{s}", f"foot_{s}"]))[0]; P = V[idx]
    hp, knee, ank, ball = (B[f"thigh.{s}"][0], B[f"shin.{s}"][0], B[f"foot.{s}"][0], B[f"toe.{s}"][0])
    dth, dsh, dft, dto = (unit(B[f"{b}.{s}"][1] - B[f"{b}.{s}"][0]) for b in ("thigh", "shin", "foot", "toe"))
    ws = chain_w(P, ["pelvis", f"thigh.{s}", f"shin.{s}", f"foot.{s}", f"toe.{s}"],
                 [(hp + [0, 0, -0.01], dth), (knee, unit(dth + dsh)), (ank + [0, 0, 0.012], unit(dsh + dft)), (ball, unit(dft + dto))], [0.05, 0.04, 0.03, 0.02])
    addw(idx, ["pelvis", f"thigh.{s}", f"shin.{s}", f"foot.{s}", f"toe.{s}"], ws)
    # arms, sleeves, hands
    S_ = SLV[s]; idx = np.nonzero(np.isin(L, [f"arm_{s}", f"sleeve_{s}", f"hand_{s}"]))[0]; P = V[idx]
    dsho = unit(S_["Sh"] - B[f"shoulder.{s}"][0])
    names = ["chest", f"shoulder.{s}", f"upper_arm.{s}", f"forearm.{s}", f"hand.{s}"]
    ws = chain_w(P, names, [(B[f"shoulder.{s}"][0] + dsho * 0.06, dsho), (S_["Sh"] - S_["d1"] * 0.01, unit(dsho + S_["d1"])), (S_["El"], unit(S_["d1"] + S_["d2"])), (S_["Wr"], S_["d2"])],
                 [0.05, 0.05, 0.05, 0.02])
    # sleeve bag: far from the forearm axis and past the elbow -> sleeve chain
    isl = L[idx] == f"sleeve_{s}"
    rel = P - S_["El"]; u = rel @ S_["d2"]; dist = np.linalg.norm(rel - np.outer(u, S_["d2"]), axis=1)
    bag = isl * ss(0.045, 0.075, dist) * ss(-0.02, 0.05, u)
    w2 = ss(0.07, 0.17, u)
    for k in range(len(ws)): ws[k] = ws[k] * (1 - bag)
    addw(idx, names + [f"sleeve.{s}.1", f"sleeve.{s}.2"], ws + [bag * (1 - w2), bag * w2])
    # side locks
    idx = np.nonzero(L == f"lock_{s}")[0]; P = V[idx]; lk = [B[f"hair_side.{s}.{i}"] for i in (1, 2, 3)]
    ws = chain_w(P, ["head"] + [f"hair_side.{s}.{i}" for i in (1, 2, 3)],
                 [(lk[0][0] - [0, 0, 0.03], -UP), (lk[1][0], unit(lk[0][1] - lk[0][0] + lk[1][1] - lk[1][0])), (lk[2][0], unit(lk[1][1] - lk[1][0] + lk[2][1] - lk[2][0]))], [0.03, 0.03, 0.03])
    addw(idx, ["head"] + [f"hair_side.{s}.{i}" for i in (1, 2, 3)], ws)
    # hands handled with arms
# torso + obi: pelvis | spine | chest, shoulders, neck base
idx = np.nonzero(np.isin(L, ["torso", "obi"]))[0]; P = V[idx]
ws = chain_w(P, ["pelvis", "spine", "chest", "neck"], [([0, 0, 1.00], UP), ([0, 0, 1.13], UP), ([0, 0, 1.335], UP)], [0.035, 0.06, 0.025])
for s, sx in (("L", 1), ("R", -1)):
    sh = ss(0.07, 0.15, sx * P[:, 0]) * ss(1.16 + DZ, 1.24 + DZ, P[:, 2]) * 0.8
    W[idx, BI[f"shoulder.{s}"]] += ws[2] * sh; ws[2] = ws[2] * (1 - sh)
addw(idx, ["pelvis", "spine", "chest", "neck"], ws)
# neck
idx = np.nonzero(L == "neck")[0]; P = V[idx]
addw(idx, ["chest", "neck", "head"], chain_w(P, ["chest", "neck", "head"], [([0, 0, 1.315], UP), ([0, 0, 1.43], UP)], [0.025, 0.03]))
# skirt: pelvis -> 8 panel chains (azimuth windows), hem near a leg follows the thigh
idx = np.nonzero(L == "skirt")[0]; P = V[idx]
t = np.clip((ztopS - P[:, 2]) / (ztopS - hem), 0, 1)
phi = np.degrees(np.arctan2(P[:, 0], -(P[:, 1] - .006)))
pan = []
for n, ph in SKA.items():
    dd = (phi - ph + 180) % 360 - 180; pan.append(np.maximum(0, np.cos(np.radians(dd) * 2)) ** float(os.environ.get('SKPOW', '4')))  # near-rigid panels, narrow seams
pan = np.array(pan); pan /= pan.sum(0) + 1e-9
tot = ss(0.02, 0.40, t); w2 = ss(0.40, 0.85, t)
leg = np.zeros(len(P)); legw = {}
for s in "LR":
    hp, kn_ = B[f"thigh.{s}"][0], B[f"thigh.{s}"][1]; dth = unit(kn_ - hp); rel = P - hp; u = rel @ dth
    dist = np.linalg.norm(rel - np.outer(u, dth), axis=1)
    f = (1 - ss(0.085, 0.140, dist)) * ss(0.35, 0.90, t); legw[s] = f; leg = leg + f
leg = np.clip(leg, 0, 1); keep = 1 - leg
W[idx, BI["pelvis"]] += (1 - tot) * keep
for i, n in enumerate(SKA):
    W[idx, BI[f"skirt.{n}.1"]] += pan[i] * tot * (1 - w2) * keep; W[idx, BI[f"skirt.{n}.2"]] += pan[i] * tot * w2 * keep
for s in "LR": W[idx, BI[f"thigh.{s}"]] += legw[s] / np.maximum(1, leg)
# head part: head + hair chains (hair material only)
# round 5: SKULL (fused, face + cranium/scalp) = rigid head, blending to the neck under the chin
idx = np.nonzero(L == "head")[0]; P = V[idx]
if not ILLUS: addw(idx, ["neck", "head"], chain_w(P, ["neck", "head"], [([0, -HF, 1.44], UP)], [0.03]))
# HAIR SHELL (separate, attached): head + hair chains (bangs, sides, back, bun, bow, ribbons)
idx = np.nonzero(L == ("head" if ILLUS else "hair_shell"))[0]; P = V[idx]; hv = hairv[idx]  # round 7: the illustration hull carries the hair chains (+ skin fade below)
ph = np.degrees(np.arctan2(P[:, 0], -(P[:, 1] - HC[1])))  # 0 front, +90 her left (+X)
def win(c, wd): dd = (ph - c + 180) % 360 - 180; return np.maximum(0, np.cos(np.clip(np.radians(dd) * 90 / wd, -np.pi / 2, np.pi / 2)))
wfront = {nm: win(c, 38) for nm, c in (("L", 34), ("C", 0), ("R", -34))}; sf = sum(wfront.values()) + 1e-9
zb_, zt_ = FR["C"]
vf = hv * ss(zt_ - 0.02, zt_ - 0.10, P[:, 2]) * (P[:, 1] < -0.06) * ss(-0.06, -0.14, P[:, 1])
vb = hv * ss(1.66 + DZ, 1.55 + DZ, P[:, 2]) * win(180, 75)
vs = {s: hv * ss(1.62 + DZ, 1.50 + DZ, P[:, 2]) * win(sg * 95, 45) * 0.6 for s, sg in (("L", 1), ("R", -1))}
used = np.zeros(len(P))
# round 2 hull head: bow (knot, lobes, ribbon tails) and bun are regions of the head part (master colours / position)
bw_ = bowv[idx]; Pb_ = P[bw_]; ib_ = np.nonzero(bw_)[0]; zc_ = G["bow_zcut"]
rib = Pb_[:, 2] < zc_; zmin_ = Pb_[:, 2].min() if len(Pb_) else zc_ - 0.2
uu = np.clip((zc_ - Pb_[:, 2]) / max(zc_ - zmin_, 1e-3), 0, 1)
for k_, (n_, w_) in enumerate((("bow_knot", 1 - ss(0.0, 0.35, uu)), ("hair_back.2", ss(0.0, 0.35, uu) * (1 - ss(0.5, 0.9, uu))), ("hair_back.3", ss(0.5, 0.9, uu)))):
    W[idx[ib_], BI[n_]] += w_ * rib
up_ = ~rib; lob = {}
for s in "LR":
    b1, b2 = B[f"bow.{s}.1"], B[f"bow.{s}.2"]
    ws_ = chain_w(Pb_, ["bow_knot", f"bow.{s}.1", f"bow.{s}.2"], [(b1[0] + unit(b1[1] - b1[0]) * 0.005, unit(b1[1] - b1[0])), (b2[0], unit(b2[1] - b1[0]))], [0.02, 0.03])
    side_ = (Pb_[:, 0] * (1 if s == "L" else -1)) > 0
    for n_, w_ in zip(["bow_knot", f"bow.{s}.1", f"bow.{s}.2"], ws_): W[idx[ib_], BI[n_]] += w_ * up_ * side_
W[idx[ib_], BI["bow_knot"]] += up_ * (Pb_[:, 0] == 0)
used[ib_] = 1.0
bdist = np.linalg.norm(P - np.array(G["bun"]["c"]), axis=1); wbun = hv * (1 - ss(0.6 * br, 1.0 * br, bdist)) * (~bw_)
W[idx, BI["bun"]] += wbun; used += wbun; hv = hv * (1 - wbun) if False else hv
vf = vf * (1 - wbun); vb = vb * (1 - wbun); vs = {s: vs[s] * (1 - wbun) for s in vs}
for nm in "LCR":
    w = vf * wfront[nm] / sf; b1 = B[f"hair_front.{nm}.1"]; b2 = B[f"hair_front.{nm}.2"]
    s2 = ss(-0.02, 0.02, (P - b2[0]) @ unit(b1[1] - b1[0] + b2[1] - b2[0]))
    W[idx, BI[f"hair_front.{nm}.1"]] += w * (1 - s2); W[idx, BI[f"hair_front.{nm}.2"]] += w * s2; used += w
hb = [B[f"hair_back.{i}"] for i in (1, 2, 3)]
sbw = chain_w(P, ["hair_back.1", "hair_back.2", "hair_back.3"], [(hb[1][0], unit(hb[0][1] - hb[0][0] + hb[1][1] - hb[1][0])), (hb[2][0], unit(hb[1][1] - hb[1][0] + hb[2][1] - hb[2][0]))], [0.03, 0.03])
for k in range(3): W[idx, BI[f"hair_back.{k+1}"]] += vb * sbw[k]
used += vb
for s in "LR":
    W[idx, BI[f"hair_side.{s}.1"]] += vs[s] * 0.6; W[idx, BI[f"hair_side.{s}.2"]] += vs[s] * 0.4 * ss(1.55 + DZ, 1.47 + DZ, P[:, 2]); used += vs[s] * (0.6 + 0.4 * ss(1.55 + DZ, 1.47 + DZ, P[:, 2]))
skin_low = (~hv) * (~bowv[idx]) * ss(1.45 + DZ, 1.40 + DZ, P[:, 2])
W[idx, BI["neck"]] += skin_low; used += skin_low
W[idx, BI["head"]] += np.clip(1 - used, 0, 1)
# unlabelled -> nearest bone head fallback
miss = W.sum(1) < 1e-6
if miss.any():
    HP = np.array([B[n][0] for n in BN]); W[np.nonzero(miss)[0], np.linalg.norm(V[miss][:, None] - HP[None], axis=-1).argmin(1)] = 1
print("missing", int(miss.sum()))
# Laplacian smoothing over the mesh graph (heals label seams)
E = set()
for f in FC:
    for i in range(len(f)):
        u_, v_ = f[i], f[(i + 1) % len(f)]; E.add((min(u_, v_), max(u_, v_)))
E = np.array(list(E)); deg = np.bincount(E.ravel(), minlength=nv).astype(np.float32)
W /= W.sum(1, keepdims=True)
for it in range(int(os.environ.get("WSMOOTH", "6"))):
    acc = np.zeros_like(W); np.add.at(acc, E[:, 0], W[E[:, 1]]); np.add.at(acc, E[:, 1], W[E[:, 0]])
    W = 0.5 * W + 0.5 * acc / np.maximum(deg, 1)[:, None]
# hair over skin: the H2 bangs/bob edge is painted on one head surface, so hair-chain weight must fade to 0 at the hair|skin boundary
# (geodesic distance in mesh edges from skin), else swinging a chain tears the forehead / nape; bangs capped at 0.6 (subtle by design)
skinv = np.zeros(nv, bool)
for fi, f in enumerate(FC):
    if fmat[fi] in ("skin", "eyes") and flab[fi] in ("head", "neck"): skinv[list(f)] = True
dsk = np.where(skinv, 0.0, np.inf); NE = int(os.environ.get("HAIRFADE", "10"))
for k in range(1, NE + 1):
    fr = dsk == k - 1
    for a_, b_ in ((0, 1), (1, 0)):
        m = fr[E[:, a_]] & np.isinf(dsk[E[:, b_]]); dsk[E[m, b_]] = k
gfade = ss(0.0, NE, np.minimum(dsk, NE))
hidx = [BI[n] for n in BN if n.startswith(("hair_front", "hair_back", "hair_side"))]
hv_all = np.isin(vlab, ["head"])
for j in hidx:
    cap = 0.6 if BN[j].startswith("hair_front") else 1.0
    new = np.where(hv_all, W[:, j] * gfade * cap, W[:, j])
    W[:, BI["head"]] += W[:, j] - new; W[:, j] = new
# torso / obi / skirt never follow the arms (a voxel bridge would otherwise smear obi colour into the armpit)
tv = np.isin(vlab, ["torso", "obi", "skirt"])
for j in [BI[n] for n in BN if n.startswith(("upper_arm", "forearm", "hand", "sleeve"))]:
    W[tv, BI["chest"]] += W[tv, j]; W[tv, j] = 0
# round 8 (ILLUS): the textured face must move rigidly with the head - no hair/neck weight on the head hull's front (face, cheeks, jaw, bangs,
# hull side locks): the illustration is painted on one surface, so any other bone there stretches the texture (smears / doubled edges).
# Only the back of the hull (bob back, bun, bow, ribbons: y > 0.02 H2) keeps its spring chains; side locks swing via the separate lock tubes.
if ILLUS:
    hidx = np.nonzero(vlab == "head")[0]; front = V[hidx, 1] < 0.02 - HF
    keepb = {BI[n] for n in BN if n.startswith(("hair_back", "bun", "bow"))}
    for j in range(len(BN)):
        if j == BI["head"] or j in keepb: continue
        W[hidx[front], BI["head"]] += W[hidx[front], j]; W[hidx[front], j] = 0
    for j in keepb:  # back chains: never on the front
        W[hidx[front], BI["head"]] += W[hidx[front], j]; W[hidx[front], j] = 0
    for j in range(len(BN)):  # any neck/chest weight that the smoothing pushed up into the jaw -> head
        if BN[j] in ("neck", "chest") or BN[j].startswith("hair_front") or BN[j].startswith("hair_side"):
            W[hidx, BI["head"]] += W[hidx, j]; W[hidx, j] = 0
# top-4 influences
o4 = np.argsort(-W, 1)[:, 4:]; np.put_along_axis(W, o4, 0, 1); W[W < 0.01] = 0; W /= W.sum(1, keepdims=True)
# ------------------------------------------------------------------ build Blender objects (contract frame)
sc = bpy.context.scene
arm = bpy.data.armatures.new("rig"); ao = bpy.data.objects.new("rig", arm); sc.collection.objects.link(ao)
bpy.context.view_layer.objects.active = ao; bpy.ops.object.mode_set(mode="EDIT")
for n in BN:
    h, t_, par, zh = B[n]; eb = arm.edit_bones.new(n); eb.head = Vector(Fw(h)); eb.tail = Vector(Fw(t_))
    zf = Fw(zh) / K; eb.align_roll(Vector(zf))
for n in BN:
    par = B[n][2]
    if par: arm.edit_bones[n].parent = arm.edit_bones[par]; arm.edit_bones[n].use_connect = False
bpy.ops.object.mode_set(mode="OBJECT")
me = bpy.data.meshes.new("body"); me.from_pydata([tuple(p) for p in Fw(V)], [], FC); me.validate()
for p in me.polygons: p.use_smooth = True
ca = me.color_attributes.new("Color", "BYTE_COLOR", "CORNER")
fa = me.attributes.new("mat", "INT", "FACE")
for p in me.polygons:
    m = fmat[p.index]; c = [x / 255 for x in MATS[m]] + [1]; fa.data[p.index].value = MN.index(m)
    for li in p.loop_indices: ca.data[li].color_srgb = c
PVC = {'hair': '#433833', 'dress': '#7d1918', 'skin': '#eaa991', 'sleeve': '#7d1918', 'socks': '#2b2927', 'boots': '#5e4a45', 'bow': '#962723', 'obi': '#857a90', 'eyes': '#342126'}
cp = me.color_attributes.new("PV", "BYTE_COLOR", "CORNER")
for p in me.polygons:
    hx_ = PVC[fmat[p.index]]; c = [int(hx_[i:i + 2], 16) / 255 for i in (1, 3, 5)] + [1]
    for li in p.loop_indices: cp.data[li].color_srgb = c
me.color_attributes.active_color = ca; me.color_attributes.render_color_index = me.color_attributes.find("Color")
# ---------------- round 2: per-view master projection for the head group (hull head + side locks) + limb ID colours
from mathutils.bvhtree import BVHTree
AL = json.load(open(os.path.join(os.path.dirname(os.path.abspath(BLEND)), "align.json")))
AZC = {"SE": (1, 1), "E": (1, 0), "S": (0, 1), "NE": (1, -1), "N": (0, -1), "SW": (-1, 1), "W": (-1, 0), "NW": (-1, -1)}  # contract-frame camera azimuths (render_motion.AZ)
def camH2(view):
    ax, ay = AZC[view]; c = np.array([-ax, -ay, 0.0]); c /= np.linalg.norm(c); el = np.radians(30)
    loc = np.array([c[0] * np.cos(el), c[1] * np.cos(el), np.sin(el)]); f = -loc / np.linalg.norm(loc)
    r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r); u = np.cross(r, f)
    ps = np.radians(AL[view].get("yaw", 0.0)); Rz = np.array([[np.cos(ps), -np.sin(ps), 0], [np.sin(ps), np.cos(ps), 0], [0, 0, 1]]); a_ = AL[view]
    def proj(P):
        Q = P @ Rz.T; return np.stack([96 + 52.608 * (Q @ r) - 32 + a_.get("reg_dx", a_["dx"]), 152 - 52.608 * (Q @ u) - 32 + a_.get("reg_dy", a_["dy"])], -1)
    return proj, Rz.T @ (-f)
nf = len(me.polygons); cen = np.zeros(nf * 3); nrm = np.zeros(nf * 3)
me.polygons.foreach_get("center", cen); me.polygons.foreach_get("normal", nrm)
cenH = (cen.reshape(-1, 3) * np.array([-1, -1, 1.0])) / K; nrmH = nrm.reshape(-1, 3) * np.array([-1, -1, 1.0])
lv = np.zeros(len(me.loops), int); me.loops.foreach_get("vertex_index", lv)
bvh = BVHTree.FromPolygons([Vector(v) for v in V], FC)
headgrp = np.isin(np.array(flab).astype(str), ["head", "lock_L", "lock_R"])
# round 5: no master-pixel projection. FACE UV for F's textures: front-orthographic planar map of the head (H2 frame):
#   u = 0.5 + x / 0.44 (her left = image right), v = (z - 1.38) / 0.44; mask attribute fmask = 1 on the front-facing skull faces of the face zone
if not ILLUS:
    uvf = me.uv_layers.new(name="face_uv"); VL = V[lv]; uvf.data.foreach_set("uv", np.stack([0.5 + VL[:, 0] / 0.44, (VL[:, 2] - 1.38) / 0.44], 1).ravel())
    fmk = me.attributes.new("fmask", "FLOAT", "FACE"); fmk.data.foreach_set("value", FZ.astype(np.float32))
    print("face zone faces", int(FZ.sum()), flush=True)
else:
    # round 7: per-view projection of the hi-res illustrations (rig/illus_map.json: illustration -> master map; master registration from
    # align.json). UV pj_<V> = illustration px / size; mask pm_<V> = head-group faces (hull + side locks) visible at rest from that view.
    IM = json.load(open(os.path.join(os.path.dirname(os.path.abspath(BLEND)), "illus_map.json")))
    from mathutils.bvhtree import BVHTree as _BVH
    nf = len(me.polygons); cen = np.zeros(nf * 3); nrm = np.zeros(nf * 3); me.polygons.foreach_get("center", cen); me.polygons.foreach_get("normal", nrm)
    cenH = (cen.reshape(-1, 3) * np.array([-1, -1, 1.0])) / K; nrmH = nrm.reshape(-1, 3) * np.array([-1, -1, 1.0])
    lv = np.zeros(len(me.loops), int); me.loops.foreach_get("vertex_index", lv); bvh = _BVH.FromPolygons([Vector(v) for v in V], FC)
    headgrp = np.isin(np.array(flab).astype(str), ["head"]); SHIFT = np.array([0, HF, 0])  # undo the head-forward move; r9: lock tubes stay flat hair (their projected cheek strip streaked when they swung)
    MIRR = {"SW": "SE", "W": "E", "NW": "NE"}; ANC = json.load(open("/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/heads/anchor.json"))["views"]
    for view in AZC:
        src = MIRR.get(view, view); mp = IM[src]; proj, dv = camH2(view)
        cr = proj(V[lv] + SHIFT)  # master-cell coords of this view
        if view in MIRR: cr[:, 0] = 128.0 - cr[:, 0]  # mirrored view = mirror of the source view's master cell
        Xi = (cr[:, 0] - mp["bx"]) / mp["ax"]; Yi = (cr[:, 1] - mp["by"]) / mp["ay"]; Wd, Ht = mp["size"]
        # round 8: lift the fringe ~1.5 sprite px above the eye line (UV warp in the forehead band, so expression textures follow):
        # a surface point in the band samples the texture from up to LIFT master rows lower -> the bang edge reads higher, eyes untouched
        an = ANC.get(src, {}); ey = [e["y0"] for e in an.get("eyes", [])]
        if ey:
            LIFT = {"SE": 3.0, "SW": 3.0}.get(view, float(os.environ.get("FRINGE_LIFT", "1.5"))); y0e = min(ey); ytop, ybot = y0e - 5.0, y0e + 1.0  # master rows: above the brows .. lash row  # r9: SE/SW lifted 1.5 px more (fringe crowded the near eye)
            exs = [e["x0"] for e in an["eyes"]]; xl, xr = min(exs) - 3.0, max(exs) + 9.0
            xm = cr[:, 0] if view not in MIRR else 128.0 - cr[:, 0]; ym = cr[:, 1]
            tt = np.clip((ym - ytop) / (ybot - ytop), 0, 1); inband = (ym > ytop) & (ym < ybot) & (xm > xl) & (xm < xr)
            Yi = Yi + np.where(inband, LIFT * np.sin(np.pi * tt) / mp["ay"], 0.0)
        if view in MIRR: Xi = Wd - Xi  # flipped illustration texture
        uvl = me.uv_layers.new(name="pj_" + view); uvl.data.foreach_set("uv", np.stack([Xi / Wd, 1 - Yi / Ht], 1).ravel())
        pm = np.zeros(nf, np.float32); D = Vector(dv)
        for fi in np.nonzero(headgrp & ((nrmH @ dv) > float(os.environ.get("PM_FACING", "-0.05"))))[0]:  # r8: grazing faces carry the drawn silhouette line -> left to the chain
            hit = bvh.ray_cast(Vector(cenH[fi]) + D * 0.006, D, 2.0)
            if hit[0] is None or hit[3] < 0.008: pm[fi] = 1.0
        at = me.attributes.new("pm_" + view, "FLOAT", "FACE"); at.data.foreach_set("value", pm)
        fa = (np.clip(nrmH @ dv, 0, 1) * pm).astype(np.float32)  # r9: rest facing of each face toward this view's camera (per-face view pick)
        at2 = me.attributes.new("fa_" + view, "FLOAT", "FACE"); at2.data.foreach_set("value", fa)
        print("illus proj", view, int(pm.sum()), "of", int(headgrp.sum()), flush=True)
    ao["head_mode"] = "illus"
LIDC = {"leg_L": (255, 0, 0), "boot_L": (255, 0, 0), "foot_L": (255, 0, 0), "leg_R": (0, 255, 0), "boot_R": (0, 255, 0), "foot_R": (0, 255, 0),
        "arm_L": (0, 0, 255), "sleeve_L": (0, 0, 255), "hand_L": (0, 0, 255), "arm_R": (255, 255, 0), "sleeve_R": (255, 255, 0), "hand_R": (255, 255, 0)}
cl = me.color_attributes.new("LID", "BYTE_COLOR", "CORNER"); lc = np.zeros((len(me.loops), 4), np.float32); lc[:, 3] = 1
fl = np.array(flab).astype(str); lst = np.zeros(nf, int); me.polygons.foreach_get("loop_start", lst); ltot = np.zeros(nf, int); me.polygons.foreach_get("loop_total", ltot)
for fi in range(nf):
    c_ = LIDC.get(fl[fi])
    if c_: lc[lst[fi]:lst[fi] + ltot[fi], :3] = np.array(c_) / 255.0
cl.data.foreach_set("color_srgb", lc.ravel()) if hasattr(cl.data[0], "color_srgb") else None
me.color_attributes.active_color = ca
bo = bpy.data.objects.new("body", me); sc.collection.objects.link(bo); bo.parent = ao
for j, n in enumerate(BN):
    vg = bo.vertex_groups.new(name=n); nz = np.nonzero(W[:, j] > 0)[0]
    for i in nz: vg.add([int(i)], float(W[i, j]), "REPLACE")
md = bo.modifiers.new("arm", "ARMATURE"); md.object = ao; md.use_deform_preserve_volume = os.environ.get("DQS", "1") == "1"
for p in ao.pose.bones: p.rotation_mode = "QUATERNION"
ao["mat_names"] = MN; ao["units_per_h2"] = K
# ---------------- round 3: FACE ANCHORS (for F): back-project the S master face anchors (v2/m96/heads/anchor.json) onto the head surface
# (ray from the S camera through the master pixel centre, first hit on the rest mesh), check them against the SE/E master anchors,
# and create empties "face.<name>" parented to the head bone (they follow the head; render_motion exports them per frame).
ANC = json.load(open("/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/heads/anchor.json"))["views"]
def m2d(view):  # master 2D anchors (centres, master cell px) per view; her right eye = screen-left in S/SE
    a_ = ANC[view]; e = a_.get("eyes", []); out = {}
    if view == "S":
        r_, l_ = sorted(e, key=lambda q: q["x0"])
        out.update({"eye.R": (r_["x0"] + 3.0, r_["y0"] + 3.5), "eye.L": (l_["x0"] + 3.0, l_["y0"] + 3.5),
                    "brow.R": (r_["x0"] + 3.0, r_["y0"] - 1.5), "brow.L": (l_["x0"] + 3.0, l_["y0"] - 1.5)})
        bl = sorted(a_["blush"], key=lambda q: q[0]); out["cheek.R"] = (bl[0][0] + 2.0, bl[0][1] + 1.0); out["cheek.L"] = (bl[1][0] + 2.0, bl[1][1] + 1.0)
    elif view == "SE":
        nr, fr = sorted(e, key=lambda q: q["x0"]); out.update({"eye.R": (nr["x0"] + 3.0, nr["y0"] + 3.5), "eye.L": (fr["x0"] + 2.0, fr["y0"] + 3.5)})
        bl = sorted(a_["blush"], key=lambda q: q[0]); out["cheek.R"] = (bl[0][0] + 2.0, bl[0][1] + 1.0); out["cheek.L"] = (bl[1][0] + 1.5, bl[1][1] + 1.0)
    elif view == "E" and e:
        out["eye.R"] = (e[0]["x0"] + 3.0, e[0]["y0"] + 3.5)
        if a_.get("blush"): out["cheek.R"] = (a_["blush"][0][0] + 2.0, a_["blush"][0][1] + 1.0)
    if a_.get("mouth"): out["mouth"] = (a_["mouth"][0] + 2.0, a_["mouth"][1] + 1.5)
    return out
def cam_ray(view, col, row):
    ax, ay = AZC[view]; c = np.array([-ax, -ay, 0.0]); c /= np.linalg.norm(c); el = np.radians(30)
    loc = np.array([c[0] * np.cos(el), c[1] * np.cos(el), np.sin(el)]); f = -loc / np.linalg.norm(loc)
    r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r); u = np.cross(r, f); a_ = AL[view]
    ps = np.radians(a_.get("yaw", 0.0)); Rz = np.array([[np.cos(ps), -np.sin(ps), 0], [np.sin(ps), np.cos(ps), 0], [0, 0, 1]])
    qa = (col - 96 + 32 - a_.get("reg_dx", a_["dx"])) / 52.608; qb = (152 - 32 + a_.get("reg_dy", a_["dy"]) - row) / 52.608
    o = qa * r + qb * u - 3.0 * f; return Rz.T @ o, Rz.T @ f
FA2 = {}
def affine(view):
    proj, _ = camH2(view); c0 = proj(np.zeros((1, 3)))[0]; Mx = np.stack([proj(np.eye(3)[i][None])[0] - c0 for i in range(3)], 1); return Mx, c0  # 2x3, 2
AFF = {v: affine(v) for v in ("S", "SE", "E")}; MV = {v: m2d(v) for v in ("S", "SE", "E")}
for n_ in MV["S"]:
    rows, rhs = [], []
    for v in ("S", "SE", "E"):
        if n_ in MV[v]: Mx, c0 = AFF[v]; rows.append(Mx); rhs.append(np.array(MV[v][n_]) - c0)
    A_ = np.concatenate(rows); b_ = np.concatenate(rhs)
    if len(rows) == 1:  # S only (brows): depth from the matching eye
        pe = FA2.get(n_.replace("brow", "eye"))
        y0 = (pe["p"][1] + HF) if pe else -0.2; A_ = np.vstack([A_, [0, 1, 0]]); b_ = np.append(b_, y0)
    P_ = np.linalg.lstsq(A_, b_, rcond=None)[0] + np.array([0, -HF, 0])  # masters place the head; round 5 moves it forward by HF
    nr_ = bvh.find_nearest(Vector(P_)); nn_ = np.array(nr_[1][:]); nn_ = nn_ / np.linalg.norm(nn_)
    nn_ = 0.5 * nn_ + 0.5 * np.array([0, -1.0, 0]); nn_ /= np.linalg.norm(nn_)  # face normal: half surface normal, half head-forward (hull normals are coarse)
    FA2[n_] = {"p": P_, "n": nn_, "surf": np.array(nr_[0][:])}
for n_ in [k for k in FA2 if k.startswith("brow")]:  # brows after eyes (depth)
    pass
for s in "LR":  # mirror-symmetrise the L/R pairs
    for b_ in ("eye", "brow", "cheek"):
        a1, a2 = FA2.get(f"{b_}.L"), FA2.get(f"{b_}.R")
        if a1 and a2:
            pm = (a1["p"] + a2["p"] * np.array([-1, 1, 1])) / 2; nm_ = (a1["n"] + a2["n"] * np.array([-1, 1, 1])) / 2
            a1["p"], a2["p"] = pm, pm * np.array([-1, 1, 1]); a1["n"], a2["n"] = nm_, nm_ * np.array([-1, 1, 1])
            sm = (a1["surf"] + a2["surf"] * np.array([-1, 1, 1])) / 2; a1["surf"], a2["surf"] = sm, sm * np.array([-1, 1, 1])
FA2["mouth"]["p"][0] = 0.0
chk = {}
for view in ("SE", "E"):
    proj, _ = camH2(view); M2 = m2d(view)
    for n_, (cx, cy) in M2.items():
        if n_ in FA2: q_ = proj(FA2[n_]["p"][None])[0]; chk[f"{view}:{n_}"] = [round(float(q_[0] - cx), 2), round(float(q_[1] - cy), 2)]
print("face anchor reprojection error vs master anchors (px):", chk, flush=True)
hb_ = ao.data.bones["head"]; FAJ = {}
for n_, a_ in FA2.items():
    e = bpy.data.objects.new("face." + n_, None); e.empty_display_type = "SPHERE"; e.empty_display_size = 0.01; sc.collection.objects.link(e)
    pw = Vector(Fw(a_["p"])); nw = Vector(Fw(a_["n"]) / K).normalized()
    e.parent = ao; e.parent_type = "BONE"; e.parent_bone = "head"
    e.matrix_world = Matrix.Translation(pw) @ nw.to_track_quat("Z", "Y").to_matrix().to_4x4()
    FAJ[n_] = {"uv": [round(0.5 + float(a_["p"][0]) / 0.44, 4), round((float(a_["p"][2]) - 1.38) / 0.44, 4)], "rest": [round(x, 5) for x in pw], "normal": [round(x, 5) for x in nw], "surf_depth_m": round(float(np.linalg.norm(a_["surf"] - a_["p"]) * K), 4), "surf": [round(x, 5) for x in Fw(a_["surf"])]}
ao["face_anchors"] = json.dumps(FAJ)
json.dump({"_doc": "R round 3: face anchors on the head (contract frame, metres, rest). Empties face.<name> in rig.blend are parented to the head bone; render_motion.py exports them per frame (info frames[i].face). Back-projected from the S master anchors (v2/m96/heads/anchor.json), mirror-symmetrised; check = reprojection error vs the SE/E master anchors in px.",
           "anchors": FAJ, "check_px": chk}, open(os.path.join(os.path.dirname(os.path.abspath(BLEND)), "face_anchors.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
# rest_skeleton.json (world rest space == armature space, armature object at identity)
out = {}
for b in arm.bones:
    M3 = b.matrix_local.to_3x3()
    out[b.name] = {"head": [round(x, 5) for x in b.head_local], "tail": [round(x, 5) for x in b.tail_local],
                   "roll": None,
                   "parent": b.parent.name if b.parent else None,
                   "matrix": [[round(M3[r][c], 5) for c in range(3)] for r in range(3)]}
bpy.context.view_layer.objects.active = ao; bpy.ops.object.mode_set(mode="EDIT")
for eb in arm.edit_bones: out[eb.name]["roll"] = round(eb.roll, 5)
bpy.ops.object.mode_set(mode="OBJECT")
json.dump(out, open(SKJ, "w"), indent=1)
print("RIG", len(BN), "bones", nv, "verts", flush=True)
