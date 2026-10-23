"""HD reference model: signed-distance parts, culled deterministic sphere tracing, posing.

Selected by a variant's `"model": "hd"` (legacy variants never import this module's tracer).
`raycast` / `occluded` have the same signature and return the same buffers as render.raycast / render.occluded
(t, prim index, world normal), so the pixel pass, face cels, line-art passes and QA are unchanged.

Part spec (character["parts"], bone space; emitted by chargen next to "primitives"):
  {"name", "bone" | "bones": [[bone, w], ...], "shape", "center", "rot", "scale", "params",
   "material", "group", "blend": {"set": str, "k": float}, "op": union|subtract|intersect, "lod": all|ref,
   "clip_all", "clip_any"}
shapes (params in the part frame = bone @ T(center) @ R(rot) @ S(scale)):
  ellipsoid {radii at top level, legacy-identical matrix}        capsule {a, b, r}
  rcone {a, b, ra, rb, flat, flat_n | flat_c}  (round ends; rb ~0.05 = sharp tip; flat < 1 = thin along flat_n)
  cone  {same, flat-cut ends}                                     tube {pts, r: [...], flat, flat_n | flat_c}
  rbox  {b: half extents, r: rounding}                            torus {R: [Rx, Rz] ring in local xz, r, w, taper}
  sweep {pts, n, w: [...], t: [...], nrm | flat_n | flat_c, lens, curl, cap0, cap1, vcut, capr, closed}  (r21: smooth
        swept sheet / ribbon / closed loop, see sweep_from_spec)
  chain sweep: {"chain": name, "sweep": {"clumps", "twist", "spread", "clump_r", "tip": sharp|fork, "tips"}}
               or {"mode": "ribbon", "strands": [...], "root_to", "extend", ...} (r21, see _pose_ribbons)
Combination: parts without a blend set are hard-unioned (hard min across parts/materials keeps colour borders
crisp); smooth-min, subtract and intersect act only inside their own set. Clip planes keep legacy semantics:
a surface point failing the clip is not drawn (no cap), the ray continues to whatever is behind.
Tracing: per-part bounding volume (exact ellipsoid / oriented box) culled through a 2D ray grid, then a fixed
maximum of STEPS float64 sphere-tracing steps. Fully deterministic (no randomness, fixed iteration order).
"""
import math

import numpy as np

from .mathutil import translate, scale, euler
from .render import _clip_ok

STEPS = 48
RELAX = 0.85            # step = RELAX * distance bound (taper / flattening make bounds approximate)
EPS = 0.004             # convergence distance (world units)
FD_H = 0.01             # finite-difference step for normals (world units)
SHADOW_T0 = 0.05
SMOOTH_JOINTS = False


# ------------------------------------------------------------------ local SDFs (p: (n,3), params broadcast)
def _sd_seg(p, P):
    """Tapered segment a->b. Round ends: exact round cone (side tangent to both end spheres, so chained segments
    sharing joint spheres are seamless). capped: frustum with flat cuts. Flattening scales the cross-section
    along n2 by `flat` (distance returned as a lower bound)."""
    a, b = P["a"], P["b"]
    ba = b - a
    l2 = (ba * ba).sum(-1)
    pa = p - a
    y = (pa * ba).sum(-1)
    hr = y / l2
    h = np.clip(hr, 0.0, 1.0)
    perp = pa - hr[:, None] * ba
    n2 = P["n2"] + h[:, None] * (P["n2b"] - P["n2"])     # flattening axis, lerped a -> b
    n2 = n2 / np.maximum(np.sqrt((n2 * n2).sum(-1)), 1e-9)[:, None]
    flat = P["flat"] + h * (P["flatb"] - P["flat"])     # cross-section flattening, lerped a -> b
    c2 = (perp * n2).sum(-1)
    q2 = np.maximum((perp * perp).sum(-1) - c2 * c2 + (c2 / flat) ** 2, 0.0)   # stretched perpendicular dist^2
    ra, rb = P["ra"], P["rb"]
    rr = ra - rb
    # round cone (IQ), in stretched space
    a2 = l2 - rr * rr
    x2 = q2 * l2 * l2
    z = y - l2
    y2, z2 = y * y * l2, z * z * l2
    k = np.sign(rr) * rr * rr * x2
    d_end = np.sqrt(x2 + z2) / l2 - rb
    d_start = np.sqrt(x2 + y2) / l2 - ra
    d_side = (np.sqrt(x2 * a2 / l2) + y * rr) / l2 - ra
    rnd = np.where(np.sign(z) * a2 * z2 > k, d_end, np.where(np.sign(y) * a2 * y2 < k, d_start, d_side))
    # flat-cut frustum
    L = np.sqrt(l2)
    cosa = L / np.sqrt(l2 + rr * rr)
    lat = (np.sqrt(q2) - (ra - hr * rr)) * cosa
    cut = np.maximum(lat, np.maximum(-hr, hr - 1.0) * L)
    return np.where(P["capped"], cut, rnd) * np.minimum(P["flat"], P["flatb"])


def _sd_rbox(p, P):
    r = P["r"]
    q = np.abs(p) - (P["b"] - r[..., None])
    return np.sqrt((np.maximum(q, 0.0) ** 2).sum(-1)) + np.minimum(q.max(-1), 0.0) - r


def _sd_torus(p, P):
    """Band ring: elliptical ring (Rx, Rz) in local xz, stadium cross-section (half thickness r, half width w),
    width tapering linearly along local x (taper > 0 = wider at +x); `round` > 0 narrows the width toward both
    x ends (w * sqrt(1 - round * (x/Rx)^2)) so a bow loop reads as a rounded petal instead of a flat plank."""
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    Rx, Rz = P["R"][..., 0], P["R"][..., 1]
    rho = np.sqrt((x / Rx) ** 2 + (z / Rz) ** 2)
    g = np.sqrt((x / Rx ** 2) ** 2 + (z / Rz ** 2) ** 2)
    e = np.where(g > 1e-9, (rho - 1.0) * rho / np.maximum(g, 1e-9), -np.minimum(Rx, Rz))
    r = P["r"]
    xn = np.clip(x / Rx, -1.0, 1.0)
    w = P["w"] * (1.0 + P["taper"] * xn)
    if np.any(P["round"]):
        w = w * np.sqrt(np.maximum(1.0 - P["round"] * xn * xn, 0.05))
    w = np.maximum(w, r)
    qy = np.maximum(np.abs(y) - (w - r), 0.0)
    return np.sqrt(e * e + qy * qy) - r


# ---- r21 (S4_hd2): smooth swept ribbons / sheets ("sweep" kind). Additive: no legacy part uses it.
SWEEP_CHUNK = 12000


def _sweep_pick(X, j, ar):
    return X[0][j] if X.shape[0] == 1 else X[ar, j]


