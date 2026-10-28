# reproportion.py SPEC.json IN_PARTS_DIR SKEL.txt OUT_PARTS_DIR
# Apply a proportion spec to the rigid parts (glb frame: Y up, faces +Z, her left +X, feet at y=-1) and re-derive pivots.json + skel.txt.
# Spec (all optional, multipliers unless noted; unknown keys ignored):
#  {"head": {"scale": 0.8, "offset": [0,0,0]},          uniform about the neck pivot; bow + bun follow the head
#   "neck": {"extra": 0.03},                             raise head/bow/bun (glb units, char height ~2)
#   "torso": {"width": 0.85, "depth": 0.9, "height": 1.0},
#   "skirt": {"width": 0.9, "depth": 0.9, "height": 1.0},
#   "arms": {"length": 1.15, "thickness": 0.9, "shoulder_x": 1.0},
#   "legs": {"length": 1.3, "thickness": 0.9, "spread": 1.0},
#   "hands": {"scale": 0.85}, "boots": {"scale": 0.85},
#   "eyes": {"dy": 0.0, "scale": 1.0}}                  eye-ID verts moved/scaled on the head surface (colour only)
# Feet stay on y=-1; everything above a scaled segment is carried up/down by that segment's length change.
import sys, os, json, shutil
import numpy as np, trimesh
spec_p, idir, skp, odir = sys.argv[1:5]
SP = json.load(open(spec_p)); os.makedirs(odir, exist_ok=True)
# accept flat keys too ("head_scale": .9, "legs.length": 1.8, "leg_length", "arm_length", "torso_waist", ...)
ALIAS = {"leg": "legs", "arm": "arms", "hand": "hands", "boot": "boots", "eye": "eyes", "shoulder": "arms", "waist": "torso"}
for k in list(SP):
    if k.startswith("_") or isinstance(SP[k], dict): continue
    if not isinstance(SP[k], (int, float)): continue
    a, _, b = k.replace(".", "_").partition("_")
    if k in ("shoulder", "shoulders"): a, b = "arms", "shoulder_x"
    if a == "waist": a, b = "torso", "waist"
    a = ALIAS.get(a, a); b = b or "scale"
    SP.setdefault(a, {})[b] = SP.pop(k)
def g(sec, k, d=1.0): return float(SP.get(sec, {}).get(k, d))
piv = json.load(open(os.path.join(idir, "pivots.json")))
def load(n):
    s = trimesh.load(os.path.join(idir, n + ".glb")); return s.dump(concatenate=True) if hasattr(s, "dump") else s
M = {n: load(n) for n in piv if os.path.exists(os.path.join(idir, n + ".glb"))}
P = {n: np.array(d["pivot"], float) for n, d in piv.items()}
FEET = -1.0
def col(m): return m.visual.vertex_colors[:, :3].astype(int)
SKIN, BOOT, EYE = (239, 179, 138), (6, 4, 6), (23, 55, 92)
def ismask(m, rgb): return np.all(np.abs(col(m) - np.array(rgb)) < 6, axis=1)
# ---------------- vertical bookkeeping
hip_y = P["leg_R"][1]; L_leg = hip_y - FEET; d_leg = (g("legs", "length") - 1) * L_leg          # legs grow downward-fixed -> body up
tor_lo = P["torso"][1]; tor_hi = M["torso"].bounds[1][1]; Ht = tor_hi - tor_lo; d_tor = (g("torso", "height") - 1) * Ht
neck = float(SP.get("neck", {}).get("extra", 0.0))
def up_above_torso(y): return d_leg + d_tor * np.clip((y - tor_lo) / Ht, 0, 1)                   # carry for points on/above the torso
out_piv = {}
# ---------------- legs
for s, sg in (("R", -1), ("L", 1)):
    n = f"leg_{s}"; m = M[n]; v = m.vertices.copy(); p = P[n].copy()
    ax_x = p[0] * g("legs", "spread"); cz = v[:, 2].mean()
    th = g("legs", "thickness"); ln = g("legs", "length")
    v[:, 0] = ax_x + (v[:, 0] - p[0]) * th; v[:, 2] = cz + (v[:, 2] - cz) * th
    v[:, 1] = FEET + (v[:, 1] - FEET) * ln                                                           # feet fixed
    b = ismask(m, BOOT); bs = g("boots", "scale")
    if b.any() and bs != 1:
        c = v[b].mean(0); c[1] = FEET; w = np.clip((v[:, 1] - (v[b][:, 1].max() + 0.05)) / -0.1, 0, 1)  # soft falloff above the boot
        v += (bs - 1) * w[:, None] * (v - c)
    m.vertices = v; p2 = p.copy(); p2[0] = ax_x; p2[1] = FEET + (p[1] - FEET) * ln; out_piv[n] = p2
