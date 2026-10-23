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
    for c, d, w in ((-30, 0.010, 6.0), (-3, 0.008, 5.0), (24, 0.011, 6.0)):
        notch += d * max(0.0, 1 - abs(th - c) / w) ** 1.3
    return base + notch

def build_bangs(mats, coll):
    parts = []
    def off_back(t, th):
        lift = 0.0065 + 0.0090 * np.asarray(t) ** 1.6 + 0.006 * (abs(th) / 80) ** 2 * np.asarray(t)
        return lift
    root = lambda th: 26 + 10 * (abs(th) / 80) ** 2
    G = sheet_patch(-80, 80, root, bang_tip, 38, 16, off_back)
    parts.append(patch_obj_parts(G) + (0,))
    # front layer clumps with pointed tips (layered over the back layer)
    for c, w, dz in ((-46, 12, -0.004), (-16, 12, -0.005), (10, 11, -0.003), (40, 12, -0.006)):
        def off_f(t, th, c=c):
            return 0.0085 + 0.0115 * np.asarray(t) ** 1.5 + 0.006 * (abs(th) / 80) ** 2 * np.asarray(t)
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
        tc = 0.36 + 0.02 * np.sin(np.radians(th) * 2.3) + 0.05 * (abs(th) / 74) ** 2
        seg = max(0.0, np.sin(j * 0.42 + 0.6)) ** 0.7
        hw = 0.065 * seg * (1 - (abs(th) / 80) ** 3) + 0.0005
        for t in (tc - hw, tc + hw * 0.6):
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
        ctrl = [p0[0], p1[0], [sx * 0.0845, -0.034, 1.372], [sx * 0.092, -0.044, 1.318], [sx * 0.110, -0.060, 1.262],
                [sx * 0.121, -0.070, 1.205], [sx * 0.119, -0.068, 1.150]]
        path = catmull(ctrl, 34)
        t = np.linspace(0, 1, len(path))
        w = np.interp(t, [0, 0.25, 0.55, 0.8, 1.0], [0.028, 0.036, 0.031, 0.020, 0.0015])
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
def back_fall(th, ztip, nv, off0):
    ph_root = 70.0
    phb = 102.0
    phs = np.linspace(ph_root, phb, 25)
    tt = np.linspace(0, 1, 25)
    P, N = surf(phs, np.full(25, th), off0 * (0.45 + 0.55 * tt))
    pb = P[-1]
    x, y = pb[0], pb[1]
    side = abs(np.sin(np.radians(th)))
    sgn = np.sign(x) if abs(x) > 1e-6 else 0
    ctrl = [P[-5], pb,
            [x * 1.03, max(y, -0.01) + 0.02 * side, pb[2] - 0.075],
            [x * 0.97 + sgn * 0.004, max(y + 0.01, 0.114 + 0.006 * side), 1.255],
            [x * 1.02 + sgn * 0.010, max(y, 0.100), 1.130],
            [x * 1.00 + sgn * 0.014, max(y - 0.01, 0.088), ztip + 0.06],
            [x * 0.96 + sgn * 0.012, max(y - 0.02, 0.084), ztip]]
    tail = catmull(ctrl, 60)
    poly = np.vstack([P[:-5], tail])
    return resample(poly, nv)