def _sd_sweep_chunk(p, P):
    """Swept cross-section along a densely sampled centre polyline C (m, S+1, 3). Per sample: thickness axis N,
    half-width w (along B = T x N), half-thickness t, arclength s (0..1). Section: rounded rectangle (w, t) whose
    thickness thins toward the edges (lens) and that is cupped about N (curl: sagitta / w). Open ends: blunt cut with
    rounding capr (fraction of the local thickness); vcut at the far end: > 0 = swallowtail notch (centre shorter by
    vcut), < 0 = V point (edges shorter by |vcut|). Interior joints use frames lerped along the nearest segment, so
    a densely sampled smooth curve gives a smooth surface (no joint rings)."""
    C = P["C"]
    A, Bp = C[:, :-1], C[:, 1:]
    BA = Bp - A
    l2 = (BA * BA).sum(-1)
    valid = l2 > 1e-12
    pa = p[:, None, :] - A
    h = np.clip((pa * BA).sum(-1) / np.maximum(l2, 1e-12), 0.0, 1.0)
    d2 = ((pa - h[..., None] * BA) ** 2).sum(-1)
    d2 = np.where(valid, d2, np.inf)
    j = np.argmin(d2, axis=1)
    n = len(p)
    ar = np.arange(n)
    hj = h[ar, j]
    a, ba = _sweep_pick(A, j, ar), _sweep_pick(BA, j, ar)
    T = _sweep_pick(P["T"][:, :-1], j, ar) * (1 - hj)[:, None] + _sweep_pick(P["T"][:, 1:], j, ar) * hj[:, None]
    T = T / np.maximum(np.sqrt((T * T).sum(-1)), 1e-9)[:, None]      # smooth tangent (continuous across joints)
    c = a + hj[:, None] * ba
    N0, N1 = _sweep_pick(P["N"][:, :-1], j, ar), _sweep_pick(P["N"][:, 1:], j, ar)
    Nv = N0 + hj[:, None] * (N1 - N0)
    Nv = Nv - (Nv * T).sum(-1)[:, None] * T
    Nv = Nv / np.maximum(np.sqrt((Nv * Nv).sum(-1)), 1e-9)[:, None]
    Bv = np.cross(T, Nv)

    def lerp(K):
        return _sweep_pick(P[K][:, :-1], j, ar) * (1 - hj) + _sweep_pick(P[K][:, 1:], j, ar) * hj
    w, t, s = lerp("w"), lerp("t"), lerp("s")
    sc = (lambda K: P[K] if P[K].shape[0] == n else np.broadcast_to(P[K], (n,)))
    lens, curl, capr = sc("lens"), sc("curl"), sc("capr")
    cap0, cap1, vcut, closed, Ltot = sc("cap0"), sc("cap1"), sc("vcut"), sc("closed"), sc("L")
    nseg = sc("nseg").astype(int)
    r = p - c
    e = (r * T).sum(-1)
    u = (r * Bv).sum(-1)
    v = (r * Nv).sum(-1)
    w = np.maximum(w, 1e-3)
    un = np.clip(u / w, -1.0, 1.0)
    v = v - curl * w * un * un
    tl = np.maximum(t * (1.0 - lens * un * un), 0.015)
    rr = np.minimum(w, tl)
    qx = np.abs(u) - (w - rr)
    qy = np.abs(v) - (tl - rr)
    dsec = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0) - rr
    # axial excess past the open ends (only on the first / last segment)
    first = (j == 0) & (hj <= 0.0) & (e < 0)
    last = (j == nseg - 1) & (hj >= 1.0) & (e > 0)
    ex = np.where(first & (cap0 > 0), -e, np.where(last & (cap1 > 0), e, -np.inf))
    # far-end V cut: axial coordinate from the end, end plane shifted by the V profile across the width
    z_end = (1.0 - s) * Ltot - np.where(last, e, 0.0)        # distance in front of the end plane (>0 inside)
    absu = np.minimum(np.abs(u) / w, 1.0)
    shift = np.where(vcut > 0, vcut * (1.0 - absu), -vcut * absu)
    nrm_v = 1.0 / np.sqrt(1.0 + (np.abs(vcut) / w) ** 2)
    ev = np.where(np.abs(vcut) > 0, (shift - z_end) * nrm_v, -np.inf)
    ex = np.where(cap1 > 0, np.maximum(ex, ev), ex)
    ex = np.where(closed > 0, -np.inf, ex)
    rc = rr * capr
    fin = np.isfinite(ex)
    exf = np.where(fin, ex, 0.0)
    rnd = (np.sqrt(np.maximum(dsec + rc, 0) ** 2 + np.maximum(exf + rc, 0) ** 2)
           + np.minimum(np.maximum(dsec + rc, exf + rc), 0) - rc)
    return np.where(fin, rnd, dsec) * sc("lip")


def _sd_sweep(p, P):
    n = len(p)
    if n <= SWEEP_CHUNK:
        return _sd_sweep_chunk(p, P)
    res = np.empty(n)
    for k0 in range(0, n, SWEEP_CHUNK):
        k1 = min(k0 + SWEEP_CHUNK, n)
        Pk = {k: (v[k0:k1] if v.shape[0] == n and n > 1 else v) for k, v in P.items()}
        res[k0:k1] = _sd_sweep_chunk(p[k0:k1], Pk)
    return res


def _catmull(ctrl, n, closed=False):
    """Uniform Catmull-Rom through control points -> n+1 samples (closed: last == first)."""
    P = np.asarray(ctrl, float)
    if len(P) == 1:
        return np.repeat(P, n + 1, 0), np.zeros(n + 1)
    if closed:
        Q = np.vstack([P[-1:], P, P[:2]])
        nsp = len(P)
    else:
        Q = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
        nsp = len(P) - 1
    u = np.linspace(0, nsp, n + 1)
    i = np.minimum(u.astype(int), nsp - 1)
    t = (u - i)[:, None]
    p0, p1, p2, p3 = Q[i], Q[i + 1], Q[i + 2], Q[i + 3]
    out = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
    return out, u / nsp


def _profile(vals, s):
    """Profile values at uniform knots over 0..1 -> values at s, Catmull-Rom interpolated (C1: no crease rings where a
    linear profile would change slope)."""
    vals = np.atleast_1d(np.asarray(vals, float))
    if len(vals) == 1:
        return np.full(len(s), vals[0])
    if len(vals) == 2:
        return np.interp(s, [0.0, 1.0], vals)
    V = np.concatenate([[2 * vals[0] - vals[1]], vals, [2 * vals[-1] - vals[-2]]])
    u = np.clip(np.asarray(s, float), 0, 1) * (len(vals) - 1)
    i = np.minimum(u.astype(int), len(vals) - 2)
    t = u - i
    p0, p1, p2, p3 = V[i], V[i + 1], V[i + 2], V[i + 3]
    out = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
    lo, hi = vals.min(), vals.max()
    return np.clip(out, lo - 0.25 * (hi - lo), hi + 0.25 * (hi - lo))


def sweep_params(C, N, w, t, lens=0.0, curl=0.0, cap0=1, cap1=1, vcut=0.0, capr=0.6, closed=False):
    """Sampled centre line C (S+1, 3), thickness axes N (S+1, 3), profiles w / t (S+1) -> param dict (batch dim 1)."""
    C = np.asarray(C, float)
    seg = np.linalg.norm(np.diff(C, axis=0), axis=1)
    L = float(seg.sum())
    s = np.concatenate([[0.0], np.cumsum(seg)]) / max(L, 1e-9)
    T = np.zeros_like(C)
    T[1:-1] = C[2:] - C[:-2]
    T[0], T[-1] = C[1] - C[0], C[-1] - C[-2]
    if closed:
        T[0] = T[-1] = C[1] - C[-2]
    T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
    N = np.asarray(N, float)
    N = N - (N * T).sum(1)[:, None] * T
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    w, t = np.asarray(w, float), np.asarray(t, float)
    lip = 1.0 / (1.0 + 1.5 * abs(curl) + 0.6 * abs(lens) + 0.5 * abs(vcut) / max(float(w.min()), 0.3))
    return {"C": C[None], "T": T[None], "N": N[None], "w": w[None], "t": t[None], "s": s[None], "L": np.array([L]),
            "nseg": np.array([float(len(C) - 1)]), "lens": np.array([float(lens)]), "curl": np.array([float(curl)]),
            "cap0": np.array([float(cap0)]), "cap1": np.array([float(cap1)]), "vcut": np.array([float(vcut)]),
            "capr": np.array([float(capr)]), "closed": np.array([1.0 if closed else 0.0]), "lip": np.array([lip])}


def sweep_from_spec(pr):
    """Static "sweep" part params: {"pts": control points, "n": samples, "w": [...], "t": [...] (profiles over the
    arclength), "nrm": [per control point] | "flat_n" | "flat_c" (thickness axis), "lens", "curl", "cap0", "cap1",
    "vcut", "capr", "closed"}."""
    closed = bool(pr.get("closed"))
    n = int(pr.get("n", 16))
    C, uc = _catmull(pr["pts"], n, closed)
    if "nrm" in pr:
        Nc = np.asarray(pr["nrm"], float)
        Nc = np.vstack([Nc, Nc[:1]]) if closed else Nc
        k = np.linspace(0, 1, len(Nc))
        N = np.stack([np.interp(uc, k, Nc[:, a]) for a in range(3)], 1)
    elif "flat_n" in pr:
        N = np.broadcast_to(np.asarray(pr["flat_n"], float), C.shape).copy()
    elif "flat_c" in pr:
        N = C - np.asarray(pr["flat_c"], float)
    else:
        N = np.broadcast_to(np.array([0, 0, 1.0]), C.shape).copy()
    seg = np.linalg.norm(np.diff(C, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)]) / max(seg.sum(), 1e-9)
    return sweep_params(C, N, _profile(pr["w"], s), _profile(pr["t"], s), pr.get("lens", 0.0), pr.get("curl", 0.0),
                        pr.get("cap0", 1), pr.get("cap1", 1), pr.get("vcut", 0.0), pr.get("capr", 0.6), closed)


DETAIL_MODES = {"none": 0, "pleats": 1, "ridges": 2, "rings": 3, "scallop": 4, "folds": 5}
DETAIL_KEYS = ("dmode", "dn", "ddepth", "dy0", "dy1", "dlip")


