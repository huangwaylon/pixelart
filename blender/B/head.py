"""Head: SDF-designed form, projected onto a quad lat-long cage with feature-aligned loops."""
import bpy, bmesh, math
import numpy as np
from common import *

O = np.array([0.0, 0.004, 1.425])   # projection centre

EYE = dict(x_in=0.0185, z_in=1.3995, x_out=0.0635, z_out=1.4105, up=0.0265, lo=0.0150,
           iris_c=0.505, iris_rx=0.262, iris_ry=0.37)
SOCKET = False
P = dict(nose_z=1.367, mouth_z=1.3395, chin_z=1.303)

# lofted-section profiles: z -> (half width, front y, back y)
PROF = np.array([
    # z      a       yf       yb
    [1.5745, 0.000,  0.008,   0.008],
    [1.568,  0.034, -0.026,   0.044],
    [1.556,  0.054, -0.050,   0.070],
    [1.535,  0.071, -0.069,   0.090],
    [1.510,  0.081, -0.082,   0.104],
    [1.485,  0.086, -0.0885,  0.112],
    [1.460,  0.0875,-0.0900,  0.1145],
    [1.435,  0.0860,-0.0885,  0.1120],
    [1.415,  0.0815,-0.0855,  0.1060],
    [1.395,  0.0770,-0.0830,  0.0960],
    [1.375,  0.0715,-0.0815,  0.0820],
    [1.358,  0.0640,-0.0795,  0.0620],
    [1.344,  0.0545,-0.0765,  0.0380],
    [1.331,  0.0430,-0.0728,  0.0120],
    [1.319,  0.0305,-0.0690, -0.0180],
    [1.309,  0.0180,-0.0650, -0.0400],
    [1.3025, 0.0075,-0.0605, -0.0530],
    [1.2995, 0.000, -0.0575, -0.0575]])

def _dense_profile():
    pts = catmull(PROF, 400)
    o = np.argsort(pts[:, 0])
    return pts[o]
_DP = None

def _base(p):
    global _DP
    if _DP is None:
        _DP = _dense_profile()
    z = p[..., 2]
    a = np.interp(z, _DP[:, 0], _DP[:, 1]); yf = np.interp(z, _DP[:, 0], _DP[:, 2]); yb = np.interp(z, _DP[:, 0], _DP[:, 3])
    a = np.maximum(a, 1e-4)
    y0 = 0.5 * (yf + yb) - 0.0 
    # widest point sits a bit forward of centre in the face zone (cheeks)
    y0 = y0 - 0.010 * np.clip((1.43 - z) / 0.06, 0, 1) * np.clip((z - 1.31) / 0.03, 0, 1)
    bf = np.maximum(y0 - yf, 1e-4); bb = np.maximum(yb - y0, 1e-4)
    dy = p[..., 1] - y0
    b = np.where(dy < 0, bf, bb)
    nexp = np.where(dy < 0, 2.0 + 0.5 * np.clip((1.45 - z) / 0.06, 0, 1), 2.0)
    q = (np.abs(p[..., 0]) / a) ** nexp + (np.abs(dy) / b) ** nexp
    f = (q ** (1.0 / nexp) - 1.0) * np.minimum(a, b)
    f = np.where((z > 1.5745) | (z < 1.2995), np.maximum(f, 0.01), f)
    d = f
    for sx in (-1, 1):
        ear = sd_ellipsoid(p, (sx * 0.080, 0.018, 1.400), (0.011, 0.018, 0.026))
        d = smin(d, ear, 0.006)
    neck = sd_capsule(p, (0, 0.018, 1.26), (0, 0.010, 1.39), 0.0272)
    d = smin(d, neck, 0.016)
    d = np.maximum(d, 1.272 - p[..., 2])
    return d

def front_y(f, x, z):
    x = np.atleast_1d(np.asarray(x, float)); z = np.atleast_1d(np.asarray(z, float))
    Oa = np.stack([x, np.full_like(x, -0.25), z], 1)
    D = np.tile([0, 1.0, 0], (len(x), 1))
    return -0.25 + ray_enter(f, Oa, D, tmax=0.3, steps=300)

