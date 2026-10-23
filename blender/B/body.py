"""Body, tights, boots, coat, belt, buttons, scarf, mittens."""
import bpy, math
import numpy as np
from common import *

K = 40
# torso rings: z, half-width, front depth, back depth, bust bump
TORSO = np.array([
    [1.262, 0.030, 0.027, 0.030, 0.0],
    [1.246, 0.046, 0.032, 0.036, 0.0],
    [1.228, 0.068, 0.040, 0.045, 0.0],
    [1.210, 0.098, 0.049, 0.052, 0.0],
    [1.190, 0.120, 0.055, 0.056, 0.0],
    [1.160, 0.128, 0.061, 0.057, 0.002],
    [1.125, 0.122, 0.068, 0.057, 0.012],
    [1.095, 0.118, 0.070, 0.056, 0.018],
    [1.065, 0.110, 0.066, 0.055, 0.012],
    [1.035, 0.100, 0.062, 0.055, 0.002],
    [1.005, 0.092, 0.059, 0.055, 0.0],
    [0.978, 0.088, 0.058, 0.057, 0.0],
    [0.945, 0.098, 0.060, 0.063, 0.0],
    [0.905, 0.116, 0.063, 0.072, 0.0],
    [0.865, 0.130, 0.065, 0.080, 0.0],
    [0.830, 0.133, 0.065, 0.082, 0.0],
    [0.795, 0.126, 0.061, 0.076, 0.0],
    [0.770, 0.104, 0.052, 0.062, 0.0],
    [0.752, 0.060, 0.034, 0.036, 0.0]])
CY = 0.006
TORSO[:, 1] *= np.where(TORSO[:, 0] < 1.235, 0.93, 1.0)
TORSO[:, 2:4] *= np.where(TORSO[:, 0] < 1.235, 0.96, 1.0)[:, None]

def torso_ring(hw, df, db, bust, z, cy=CY, n=2.3, K=K, mod=None):
    a = np.linspace(0, 2 * np.pi, K, endpoint=False)
    s, c = np.sin(a), np.cos(a)
    x = hw * np.sign(s) * np.abs(s) ** (2 / n)
    d = np.where(c > 0, df, db)
    y = cy - d * np.sign(c) * np.abs(c) ** (2 / n)
    if bust:
        y = y - bust * np.exp(-((np.abs(x) - 0.052) / 0.034) ** 2) * (c > 0)
    if mod is not None:
        r = mod(a)
        x = x * (1 + r); y = cy + (y - cy) * (1 + r)
    return np.stack([x, y, np.full(K, z)], 1)

def interp_row(table, z):
    o = np.argsort(table[:, 0])
    return np.array([np.interp(z, table[o, 0], table[o, k]) for k in range(table.shape[1])])

# ------------------------------------------------------------------ arm skeleton
S_L = np.array([0.116, 0.004, 1.186])
D1 = norm(np.array([0.41, 0.0, -0.91]))
E_L = S_L + 0.245 * D1
D2 = norm(np.array([0.33, -0.10, -0.94]))
W_L = E_L + 0.212 * D2
D3 = norm(D2 + np.array([0.05, 0.0, 0.0]))

def mirror(P):
    P = np.array(P, float).copy(); P[..., 0] *= -1; return P

def arm_path(ext=0.0):
    pts = [S_L - 0.035 * D1, S_L, S_L + 0.12 * D1, E_L, E_L + 0.10 * D2, W_L + ext * D2]
    return catmull(pts, 26)

