"""Hair sheets, ponytail, strands and bow. Sheets are surface-following patches / custom-profile sweeps."""
import bpy, math
import numpy as np
from common import *
import head

_G = {}

def _dirs(ph, th):
    ph = np.radians(ph); th = np.radians(th)
    return np.stack([np.sin(ph) * np.sin(th), -np.sin(ph) * np.cos(th), np.cos(ph)], -1)

def surf_grid():
    if 'r' in _G:
        return
    PH = np.arange(0, 181, 1.0); TH = np.arange(-180, 181, 2.0)
    P, T = np.meshgrid(PH, TH, indexing='ij')
    D = _dirs(P, T).reshape(-1, 3)
    r = ray_exit(head.head_f, head.O, D, tmax=0.25, steps=200, iters=24)
    _G['r'] = r.reshape(P.shape); _G['PH'] = PH; _G['TH'] = TH

def surf(ph, th, off=0.0):
    """point on head surface at polar angle ph (0=top), azimuth th (0=front, +=her left) plus offset along normal."""
    surf_grid()
    ph = np.atleast_1d(np.asarray(ph, float)); th = np.atleast_1d(np.asarray(th, float))
    th = (th + 180) % 360 - 180
    fi = np.clip(ph, 0, 179.999); ti = (th + 180) / 2.0
    i0 = np.floor(fi).astype(int); j0 = np.clip(np.floor(ti).astype(int), 0, 179)
    a = fi - i0; b = ti - j0
    R = _G['r']
    r = (R[i0, j0] * (1 - a) * (1 - b) + R[i0 + 1, j0] * a * (1 - b) + R[i0, j0 + 1] * (1 - a) * b + R[i0 + 1, j0 + 1] * a * b)
    D = _dirs(ph, th)
    P = head.O + D * r[:, None]
    N = grad(head.head_f, P)
    off = np.broadcast_to(np.asarray(off, float), r.shape)
    return P + N * off[:, None], N

def phi_for_z(th, z, off=0.0, lo=20, hi=175):
    ph = np.linspace(lo, hi, 300)
    P, _ = surf(ph, np.full_like(ph, th), off)
    zz = P[:, 2]
    k = np.argmax(zz < z)
    if k == 0:
        return hi
    return ph[k - 1] + (ph[k] - ph[k - 1]) * (zz[k - 1] - z) / (zz[k - 1] - zz[k])

def patch_faces(nv, nu):
    return grid_faces(nv, nu, closed=False)

# ---------------------------------------------------------------- cap
G_PH, G_TH = 68.0, 180.0

def build_cap(mats, coll):
    nph, nth = 18, 48
    TH = np.linspace(-180, 180, nth, endpoint=False)
    rows = []
    gp, _ = surf([G_PH], [G_TH], 0.0)
    axis = norm(gp[0] - head.O)
    ref = norm(np.cross(axis, [1, 0, 0]))
    ref2 = np.cross(axis, ref)
    for i in range(1, nph + 1):
        t = i / nph
        phmax = 64 + 66 * (1 - np.cos(np.radians(TH))) / 2 + 10 * np.sin(np.radians(TH)) ** 2
        ph = phmax * t
        P, N = surf(ph, TH, 0.0)
        # flow grooves converging on the ponytail gather point
        d = P - head.O
        psi = np.arctan2(d @ ref2, d @ ref)
        groove = 0.0011 * np.cos(18 * psi) * np.clip(t * 2, 0, 1)
        off = 0.0085 + groove
        rows.append(P + N * off[:, None])
    top, _ = surf([0.0], [0.0], 0.0085)
    V = [top[0]] + list(np.concatenate(rows))
    F = [(0, 1 + j, 1 + (j + 1) % nth) for j in range(nth)]
    F += [tuple(i + 1 for i in f) for f in grid_faces(nph, nth, True)]
    ob = mesh_obj('Hair_Cap', V, F, mats=[mats['hair']], coll=coll)
    recalc_normals(ob)
    add_mod(ob, 'SOLIDIFY', thickness=0.004, offset=-1.0)
    add_mod(ob, 'SUBSURF', levels=1, render_levels=1)
    return ob

