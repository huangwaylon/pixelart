# repro_h.py (G96: repro_g + legs.sock thigh-high sock colour band, arms.flare kimono sleeve flare, arms.slen sleeve over-length)
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
SOCK = (5, 6, 16)  # G96 sock ID (sRGB ~ (38,42,71) in the matid render)
def ismask(m, rgb): return np.all(np.abs(col(m) - np.array(rgb)) < 6, axis=1)
# ---------------- vertical bookkeeping
hip_y = P["leg_R"][1]; L_leg = hip_y - FEET
# RIGCAL: piecewise leg map (shin = feet..knee, thigh = knee..hip), multipliers on top of legs.length
_sk0 = np.loadtxt(skp); KNEE_Y = float(_sk0[45, 4])
LN, TH, SH = g("legs", "length"), g("legs", "thigh"), g("legs", "shin")
def leg_y(y):
    y = np.asarray(y, float); lo = FEET + (y - FEET) * LN * SH; yk = FEET + (KNEE_Y - FEET) * LN * SH
    return np.where(y <= KNEE_Y, lo, yk + (y - KNEE_Y) * LN * TH)
d_leg = float(leg_y(hip_y)) - hip_y          # legs grow downward-fixed -> body up
tor_lo = P["torso"][1]; tor_hi = M["torso"].bounds[1][1]; Ht = tor_hi - tor_lo; d_tor = (g("torso", "height") - 1) * Ht
neck = float(SP.get("neck", {}).get("extra", 0.0))
def up_above_torso(y): return d_leg + d_tor * np.clip((y - tor_lo) / Ht, 0, 1)                   # carry for points on/above the torso
out_piv = {}
# ---------------- legs
for s, sg in (("R", -1), ("L", 1)):
    n = f"leg_{s}"; m = M[n]; v = m.vertices.copy(); p = P[n].copy()
    ax_x = p[0] * g("legs", "spread"); cz = v[:, 2].mean()
    th = g("legs", "thickness"); ln = g("legs", "length")
    kb = np.clip((v[:, 1] - (KNEE_Y - 0.06)) / 0.12, 0, 1); kb = kb * kb * (3 - 2 * kb)            # 0 shin .. 1 thigh
    thv = th * (g("legs", "shin_w") * (1 - kb) + g("legs", "thigh_w") * kb)
    thd = th * (g("legs", "shin_d", g("legs", "shin_w")) * (1 - kb) + g("legs", "thigh_d", g("legs", "thigh_w")) * kb)
    v[:, 0] = ax_x + (v[:, 0] - p[0]) * thv; v[:, 2] = cz + (v[:, 2] - cz) * thd
    if "prof" in SP.get("legs", {}):  # RIGCAL: absolute leg profile [thigh_x, thigh_z, shin_x, shin_z] (glb units): straight thigh, knee step, straight shin
        tx, tz, sx_, sz_ = [float(t) for t in SP["legs"]["prof"]]; y0 = v[:, 1].copy()
        ytop = p[1] + float(SP["legs"].get("ytop", -0.10)); ybot = FEET + g("boots", "ankle", 0.15) / (LN * SH)                       # factors frozen above ytop / below the boot line
        bins = np.arange(y0.min(), y0.max() + 0.03, 0.03); idx = np.clip(np.digitize(y0, bins) - 1, 0, len(bins) - 1)
        cx_ = np.zeros(len(bins)); cz_ = np.zeros(len(bins)); wx_ = np.zeros(len(bins)); wz_ = np.zeros(len(bins))
        for b_ in range(len(bins)):
            k_ = idx == b_
            if k_.sum() < 6: wx_[b_] = np.nan; continue
            q = v[k_]; cx_[b_] = (q[:, 0].max() + q[:, 0].min()) / 2; cz_[b_] = (q[:, 2].max() + q[:, 2].min()) / 2; wx_[b_] = np.ptp(q[:, 0]); wz_[b_] = np.ptp(q[:, 2])
        ok = ~np.isnan(wx_); yb = bins + 0.015
        for arr in (cx_, cz_, wx_, wz_): arr[~ok] = np.interp(yb[~ok], yb[ok], arr[ok])
        yc = np.clip(yb, ybot, ytop); wxc = np.interp(yc, yb, wx_); wzc = np.interp(yc, yb, wz_)
        kb_ = np.clip((yc - (KNEE_Y - 0.04)) / 0.08, 0, 1); kb_ = kb_ * kb_ * (3 - 2 * kb_)
        tp_ = float(SP["legs"].get("taper", 0.0))  # H2 legs.taper: thigh WIDTH narrows linearly from ytop (x1) to the knee (x(1-taper))
        if tp_: u_ = np.clip((yc - KNEE_Y) / max(ytop - KNEE_Y, 1e-3), 0, 1); tx = tx * (1 - tp_ * (1 - u_))  # width only (E depth profile unchanged)
        fx = np.clip((sx_ + (tx - sx_) * kb_) / np.maximum(wxc, 1e-3), 0.4, 3); fz = np.clip((sz_ + (tz - sz_) * kb_) / np.maximum(wzc, 1e-3), 0.4, 3)
        fx = np.convolve(np.pad(fx, 1, mode="edge"), [0.25, 0.5, 0.25], "valid"); fz = np.convolve(np.pad(fz, 1, mode="edge"), [0.25, 0.5, 0.25], "valid")
        ccx = np.interp(yc, yb, cx_); ccz = np.interp(yc, yb, cz_)
        v[:, 0] = ccx[idx] + (v[:, 0] - ccx[idx]) * fx[idx]; v[:, 2] = ccz[idx] + (v[:, 2] - ccz[idx]) * fz[idx]
        st = g("legs", "straight", 0.0)  # RIGCAL: 0..1 pull the leg axis (above the boot) onto a vertical line through the boot-top centre (parallel thighs)
        if st:
            x_t = float(np.interp(KNEE_Y + 0.15, yb, cx_))  # upper-thigh centre; whole leg (boot included) moved onto x = x_t
            v[:, 0] += st * (x_t - np.interp(np.clip(y0, ybot, None), yb, cx_))
    v[:, 1] = leg_y(v[:, 1])                                                                           # feet fixed
    b = ismask(m, BOOT); bs = g("boots", "scale")
    if b.any() and bs != 1:
        c = v[b].mean(0); c[1] = FEET; w = np.clip((v[:, 1] - (v[b][:, 1].max() + 0.05)) / -0.1, 0, 1)  # soft falloff above the boot
        v += (bs - 1) * w[:, None] * (v - c)
    if SP.get("boots", {}).get("fwd"):  # RIGCAL: turn the toe-out boot to point straight forward (+z), about the leg axis at the ankle
        top_ = FEET + g("boots", "top", 0.3); lo_ = v[:, 1] < top_ + 0.05; ft = v[:, 1] < FEET + 0.08
        q = v[ft][:, [0, 2]]; q = q - q.mean(0); _, _, vt = np.linalg.svd(q, full_matrices=False); d_ = vt[0] if vt[0][1] > 0 else -vt[0]
        if np.dot(v[ft][:, 2] - v[ft][:, 2].mean(), (v[ft][:, [0, 2]] - v[ft][:, [0, 2]].mean(0)) @ d_) < 0: d_ = -d_
        ang = np.arctan2(d_[0], d_[1]) * float(SP["boots"]["fwd"]); ax_c = v[(v[:, 1] > top_) & (v[:, 1] < top_ + 0.08)][:, [0, 2]].mean(0)
        wr = np.clip((top_ + 0.05 - v[:, 1]) / 0.1, 0, 1); a_ = -ang * wr; c_, s_ = np.cos(a_), np.sin(a_)
        dx_, dz_ = v[:, 0] - ax_c[0], v[:, 2] - ax_c[1]; v[:, 0] = ax_c[0] + c_ * dx_ + s_ * dz_; v[:, 2] = ax_c[1] - s_ * dx_ + c_ * dz_
    if "top" in SP.get("boots", {}):  # RIGCAL: clean boot line at FEET+top (output units), foot x/z scale + forward shift below it
        top = FEET + g("boots", "top"); vc = m.visual.vertex_colors.copy(); low = v[:, 1] < top
        vc[low] = list(BOOT) + [255]; vc[~low] = list(SKIN) + [255]
        if "sock" in SP.get("legs", {}):  # G96: thigh-high sock band from the boot line up to FEET + legs.sock (output units)
            vc[(~low) & (v[:, 1] < FEET + g("legs", "sock"))] = list(SOCK) + [255]
        m.visual.vertex_colors = vc
        w = np.clip((top + float(SP["boots"].get("ramp", 0.04)) - v[:, 1]) / 0.08, 0, 1); bc = v[low].mean(0)  # H2 boots.ramp: flare start vs the boot line (lower = straighter shaft top)
        if g("boots", "centre", 0.0):  # RIGCAL: centre the boot (sole) under the leg axis
            ax0 = v[(v[:, 1] > top + 0.02) & (v[:, 1] < top + 0.12), 0]; sole_ = v[:, 1] < FEET + 0.06
            if len(ax0) and sole_.any(): v[:, 0] += w * g("boots", "centre") * ((ax0.max() + ax0.min()) / 2 - (v[sole_, 0].max() + v[sole_, 0].min()) / 2)
            bc = v[low].mean(0)
        v[:, 0] = v[:, 0] + w * (v[:, 0] - bc[0]) * (g("boots", "sx") - 1)
        if g("boots", "toe", 0.0):  # RIGCAL: box toe: widen the front of the foot (x) toward the toe tip
            zf = v[low, 2].max(); tt = np.clip((v[:, 2] - bc[2]) / max(zf - bc[2], 1e-3), 0, 1)
            v[:, 0] = v[:, 0] + w * (v[:, 0] - bc[0]) * g("boots", "toe") * tt
        v[:, 2] = v[:, 2] + w * ((v[:, 2] - bc[2]) * (g("boots", "sz") - 1) + g("boots", "dz", 0.0))
    m.vertices = v; p2 = p.copy(); p2[0] = ax_x; p2[1] = float(leg_y(p[1])); out_piv[n] = p2