def _detail(q, d, P):
    """Surface detail as a displacement in the part frame (angle about local y, height = local y).
    pleats: box-pleat folds deepening from y0 down to y1 | ridges: n ribs around y (knit, ribbed cuffs)
    folds (r21): n soft sinusoidal folds easing in from y0 to y1
    rings: n grooves between y0 and y1 | scallop: n scallops on the edge below y0 (to y1)."""
    mode = P["dmode"]
    if not np.any(mode):
        return d
    th = np.arctan2(q[:, 0], q[:, 2])
    y = q[:, 1]
    n, dep = P["dn"], P["ddepth"]
    span = np.where(np.abs(P["dy0"] - P["dy1"]) > 1e-9, P["dy0"] - P["dy1"], 1.0)
    w = np.clip((P["dy0"] - y) / span, 0.0, 1.0)
    box = np.clip(2.5 * np.cos(n * th), -1.0, 1.0)
    disp = np.select([mode == 1, mode == 2, mode == 3, mode == 4, mode == 5],
                     [dep * 0.5 * (1 - box) * w,
                      dep * 0.5 * (1 + np.cos(n * th)),
                      dep * 0.5 * (1 + np.cos(2 * np.pi * n * (P["dy0"] - y) / span)) * (w > 0) * (w < 1),
                      dep * np.abs(np.sin(n * th / 2)) * w,
                      # r21 folds: soft rounded (sinusoidal) folds fading in from y0 to y1 (eased), no box edges
                      dep * 0.5 * (1 - np.cos(n * th)) * (w * w * (3 - 2 * w))], 0.0)
    return (d + disp) * P["dlip"]


def _with_detail(f):
    def g(q, P):
        return _detail(q, f(q, P), P) if "dmode" in P else f(q, P)
    return g


SDF = {"seg": _with_detail(_sd_seg), "rbox": _with_detail(_sd_rbox), "torus": _with_detail(_sd_torus),
       "sweep": _with_detail(_sd_sweep)}
PARAM_KEYS = {"seg": ("a", "b", "ra", "rb", "n2", "n2b", "flat", "flatb", "capped") + DETAIL_KEYS,
              "rbox": ("b", "r") + DETAIL_KEYS, "torus": ("R", "r", "w", "taper", "round") + DETAIL_KEYS,
              "sweep": ("C", "T", "N", "w", "t", "s", "L", "nseg", "lens", "curl", "cap0", "cap1", "vcut", "capr", "closed",
                        "lip") + DETAIL_KEYS}


def _detail_params(det, size):
    """Part-spec "detail" -> param arrays (`size` ~ part radius, for the Lipschitz correction)."""
    if not det:
        return {"dmode": np.array([0]), "dn": np.array([0.0]), "ddepth": np.array([0.0]), "dy0": np.array([0.0]),
                "dy1": np.array([0.0]), "dlip": np.array([1.0])}
    n, dep = float(det.get("n", 8)), float(det.get("depth", 0.2))
    return {"dmode": np.array([DETAIL_MODES[det["type"]]]), "dn": np.array([n]), "ddepth": np.array([dep]),
            "dy0": np.array([float(det.get("y0", 0.0))]), "dy1": np.array([float(det.get("y1", 0.0))]),
            "dlip": np.array([1.0 / (1.0 + dep * n * 0.6 / max(size, 0.5))])}


def _local_box(part):
    """Local-frame AABB (lo, hi) of a part's shape."""
    k, P = part["kind"], part["params"]
    if k == "ell":
        return -np.ones(3), np.ones(3)
    if k == "seg":
        r = max(float(P["ra"][0]), float(P["rb"][0]))
        a, b = P["a"][0], P["b"][0]
        return np.minimum(a, b) - r, np.maximum(a, b) + r
    if k == "rbox":
        return -P["b"][0], P["b"][0]
    if k == "torus":
        Rx, Rz = P["R"][0]
        r = float(P["r"][0])
        w = float(P["w"][0]) * (1 + abs(float(P["taper"][0])))
        h = np.array([Rx + r, max(r, w), Rz + r])
        return -h, h
    if k == "sweep":
        C = P["C"][0]
        m = float(max(P["w"][0].max(), P["t"][0].max())) * (1.0 + abs(float(P["curl"][0]))) + 0.05
        return C.min(0) - m, C.max(0) + m
    raise ValueError(k)


# ------------------------------------------------------------------ compiled scene
def _stack_param(arrs):
    """Concatenate per-part param arrays; sampled sweep arrays of different lengths are padded by repeating the
    last sample (zero-length padding segments are ignored by the sweep SDF)."""
    if arrs[0].ndim < 2 or all(a.shape[1:] == arrs[0].shape[1:] for a in arrs):
        return np.concatenate(arrs)
    S = max(a.shape[1] for a in arrs)
    return np.concatenate([np.concatenate([a, np.repeat(a[:, -1:], S - a.shape[1], 1)], 1) if a.shape[1] < S else a
                           for a in arrs])


class _Compiled:
    def __init__(self, prims):
        self.prims = prims
        n = len(prims)
        self.Fi = np.zeros((n, 3, 3))
        self.ft = np.zeros((n, 3))
        self.sv = np.ones(n)
        self.lo = np.zeros((n, 3))
        self.hi = np.zeros((n, 3))
        self.center = np.zeros((n, 3))
        self.radius = np.zeros(n)
        rep, rep_of = {}, np.arange(n)
        sets = {}
        for i, p in enumerate(prims):
            if p["kind"] != "ell" and "dmode" not in p["params"]:
                p["params"].update(_detail_params(None, 1.0))
            M = p["M"]
            Mi = np.linalg.inv(M)
            self.Fi[i], self.ft[i] = Mi[:3, :3], Mi[:3, 3]
            sing = np.linalg.svd(M[:3, :3], compute_uv=False)
            self.sv[i] = sing.min()
            lo, hi = _local_box(p)
            st = p.get("set")
            if st:
                m = (p.get("k", 0.0) * 0.25 + 0.05) / self.sv[i]   # smooth-min may bulge by k/4
                lo, hi = lo - m, hi + m
            self.lo[i], self.hi[i] = lo, hi
            c = (lo + hi) / 2
            self.center[i] = M[:3, :3] @ c + M[:3, 3]
            self.radius[i] = sing.max() * float(np.linalg.norm((hi - lo) / 2)) + 1e-6
            key = p.get("vote")
            if key is not None:
                rep_of[i] = rep.setdefault(key, i)
            if st:
                sets.setdefault(st, []).append(i)
        self.rep_of = rep_of
        # consecutive segments of one strand (tube / sweep clump): neighbours for G1-smoothed shading normals
        self.prev = np.full(n, -1, int)
        self.next = np.full(n, -1, int)
        for i in range(1, n):
            sid = prims[i].get("strand")
            if sid is not None and prims[i - 1].get("strand") == sid:
                self.prev[i], self.next[i - 1] = i - 1, i
        # a set reduced to one plain union member by LOD filtering is just a singleton
        self.sets = []
        single = set(range(n))
        for name, idx in sets.items():
            ops = [prims[i].get("op", "union") for i in idx]
            if len(idx) == 1 and ops[0] == "union":
                continue
            self.sets.append(([i for i, o in zip(idx, ops) if o == "union"],
                              [i for i, o in zip(idx, ops) if o == "subtract"],
                              [i for i, o in zip(idx, ops) if o == "intersect"]))
            single -= set(idx)
        self.ell = [i for i in sorted(single) if prims[i]["kind"] == "ell" and prims[i].get("op", "union") == "union"]
        self.batch = {k: [i for i in sorted(single) if prims[i]["kind"] == k and prims[i].get("op", "union") == "union"]
                      for k in SDF}
        self.stack = {}
        for k, ids in self.batch.items():
            if ids:
                self.stack[k] = {key: _stack_param([prims[i]["params"][key] for i in ids]) for key in PARAM_KEYS[k]}
                pos = np.full(n, -1, int)
                pos[ids] = np.arange(len(ids))
                self.stack[k]["_pos"] = pos

    def part_sdf_world(self, i, p):
        """World-space distance bound of part i at world points p."""
        q = p @ self.Fi[i].T + self.ft[i]
        pr = self.prims[i]
        if pr["kind"] == "ell":
            k = np.maximum(np.sqrt((q * q).sum(-1)), 1e-9)
            g = np.sqrt((((q / k[:, None]) @ self.Fi[i]) ** 2).sum(-1))
            return (k - 1.0) / np.maximum(g, 1e-9)
        return SDF[pr["kind"]](q, pr["params"]) * self.sv[i]

    def set_sdf(self, st, p):
        uni, sub, inter = st
        d = arg = raw = None
        for j, i in enumerate(uni):
            di = self.part_sdf_world(i, p)
            if d is None:
                d, raw, arg = di, di.copy(), np.zeros(len(p), int)
                continue
            k = self.prims[i].get("k", 0.0)
            if k > 0:
                h = np.maximum(k - np.abs(d - di), 0.0) / k
                d = np.minimum(d, di) - h * h * k * 0.25
            else:
                d = np.minimum(d, di)
            better = di < raw
            raw = np.where(better, di, raw)
            arg = np.where(better, j, arg)
        for i in sub:
            ds = -self.part_sdf_world(i, p)
            k = self.prims[i].get("k", 0.0)
            if k > 0:
                h = np.maximum(k - np.abs(d - ds), 0.0) / k
                d = np.maximum(d, ds) + h * h * k * 0.25
            else:
                d = np.maximum(d, ds)
        for i in inter:
            d = np.maximum(d, self.part_sdf_world(i, p))
        return d, np.asarray(uni)[arg]

    def clip_ok_world(self, i, p):
        pr = self.prims[i]
        if not pr.get("clip_all") and not pr.get("clip_any"):
            return np.ones(len(p), bool)
        return _clip_ok(p @ self.Fi[i].T + self.ft[i], pr)