# ---------------------------------------------------------------- generic surface-following sheet
def sheet_patch(th0, th1, ph_root, z_tip_fn, nu, nv, off_fn, taper=None, fall=None, side_lift=0.0):
    """Columns at azimuths th; each column follows the head surface from ph_root down to z_tip
    (or follows surface then 'fall' path). Returns grid (nv, nu, 3)."""
    TH = np.linspace(th0, th1, nu)
    cols = []
    for k, th in enumerate(TH):
        ztip = z_tip_fn(th)
        if fall is None:
            ph_t = phi_for_z(th, ztip, off_fn(1.0, th))
            phs = np.linspace(ph_root(th) if callable(ph_root) else ph_root, ph_t, 60)
            tt = np.linspace(0, 1, 60)
            P, N = surf(phs, np.full(60, th), off_fn(tt, th))
            col = resample(P, nv)
        else:
            col = fall(th, ztip, nv)
        cols.append(col)
    G = np.stack(cols, 1)       # (nv, nu, 3)
    if taper is not None:
        c = G[:, nu // 2:nu // 2 + 1, :] if nu % 2 else 0.5 * (G[:, nu // 2 - 1:nu // 2, :] + G[:, nu // 2:nu // 2 + 1, :])
        tv = np.linspace(0, 1, nv)[:, None, None]
        G = c + (G - c) * taper(tv)
    return G

def patch_obj_parts(G):
    nv, nu = G.shape[:2]
    return list(G.reshape(-1, 3)), patch_faces(nv, nu)

# ---------------------------------------------------------------- bangs
def bang_tip(th):
    a = abs(th)
    base = np.interp(a, [0, 20, 35, 50, 62, 72, 82], [1.4330, 1.4325, 1.4285, 1.4180, 1.4020, 1.3840, 1.3600])
    notch = 0.0
    for c, d, w in ((-30, 0.016, 7.0), (-2, 0.011, 5.5), (25, 0.017, 7.0)):
        notch += d * max(0.0, 1 - abs(th - c) / w) ** 1.3
    return base + notch

def build_bangs(mats, coll):
    parts = []
    def off_back(t, th):
        t = np.asarray(t)
        side = (abs(th) / 80) ** 2
        lift = 0.0065 + (0.0085 * t + 0.0075 * np.sin(np.pi * np.clip(t, 0, 1)) ** 1.2) * (1 - 0.35 * side) + 0.004 * side * t
        return lift
    root = lambda th: 26 + 10 * (abs(th) / 80) ** 2
    G = sheet_patch(-80, 80, root, bang_tip, 38, 16, off_back)
    parts.append(patch_obj_parts(G) + (0,))
    # front layer clumps with pointed tips (layered over the back layer)
    for c, w, dz in ((-46, 12, -0.004), (-16, 12, -0.005), (10, 11, -0.003), (40, 12, -0.006)):
        def off_f(t, th, c=c):
            t = np.asarray(t); side = (abs(th) / 80) ** 2
            return 0.0090 + (0.0090 * t + 0.0080 * np.sin(np.pi * np.clip(t, 0, 1)) ** 1.2) * (1 - 0.35 * side) + 0.004 * side * t
        tipf = lambda th, c=c, dz=dz, w=w: bang_tip(c) - dz * 0 + dz - 0.006 * (abs(th - c) / w) ** 2 * 0
        Gc = sheet_patch(c - w, c + w, lambda th: 30 + 10 * (abs(th) / 80) ** 2, tipf, 9, 15, off_f,
                         taper=lambda tv: np.clip(1.15 - tv ** 3 * 1.15, 0.02, 1.0))
        parts.append(patch_obj_parts(Gc) + (0,))
    # anime highlight band ('angel ring'): thin zig-zag strip riding just above the back-layer surface
    Gh = sheet_patch(-74, 74, root, bang_tip, 60, 60, lambda t, th: off_back(t, th) + 0.0042)
    nv, nu = Gh.shape[:2]
    tt = np.linspace(0, 1, nv)
    rows_lo, rows_hi = [], []
    HV, HF = [], []
    for j in range(nu):
        th = -74 + 148 * j / (nu - 1)
        tc = 0.27 + 0.03 * (abs(th) / 74) ** 2
        zig = 0.040 * max(0.0, np.cos(j * 2 * np.pi / 7.0)) ** 6 + 0.006 * np.sin(j * 0.9) ** 2
        fade = (1 - (abs(th) / 76) ** 4)
        for t in (tc - 0.012 * fade, tc + (0.009 + zig) * fade):
            k = t * (nv - 1); i0 = int(np.clip(np.floor(k), 0, nv - 2)); a = k - i0
            HV.append(Gh[i0, j] * (1 - a) + Gh[i0 + 1, j] * a)
    for j in range(nu - 1):
        HF.append((2 * j, 2 * j + 2, 2 * j + 3, 2 * j + 1))
    hob = mesh_obj('Hair_Highlight', HV, HF, mats=[mats['hair_hi']], coll=coll)
    add_mod(hob, 'SOLIDIFY', thickness=0.0004, offset=-1.0)
    ob = join_parts('Hair_Bangs', parts, [mats['hair']], coll=coll)
    recalc_normals(ob)
    add_mod(ob, 'SOLIDIFY', thickness=0.0035, offset=-1.0)
    add_mod(ob, 'SUBSURF', levels=1, render_levels=2)
    return ob

# ---------------------------------------------------------------- side locks (custom lens profile sweep)
def build_sidelocks(mats, coll):
    parts = []
    for sx in (1, -1):
        p0, _ = surf([48], [sx * 84], 0.004)
        p1, _ = surf([80], [sx * 80], 0.013)
        ctrl = [p0[0], p1[0], [sx * 0.0915, -0.010, 1.372], [sx * 0.102, -0.020, 1.318], [sx * 0.112, -0.050, 1.262],
                [sx * 0.122, -0.066, 1.205], [sx * 0.120, -0.066, 1.150]]
        path = catmull(ctrl, 34)
        t = np.linspace(0, 1, len(path))
        w = np.interp(t, [0, 0.25, 0.55, 0.8, 1.0], [0.026, 0.028, 0.027, 0.019, 0.0012])
        th = np.interp(t, [0, 0.3, 0.8, 1.0], [0.008, 0.0085, 0.006, 0.001])
        Nn = np.tile(norm(np.array([sx * 0.62, -0.78, 0.0])), (len(path), 1))
        cup = np.interp(t, [0, 0.5, 1], [0.002, 0.004, 0.0005])
        v, f = sweep(path, Nn, w, th, K=12, cup=cup)
        parts.append((v, f, 0))
        # second, slimmer lock behind for layered volume
        q0, _ = surf([55], [sx * 96], 0.004)
        q1, _ = surf([88], [sx * 94], 0.012)
        ctrl = [q0[0], q1[0], [sx * 0.093, -0.006, 1.360], [sx * 0.104, -0.020, 1.300], [sx * 0.124, -0.034, 1.245], [sx * 0.132, -0.040, 1.205]]
        path = catmull(ctrl, 28)
        t = np.linspace(0, 1, len(path))
        w = np.interp(t, [0, 0.3, 0.7, 1.0], [0.026, 0.032, 0.022, 0.0015])
        th = np.interp(t, [0, 0.5, 1.0], [0.008, 0.007, 0.001])
        Nn = np.tile(norm(np.array([sx * 0.9, -0.45, 0.0])), (len(path), 1))
        v, f = sweep(path, Nn, w, th, K=12, cup=np.full(len(path), 0.003))
        parts.append((v, f, 0))
    ob = join_parts('Hair_SideLocks', parts, [mats['hair']], coll=coll)
    recalc_normals(ob)
    add_mod(ob, 'SUBSURF', levels=1, render_levels=2)
    return ob

# ---------------------------------------------------------------- back hair: broad tapering sheets
def _smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)