# ---------------- skirt + torso
for n, sec in (("skirt", "skirt"), ("torso", "torso")):
    m = M[n]; v = m.vertices.copy(); p = P[n].copy(); cx, cz = 0.0, v[:, 2].mean()
    v[:, 0] = cx + (v[:, 0] - cx) * g(sec, "width"); v[:, 2] = cz + (v[:, 2] - cz) * g(sec, "depth")
    if n == "torso" and g("torso", "waist") != 1:  # waist taper: extra x(+z/2) scale at the bottom of the torso fading to 1 at the chest
        y0, y1 = v[:, 1].min(), v[:, 1].max(); tw = np.clip(1 - (v[:, 1] - y0) / (0.6 * (y1 - y0)), 0, 1)
        f_ = 1 + (g("torso", "waist") - 1) * tw; v[:, 0] = cx + (v[:, 0] - cx) * f_; v[:, 2] = cz + (v[:, 2] - cz) * (1 + (f_ - 1) / 2)
    if n == "skirt" and g("torso", "waist") != 1:  # skirt waistband follows the waist, hem keeps its width
        y0, y1 = v[:, 1].min(), v[:, 1].max(); tw = np.clip((v[:, 1] - y0) / (y1 - y0), 0, 1) ** 2
        f_ = 1 + (g("torso", "waist") - 1) * tw; v[:, 0] = cx + (v[:, 0] - cx) * f_; v[:, 2] = cz + (v[:, 2] - cz) * (1 + (f_ - 1) / 2)
    if n == "torso": v[:, 1] = tor_lo + (v[:, 1] - tor_lo) * g("torso", "height") + d_leg
    else:  # skirt hangs from its waist pivot
        v[:, 1] = p[1] + (v[:, 1] - p[1]) * g("skirt", "height") + d_leg
    m.vertices = v; p2 = p.copy(); p2[1] += d_leg; out_piv[n] = p2
# ---------------- arms (+ hands)
for s in ("R", "L"):
    n = f"arm_{s}"; m = M[n]; v = m.vertices.copy(); p = P[n].copy()
    far = v[np.argmax(np.linalg.norm(v - p, axis=1))]; ax = (far - p) / np.linalg.norm(far - p)
    rel = v - p; t = rel @ ax; perp = rel - t[:, None] * ax
    v = p + (t * g("arms", "length"))[:, None] * ax + perp * g("arms", "thickness")
    h = ismask(m, SKIN); hs = g("hands", "scale")
    if h.any() and hs != 1: c = v[h].mean(0); v[h] = c + (v[h] - c) * hs
    p2 = p.copy(); p2[0] *= g("torso", "width") * g("arms", "shoulder_x"); p2[1] += up_above_torso(p[1])
    v += p2 - p; m.vertices = v; out_piv[n] = p2
# ---------------- head, bow, bun
hp = P["head"].copy(); hs = g("head", "scale"); off = np.array(SP.get("head", {}).get("offset", [0, 0, 0]), float)
hp2 = hp.copy(); hp2[1] += up_above_torso(hp[1]) + neck; hp2 += off
for n in ("head", "bow", "bun"):
    if n not in M: continue
    m = M[n]; v = m.vertices.copy(); v = hp2 + (v - hp) * hs; m.vertices = v; out_piv[n] = hp2.copy()