class _RayGrid:
    """Rays bucketed on the plane perpendicular to their (shared) direction -> candidate lists per bound."""

    def __init__(self, origins, direction):
        d = np.asarray(direction, float) / np.linalg.norm(direction)
        a = np.array([1.0, 0, 0]) if abs(d[0]) < 0.9 else np.array([0, 1.0, 0])
        e1 = np.cross(d, a)
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(d, e1)
        self.e1, self.e2 = e1, e2
        u, v = origins @ e1, origins @ e2
        self.u0, self.v0 = u.min(), v.min()
        ext = max(u.max() - self.u0, v.max() - self.v0, 1e-6)
        self.cell = ext / 64.0 + 1e-9
        iu = ((u - self.u0) / self.cell).astype(int)
        iv = ((v - self.v0) / self.cell).astype(int)
        self.nu, self.nv = iu.max() + 1, iv.max() + 1
        key = iv * self.nu + iu
        self.order = np.argsort(key, kind="stable")
        self.starts = np.searchsorted(key[self.order], np.arange(self.nu * self.nv + 1))

    def query(self, c, rho):
        cu, cv = c @ self.e1, c @ self.e2
        iu0 = max(int(math.floor((cu - rho - self.u0) / self.cell)), 0)
        iu1 = min(int(math.floor((cu + rho - self.u0) / self.cell)), self.nu - 1)
        iv0 = max(int(math.floor((cv - rho - self.v0) / self.cell)), 0)
        iv1 = min(int(math.floor((cv + rho - self.v0) / self.cell)), self.nv - 1)
        if iu0 > iu1 or iv0 > iv1:
            return np.zeros(0, int)
        segs = [self.order[self.starts[r * self.nu + iu0]:self.starts[r * self.nu + iu1 + 1]] for r in range(iv0, iv1 + 1)]
        out = np.concatenate(segs)
        return np.sort(out)


def _slab(ol, dl, lo, hi):
    with np.errstate(divide="ignore", invalid="ignore"):
        zero = np.abs(dl) < 1e-12
        inv = np.where(zero, 0.0, 1.0 / np.where(zero, 1.0, dl))
        t1 = (lo - ol) * inv
        t2 = (hi - ol) * inv
        inside = (ol >= lo) & (ol <= hi)
        tmin = np.where(zero, np.where(inside, -np.inf, np.inf), np.minimum(t1, t2))
        tmax = np.where(zero, np.where(inside, np.inf, -np.inf), np.maximum(t1, t2))
    return tmin.max(-1), tmax.min(-1)


def _trace(f, o, d, t0, t1):
    """Fixed-step sphere tracing. f(idx, points) -> distance bound. Returns (hit, t)."""
    n = len(t0)
    t = t0.copy()
    hit = np.zeros(n, bool)
    act = np.arange(n)
    for _ in range(STEPS):
        if not act.size:
            break
        dist = f(act, o[act] + t[act, None] * d[act])
        conv = dist < EPS
        hit[act[conv]] = True
        t[act] += np.where(conv, np.maximum(dist, 0.0), dist * RELAX)
        act = act[~conv]
        act = act[t[act] <= t1[act]]
    if act.size:                                  # grazing rays that used every step: accept if close
        dist = f(act, o[act] + t[act, None] * d[act])
        hit[act[dist < 10 * EPS]] = True
    return hit & (t <= t1 + EPS), t


def _batch_pairs(C, kind, grid, origins, direction, tlimit, tmin, ray_ok=None, skip_groups=None):
    """(ray, part, o_local, d_local, t0, t1) for every ray whose path enters a part's bounding box."""
    R, Pi, OL, DL, T0, T1 = [], [], [], [], [], []
    for i in C.batch[kind]:
        cand = grid.query(C.center[i], C.radius[i])
        if ray_ok is not None and cand.size:
            cand = cand[ray_ok[cand]]
        if skip_groups is not None and cand.size:
            cand = cand[skip_groups[cand] != C.prims[i]["group"]]
        if not cand.size:
            continue
        ol = origins[cand] @ C.Fi[i].T + C.ft[i]
        dl = C.Fi[i] @ direction
        ta, tb = _slab(ol, dl, C.lo[i], C.hi[i])
        ta = np.maximum(ta, tmin)
        tb = np.minimum(tb, tlimit[cand])
        keep = tb > ta
        if not keep.any():
            continue
        R.append(cand[keep]); Pi.append(np.full(int(keep.sum()), i)); OL.append(ol[keep])
        DL.append(np.broadcast_to(dl, (int(keep.sum()), 3))); T0.append(ta[keep]); T1.append(tb[keep])
    if not R:
        return None
    return (np.concatenate(R), np.concatenate(Pi), np.concatenate(OL), np.concatenate(DL),
            np.concatenate(T0), np.concatenate(T1))


def _batch_trace(C, kind, pairs):
    r, pid, ol, dl, t0, t1 = pairs
    st = C.stack[kind]
    pos = st["_pos"][pid]
    prm = {k: st[k][pos] for k in PARAM_KEYS[kind]}
    sv = C.sv[pid]
    fn = SDF[kind]

    def f(act, p):
        return fn(p, {k: v[act] for k, v in prm.items()}) * sv[act]

    hit, t = _trace(f, ol, dl, t0, t1)
    # legacy clip semantics: a clipped surface point is simply not there
    for i in np.unique(pid[hit]):
        pr = C.prims[i]
        if pr.get("clip_all") or pr.get("clip_any"):
            m = hit & (pid == i)
            loc = ol[m] + t[m, None] * dl[m]
            ok = _clip_ok(loc, pr)
            hit[np.nonzero(m)[0][~ok]] = False
    return hit, t, pos, prm


def _first_per_ray(r, t, pid):
    order = np.lexsort((pid, t, r))
    r, t, pid = r[order], t[order], pid[order]
    first = np.ones(len(r), bool)
    first[1:] = r[1:] != r[:-1]
    return order[first]


def _ellipsoid_hits(C, i, origins, direction, cand):
    o = origins[cand] @ C.Fi[i].T + C.ft[i]
    d = C.Fi[i] @ direction
    a = d @ d
    b = o @ d
    c = np.einsum("ij,ij->i", o, o) - 1.0
    disc = b * b - a * c
    hit = disc > 0
    s = np.sqrt(np.where(hit, disc, 0))
    return o, d, a, b, s, hit