def back_fall(th, ztip, nv, off0):
    """Surface-follow to the widest point, then fall and fan out over the back (width ~0.34 m)."""
    ph_root = 70.0
    phb = 102.0
    phs = np.linspace(ph_root, phb, 25)
    tt = np.linspace(0, 1, 25)
    P, N = surf(phs, np.full(25, th), off0 * (0.45 + 0.55 * tt))
    pb = P[-1]
    x, y = pb[0], pb[1]
    side = abs(np.sin(np.radians(th)))
    sgn = np.sign(x) if abs(x) > 1e-6 else 0
    def fan(z):
        return 1.0 + 0.55 * _smooth(1.32, 1.05, z)
    ctrl = [P[-5], pb,
            [x * 1.04, max(y, -0.01) + 0.02 * side, pb[2] - 0.075]]
    for z in (1.255, 1.13, ztip + 0.06, ztip):
        yy = max(y + 0.01, 0.116 + 0.008 * side) if z > 1.2 else max(y - 0.012 * (1.25 - z) / 0.25, 0.088 + 0.012 * side)
        xx = x * fan(z) + sgn * 0.030 * _smooth(1.32, 1.15, z) * side
        ctrl.append([xx, yy, z])
    tail = catmull(ctrl, 60)
    poly = np.vstack([P[:-5], tail])
    return resample(poly, nv)