def build_body(mats, coll):
    parts = []
    rings = [torso_ring(r[1], r[2], r[3], r[4], r[0], K=28) for r in TORSO]
    parts.append(loft(rings, True, cap0=True, cap1=True) + (0,))
    # neck
    nr = [ring((0, 0.014, z), (1, 0, 0), (0, 1, 0), 0.0255, 0.0260, 24) for z in np.linspace(1.24, 1.355, 6)]
    parts.append(loft(nr, True, True, True) + (0,))
    # arms (skin, hidden under sleeves)
    for sx in (1, -1):
        path = arm_path(0.02)
        if sx < 0: path = mirror(path)
        t = np.linspace(0, 1, len(path))
        rr = np.interp(t, [0, 0.15, 0.5, 0.55, 0.8, 1], [0.034, 0.034, 0.026, 0.024, 0.023, 0.019])
        parts.append(tube_along(path, rr, rr * 0.92, 14, up_hint=(0, 1, 0)) + (0,))
    ob = join_parts('Body', [(v, f, m) for v, f, m in parts], [mats['skin']], coll=coll)
    recalc_normals(ob)
    add_mod(ob, 'SUBSURF', levels=1, render_levels=1)
    return ob

# ------------------------------------------------------------------ legs / tights
LEG = np.array([
    # z,    cx,    cy,     rx,    ry
    [0.880, 0.070, 0.004, 0.070, 0.074],
    [0.800, 0.076, 0.004, 0.073, 0.076],
    [0.740, 0.080, 0.002, 0.068, 0.070],
    [0.660, 0.080, 0.000, 0.062, 0.064],
    [0.580, 0.075, 0.000, 0.055, 0.058],
    [0.500, 0.073, 0.002, 0.048, 0.050],
    [0.450, 0.072, 0.002, 0.043, 0.045],
    [0.405, 0.072, 0.004, 0.042, 0.045],
    [0.350, 0.073, 0.008, 0.045, 0.050],
    [0.290, 0.074, 0.010, 0.041, 0.045],
    [0.220, 0.075, 0.012, 0.034, 0.037],
    [0.150, 0.076, 0.013, 0.029, 0.031],
    [0.090, 0.077, 0.014, 0.027, 0.029],
    [0.060, 0.077, 0.014, 0.026, 0.029]])

def leg_at(z):
    r = interp_row(LEG, z)
    k = np.interp(z, [0.06, 0.12, 0.22, 0.35, 0.45, 0.52, 0.62, 0.88], [0.86, 0.86, 0.90, 0.92, 0.80, 0.83, 0.82, 0.84])
    r[3] *= k; r[4] *= k
    return r

def build_tights(mats, coll):
    parts = []
    zs = np.r_[np.linspace(0.88, 0.06, 30)]
    for sx in (1, -1):
        rings = []
        for z in zs:
            r = leg_at(z)
            # inner thigh slightly flatter, calf bulge at back-outside
            def mod(a, z=z):
                calf = 0.16 * np.exp(-((z - 0.35) / 0.06) ** 2) * np.clip(np.cos(a - np.pi * 0.85), 0, 1) ** 2
                return calf
            rg = ring((sx * r[1], r[2], z), (1, 0, 0), (0, -1, 0), r[3], r[4], 24, mod=mod)
            rings.append(rg)
        v, f = loft(rings, True, cap0=True, cap1=True)
        parts.append((v, f, 0))
    ob = join_parts('Tights', parts, [mats['tights']], coll=coll)
    recalc_normals(ob)
    add_mod(ob, 'SUBSURF', levels=1, render_levels=2)
    return ob

# ------------------------------------------------------------------ boots
FOOT = np.array([
    # y,      hw,    top
    [0.064, 0.020, 0.060],
    [0.058, 0.032, 0.085],
    [0.045, 0.040, 0.105],
    [0.020, 0.043, 0.112],
    [-0.010, 0.044, 0.100],
    [-0.045, 0.045, 0.080],
    [-0.080, 0.045, 0.064],
    [-0.110, 0.043, 0.057],
    [-0.135, 0.037, 0.052],
    [-0.152, 0.026, 0.045],
    [-0.160, 0.010, 0.036]])
SHAFT = np.array([
    [0.300, 0.0500, 0.0540],
    [0.265, 0.0460, 0.0500],
    [0.220, 0.0410, 0.0450],
    [0.175, 0.0355, 0.0395],
    [0.135, 0.0330, 0.0385],
    [0.105, 0.0350, 0.0430],
    [0.085, 0.0390, 0.0480]])