# ------------------------------------------------------------------ public API (same as render.raycast/occluded)
def raycast(prims, origins, direction):
    n = origins.shape[0]
    tbest = np.full(n, np.inf)
    ibest = np.full(n, -1, int)
    nbest = np.zeros((n, 3))
    if not prims:
        return tbest, ibest, nbest
    C = _Compiled(prims)
    grid = _RayGrid(origins, direction)
    # 1) analytic ellipsoids (legacy math)
    for i in C.ell:
        cand = grid.query(C.center[i], C.radius[i])
        if not cand.size:
            continue
        o, d, a, b, s, hit = _ellipsoid_hits(C, i, origins, direction, cand)
        if not hit.any():
            continue
        t0 = (-b - s) / a
        p0 = o + t0[:, None] * d
        ok = hit & _clip_ok(p0, C.prims[i])
        better = ok & (t0 < tbest[cand])
        if better.any():
            sel = cand[better]
            tbest[sel] = t0[better]
            ibest[sel] = i
            nl = p0[better] @ C.Fi[i]
            nbest[sel] = nl / np.linalg.norm(nl, axis=1, keepdims=True)
    # 2) batched traced singletons
    for kind in SDF:
        if not C.batch[kind]:
            continue
        pairs = _batch_pairs(C, kind, grid, origins, direction, tbest, -np.inf)
        if pairs is None:
            continue
        r, pid, ol, dl, _, _ = pairs
        hit, t, pos, prm = _batch_trace(C, kind, pairs)
        if not hit.any():
            continue
        hs = np.nonzero(hit)[0]
        w = hs[_first_per_ray(r[hs], t[hs], pid[hs])]
        better = t[w] < tbest[r[w]]
        w = w[better]
        if not w.size:
            continue
        tbest[r[w]] = t[w]
        ibest[r[w]] = pid[w]
        pl = ol[w] + t[w, None] * dl[w]
        P = {k: v[w] for k, v in prm.items()}
        fn = SDF[kind]
        if kind == "seg" and SMOOTH_JOINTS:
            # shading normal from the strand smooth-min'd with its neighbour segments: no ring at every joint
            st_ = C.stack[kind]
            pw_, nx_ = C.prev[pid[w]], C.next[pid[w]]
            Pp = {k: st_[k][st_["_pos"][np.where(pw_ >= 0, pw_, pid[w])]] for k in PARAM_KEYS[kind]}
            Pn = {k: st_[k][st_["_pos"][np.where(nx_ >= 0, nx_, pid[w])]] for k in PARAM_KEYS[kind]}
            kp, kn = 0.6 * P["ra"], 0.6 * P["rb"]

            def fn(q, P_, Pp=Pp, Pn=Pn, kp=kp, kn=kn):
                d = _sd_seg(q, P_)
                for Q, k in ((Pp, kp), (Pn, kn)):
                    dq = _sd_seg(q, Q)
                    h = np.maximum(k - np.abs(d - dq), 0.0) / k
                    d = np.minimum(d, dq) - h * h * k * 0.25
                return d
        g = np.zeros((len(w), 3))
        hl = FD_H / C.sv[pid[w]]
        for ax in range(3):
            e = np.zeros((len(w), 3))
            e[:, ax] = hl
            g[:, ax] = fn(pl + e, P) - fn(pl - e, P)
        nw = np.einsum("nij,ni->nj", C.Fi[pid[w]], g)
        nbest[r[w]] = nw / np.maximum(np.linalg.norm(nw, axis=1, keepdims=True), 1e-12)
    # 3) blend / CSG sets
    for st in C.sets:
        cand, t0, t1 = _set_interval(C, st, grid, origins, direction, -np.inf)
        if cand is None:
            continue
        t1 = np.minimum(t1, tbest[cand])
        keep = t1 > t0
        cand, t0, t1 = cand[keep], t0[keep], t1[keep]
        if not cand.size:
            continue
        O, Dd = origins[cand], np.broadcast_to(direction, (len(cand), 3))
        hit, t = _trace(lambda act, p: C.set_sdf(st, p)[0], O, Dd, t0, t1)
        hs = np.nonzero(hit)[0]
        if not hs.size:
            continue
        pw = O[hs] + t[hs, None] * direction
        _, mem = C.set_sdf(st, pw)
        ok = np.ones(len(hs), bool)
        for i in np.unique(mem):
            m = mem == i
            ok[m] = C.clip_ok_world(i, pw[m])
        hs, pw, mem = hs[ok], pw[ok], mem[ok]
        better = t[hs] < tbest[cand[hs]]
        hs, pw, mem = hs[better], pw[better], mem[better]
        if not hs.size:
            continue
        sel = cand[hs]
        tbest[sel] = t[hs]
        ibest[sel] = mem
        g = np.zeros((len(hs), 3))
        for ax in range(3):
            e = np.zeros(3)
            e[ax] = FD_H
            g[:, ax] = C.set_sdf(st, pw + e)[0] - C.set_sdf(st, pw - e)[0]
        nbest[sel] = g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-12)
    hitm = ibest >= 0
    ibest[hitm] = C.rep_of[ibest[hitm]]
    return tbest, ibest, nbest


def _set_interval(C, st, grid, origins, direction, tmin, ray_ok=None):
    uni = st[0]
    cands = [grid.query(C.center[i], C.radius[i]) for i in uni]
    cand = np.unique(np.concatenate(cands)) if cands else np.zeros(0, int)
    if ray_ok is not None and cand.size:
        cand = cand[ray_ok[cand]]
    if not cand.size:
        return None, None, None
    t0 = np.full(len(cand), np.inf)
    t1 = np.full(len(cand), -np.inf)
    for i in uni:
        ol = origins[cand] @ C.Fi[i].T + C.ft[i]
        ta, tb = _slab(ol, C.Fi[i] @ direction, C.lo[i], C.hi[i])
        v = tb > np.maximum(ta, tmin)
        t0 = np.where(v, np.minimum(t0, np.maximum(ta, tmin)), t0)
        t1 = np.where(v, np.maximum(t1, tb), t1)
    keep = t1 > t0
    return cand[keep], t0[keep], t1[keep]


def occluded(prims, origins, direction, skip_groups):
    """Shadow rays; a part never shadows its own group (handled by N.L), as in render.occluded."""
    n = origins.shape[0]
    occ = np.zeros(n, bool)
    if not prims or not n:
        return occ
    C = _Compiled(prims)
    grid = _RayGrid(origins, direction)
    for i in C.ell:
        cand = grid.query(C.center[i], C.radius[i])
        if not cand.size:
            continue
        o, d, a, b, s, hit = _ellipsoid_hits(C, i, origins, direction, cand)
        hit &= skip_groups[cand] != C.prims[i]["group"]
        if not hit.any():
            continue
        for t in ((-b - s) / a, (-b + s) / a):
            p = o + t[:, None] * d
            occ[cand] |= hit & (t > SHADOW_T0) & _clip_ok(p, C.prims[i])
    inf = np.full(n, np.inf)
    for kind in SDF:
        if not C.batch[kind]:
            continue
        pairs = _batch_pairs(C, kind, grid, origins, direction, inf, SHADOW_T0, ray_ok=~occ, skip_groups=skip_groups)
        if pairs is None:
            continue
        hit, _, _, _ = _batch_trace(C, kind, pairs)
        occ[pairs[0][hit]] = True
    for st in C.sets:
        grp = C.prims[st[0][0]]["group"] if st[0] else None
        cand, t0, t1 = _set_interval(C, st, grid, origins, direction, SHADOW_T0, ray_ok=~occ)
        if cand is None:
            continue
        keep = skip_groups[cand] != grp
        cand, t0, t1 = cand[keep], t0[keep], t1[keep]
        if not cand.size:
            continue
        O, Dd = origins[cand], np.broadcast_to(direction, (len(cand), 3))
        hit, t = _trace(lambda act, p: C.set_sdf(st, p)[0], O, Dd, t0, t1)
        hs = np.nonzero(hit)[0]
        if hs.size:
            pw = O[hs] + t[hs, None] * direction
            _, mem = C.set_sdf(st, pw)
            ok = np.ones(len(hs), bool)
            for i in np.unique(mem):
                m = mem == i
                ok[m] = C.clip_ok_world(i, pw[m])
            occ[cand[hs[ok]]] = True
    return occ


def sdf_units(C):
    """Independent hard-union units of a compiled part list: ("set", st) or ("part", i), with a world bound sphere."""
    units, in_set = [], set()
    for st in C.sets:
        in_set |= set(st[0]) | set(st[1]) | set(st[2])
        c = np.mean([C.center[i] for i in st[0]], 0)
        r = max(np.linalg.norm(C.center[i] - c) + C.radius[i] for i in st[0])
        units.append((("set", st), c, r))
    for i, pr in enumerate(C.prims):
        if i not in in_set and pr.get("op", "union") == "union":
            units.append((("part", i), C.center[i], C.radius[i]))
    return units