# ---------------- skirt + torso
for n, sec in (("skirt", "skirt"), ("torso", "torso")):
    m = M[n]; v = m.vertices.copy(); p = P[n].copy(); cx, cz = 0.0, v[:, 2].mean()
    v[:, 0] = cx + (v[:, 0] - cx) * g(sec, "width"); v[:, 2] = cz + (v[:, 2] - cz) * g(sec, "depth")
    if n == "torso" and g("torso", "waist") != 1:  # waist taper: extra x(+z/2) scale at the bottom of the torso fading to 1 at the chest
        y0, y1 = v[:, 1].min(), v[:, 1].max(); tw = np.clip(1 - (v[:, 1] - y0) / (0.6 * (y1 - y0)), 0, 1)
        f_ = 1 + (g("torso", "waist") - 1) * tw; v[:, 0] = cx + (v[:, 0] - cx) * f_; v[:, 2] = cz + (v[:, 2] - cz) * (1 + (f_ - 1) * g("torso", "waist_zk", 0.5))
    if n == "skirt" and g("skirt", "flare") != 1:  # RIGCAL: A-line flare, x/z scale ramping from 1 at the waistband to 'flare' at the hem
        y0, y1 = v[:, 1].min(), v[:, 1].max(); tf = np.clip((y1 - v[:, 1]) / (y1 - y0), 0, 1); f_ = 1 + (g("skirt", "flare") - 1) * tf
        fzk = 1 + (g("skirt", "flarez", g("skirt", "flare")) - 1) * tf  # G96: separate depth flare
        v[:, 0] = cx + (v[:, 0] - cx) * f_; v[:, 2] = cz + (v[:, 2] - cz) * fzk
    if n == "skirt" and g("torso", "waist") != 1:  # skirt waistband follows the waist, hem keeps its width
        y0, y1 = v[:, 1].min(), v[:, 1].max(); tw = np.clip((v[:, 1] - y0) / (y1 - y0), 0, 1) ** 2
        f_ = 1 + (g("torso", "waist") - 1) * tw; v[:, 0] = cx + (v[:, 0] - cx) * f_; v[:, 2] = cz + (v[:, 2] - cz) * (1 + (f_ - 1) / 2)
    if n == "torso" and g("torso", "sh") != 1:  # RIGCAL: square shoulders: extra x scale ramping in over the top 35% of the torso
        y0, y1 = v[:, 1].min(), v[:, 1].max(); ws = np.clip((v[:, 1] - (y1 - 0.35 * (y1 - y0))) / (0.2 * (y1 - y0)), 0, 1)
        v[:, 0] = cx + (v[:, 0] - cx) * (1 + (g("torso", "sh") - 1) * ws)
    if n == "torso" and g("torso", "sq", 0.0):  # RIGCAL: square the shoulder slope: lift the top-outer torso toward the top plane
        y0, y1 = v[:, 1].min(), v[:, 1].max(); wt_ = np.clip((v[:, 1] - (y1 - 0.3 * (y1 - y0))) / (0.3 * (y1 - y0)), 0, 1); ax_ = np.abs(v[:, 0]) / np.abs(v[:, 0]).max()
        v[:, 1] = v[:, 1] + g("torso", "sq") * wt_ * np.clip(ax_ * 1.4, 0, 1) * (y1 - 0.02 - v[:, 1]).clip(0)
    if n == "torso": v[:, 1] = tor_lo + (v[:, 1] - tor_lo) * g("torso", "height") + d_leg
    else:  # skirt hangs from its waist pivot
        v[:, 1] = p[1] + (v[:, 1] - p[1]) * g("skirt", "height") + d_leg
    m.vertices = v; p2 = p.copy(); p2[1] += d_leg; out_piv[n] = p2