def build_boots(mats, coll):
    parts = []
    for sx in (1, -1):
        cx = 0.077 * sx
        # shaft
        rings = []
        for z in np.linspace(0.300, 0.075, 12):
            r = interp_row(SHAFT, z)
            rings.append(ring((cx, 0.014, z), (1, 0, 0), (0, -1, 0), r[1], r[2], 28))
        v, f = loft(rings, True, cap0=True, cap1=True)
        parts.append((v, f, 0))
        # foot: loft along -Y, superelliptic sections in XZ
        rings = []
        ys = np.linspace(FOOT[0, 0], FOOT[-1, 0], 18)
        for y in ys:
            r = interp_row(FOOT[::-1], y)
            hw, top = r[1], r[2]
            h = (top - 0.010) / 2
            toe_out = sx * 0.006 * np.clip((0.02 - y) / 0.17, 0, 1)
            a = np.linspace(0, 2 * np.pi, 28, endpoint=False)
            ca, sa = np.cos(a), np.sin(a)
            n = 2.6
            xx = cx + toe_out + hw * np.sign(ca) * np.abs(ca) ** (2 / n)
            zz = 0.010 + h + h * np.sign(sa) * np.abs(sa) ** (2 / n)
            rings.append(np.stack([xx, np.full(28, y), zz], 1))
        v, f = loft(rings, True, cap0=True, cap1=True)
        V = np.array(v)
        parts.append((v, f, 0))
        # 10 mm sole slab following the foot outline (slightly proud), crisp via support rings
        ys2 = np.linspace(FOOT[0, 0] + 0.004, FOOT[-1, 0] - 0.004, 18)
        hw2 = np.array([interp_row(FOOT[::-1], y)[1] for y in ys2]) + 0.0035
        to2 = sx * 0.006 * np.clip((0.02 - ys2) / 0.17, 0, 1)
        outline = np.concatenate([np.stack([cx + to2 + hw2, ys2], 1), np.stack([cx + to2 - hw2, ys2], 1)[::-1]])
        cen = outline.mean(0)
        srings = []
        for z, ins in ((0.0, 0.0012), (0.0015, 0.0), (0.0095, 0.0), (0.0112, 0.0012)):
            o2 = cen + (outline - cen) * (1 - ins / 0.04)
            srings.append(np.stack([o2[:, 0], o2[:, 1], np.full(len(o2), z)], 1))
        v, f = loft(srings, True, cap0=True, cap1=True)
        parts.append((v, f, 2))
        # fur cuff: lumpy torus
        nu, nv = 40, 10
        U = np.linspace(0, 2 * np.pi, nu, endpoint=False)
        Vv = np.linspace(0, 2 * np.pi, nv, endpoint=False)
        pts = []
        for u in U:
            for w in Vv:
                lump = 1 + 0.20 * np.sin(7 * u + 1.7 * sx) * np.cos(3 * w) + 0.12 * np.sin(13 * u + 2 * w + sx) + 0.06 * np.sin(23 * u)
                rr = 0.0240 * lump; rz = 0.0265 * lump
                R = np.array([0.0545 * np.sin(u), -0.0585 * np.cos(u)])
                rad = norm(np.array([np.sin(u) / 0.0545, -np.cos(u) / 0.0585]))
                p = np.array([cx + R[0] + rad[0] * rr * np.cos(w), 0.014 + R[1] + rad[1] * rr * np.cos(w), 0.306 + rz * np.sin(w)])
                pts.append(p)
        Ff = torus_faces(nu, nv)
        parts.append((pts, Ff, 1))
    ob = join_parts('Boots', parts, [mats['boots'], mats['fur'], mats['sole']], coll=coll)
    recalc_normals(ob)
    add_mod(ob, 'SUBSURF', levels=1, render_levels=2)
    return ob