def build_back(mats, coll):
    parts = []
    # under-layer (continuous) + overlapping broad sheets with V tips
    specs = [  # centre theta, half width, tip z, offset
        (180, 82, 1.060, 0.0075, None),
        (124, 26, 1.040, 0.0115, 1), (-124, 26, 1.030, 0.0115, 1),
        (156, 22, 0.985, 0.0140, 1), (-154, 22, 0.995, 0.0140, 1),
        (180, 16, 0.960, 0.0160, 1),
        (102, 12, 1.110, 0.0125, 1), (-102, 12, 1.100, 0.0125, 1)]
    for c, hw, ztip, off, tp in specs:
        th0, th1 = c - hw, c + hw
        nu = max(7, int(hw / 3.2) | 1)
        G = sheet_patch(th0, th1, 70, lambda th, z=ztip: z, nu, 22, None,
                        taper=(lambda tv: np.clip((1 - tv) / 0.30, 0, 1) ** 0.6 * 0.98 + 0.02) if tp else (lambda tv: np.clip((1 - tv) / 0.25, 0, 1) * 0.9 + 0.1),
                        fall=lambda th, z, nv, off=off: back_fall(th, z, nv, off))
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
    G, n = gather_point()
    C = G + np.array([0, 0.046, 0.026])
    parts = []
    for sx in (1, -1):
        # puffy loop: ribbon whose width runs along Z, path is a teardrop in the X/Y plane
        tau = np.linspace(0, 2 * np.pi, 42, endpoint=False)
        span = 0.138
        s = (1 - np.cos(tau)) / 2
        xl = 0.010 + span * s
        yl = 0.030 * np.sin(tau) * (s ** 0.40) * (1 - 0.15 * s)
        width = 0.024 + 0.050 * np.clip(np.sin(np.pi * s), 0, 1) ** 0.35
        pts = []
        nw = 9
        for i in range(len(tau)):
            for j in range(nw):
                u = (j / (nw - 1)) * 2 - 1
                # outward normal of loop in XY
                nrm = norm(np.array([np.cos(tau[i] + np.pi / 2) * 0.2, np.sign(np.sin(tau[i]) + 1e-6), 0.0]))
                puff = 0.014 * (1 - u * u) * np.sin(np.pi * s[i]) ** 0.7
                p = np.array([xl[i], yl[i] + np.sign(np.sin(tau[i]) + 1e-9) * puff, u * width[i] / 2])
                pts.append(p)
        pts = np.array(pts)
        # tilt: outer end lifts and sweeps forward
        ang_z = np.radians(-16); ang_y = np.radians(-12)
        x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
        al = np.radians(38) * np.clip(x / 0.05, 0, 1)
        y, z = y * np.cos(al) - z * np.sin(al), y * np.sin(al) + z * np.cos(al)
        z2 = z + x * np.tan(ang_z)
        y2 = y - 0.42 * x ** 1.3
        pts = np.stack([sx * x, y2, z2], 1) + C
        F = []
        nt = len(tau)
        for i in range(nt):
            i2 = (i + 1) % nt
            for j in range(nw - 1):
                F.append((i * nw + j, i * nw + j + 1, i2 * nw + j + 1, i2 * nw + j))
        if sx < 0:
            F = [tuple(reversed(f)) for f in F]
        parts.append((pts, F, 0))
        # tails with V-cut ends
        tp = np.array([[sx * 0.006, 0.012, -0.006], [sx * 0.030, 0.026, -0.045], [sx * 0.058, 0.026, -0.095], [sx * 0.078, 0.016, -0.140]]) + C
        tp = catmull(tp, 14)
        nw = 7
        pts = []
        for i, p in enumerate(tp):
            t = i / (len(tp) - 1)
            w = 0.030 + 0.016 * t
            tan = tp[min(i + 1, len(tp) - 1)] - tp[max(i - 1, 0)]
            side = norm(np.cross(tan, [0, 1.0, 0]))
            for j in range(nw):
                u = (j / (nw - 1)) * 2 - 1
                q = p + side * u * w / 2 + np.array([0, 1, 0]) * 0.004 * (1 - u * u) * np.sin(np.pi * t)
                if i == len(tp) - 1:
                    q = q + norm(tan) * -0.020 * (1 - abs(u)) ** 1.0
                pts.append(q)
        F = grid_faces(len(tp), nw, closed=False)
        parts.append((pts, F, 0))
    # pinched knot
    rings = []
    for k, (dx, rz, ry) in enumerate(((-0.020, 0.010, 0.008), (-0.016, 0.019, 0.014), (-0.008, 0.023, 0.017), (0, 0.024, 0.018),
                                       (0.008, 0.023, 0.017), (0.016, 0.019, 0.014), (0.020, 0.010, 0.008))):
        rings.append(ring(C + np.array([dx, 0.010, 0]), (0, 0, 1), (0, 1, 0), rz, ry, 20,
                          mod=lambda a: 0.06 * np.cos(5 * a)))
    v, f = loft(rings, True, True, True)
    parts.append((v, f, 0))
    ob = join_parts('Bow', parts, [mats['teal']], coll=coll)
    recalc_normals(ob)
    add_mod(ob, 'SOLIDIFY', thickness=0.0035, offset=0.0)
    add_mod(ob, 'SUBSURF', levels=1, render_levels=2)
    return ob