if "eyes" in SP and "head" in M:
    m = M["head"]; e = ismask(m, EYE)
    if e.any():
        dy = float(SP["eyes"].get("dy", 0.0)) * hs; es = float(SP["eyes"].get("scale", 1.0))
        vc = m.visual.vertex_colors.copy(); skin_c = np.array(list(SKIN) + [255], np.uint8)
        V = m.vertices; cen = [V[e & (V[:, 0] * sg > 0)].mean(0) for sg in (-1, 1)]
        vc[e] = skin_c
        for c in cen:
            c = c + np.array([0, dy, 0]); r = 0.065 * hs * es
            near = np.linalg.norm((V - c)[:, :2] / [1, 1.25], axis=1) < r
            sel = near & (V[:, 2] > c[2] - 0.08) & (ismask(m, SKIN) | e)
            vc[sel] = list(EYE) + [255]
        m.visual.vertex_colors = vc
# ---------------- katana prop untouched; write parts + pivots
for n, m in M.items():
    m.export(os.path.join(odir, n + ".glb"))
pj = json.load(open(os.path.join(idir, "pivots.json")))
for n, p in out_piv.items(): pj[n]["pivot"] = [round(float(x), 4) for x in p]
pj["_reproportion"] = {"spec": SP, "src": os.path.abspath(idir), "d_leg": round(float(d_leg), 4), "d_torso": round(float(d_tor), 4)}
json.dump(pj, open(os.path.join(odir, "pivots.json"), "w"), indent=1)
# ---------------- skeleton (Omni 51-joint rows: 0-1 spine/chest, 2-6 neck/head, 7-25 R arm+hand, 26-44 L arm+hand, 45-50 legs)
sk = np.loadtxt(skp); sk2 = sk.copy()
def tf_leg(q, s):
    p = P[f"leg_{s}"]; q = q.copy(); q[0] = out_piv[f"leg_{s}"][0] + (q[0] - p[0]) * g("legs", "thickness"); q[1] = FEET + (q[1] - FEET) * g("legs", "length"); return q
def tf_arm(q, s):
    p = P[f"arm_{s}"]; p2 = out_piv[f"arm_{s}"]; return p2 + (q - p) * g("arms", "length")
def tf_trunk(q):
    q = q.copy(); q[0] *= g("torso", "width"); q[1] = q[1] + up_above_torso(q[1]) + (d_tor * 0); return q
def tf_head(q): return hp2 + (q - hp) * hs
for r in range(len(sk)):
    for c in (0, 3):
        q = sk[r, c:c + 3]
        if 45 <= r <= 50: q2 = tf_leg(q, "R" if r <= 47 else "L")
        elif 7 <= r <= 25: q2 = tf_arm(q, "R")
        elif 26 <= r <= 44: q2 = tf_arm(q, "L")
        elif r >= 3 or (r == 2 and c == 3): q2 = tf_head(q)
        else: q2 = tf_trunk(q)
        sk2[r, c:c + 3] = q2
np.savetxt(os.path.join(odir, "skel.txt"), sk2, fmt="%.5f")
print("reproportioned ->", odir, {k: [round(float(x), 3) for x in v] for k, v in out_piv.items()})
# ---------------- measure (head = head mesh without bow; widths in x)
H = M["head"].bounds; hh = H[1][1] - H[0][1]; hw = H[1][0] - H[0][0]
top = max(m.bounds[1][1] for n, m in M.items() if n not in ("bow", "katana")); tot = top - FEET
tv = M["torso"].vertices; ty0, ty1 = tv[:, 1].min(), tv[:, 1].max()
def wid(lo, hi): s = tv[(tv[:, 1] >= lo) & (tv[:, 1] <= hi)]; return float(np.ptp(s[:, 0])) if len(s) else 0.0
sh_w = abs(out_piv["arm_L"][0] - out_piv["arm_R"][0]); waist = wid(ty0, ty0 + 0.15 * (ty1 - ty0))
leg_frac = (out_piv["leg_R"][1] - FEET) / tot; neck_gap = H[0][1] - ty1
meas = {"heads_tall": round(tot / hh, 2), "shoulder_over_headw": round(sh_w / hw, 2), "waist_over_headw": round(waist / hw, 2),
        "legs_frac_of_height": round(float(leg_frac), 3), "neck_gap": round(float(neck_gap), 3), "head_h": round(float(hh), 3), "total_h": round(float(tot), 3)}
pj["_reproportion"]["measure"] = meas; json.dump(pj, open(os.path.join(odir, "pivots.json"), "w"), indent=1)
print("measure", meas)