def build_back(mats, coll):
    parts = []
    # under-layer (continuous) + overlapping broad sheets with V tips
    rng = np.random.default_rng(11)
    specs = [  # centre theta, half width, tip z, offset, taper power, tip shift
        (180, 84, 1.050, 0.0075, None, 0),
        (122, 24, 1.035, 0.0112, 0.55, 0.15), (-121, 24, 1.010, 0.0112, 0.75, -0.2),
        (152, 21, 0.975, 0.0138, 0.65, -0.1), (-153, 22, 0.990, 0.0138, 0.50, 0.25),
        (180, 15, 0.950, 0.0158, 0.70, 0.1),
        (103, 13, 1.105, 0.0124, 0.6, 0.3), (-103, 12, 1.080, 0.0124, 0.8, -0.3),
        (137, 9, 1.000, 0.0150, 0.9, 0.0), (-168, 9, 0.965, 0.0168, 0.6, 0.2)]
    for c, hw, ztip, off, tp, shift in specs:
        th0, th1 = c - hw, c + hw
        nu = max(7, int(hw / 3.2) | 1)
        if tp is None:
            zt = lambda th, z=ztip: z + 0.022 * np.sin(np.radians(th) * 3.7 + 0.5) + 0.014 * np.sin(np.radians(th) * 9.1)
            taper = lambda tv: np.clip((1 - tv) / 0.25, 0, 1) * 0.9 + 0.1
        else:
            zt = lambda th, z=ztip: z
            taper = lambda tv, p=tp: np.clip((1 - tv) / 0.30, 0, 1) ** p * 0.98 + 0.02
        G = sheet_patch(th0, th1, 70, zt, nu, 22, None, taper=taper,
                        fall=lambda th, z, nv, off=off: back_fall(th, z, nv, off))
        if tp is not None and shift:
            # asymmetric tip: slide the converging tip sideways a little
            tv = np.linspace(0, 1, G.shape[0])[:, None, None]
            side = G[:, -1:, :] - G[:, :1, :]
            G = G + side * shift * 0.5 * _smooth(0.6, 1.0, tv)
        parts.append(patch_obj_parts(G) + (0,))
    ob = join_parts('Hair_Back', parts, [mats['hair']], coll=coll)
    recalc_normals(ob)
    add_mod(ob, 'SOLIDIFY', thickness=0.0045, offset=-1.0)
    add_mod(ob, 'SUBSURF', levels=1, render_levels=1)
    return ob

# ---------------------------------------------------------------- ponytail: layered clumps around a swept axis
def gather_point():
    g, n = surf([G_PH], [G_TH], 0.008)
    return g[0], n[0]

def build_ponytail(mats, coll):
    G, n = gather_point()
    axis_ctrl = [G - n * 0.012, G + np.array([0, 0.036, -0.006]), G + np.array([0, 0.078, -0.022]),
                 G + np.array([0, 0.098, -0.080]), G + np.array([0, 0.094, -0.175]), G + np.array([0, 0.072, -0.265]),
                 G + np.array([0, 0.050, -0.345])]
    axis = catmull(axis_ctrl, 50)
    T, Nn, B = frames(axis, (0, 0, 1))
    parts = []
    rng = np.random.default_rng(7)
    nclump = 11
    for k in range(nclump):
        psi = 2 * np.pi * k / nclump + rng.uniform(-0.15, 0.15)
        L = [1.0, 0.86, 0.95, 0.80, 1.0, 0.90, 0.78, 0.97, 0.88, 0.92, 0.84][k]
        npts = int(26 * L)
        t = np.linspace(0, 1, npts)
        tl = t * L
        R = np.interp(tl, [0, 0.06, 0.22, 0.5, 0.8, 1.0], [0.004, 0.012, 0.046, 0.054, 0.040, 0.028])
        R = R + 0.006 * np.sin(psi * 3 + 1)
        flick = 0.012 * np.clip((t - 0.75) / 0.25, 0, 1) ** 2
        idx = np.clip((tl * 49).astype(int), 0, 49)
        rad = np.cos(psi) * B[idx] + np.sin(psi) * Nn[idx]
        path = axis[idx] + rad * (R + flick)[:, None]
        path = catmull(path[::3] if len(path) > 9 else path, npts)
        w = np.interp(t, [0, 0.08, 0.35, 0.65, 0.88, 1.0], [0.018, 0.040, 0.068, 0.060, 0.032, 0.001])
        th = np.interp(t, [0, 0.3, 0.7, 1.0], [0.012, 0.020, 0.015, 0.001])
        cup = np.interp(t, [0, 0.4, 1.0], [0.002, 0.007, 0.002])
        v, f = sweep(path, rad, w, th, K=10, cup=cup, twist=np.full(npts, 0.0) + 0.25 * np.sin(t * 3 + k))
        parts.append((v, f, 0))
    ob = join_parts('Hair_Ponytail', parts, [mats['hair']], coll=coll)
    recalc_normals(ob)
    add_mod(ob, 'SUBSURF', levels=1, render_levels=2)
    ob['axis'] = [list(map(float, a)) for a in axis]
    return ob, axis