# ------------------------------------------------------------------ coat
SKIRT = np.array([
    # z,     hw,    df,    db
    [0.978, 0.099, 0.069, 0.068],
    [0.950, 0.112, 0.074, 0.078],
    [0.915, 0.132, 0.083, 0.092],
    [0.875, 0.152, 0.095, 0.106],
    [0.835, 0.168, 0.110, 0.120],
    [0.790, 0.184, 0.128, 0.136],
    [0.740, 0.199, 0.145, 0.153],
    [0.690, 0.206, 0.156, 0.164],
    [0.645, 0.214, 0.166, 0.174],
    [0.615, 0.218, 0.170, 0.178],
    [0.598, 0.219, 0.171, 0.179]])
SKIRT[:, 1] *= np.interp(SKIRT[:, 0], [0.6, 0.98], [0.86, 0.93])
SKIRT[:, 2:4] *= np.interp(SKIRT[:, 0], [0.6, 0.98], [0.88, 0.95])[:, None]
COAT_OFF = 0.0105
HEM_Z = 0.632

def coat_rows():
    rows = []
    for r in TORSO:
        if r[0] > 1.250 or r[0] < 0.99:
            continue
        rows.append((r[0], r[1] + COAT_OFF, r[2] + COAT_OFF, r[3] + COAT_OFF, r[4] * 0.85))
    rows.insert(0, (1.257, 0.050, 0.038, 0.042, 0.0))
    for r in SKIRT:
        rows.append((r[0], r[1], r[2], r[3], 0.0))
    return rows

def fold_mod(z):
    A = 0.075 * np.clip((0.955 - z) / 0.36, 0, 1) ** 1.4
    def m(a):
        s = np.cos(9 * a + 0.35)
        return A * 0.30 * np.sign(s) * np.abs(s) ** 0.8
    return m

def coat_ring(z, row):
    return torso_ring(row[1], row[2], row[3], row[4], z, mod=fold_mod(z) if z < 0.96 else None, K=54)

def coat_front_y(x, z):
    rows = coat_rows()
    zs = np.array([r[0] for r in rows])
    tab = np.array(rows)
    row = interp_row(tab, z)
    rg = torso_ring(row[1], row[2], row[3], row[4], z, K=256)
    front = rg[rg[:, 1] < CY]
    o = np.argsort(front[:, 0])
    return float(np.interp(x, front[o, 0], front[o, 1]))

def build_coat(mats, coll):
    rows = coat_rows()
    rings = [coat_ring(r[0], r) for r in rows]
    # extra subdivision rows in skirt for smooth folds
    v, f = loft(rings, True, cap0=False, cap1=False)
    V = np.array(v)
    mi = [1 if V[list(fc)][:, 2].mean() < HEM_Z else 0 for fc in f]
    parts = [(v, f, mi)]
    # sleeves
    for sx in (1, -1):
        path = arm_path(0.0)
        if sx < 0: path = mirror(path)
        t = np.linspace(0, 1, len(path))
        rr = np.interp(t, [0, 0.1, 0.2, 0.5, 0.75, 0.86, 0.87, 1.0], [0.040, 0.044, 0.040, 0.035, 0.034, 0.036, 0.042, 0.044])
        v, f = tube_along(path, rr, rr * 0.94, 28, up_hint=(0, 1, 0), cap0=True, cap1=False)
        V = np.array(v)
        # cuff faces = last 13% of path
        cut = len(path) * 28 * 0
        tz = []
        for fc in f:
            idx = max(fc) // 28
            tz.append(1 if idx >= int(0.87 * len(path)) else 0)
        parts.append((v, f, tz))
    # little round collar
    cr = []
    for z, rx, ry in ((1.262, 0.036, 0.034), (1.252, 0.054, 0.050), (1.236, 0.070, 0.066)):
        cr.append(ring((0, 0.010, z), (1, 0, 0), (0, -1, 0), rx, ry, 40))
    v, f = loft(cr, True)
    parts.append((v, f, 0))
    ob = join_parts('Coat', parts, [mats['coat'], mats['rust']], coll=coll)
    recalc_normals(ob)
    add_mod(ob, 'SOLIDIFY', thickness=0.005, offset=-1.0)
    add_mod(ob, 'SUBSURF', levels=1, render_levels=2)
    return ob