def unit_sdf(C, unit, pts):
    """(distance, part index) of one unit at world points; clip planes act as half-space intersections."""
    kind, v = unit
    if kind == "set":
        return C.set_sdf(v, pts)
    i = v
    di = C.part_sdf_world(i, pts)
    pr = C.prims[i]
    if pr.get("clip_all") or pr.get("clip_any"):
        q = pts @ C.Fi[i].T + C.ft[i]
        s_ = C.sv[i]
        for nx, ny, nz, c0 in pr.get("clip_all", []):
            di = np.maximum(di, (c0 - (q[:, 0] * nx + q[:, 1] * ny + q[:, 2] * nz)) * s_)
        if pr.get("clip_any"):
            m = np.full(len(pts), np.inf)
            for nx, ny, nz, c0 in pr["clip_any"]:
                m = np.minimum(m, (c0 - (q[:, 0] * nx + q[:, 1] * ny + q[:, 2] * nz)) * s_)
            di = np.maximum(di, m)
    return di, np.full(len(pts), i)


def scene_sdf(prims, pts, C=None):
    """Union SDF of a posed part list at world points. Returns (distance, part index of the nearest surface)."""
    C = C or _Compiled(prims)
    d = np.full(len(pts), np.inf)
    arg = np.full(len(pts), -1, int)
    for unit, _, _ in sdf_units(C):
        dd, a = unit_sdf(C, unit, pts)
        better = dd < d
        d[better], arg[better] = dd[better], a[better]
    return d, arg


# ------------------------------------------------------------------ posing
def _vec(v):
    return np.asarray(v, float)


def _seg_params(a, b, ra, rb, flat=1.0, n2=None, capped=False, n2b=None, flatb=None):
    """Tapered segment. Flattening axis n2 (at a) -> n2b (at b), orthogonalised against the segment axis;
    consecutive segments sharing the joint axis give seamless tubes."""
    a, b = _vec(a), _vec(b)
    u = (b - a) / max(np.linalg.norm(b - a), 1e-9)

    def ortho(n):
        if n is None:
            return None
        n = _vec(n) - (_vec(n) @ u) * u
        nn = np.linalg.norm(n)
        return n / nn if nn > 1e-9 else None
    na = ortho(n2)
    nb = ortho(n2b if n2b is not None else n2)
    flatb = flat if flatb is None else flatb
    if na is None or nb is None or min(flat, flatb) >= 0.999:
        na = nb = np.array([1.0, 0, 0])
        flat = flatb = 1.0
    L = float(np.linalg.norm(b - a))
    ra, rb = float(ra), max(float(rb), 1e-3)
    if abs(ra - rb) > 0.95 * L:           # one end sphere would swallow the other: keep a valid round cone
        m = (ra + rb) / 2
        ra, rb = m + np.sign(ra - rb) * 0.475 * L, m - np.sign(ra - rb) * 0.475 * L
    return {"a": a[None], "b": b[None], "ra": np.array([ra]), "rb": np.array([max(rb, 1e-3)]),
            "n2": na[None], "n2b": nb[None], "flat": np.array([float(flat)]),
            "flatb": np.array([float(flatb)]), "capped": np.array([bool(capped)])}


def _point_normals(pr, pts):
    """Per-point flattening axes for a tube (flat_n constant, or radial from flat_c), made normal to the tangent."""
    pts = [_vec(p) for p in pts]
    out = []
    for k, p in enumerate(pts):
        t = pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]
        t = t / max(np.linalg.norm(t), 1e-9)
        n = _vec(pr["flat_n"]) if "flat_n" in pr else (p - _vec(pr["flat_c"]) if "flat_c" in pr else np.array([0, 0, 1.0]))
        n = n - (n @ t) * t
        out.append(n / max(np.linalg.norm(n), 1e-9))
    return out


def _flat_dir(pr, a, b):
    if "flat_n" in pr:
        return _vec(pr["flat_n"])
    if "flat_c" in pr:
        return (_vec(a) + _vec(b)) / 2 - _vec(pr["flat_c"])
    return np.array([0.0, 0.0, 1.0])


def _base(sp):
    b = sp.get("blend") or {}
    return {"name": sp["name"], "material": sp["material"], "group": sp.get("group", sp.get("bone", "head")),
            "set": b.get("set"), "k": float(b.get("k", 0.0)), "op": sp.get("op", "union"),
            "clip_all": sp.get("clip_all", []), "clip_any": sp.get("clip_any", []),
            # "vote": parts sharing a key act as one part for the pixel pass (an explicit key lets a converted legacy
            # ellipsoid, e.g. the hair cap under the HD clumps, join the clumps so their seams don't blur the shading)
            "vote": sp.get("vote") or (None if sp.get("legacy") else f'{sp["material"]}|{sp.get("group", "head")}')}


def _bone_matrix(sp, worlds):
    if "bones" in sp:
        return sum(float(w) * worlds[b] for b, w in sp["bones"])
    return worlds[sp["bone"]]


def _pose_static(sp, worlds, face_m, lods=("all", "ref")):
    W = _bone_matrix(sp, worlds)
    shape = sp["shape"]
    base = _base(sp)
    if shape == "ellipsoid":
        # identical expression to rig.body_primitives so converted parts keep the legacy matrix bits
        M = W @ translate(*sp["center"]) @ euler(*sp.get("rot", [0, 0, 0])) @ scale(*sp["radii"])
        return [dict(base, kind="ell", M=face_m @ M, params={})]
    F = W @ translate(*sp.get("center", [0, 0, 0])) @ euler(*sp.get("rot", [0, 0, 0]))
    if sp.get("scale"):
        F = F @ scale(*sp["scale"])
    F = face_m @ F
    pr = sp.get("params", {})
    out = []
    det = sp.get("detail") if sp.get("detail", {}).get("lod", "all") in lods else None
    if shape in ("capsule", "rcone", "cone"):
        ra = pr.get("ra", pr.get("r"))
        rb = pr.get("rb", pr.get("r"))
        prm = _seg_params(pr["a"], pr["b"], ra, rb, pr.get("flat", 1.0), _flat_dir(pr, pr["a"], pr["b"]),
                          capped=shape == "cone")
        out.append(dict(base, kind="seg", M=F, params=prm))
    elif shape == "tube":
        pts, rr = pr["pts"], pr["r"]
        nrm = _point_normals(pr, pts)
        for k in range(len(pts) - 1):
            prm = _seg_params(pts[k], pts[k + 1], rr[k], rr[k + 1], pr.get("flat", 1.0), nrm[k],
                              capped=bool(pr.get("cut_end")) and k == len(pts) - 2, n2b=nrm[k + 1])
            out.append(dict(base, name=f'{sp["name"]}_{k}', kind="seg", M=F, params=prm, strand=sp["name"]))
    elif shape == "rbox":
        out.append(dict(base, kind="rbox", M=F, params={"b": _vec(pr["b"])[None], "r": np.array([float(pr.get("r", 0.0))])}))
    elif shape == "torus":
        R = pr["R"] if isinstance(pr["R"], (list, tuple)) else [pr["R"], pr["R"]]
        out.append(dict(base, kind="torus", M=F, params={
            "R": _vec(R)[None], "r": np.array([float(pr["r"])]), "w": np.array([float(pr.get("w", pr["r"]))]),
            "taper": np.array([float(pr.get("taper", 0.0))]), "round": np.array([float(pr.get("round", 0.0))])}))
    elif shape == "sweep":
        out.append(dict(base, kind="sweep", M=F, params=sweep_from_spec(pr)))
    else:
        raise ValueError(f"unknown shape {shape!r} in part {sp['name']}")
    if det:
        for o in out:
            P = o["params"]
            size = float(np.max(P["ra"])) if o["kind"] == "seg" else (
                float(np.min(P["R"])) if o["kind"] == "torus" else (
                    float(np.max(P["w"])) if o["kind"] == "sweep" else float(np.min(P["b"]))))
            P.update(_detail_params(det, size))
    return out


def _chain_frames(pts, body_c):
    """Per-point tangent T, sideways X and outward Z (same convention as rig.chain_primitives beads)."""
    n = len(pts)
    T = np.zeros((n, 3))
    for k in range(n):
        a, b = pts[max(k - 1, 0)], pts[min(k + 1, n - 1)]
        T[k] = (b - a) / max(np.linalg.norm(b - a), 1e-9)
    X, Z = np.zeros((n, 3)), np.zeros((n, 3))
    for k in range(n):
        out = pts[k] - body_c
        out[1] = 0
        hint = out if np.linalg.norm(out) > 1e-6 else np.array([0, 0, 1.0])
        if abs(np.dot(hint / np.linalg.norm(hint), T[k])) > 0.95:
            hint = np.array([1.0, 0, 0])
        x = np.cross(T[k], hint)
        X[k] = x / np.linalg.norm(x)
        Z[k] = np.cross(X[k], T[k])
    return T, X, Z