_feat = {}
def _setup_features():
    yb = lambda x, z: float(front_y(_base, x, z)[0])
    _feat['nose'] = yb(0, P['nose_z'])
    _feat['bridge'] = yb(0, 1.398)
    _feat['ul'] = yb(0, 1.3445)
    _feat['ll'] = yb(0, 1.3335)
    _feat['eye'] = yb(0.041, 1.407)
    _feat['chin'] = yb(0, 1.312)

def head_f(p):
    if not _feat:
        _setup_features()
    d = _base(p)
    # nose: soft bridge + tiny tip
    nb = sd_capsule(p, (0, _feat['bridge'] + 0.0032, 1.398), (0, _feat['nose'] + 0.0025, 1.371), 0.0030)
    nt = sd_ellipsoid(p, (0, _feat['nose'] + 0.0042, P['nose_z']), (0.0050, 0.0068, 0.0055))
    d = smin(d, smin(nb, nt, 0.006), 0.007)
    # lips (small + full)
    ul = sd_ellipsoid(p, (0, _feat['ul'] + 0.0030, 1.3448), (0.0110, 0.0055, 0.0040))
    ll = sd_ellipsoid(p, (0, _feat['ll'] + 0.0032, 1.3338), (0.0095, 0.0058, 0.0046))
    d = smin(d, smin(ul, ll, 0.002), 0.004)
    # chin point

    # shallow almond eye sockets
    for sx in (-1, 1):
        so = sd_ellipsoid(p, (sx * 0.0412, _feat['eye'] + 0.0058, 1.4075), (0.0245, 0.0068, 0.0185))
        d = smax(d, -so, 0.004) if SOCKET else d
    return d

def _density_samples(n, lo, hi, centers, amp, width, wrap=False):
    xs = np.linspace(lo, hi, 4000)
    rho = np.ones_like(xs)
    for c, a, w in zip(centers, amp, width):
        dd = xs - c
        if wrap:
            dd = (dd + 180) % 360 - 180
        rho += a * np.exp(-(dd / w) ** 2)
    cdf = np.r_[0, np.cumsum((rho[1:] + rho[:-1]) * 0.5 * np.diff(xs))]
    cdf /= cdf[-1]
    t = np.linspace(0, 1, n + (0 if wrap else 1), endpoint=not wrap)
    return np.interp(t, cdf, xs)

def lid_curves(sx=1):
    e = EYE
    def up(s):
        base = e['z_in'] + (e['z_out'] - e['z_in']) * s
        return base + e['up'] * np.sin(np.pi * np.clip(s, 0, 1)) ** 0.75 * (1.0 + 0.10 * (0.5 - s))
    def lo(s):
        base = e['z_in'] + (e['z_out'] - e['z_in']) * s
        ss = np.clip(s, 0, 1) ** 0.85
        return base - e['lo'] * np.sin(np.pi * ss) ** 1.15
    def X(s):
        return sx * (e['x_in'] + (e['x_out'] - e['x_in']) * s)
    return X, up, lo

def build_head(mats, coll, nrow=42, ncol=54):
    skin, lip = mats['skin'], mats['lip']
    phis = _density_samples(nrow, 0.0, 180.0, [100, 132], [1.6, 1.0], [26, 12])
    thetas = _density_samples(ncol, -180.0, 180.0, [0.0], [1.4], [55.0], wrap=True)
    ph = np.radians(phis[1:-1]); th = np.radians(thetas)
    PH, TH = np.meshgrid(ph, th, indexing='ij')
    D = np.stack([np.sin(PH) * np.sin(TH), -np.sin(PH) * np.cos(TH), np.cos(PH)], -1).reshape(-1, 3)
    r = ray_exit(head_f, O, D, tmax=0.25, steps=260)
    V = list(O + D * r[:, None])
    nr, nc = len(ph), len(th)
    F = grid_faces(nr, nc, closed=True)
    top = len(V); V.append(O + np.array([0, 0, 1]) * ray_exit(head_f, O, np.array([[0, 0, 1.0]]))[0])
    bot = len(V); V.append(O + np.array([0, 0, -1]) * ray_exit(head_f, O, np.array([[0, 0, -1.0]]))[0])
    F += [(top, j, (j + 1) % nc) for j in range(nc)]
    o = (nr - 1) * nc
    F += [(bot, o + (j + 1) % nc, o + j) for j in range(nc)]
    V = np.array(V)
    # lip material on lower lip
    MI = []
    for f in F:
        c = V[list(f)].mean(0)
        inlip = ((c[0] / 0.0105) ** 2 + ((c[2] - 1.3335) / 0.0042) ** 2) < 1 and c[1] < -0.05
        MI.append(0)
    ob = mesh_obj('Head', V, F, mats=[skin, lip], mat_idx=MI, coll=coll)
    recalc_normals(ob)
    add_mod(ob, 'SUBSURF', levels=1, render_levels=2)
    return ob