def build_belt_buttons(mats, coll):
    parts = []
    z0, z1 = 0.986, 0.968
    row = interp_row(np.array(coat_rows()), 0.977)
    rings = []
    for z, off in ((z0, 0.002), (z0 - 0.002, 0.004), (z1 + 0.002, 0.004), (z1, 0.002), (z1, -0.001), (z0, -0.001)):
        rings.append(torso_ring(row[1] + off, row[2] + off, row[3] + off, 0, z, K=48))
    v, f = loft_cyclic(rings)
    parts.append((v, f, 0))
    # buckle: rounded-rect frame
    yb = coat_front_y(0.0, 0.977) - 0.005
    def rr_ring(w, h, y, n=32, p=4.0):
        a = np.linspace(0, 2 * np.pi, n, endpoint=False)
        ca, sa = np.cos(a), np.sin(a)
        return np.stack([w * np.sign(ca) * np.abs(ca) ** (2 / p), np.full(n, y), 0.977 + h * np.sign(sa) * np.abs(sa) ** (2 / p)], 1)
    fr = [rr_ring(0.0135, 0.0105, yb + 0.002), rr_ring(0.0135, 0.0105, yb - 0.001), rr_ring(0.0085, 0.0062, yb - 0.001), rr_ring(0.0085, 0.0062, yb + 0.002)]
    v, f = loft_cyclic(fr)
    parts.append((v, f, 1))
    # 6 buttons (2 x 3)
    for z in (1.128, 1.072, 1.018):
        for x in (-0.030, 0.030):
            y = coat_front_y(x, z)
            if x > 0: y = coat_front_y(x, z)
            dome = []
            for k, (rr, dy) in enumerate(((0.0062, 0.0005), (0.0060, -0.0012), (0.0048, -0.0026), (0.0025, -0.0032))):
                dome.append(ring((x, y + dy, z), (1, 0, 0), (0, 0, 1), rr, rr, 16))
            v, f = loft(dome, True, cap0=True, cap1=True)
            parts.append((v, f, 1))
    ob = join_parts('Belt', parts, [mats['belt'], mats['gold']], coll=coll)
    recalc_normals(ob)
    add_mod(ob, 'SUBSURF', levels=1, render_levels=2)
    return ob

# ------------------------------------------------------------------ scarf
def build_scarf(mats, coll):
    """Chunky roll (drape ported from modeller A: front dips, twisted cable ribs) + left tail with fringe."""
    parts = []
    C = np.array([0.0, 0.010, 1.266])
    NP, NS = 64, 14
    pts = []
    for i in range(NP):
        a = 2 * np.pi * i / NP
        d = np.array([np.sin(a), -np.cos(a), 0.0])
        R = 0.071 + 0.006 * np.cos(a)
        P = C + d * R + np.array([0, 0, -0.012 * max(0.0, np.cos(a)) + 0.004 * max(0.0, -np.cos(a))])
        Tn = np.array([np.cos(a), np.sin(a), 0.0]); Bv = np.cross(Tn, d)
        for k in range(NS):
            bb = 2 * np.pi * k / NS
            ph = bb + a * 7
            r = 0.034 * (1 + 0.09 * np.cos(4 * ph))
            pts.append(P + d * (r * 1.05 * np.cos(bb)) + Bv * (r * 0.92 * np.sin(bb)))
    parts.append((pts, torus_faces(NP, NS), 0))
    # tail on HER LEFT (+X): follows the coat front, ribbed front face, flat back
    zs = np.linspace(1.215, 0.94, 7)
    ctrl = [[0.050, -0.074, 1.252]]
    for z in zs:
        x = 0.068 + 0.012 * np.clip((1.215 - z) / 0.1, 0, 1)
        ctrl.append([x, coat_front_y(x, z) - 0.016, z])
    path = resample(catmull(ctrl, 60), 22)
    T, Nn, B = frames(path, (0, -1, 0))
    HW, HT, nsx = 0.035, 0.0120, 9
    rings = []
    for i, p in enumerate(path):
        s = i / (len(path) - 1)
        hw = HW * (0.85 + 0.15 * min(1.0, s / 0.25))
        rg = []
        for k in range(nsx):
            u = -1 + 2 * k / (nsx - 1)
            th = HT * (1 + 0.28 * np.cos(3 * np.pi * u))
            rg.append(p + B[i] * (u * hw) + Nn[i] * th)
        for k in range(nsx):
            u = 1 - 2 * k / (nsx - 1)
            rg.append(p + B[i] * (u * hw) - Nn[i] * HT * 0.8)
        rings.append(np.array(rg))
    v, f = loft(rings, True, True, True)
    parts.append((v, f, 0))
    end = path[-1]; Tn = T[-1]
    for k in range(7):
        u = -0.84 + 1.68 * k / 6
        base = end + B[-1] * (u * HW) + Tn * -0.004
        fp = np.array([base + Tn * (0.012 * j) + B[-1] * (0.0015 * np.sin(j + k)) for j in range(4)])
        fp = catmull(fp, 6)
        rr = np.linspace(0.0050, 0.0020, 6)
        v, f = tube_along(fp, rr, rr * 0.8, 8, up_hint=(0, -1, 0))
        parts.append((v, f, 0))
    ob = join_parts('Scarf', parts, [mats['knit']], coll=coll)
    recalc_normals(ob)
    add_mod(ob, 'SUBSURF', levels=1, render_levels=1)
    return ob