def _pose_sweep(sp, chain, pts, body_c, face_m, subdiv, clip=None, worlds=None):
    """Chain-driven swept clumps along the Catmull-Rom resampled chain (tapered tubes, sharp or forked tips).
    "by_clip": {clip: {sweep keys}} overrides sweep keys for one clip (e.g. a fuller tip in the run swing)."""
    from .rig import _subdivide
    sw = sp.get("sweep", {})
    if clip in sw.get("by_clip", {}):
        sw = dict(sw, **sw["by_clip"][clip])
    if sw.get("mode") == "ribbon":
        return _pose_ribbons(sp, sw, chain, pts, body_c, face_m, worlds)
    widths = chain.get("widths", [1.0])
    pts = np.asarray(pts, float)
    if subdiv > 1 and len(pts) >= 3:
        pts, ws = _subdivide(pts, widths, subdiv)
        ws = list(ws) + [widths[-1]]
    else:
        ws = [widths[min(k, len(widths) - 1)] for k in range(len(pts))]
    ws = np.asarray(ws, float) * sw.get("width_scale", 1.0)
    if sw.get("extend"):              # opt-in: continue past the last chain point along its tangent (tapered tip length)
        tq = pts[-1] - pts[-2]
        tq = tq / max(np.linalg.norm(tq), 1e-9)
        n_ext = int(sw.get("extend_steps", 2))
        ext = [pts[-1] + tq * float(sw["extend"]) * (k + 1) / n_ext for k in range(n_ext)]
        pts = np.vstack([pts] + [e[None] for e in ext])
        ws = np.concatenate([ws, [ws[-1] * (1 - 0.35 * (k + 1)) for k in range(n_ext)]])
    thick = float(sw.get("thickness", chain.get("thickness", 1.0)))
    ez = np.minimum(thick, ws)
    seglen = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seglen)])
    s = s / max(s[-1], 1e-9)
    T, X, Z = _chain_frames(pts, body_c)
    # chain parts keep the chain's group (as legacy beads do) so body-only QA bboxes still exclude them
    base = dict(_base(sp), group=chain.get("group", chain["name"]))
    base["vote"] = f'{sp["material"]}|{base["group"]}'

    out = []
    tip_r = float(sw.get("tip_r", 0.04))
    nc = int(sw.get("clumps", 1))
    if nc <= 1:                                     # one flat ribbon (bow tails), optional forked V-cut tip
        rr, flat = ws, np.clip(ez / np.maximum(ws, 1e-6), 0.05, 1.0)
        tipk = sw.get("tip", "sharp")
        fork = tipk == "fork"
        last = len(pts) - (2 if fork else 1)
        cut = fork or tipk in ("cut", "fringe")
        for k in range(last if not sw.get("only_fringe") else 0):
            prm = _seg_params(pts[k], pts[k + 1], rr[k], rr[k + 1], flat[k], Z[k],
                              capped=cut and k == last - 1, n2b=Z[k + 1], flatb=flat[k + 1])
            out.append(dict(base, name=f'{sp["name"]}_{k}', kind="seg", M=face_m, params=prm, strand=sp["name"]))
        if tipk == "fringe":                      # flat-cut end with a row of fringe capsules
            nf = int(sw.get("fringe", 6))
            fl, fr = float(sw.get("fringe_len", 1.2)), float(sw.get("fringe_r", 0.3))
            Pe, Te = pts[-1], T[-1]
            for f in range(nf):
                u = -0.8 + 1.6 * f / max(nf - 1, 1)
                a = Pe + u * rr[-1] * X[-1] - Te * fr
                b = a + Te * fl + u * 0.15 * fl * X[-1]
                prm = _seg_params(a, b, fr, fr * 0.8)
                out.append(dict(base, name=f'{sp["name"]}_fringe{f}', kind="seg", M=face_m, params=prm))
        if fork:
            P0, P1 = pts[-2], pts[-1]
            w0 = rr[-2]
            depth = float(sw.get("fork_depth", 0.6))
            for sgn in (-1, 1):
                a = P0 + sgn * 0.45 * w0 * X[-2]
                b = P1 + sgn * 0.75 * w0 * X[-1] + T[-1] * depth * w0 * 0.3
                prm = _seg_params(a, b, 0.55 * w0, tip_r, flat[-2], Z[-2], n2b=Z[-1])
                out.append(dict(base, name=f'{sp["name"]}_fork{sgn:+d}', kind="seg", M=face_m, params=prm))
        return out
    spread = float(sw.get("spread", 0.45))
    cr = float(sw.get("clump_r", 1.0 - spread + 0.05))
    twist = math.radians(float(sw.get("twist", 0.0)))
    taper_len = float(sw.get("taper_len", 0.35))
    side_end = float(sw.get("side_end", 0.9))
    ntips = int(sw.get("tips", 1))
    k_mid = int(np.argmax(ws))
    for j in range(nc):
        th0 = 2 * math.pi * j / nc + math.radians(float(sw.get("phase", 90.0)))
        th_end = th0 + twist
        side = math.cos(th_end)
        tip = 0
        if ntips >= 3 and abs(side) > 0.5:
            tip = 1 if side > 0 else -1
        end = 1.0 if tip == 0 else side_end
        keep = np.nonzero(s <= end + 1e-9)[0]
        if len(keep) < 2:
            continue
        cpts, crad = [], []
        root_len = float(sw.get("root_len", 0.0))
        for k in keep:
            th = th0 + twist * s[k]
            g = 1.0 if root_len <= 0 else min(s[k] / root_len, 1.0)
            g = 0.35 + 0.65 * g * g * (3 - 2 * g)          # clumps gathered at the tie, fanning out below it
            off = g * spread * (ws[k] * math.cos(th) * X[k] + ez[k] * math.sin(th) * Z[k])
            u = min(max((s[k] - (end - taper_len)) / taper_len, 0.0), 1.0)
            u = u * u * (3 - 2 * u)
            tip_off = tip * 0.42 * ws[k_mid] * (1 - s[k] * 0.5) * X[k]
            c = pts[k] + off * (1 - u) + tip_off * u
            cpts.append(c)
            crad.append(cr * ws[k] * (1 - u) + tip_r * u)
        cpts, crad = np.array(cpts), np.array(crad)
        crad[-1] = tip_r
        flat = np.clip(ez[keep] / np.maximum(ws[keep], 1e-6), 0.2, 1.0)
        for k in range(len(cpts) - 1):
            prm = _seg_params(cpts[k], cpts[k + 1], crad[k], crad[k + 1], flat[k],
                              Z[keep[k]], n2b=Z[keep[k + 1]], flatb=flat[k + 1])
            out.append(dict(base, name=f'{sp["name"]}_c{j}_{k}', kind="seg", M=face_m, params=prm,
                            strand=f'{sp["name"]}_c{j}'))
    return out


def _pose_ribbons(sp, sw, chain, pts, body_c, face_m, worlds=None):
    """r21 chain sweep "mode": "ribbon": each strand is one smooth swept sheet ("sweep" kind) along the Catmull-Rom
    resampled chain, offset in the chain frame (X sideways, Z outward from the body):
      sweep: {"mode": "ribbon", "n": samples, "extend": units past the chain end, "strands": [
        {"dx": [profile], "dz": [profile], "w": [profile], "t": [profile], "lens", "curl", "vcut", "cap1", "capr",
         "nz_tilt": [profile] (rotates the thickness axis about the tangent toward X, radians)}]}
    Profiles are sampled over the arclength 0..1 (root -> tip), in world units.
    "root_to": [bone, [x, y, z]] prepends a bone-space point (e.g. sheets fanning out from the ponytail root)."""
    pts = np.asarray(pts, float)
    if sw.get("root_to") and worlds is not None:
        b, q = sw["root_to"]
        m = worlds[b]
        pts = np.vstack([(m[:3, :3] @ np.asarray(q, float) + m[:3, 3])[None], pts])
    if sw.get("extend"):
        tq = pts[-1] - pts[-2]
        tq = tq / max(np.linalg.norm(tq), 1e-9)
        pts = np.vstack([pts, pts[-1] + tq * float(sw["extend"])])
    if sw.get("root_pull"):
        # pull the first point back along the chain (root tucked under the hair cap / bow knot)
        t0 = pts[1] - pts[0]
        t0 = t0 / max(np.linalg.norm(t0), 1e-9)
        pts = np.vstack([pts[0] - t0 * float(sw["root_pull"]), pts[1:]])
    n = int(sw.get("n", 24))
    C, _ = _catmull(pts, n)
    T, X, Z = _chain_frames(C, body_c)
    seg = np.linalg.norm(np.diff(C, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)]) / max(seg.sum(), 1e-9)
    base = dict(_base(sp), group=chain.get("group", chain["name"]))
    base["vote"] = f'{sp["material"]}|{base["group"]}'
    out = []
    for k, st in enumerate(sw.get("strands", [{}])):
        dx, dz = _profile(st.get("dx", [0.0]), s), _profile(st.get("dz", [0.0]), s)
        Ck = C + dx[:, None] * X + dz[:, None] * Z
        tilt = _profile(st.get("nz_tilt", [0.0]), s)
        N = np.cos(tilt)[:, None] * Z + np.sin(tilt)[:, None] * X
        prm = sweep_params(Ck, N, _profile(st.get("w", [1.0]), s), _profile(st.get("t", [0.5]), s),
                           st.get("lens", 0.0), st.get("curl", 0.0), st.get("cap0", 1), st.get("cap1", 1),
                           st.get("vcut", 0.0), st.get("capr", 0.6))
        out.append(dict(base, name=f'{sp["name"]}_r{k}', kind="sweep", M=face_m, params=prm))
    return out