# ---------------------------------------------------------------- loose thin strands (real Blender curves)
def build_strands(mats, coll):
    cu = bpy.data.curves.new('Hair_Strands', 'CURVE')
    cu.dimensions = '3D'; cu.bevel_depth = 0.0016; cu.bevel_resolution = 1; cu.resolution_u = 6
    cu.use_fill_caps = True
    specs = []
    for sx in (1, -1):
        a, _ = surf([70], [sx * 70], 0.012)
        specs.append([a[0], [sx * 0.078, -0.052, 1.40], [sx * 0.083, -0.058, 1.35], [sx * 0.090, -0.064, 1.31]])
        b, _ = surf([95], [sx * 112], 0.014)
        specs.append([b[0], [sx * 0.098, 0.050, 1.33], [sx * 0.104, 0.090, 1.22], [sx * 0.110, 0.094, 1.12], [sx * 0.104, 0.090, 1.05]])
    for pts in specs:
        sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            sp.points[i].co = (p[0], p[1], p[2], 1.0)
            sp.points[i].radius = 1.0 - 0.9 * i / (len(pts) - 1)
        sp.use_endpoint_u = True; sp.order_u = 3
    ob = bpy.data.objects.new('Hair_Strands_curve', cu)
    (coll or bpy.context.scene.collection).objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob)
    me.materials.clear(); me.materials.append(mats['hair'])
    mo = bpy.data.objects.new('Hair_Strands', me)
    (coll or bpy.context.scene.collection).objects.link(mo)
    me.shade_smooth()
    add_mod(mo, 'WELD', merge_threshold=0.0002)
    return mo