# ---------------- arms (+ hands)
for s in ("R", "L"):
    n = f"arm_{s}"; m = M[n]; v = m.vertices.copy(); p = P[n].copy()
    far = v[np.argmax(np.linalg.norm(v - p, axis=1))]; ax = (far - p) / np.linalg.norm(far - p)
    rel = v - p; t = rel @ ax; perp = rel - t[:, None] * ax
    h = ismask(m, SKIN); tn = t / max(t.max(), 1e-6)
    fl = g("arms", "flare"); f0 = g("arms", "flare0", 0.35)  # G96: sleeve cone: perp scale ramps 1 -> flare from f0 to the cuff (sleeve verts only)
    fk = np.where(h, 1.0, 1 + (fl - 1) * np.clip((tn - f0) / max(1 - f0, 1e-3), 0, 1) ** 1.5)
    rmp = np.where(h, 0.0, np.clip((tn - f0) / max(1 - f0, 1e-3), 0, 1) ** 1.5)
    fz = 1 + (g("arms", "flarez", fl) - 1) * rmp  # G96: separate flare along world z (depth; side-view sleeve width)
    pz = perp.copy(); pz[:, [0, 1]] = 0; pxy = perp - pz
    v = p + (t * g("arms", "length"))[:, None] * ax + (pxy * fk[:, None] + pz * fz[:, None]) * g("arms", "thickness")
    hs = g("hands", "scale")
    if h.any() and hs != 1: c = v[h].mean(0); v[h] = c + (v[h] - c) * hs
    p2 = p.copy(); p2[0] *= g("torso", "width") * g("arms", "shoulder_x"); p2[1] += up_above_torso(p[1]) + g("arms", "dy", 0.0)  # RIGCAL arms.dy: raise the shoulder joint
    v += p2 - p; m.vertices = v; out_piv[n] = p2