# ---------------------------------------------------------------- eye texture
def eye_image(name, sx):
    Wd = 256
    X, up, lo = lid_curves(sx)
    xs = np.array([X(0), X(1)]); xmin, xmax = xs.min(), xs.max()
    zmin, zmax = lo(0.55) - 0.002, up(0.5) + 0.002
    u = (np.arange(Wd) + 0.5) / Wd
    U, Vv = np.meshgrid(u, u)
    xw = xmin + U * (xmax - xmin); zw = zmin + Vv * (zmax - zmin)
    s = (np.abs(xw) - EYE['x_in']) / (EYE['x_out'] - EYE['x_in'])
    upz = up(s)
    col = np.zeros((Wd, Wd, 3))
    white = np.array([1.0, 1.0, 1.0]); shade = np.array([0.80, 0.86, 0.92])
    t_sh = np.clip((zw - (upz - 0.0095)) / 0.0015, 0, 1)
    col[:] = white * (1 - t_sh[..., None]) + shade * t_sh[..., None]
    # iris
    xc = (EYE['x_in'] + 0.5 * (EYE['x_out'] - EYE['x_in'])) * sx
    zc = 1.4075
    rx = 0.0118; rz = 0.0182
    q = np.sqrt(((xw - xc) / rx) ** 2 + ((zw - zc) / rz) ** 2)
    def h2(h):
        h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
    light, mid, dark, deep = h2('#6ACBB6'), h2('#2C9696'), h2('#1C4C54'), h2('#12303A')
    tv = np.clip((zw - (zc - rz)) / (2 * rz), 0, 1)[..., None]
    ic = np.where(tv < 0.45, light * (1 - tv / 0.45) + mid * (tv / 0.45),
                  mid * (1 - (tv - 0.45) / 0.55) + dark * ((tv - 0.45) / 0.55))
    # soft ring of lighter teal low in iris
    ring_l = np.exp(-((q - 0.72) / 0.10) ** 2) * (zw < zc - 0.004)
    ic = ic * (1 - 0.5 * ring_l[..., None]) + light * 0.5 * ring_l[..., None]
    rim = np.clip((q - 0.86) / 0.06, 0, 1)[..., None]
    ic = ic * (1 - rim) + dark * rim
    pq = np.sqrt(((xw - xc) / (rx * 0.42)) ** 2 + ((zw - (zc + 0.0012)) / (rz * 0.46)) ** 2)
    pup = np.clip((1.0 - pq) / 0.08, 0, 1)[..., None]
    ic = ic * (1 - pup) + deep * pup
    a_ir = np.clip((1.0 - q) / 0.04, 0, 1)[..., None]
    # lid shadow over iris
    ic = ic * (1 - 0.35 * t_sh[..., None])
    col = col * (1 - a_ir) + ic * a_ir
    # highlights (same world side for both eyes: upper-left in image = -x)
    for (hx, hz, hrx, hrz) in [(-0.0042, 0.0072, 0.0033, 0.0040), (0.0050, -0.0085, 0.0016, 0.0016),
                                 (0.0055, 0.0040, 0.0011, 0.0011)]:
        hq = np.sqrt(((xw - (xc + hx)) / hrx) ** 2 + ((zw - (zc + hz)) / hrz) ** 2)
        a = np.clip((1 - hq) / 0.12, 0, 1)[..., None]
        col = col * (1 - a) + a
    img = bpy.data.images.new(name, Wd, Wd, alpha=True)
    rgba = np.concatenate([col, np.ones((Wd, Wd, 1))], -1)
    img.pixels.foreach_set(rgba.astype(np.float32).ravel())
    img.pack()
    return img, (xmin, xmax, zmin, zmax)