def _ell_from_legacy(p, M):
    return {"name": p["name"], "material": p["material"], "group": p["group"], "kind": "ell", "M": M, "params": {},
            "set": None, "k": 0.0, "op": "union", "clip_all": p.get("clip_all", []), "clip_any": p.get("clip_any", []),
            "vote": None}


def pose_parts(char, worlds, chain_pts, body_c, face_m, lod="all", subdiv=1, clip=None):
    """Posed HD part list (world space, facing applied) for one frame."""
    from .rig import chain_primitives
    lods = ("all",) if lod == "all" else ("all", "ref")
    out, sweeps = [], {}
    for sp in char["parts"]:
        if sp.get("lod", "all") not in lods:
            continue
        if "chain" in sp:
            sweeps.setdefault(sp["chain"], []).append(sp)
            continue
        if sp.get("follow"):
            out += _pose_static(sp, _follow_worlds(sp, char, worlds, chain_pts, clip), face_m, lods)
            continue
        out += _pose_static(sp, worlds, face_m, lods)
    for c in char.get("chains", []):
        pts = chain_pts[c["name"]]
        if c["name"] in sweeps:
            for sp in sweeps[c["name"]]:
                out += _pose_sweep(sp, c, pts, body_c, face_m, subdiv, clip, worlds=worlds)
            tip = c.get("tip")
            if tip:
                r = tip["radius"]
                out.append(_ell_from_legacy({"name": c["name"] + "_tip", "material": tip["material"], "group": c["name"]},
                                            face_m @ (translate(*pts[-1]) @ scale(r, r, r))))
        else:
            for p in chain_primitives(c, pts, body_c, subdiv=subdiv):
                out.append(_ell_from_legacy(p, face_m @ p["M"]))
    return out


def _follow_worlds(sp, char, worlds, chain_pts, clip=None):
    """"follow": {"chain", "gain", "gain_by_clip": {clip: g}, "max_drop"}: a rigid part (e.g. a bow loop) rides a
    spring chain. Its bone frame is rotated about the chain anchor by the chain's deflection from its rest direction
    (times gain) -> bounce and lag. max_drop limits how far the direction may sink below rest (sine, bone-up axis),
    so a lagging loop never drops behind the crown."""
    fo = sp["follow"]
    gain = float(fo.get("gain_by_clip", {}).get(clip, fo.get("gain", 1.0)))
    c = next(c for c in char["chains"] if c["name"] == fo["chain"])
    m = worlds[c["anchor_bone"]]
    a = m[:3, :3] @ np.asarray(c["anchor"], float) + m[:3, 3]
    r = m[:3, :3] @ np.asarray(c["rest_dir"], float)
    r /= np.linalg.norm(r)
    pts = chain_pts[c["name"]]
    u = np.asarray(pts[1], float) - np.asarray(pts[0], float)
    u /= max(np.linalg.norm(u), 1e-9)
    if "max_drop" in fo:
        up = m[:3, 1] / np.linalg.norm(m[:3, 1])
        lo = float(r @ up) - float(fo["max_drop"])
        if fo.get("drop_frame") == "world":
            # world-up clamp against the rest direction of an UPRIGHT head (yaw only): when the head pitches down in a
            # crouch the loops stay lifted instead of tipping behind the crown
            up = np.array([0.0, 1.0, 0.0])
            f = m[:3, 2] - (m[:3, 2] @ up) * up
            f /= max(np.linalg.norm(f), 1e-9)
            x = np.cross(up, f)
            rd = np.asarray(c["rest_dir"], float)
            rw = rd[0] * x + rd[1] * up + rd[2] * f
            rw /= np.linalg.norm(rw)
            lo = float(rw @ up) - float(fo["max_drop"])
        if float(u @ up) < lo:
            h = u - (u @ up) * up
            hn = np.linalg.norm(h)
            h = h / hn if hn > 1e-9 else r - (r @ up) * up
            h /= max(np.linalg.norm(h), 1e-9)
            u = h * math.sqrt(max(1 - lo * lo, 0.0)) + up * lo
    ax = np.cross(r, u)
    s_, c_ = np.linalg.norm(ax), float(np.clip(r @ u, -1, 1))
    ang = math.atan2(s_, c_) * gain
    if gain == 0.0:
        return worlds
    R = np.eye(4)
    if s_ > 1e-9:
        k = ax / s_
        K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
        R[:3, :3] = np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * (K @ K)
    M = translate(*a) @ R @ translate(*(-a)) @ worlds[sp["bone"]]
    return dict(worlds, **{sp["bone"]: M})


def legacy_to_parts(prims):
    """Already-posed legacy primitive dicts (props, fx) -> analytic ellipsoid parts."""
    return [_ell_from_legacy(p, p["M"]) for p in prims]


# ------------------------------------------------------------------ QA: sprite-LOD features must be >= 1 px
def feature_px(sp, chains, ppu):
    """Smallest visible extent (px) of an authored part spec at the sprite camera, or None if not applicable.
    Visible extent = the shape's width across its silhouette (not the flattened thickness of a lying clump)."""
    if sp.get("legacy"):
        return None
    pr = sp.get("params", {})
    sh = sp.get("shape")
    if "chain" in sp:
        sw = sp.get("sweep", {})
        c = next((c for c in chains if c["name"] == sp["chain"]), None)
        if c is None:
            return None
        if sw.get("mode") == "ribbon":
            w = 2 * min(max(st.get("w", [1.0])) for st in sw.get("strands", [{}]))
        elif sw.get("only_fringe") or sw.get("tip") == "fringe":
            w = 2 * float(sw.get("fringe_r", 0.3))
        elif int(sw.get("clumps", 1)) > 1:
            w = 2 * float(sw.get("clump_r", 0.55)) * max(c.get("widths", [1.0]))
        else:
            w = 2 * max(c.get("widths", [1.0]))
    elif sh == "ellipsoid":
        w = 2 * sorted(sp["radii"])[1]
    elif sh in ("capsule", "rcone", "cone"):
        w = 2 * max(pr.get("ra", pr.get("r", 0)), pr.get("rb", pr.get("r", 0)))
    elif sh == "tube":
        w = 2 * max(pr["r"])
    elif sh == "rbox":
        w = 2 * sorted(pr["b"])[1]
    elif sh == "torus":
        w = 2 * max(pr["r"], pr.get("w", pr["r"]))
    elif sh == "sweep":
        w = 2 * max(np.atleast_1d(pr["w"]).max(), np.atleast_1d(pr["t"]).max())
    else:
        return None
    if sp.get("scale"):
        w *= sorted(sp["scale"])[1]
    out = w * ppu
    det = sp.get("detail")
    if det and det.get("lod", "all") == "all":
        R = max(pr.get("ra", 0), pr.get("rb", 0), max(pr.get("R", [0])) if isinstance(pr.get("R"), list) else pr.get("R", 0))
        if R:
            out = min(out, 2 * math.pi * R / float(det.get("n", 8)) * ppu)      # one pleat / scallop period
    return out


def subpixel_features(char, ppu):
    """[(part name, px)] for lod 'all' parts (or lod 'all' details) smaller than 1 px."""
    bad = []
    for sp in char.get("parts", []):
        if sp.get("lod", "all") != "all":
            continue
        px = feature_px(sp, char.get("chains", []), ppu)
        if px is not None and px < 1.0:
            bad.append((sp["name"], round(px, 2)))
    return bad