# ---------------- head, bow, bun
hp = P["head"].copy(); hs = g("head", "scale"); off = np.array(SP.get("head", {}).get("offset", [0, 0, 0]), float)
hp2 = hp.copy(); hp2[1] += up_above_torso(hp[1]) + neck; hp2 += off
for n in ("head", "bow", "bun"):
    if n not in M: continue
    m = M[n]; v = m.vertices.copy()
    if n in ("bow", "bun"):  # G96: knot (bun) + bow on the head midline, at the back-top (lead 10-27: centred bow); offsets in input head units
        v[:, 0] -= v[:, 0].mean() if n == "bun" else (v[:, 0].max() + v[:, 0].min()) / 2
        v[:, 1] += float(SP.get(n, {}).get("dy", 0.0)); v[:, 2] += float(SP.get(n, {}).get("dz", 0.0))
        sc_ = float(SP.get(n, {}).get("scale", 1.0))  # H2: bow/bun size about their own centre
        if sc_ != 1.0: c_ = (v.max(0) + v.min(0)) / 2; v = c_ + (v - c_) * sc_
    v = hp2 + (v - hp) * hs
    v[:, 0] = hp2[0] + (v[:, 0] - hp2[0]) * g("head", "wx"); v[:, 2] = hp2[2] + (v[:, 2] - hp2[2]) * g("head", "wz", g("head", "wx"))  # RIGCAL: head width
    if n == "head" and float(SP.get("head", {}).get("sq", 0.0)):  # H2: head squareness = diagonal (3/4 view) bulge in xz; S/N and E widths unchanged
        k_ = float(SP["head"]["sq"]); c_ = (v.max(0) + v.min(0)) / 2; hx_ = (v[:, 0].max() - v[:, 0].min()) / 2; hz_ = (v[:, 2].max() - v[:, 2].min()) / 2
        u_ = (v[:, 0] - c_[0]) / hx_; w_ = (v[:, 2] - c_[2]) / hz_; th_ = np.arctan2(w_, u_); f_ = 1 + k_ * np.sin(2 * th_) ** 2
        v[:, 0] = c_[0] + (v[:, 0] - c_[0]) * f_; v[:, 2] = c_[2] + (v[:, 2] - c_[2]) * f_
    m.vertices = v; out_piv[n] = hp2.copy()