# ------------------------------------------------------------------ mittens
def build_mittens(mats, coll):
    parts = []
    for sx in (1, -1):
        W = W_L.copy(); d = D3.copy()
        if sx < 0:
            W = mirror(W); d = mirror(d)
        u = norm(np.cross(d, np.array([sx * 1.0, 0, 0])))   # front/back width axis
        if u[1] > 0: u = -u
        v = norm(np.cross(u, d))
        prof = [(0.000, 0.0215, 0.0180), (0.015, 0.0235, 0.0185), (0.035, 0.0300, 0.0190), (0.060, 0.0335, 0.0205),
                (0.085, 0.0330, 0.0200), (0.103, 0.0290, 0.0180), (0.116, 0.0215, 0.0145), (0.124, 0.0110, 0.0085), (0.127, 0.003, 0.003)]
        rings = [ring(W + d * (t + 0.004), u, v, a, b, 24) for t, a, b in prof]
        vv, ff = loft(rings, True, cap0=True, cap1=True)
        parts.append((vv, ff, 0))
        # thumb
        base = W + d * 0.040 + u * 0.020 + v * 0.004 * sx
        tdir = norm(d * 0.55 + u * 0.75)
        tp = catmull([base - tdir * 0.01, base + tdir * 0.020, base + tdir * 0.038 + d * 0.006], 8)
        tr = np.interp(np.linspace(0, 1, 8), [0, 0.6, 0.85, 1], [0.0125, 0.0115, 0.009, 0.002])
        vv, ff = tube_along(tp, tr, tr * 0.9, 16, up_hint=v)
        parts.append((vv, ff, 0))
        # ribbed cuff
        rings = []
        for t, a, b in ((-0.006, 0.0260, 0.0225), (0.002, 0.0270, 0.0235), (0.016, 0.0262, 0.0228), (0.022, 0.0250, 0.0215), (0.022, 0.0215, 0.0185), (-0.006, 0.0225, 0.0190)):
            rings.append(ring(W + d * t, u, v, a, b, 32, mod=lambda ang: 0.04 * np.cos(16 * ang)))
        vv, ff = loft_cyclic(rings)
        parts.append((vv, ff, 1))
    ob = join_parts('Mittens', parts, [mats['knit'], mats['teal_dark']], coll=coll)
    recalc_normals(ob)
    add_mod(ob, 'SUBSURF', levels=1, render_levels=2)
    return ob