# ---------------------------------------------------------------- bow
def build_bow(mats, coll, axis=None):
    """Satin bow: perky tilted loops (0.32 m tip to tip) with two crease folds each,
    a 25 mm pinched knot and 120 mm V-cut tails."""
    G, n = gather_point()
    K = G + np.array([0, 0.046, 0.026])
    parts = []
    L = 0.148; tilt = np.tan(np.radians(17))
    NP, NW = 28, 11
    for sx in (1, -1):
        rings = []
        for i in range(NP):
            t = 2 * np.pi * i / NP
            x = L * 0.5 * (1 - np.cos(t))
            xl = x / L
            puff = 0.020 * np.sin(t) * (0.5 + 0.5 * np.sin(np.pi * xl) ** 0.6)
            y = puff * (1.0 if np.sin(t) >= 0 else 0.8)
            z = tilt * x + 0.006 * np.sin(np.pi * xl)
            p = K + np.array([sx * (x + 0.012), y, z])
            hgt = 0.011 + 0.040 * xl ** 1.1 + 0.006 * np.sin(np.pi * xl) ** 2
            if xl > 0.90:
                hgt *= max(np.sqrt(max(0.0, 1 - ((xl - 0.90) / 0.13) ** 2)), 0.80)
            outward = 1.0 if y >= 0 else -1.0
            rg_ = []
            for k in range(NW):
                u = -1 + 2 * k / (NW - 1)
                bulge = 0.010 * (1 - u * u) * (0.3 + xl)
                crease = 0.0035 * xl * np.exp(-((abs(u) - 0.42) / 0.10) ** 2)
                rg_.append(p + np.array([-sx * 0.012 * u * u * xl ** 4, outward * (bulge - crease), u * hgt]))
            rings.append(rg_)
        V = np.array(rings).reshape(-1, 3)
        F = []
        for i in range(NP):
            i2 = (i + 1) % NP
            for k in range(NW - 1):
                F.append((i * NW + k, i * NW + k + 1, i2 * NW + k + 1, i2 * NW + k))
        parts.append((V, F, 0))
        # 120 mm tails, V-cut ends
        tp = np.array([[sx * 0.008, 0.006, -0.012], [sx * 0.036, 0.018, -0.052], [sx * 0.060, 0.026, -0.098], [sx * 0.074, 0.030, -0.135]]) + K
        tp = resample(catmull(tp, 40), 12)
        pts = []
        for i, p in enumerate(tp):
            s = i / (len(tp) - 1)
            w = 0.020 + 0.010 * s
            T = norm(tp[min(i + 1, 11)] - tp[max(i - 1, 0)])
            S = norm(np.array([1.0, 0, 0]) - T * T[0])
            for k in range(7):
                u = -1 + 2 * k / 6
                vcut = 0.022 * (1 - abs(u)) if i == len(tp) - 1 else 0.0
                pts.append(p + S * (u * w) + np.array([0, 0.004 * (1 - u * u), 0]) - T * vcut)
        parts.append((pts, grid_faces(len(tp), 7, closed=False), 0))
    # 25 mm pinched knot
    rings = []
    for dz, sc in ((-0.0125, 0.25), (-0.010, 0.75), (-0.005, 0.95), (0.0, 0.80), (0.005, 0.95), (0.010, 0.75), (0.0125, 0.25)):
        rings.append(ring(K + np.array([0, 0.004, dz]), (1, 0, 0), (0, 1, 0), 0.0125 * sc, 0.0115 * sc, 20,
                          mod=lambda a: 0.07 * np.cos(5 * a)))
    v, f = loft(rings, True, True, True)
    parts.append((v, f, 0))
    ob = join_parts('Bow', parts, [mats['teal']], coll=coll)
    recalc_normals(ob)
    add_mod(ob, 'SOLIDIFY', thickness=0.0035, offset=0.0)
    add_mod(ob, 'SUBSURF', levels=1, render_levels=2)
    return ob

# ---------------------------------------------------------------- smooth-normal proxies
def hair_proxy(coll):
    rows = [(1.605, 0.010, 0.010, 0.010), (1.585, 0.055, 0.060, 0.012), (1.55, 0.090, 0.100, 0.014), (1.50, 0.110, 0.122, 0.016),
            (1.44, 0.118, 0.130, 0.018), (1.38, 0.120, 0.132, 0.022), (1.30, 0.135, 0.130, 0.035), (1.20, 0.160, 0.110, 0.050),
            (1.10, 0.175, 0.100, 0.055), (0.95, 0.180, 0.095, 0.055), (0.88, 0.180, 0.090, 0.055)]
    rings = [ring((0, cy, z), (1, 0, 0), (0, -1, 0), rx, ry, 48) for z, rx, ry, cy in rows]
    v, f = loft(rings, True, True, True)
    ob = mesh_obj('HairNormalProxy', v, f, mats=[], coll=coll)
    recalc_normals(ob)
    add_mod(ob, 'SUBSURF', levels=2, render_levels=2)
    ob.hide_render = True; ob.hide_viewport = True
    return ob

def tube_proxy(name, axis, radius, coll):
    v, f = tube_along(axis, radius, radius, 24, up_hint=(0, 0, 1))
    ob = mesh_obj(name, v, f, mats=[], coll=coll)
    recalc_normals(ob)
    add_mod(ob, 'SUBSURF', levels=1, render_levels=1)
    ob.hide_render = True; ob.hide_viewport = True
    return ob

def transfer_normals(ob, proxy, factor=1.0):
    m = ob.modifiers.new('SmoothNormals', 'DATA_TRANSFER')
    m.object = proxy; m.use_loop_data = True; m.data_types_loops = {'CUSTOM_NORMAL'}
    m.loop_mapping = 'POLYINTERP_NEAREST'; m.mix_factor = factor
    return m