if float(SP.get("neck", {}).get("r", 0)) > 0:  # RIGCAL: visible neck = skin cylinder on the torso from inside the chest up into the head
    tv_ = M["torso"].vertices; ttop = tv_[:, 1].max(); sk_ = ismask(M["torso"], SKIN); zc = float(tv_[sk_, 2].mean()) if sk_.any() else 0.0
    y0, y1 = ttop - 0.08, hp2[1] + 0.12; r_ = float(SP["neck"]["r"])
    cyl = trimesh.creation.cylinder(radius=r_, height=y1 - y0, sections=24); cyl.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))
    cyl.apply_translation([0, (y0 + y1) / 2, zc + float(SP["neck"].get("dz", 0.0))])
    cyl.visual = trimesh.visual.ColorVisuals(cyl, vertex_colors=np.tile(np.array(list(SKIN) + [255], np.uint8), (len(cyl.vertices), 1)))
    tm_ = M["torso"]; vc_ = tm_.visual.vertex_colors
    M["torso"] = trimesh.util.concatenate([tm_, cyl])
HAIR = (12, 8, 9)
if float(SP.get("head", {}).get("fringe", 0)) > 0 and "head" in M:  # RIGCAL: lift the fringe (hairline) by head.fringe (input head units) -> more face, eyes can rise
    m = M["head"]; V = m.vertices; vc = m.visual.vertex_colors.copy(); sk_ = ismask(m, SKIN) | ismask(m, EYE); hl = V[sk_, 1].max()
    band = sk_ & (V[:, 1] > hl - 0.06); x0_, x1_ = V[band, 0].min(), V[band, 0].max(); f_ = float(SP["head"]["fringe"]) * hs
    sel = ismask(m, HAIR) & (V[:, 1] >= hl - 0.01) & (V[:, 1] < hl + f_) & (V[:, 0] > x0_ + 0.01) & (V[:, 0] < x1_ - 0.01) & (m.vertex_normals[:, 2] > 0.35)
    vc[sel] = list(SKIN) + [255]; m.visual.vertex_colors = vc
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
    p = P[f"leg_{s}"]; q = q.copy(); q[0] = out_piv[f"leg_{s}"][0] + (q[0] - p[0]) * g("legs", "thickness"); q[1] = float(leg_y(q[1])); return q
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