def build_eyes(mats, coll):
    parts_lash = []
    eye_objs = []
    for sx, tag in ((1, 'L'), (-1, 'R')):   # +X is her left
        X, up, lo = lid_curves(sx)
        img, (xmin, xmax, zmin, zmax) = eye_image('EyeTex_' + tag, sx)
        m = toon_mat('Eye_' + tag, '#FFFFFF', '#FFFFFF', emit_only=True, image=img)
        ns, nt = 18, 10
        V, UV = [], []
        S = np.linspace(0, 1, ns)
        for j in range(nt):
            t = j / (nt - 1)
            for s in S:
                x = X(s); z = lo(s) + (up(s) - lo(s)) * t
                V.append([x, 0, z])
        V = np.array(V)
        V[:, 1] = front_y(head_f, V[:, 0], V[:, 2]) - 0.0007
        UV = np.stack([(V[:, 0] - xmin) / (xmax - xmin), (V[:, 2] - zmin) / (zmax - zmin)], 1)
        F = grid_faces(nt, ns, closed=False)
        if sx < 0:
            F = [tuple(reversed(f)) for f in F]
        ob = mesh_obj('Eye_' + tag, V, F, mats=[m], coll=coll, uvs=UV)
        eye_objs.append(ob)
        # ---- upper lash with outer wing (2D strip in x,z then projected)
        ss = np.r_[np.linspace(-0.03, 1.0, 22), np.linspace(1.04, 1.30, 7)]
        low, upp = [], []
        for s in ss:
            if s <= 1.0:
                x, z = X(s), up(s) - 0.0009
                th = 0.0012 + 0.0034 * np.clip(s / 0.75, 0, 1) ** 1.1
                ds = 0.01; x2, z2 = X(min(s + ds, 1.0)), up(min(s + ds, 1.0))
                x1, z1 = X(max(s - ds, -0.03)), up(max(s - ds, -0.03))
            else:
                k = (s - 1.0) / 0.30
                x = X(1.0) + sx * 0.0120 * k
                z = up(1.0) - 0.0006 + 0.0070 * k ** 1.1
                th = 0.0046 * max(0.0, 1 - k) ** 0.8 + 0.0001
                x1, z1, x2, z2 = X(1.0), up(1.0), X(1.0) + sx * 0.0105, up(1.0) + 0.0062
            tx, tz = x2 - x1, z2 - z1; L = math.hypot(tx, tz)
            nx, nz = -tz / L * sx, tx / L * sx
            if nz < 0:
                nx, nz = -nx, -nz
            low.append([x, 0, z]); upp.append([x + nx * th, 0, z + nz * th])
        LV = np.array(low + upp)
        LV[:, 1] = front_y(head_f, LV[:, 0], LV[:, 2]) - 0.0013
        n = len(ss)
        LF = [(i, i + 1, n + i + 1, n + i) for i in range(n - 1)]
        parts_lash.append((LV, LF, 0))
        # lower lash (outer 55%)
        ss = np.linspace(0.42, 1.0, 12)
        low = np.array([[X(s), 0, lo(s) + 0.0002] for s in ss])
        thk = 0.00045 + 0.0008 * (ss - 0.42) / 0.58
        upp = low.copy(); upp[:, 2] -= thk
        LV = np.vstack([upp, low]); LV[:, 1] = front_y(head_f, LV[:, 0], LV[:, 2]) - 0.0010
        n = len(ss)
        parts_lash.append((LV, [(i, i + 1, n + i + 1, n + i) for i in range(n - 1)], 0))
        # double-lid crease
        ss = np.linspace(0.18, 0.92, 14)
        low = np.array([[X(s), 0, up(s) + 0.0036 + 0.0008 * s] for s in ss])
        thk = 0.00055 * np.clip(np.sin(np.pi * (ss - 0.18) / 0.74), 0, 1) ** 0.5
        upp = low.copy(); upp[:, 2] += thk
        LV = np.vstack([low, upp]); LV[:, 1] = front_y(head_f, LV[:, 0], LV[:, 2]) - 0.0008
        n = len(ss)
        parts_lash.append((LV, [(i, i + 1, n + i + 1, n + i) for i in range(n - 1)], 2))
        # brow
        bs = np.linspace(0, 1, 16)
        bx = sx * (0.021 + 0.046 * bs)
        bz = 1.4475 + 0.0050 * np.sin(np.pi * bs ** 0.8) - 0.004 * bs
        th = 0.0022 * (1 - bs) ** 0.6 + 0.0005
        low = np.stack([bx, 0 * bx, bz - th / 2], 1); upp = np.stack([bx, 0 * bx, bz + th / 2], 1)
        LV = np.vstack([low, upp]); LV[:, 1] = front_y(head_f, LV[:, 0], LV[:, 2]) - 0.0009
        n = len(bs)
        parts_lash.append((LV, [(i, i + 1, n + i + 1, n + i) for i in range(n - 1)], 1))
        # blush
        a = np.linspace(0, 2 * np.pi, 20, endpoint=False)
        bxy = np.stack([sx * 0.047 + 0.0135 * np.cos(a), 0 * a, 1.3725 + 0.0062 * np.sin(a)], 1)
        BV = np.vstack([bxy, [[sx * 0.047, 0, 1.3725]]])
        BV[:, 1] = front_y(head_f, BV[:, 0], BV[:, 2]) - 0.0005
        BF = [(20, (i + 1) % 20, i) if sx > 0 else (20, i, (i + 1) % 20) for i in range(20)]
        parts_lash.append((BV, BF, 3))
    # soft lower-lip tint
    a = np.linspace(0, 2 * np.pi, 20, endpoint=False)
    lv = np.stack([0.0072 * np.cos(a), 0 * a, 1.3335 + 0.0028 * np.sin(a)], 1)
    LV = np.vstack([lv, [[0, 0, 1.3335]]]); LV[:, 1] = front_y(head_f, LV[:, 0], LV[:, 2]) - 0.0005
    parts_lash.append((LV, [(20, (i + 1) % 20, i) for i in range(20)], 3))
    # tiny nose shadow tick (shaded side)
    ns_ = np.linspace(0, 1, 8)
    nx = 0.0030 + 0.0022 * ns_; nz = P['nose_z'] - 0.0035 - 0.0020 * ns_
    th = 0.0009 * np.sin(np.pi * ns_) + 0.0001
    low = np.stack([nx, 0 * nx, nz - th / 2], 1); upp = np.stack([nx, 0 * nx, nz + th / 2], 1)
    LV = np.vstack([low, upp]); LV[:, 1] = front_y(head_f, LV[:, 0], LV[:, 2]) - 0.0006
    parts_lash.append((LV, [(i, i + 1, 8 + i + 1, 8 + i) for i in range(7)], 2))
    # mouth line
    ms = np.linspace(-1, 1, 15)
    mx = 0.0098 * ms; mz = P['mouth_z'] + 0.0017 * ms ** 2 - 0.0003
    th = 0.0010 * (1 - ms ** 2) ** 0.5 + 0.0002
    low = np.stack([mx, 0 * mx, mz - th / 2], 1); upp = np.stack([mx, 0 * mx, mz + th / 2], 1)
    LV = np.vstack([low, upp]); LV[:, 1] = front_y(head_f, LV[:, 0], LV[:, 2]) - 0.0007
    n = len(ms)
    parts_lash.append((LV, [(i, i + 1, n + i + 1, n + i) for i in range(n - 1)], 4))
    face = join_parts('FaceLines', parts_lash, [mats['lash'], mats['brow'], mats['crease'], mats['blush'], mats['mouth']], coll=coll)
    add_mod(face, 'SOLIDIFY', thickness=0.0003, offset=1.0)
    eyes = eye_objs[0]
    # merge eyes into one object named Eyes
    bpy.ops.object.select_all(action='DESELECT')
    for o in eye_objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = eye_objs[0]
    bpy.ops.object.join()
    eye_objs[0].name = 'Eyes'
    add_mod(eye_objs[0], 'SOLIDIFY', thickness=0.0004, offset=1.0)
    return eye_objs[0], face
