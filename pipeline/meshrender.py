"""Triangle-mesh renderer (numpy z-buffer) with the pipeline's orthographic iso Camera.

Used to compare external / alternative meshes (e.g. a Gemini-generated OBJ) with our SDF model exported by
meshexport.py, in the same camera, directions and palette:

    load_obj(path, up="y")                    -> {material: (T,3,3) triangles} in pipeline world space
    render_shaded(meshes, palette, yaw, ...)  -> RGB uint8 hi-res lambert render (palette ramp colours) + outline
    MeshTracer(meshes)                         -> drop-in `tracer` for render.render_pixels (sprite-scale pixelisation)
    render_sprite(meshes, palette, direction)  -> 48x64 palette-index sprite (render_pixels + despeckle + outline)

World space = pipeline convention: x right, y up (feet at y=0), +z toward the viewer for direction "S".
OBJs authored Z-up / facing -Y are converted with up="z".
"""
import numpy as np

from .mathutil import rot_y
from .render import Camera, DIRECTION_YAW, render_pixels, despeckle, add_outline

# external material names -> pipeline material (ramp) names. Ours already use pipeline names.
MAT_MAP = {"hair_1": "hair", "hair_2": "hair_hi", "teal": "scarf", "oat": "coat", "rust": "coat_trim",
           "tights": "pants", "white": "eye_white", "iris": "iris", "ink": "ink", "gold": "gold", "blush": "blush"}
# ramps for decal / extra materials the master palettes do not define
EXTRA_RAMPS = {"hair_hi": ["hair_1", "hair_2"], "iris": ["teal_0", "teal_1"], "ink": ["ink", "ink"], "eye_white": ["snow_3", "snow_3"],
               "gold": ["gold_0", "gold_1"], "blush": ["red_2", "red_2"], "belt": ["gold_0", "gold_1"], "other": ["mauve", "oat_1"]}
BG = (223, 234, 246)
LINE = (36, 22, 40)


def load_obj(path, up="y", height=None, map_names=True):
    """OBJ (v / f / usemtl, polygons fan-triangulated) -> {material: (T,3,3) float64}.
    up="z": source is Z-up facing -Y -> converted to y-up facing +z. height: rescale so max y == height, feet at 0."""
    V, faces = [], {}
    mat = "default"
    with open(path) as fh:
        for ln in fh:
            s = ln.split()
            if not s:
                continue
            if s[0] == "v":
                V.append([float(t) for t in s[1:4]])
            elif s[0] == "usemtl":
                mat = s[1]
            elif s[0] == "f":
                ids = [int(t.split("/")[0]) for t in s[1:]]
                ids = [i - 1 if i > 0 else len(V) + i for i in ids]
                lst = faces.setdefault(mat, [])
                for k in range(1, len(ids) - 1):
                    lst.append((ids[0], ids[k], ids[k + 1]))
    V = np.asarray(V, float)
    if up == "z":
        V = np.stack([V[:, 0], V[:, 2], -V[:, 1]], 1)
    lo = V[:, 1].min()
    V[:, 1] -= lo
    if height:
        V *= height / V[:, 1].max()
    out = {}
    for m, f in faces.items():
        name = MAT_MAP.get(m, m) if map_names else m
        T = V[np.asarray(f, int)]
        out[name] = np.concatenate([out[name], T]) if name in out else T
    return out


def ensure_ramps(palette, meshes):
    for m in meshes:
        if m not in palette.ramps:
            palette.ramps[m] = EXTRA_RAMPS.get(m, EXTRA_RAMPS["other"])


# ---------------------------------------------------------------- z-buffer core
def _zbuffer(P, Z, shape, keep="min", budget=3_000_000):
    """P: (T,3,2) triangle vertices in grid coords (cell (r, c) centre = (c + .5, r + .5)), Z: (T,3) depth.
    Returns (best depth (H,W), triangle id (H,W) or -1). keep='min' nearest smallest Z, 'max' largest Z."""
    H, W = shape
    best = np.full(H * W, np.inf if keep == "min" else -np.inf)
    bid = np.full(H * W, -1, np.int64)
    sgn = 1.0 if keep == "min" else -1.0
    x0 = np.clip(np.ceil(P[:, :, 0].min(1) - 0.5), 0, W).astype(np.int64)
    x1 = np.clip(np.floor(P[:, :, 0].max(1) - 0.5) + 1, 0, W).astype(np.int64)
    y0 = np.clip(np.ceil(P[:, :, 1].min(1) - 0.5), 0, H).astype(np.int64)
    y1 = np.clip(np.floor(P[:, :, 1].max(1) - 0.5) + 1, 0, H).astype(np.int64)
    w, h = np.maximum(x1 - x0, 0), np.maximum(y1 - y0, 0)
    n = w * h
    a, b, c = P[:, 0], P[:, 1], P[:, 2]
    area = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    valid = np.nonzero((n > 0) & (np.abs(area) > 1e-12))[0]
    cs = np.cumsum(n[valid])
    start = 0
    while start < len(valid):
        base = cs[start - 1] if start else 0
        stop = max(start + 1, int(np.searchsorted(cs, base + budget, side="right")))
        tid = valid[start:stop]
        start = stop
        cnt = n[tid]
        tri = np.repeat(tid, cnt)
        off = np.arange(cnt.sum()) - np.repeat(np.cumsum(cnt) - cnt, cnt)
        px = x0[tri] + off % w[tri]
        py = y0[tri] + off // w[tri]
        sx, sy = px + 0.5, py + 0.5
        A, B, C = a[tri], b[tri], c[tri]
        ar = area[tri]
        l0 = ((B[:, 0] - sx) * (C[:, 1] - sy) - (B[:, 1] - sy) * (C[:, 0] - sx)) / ar
        l1 = ((C[:, 0] - sx) * (A[:, 1] - sy) - (C[:, 1] - sy) * (A[:, 0] - sx)) / ar
        l2 = 1.0 - l0 - l1
        ins = (l0 >= -1e-9) & (l1 >= -1e-9) & (l2 >= -1e-9)
        if not ins.any():
            continue
        tri, px, py = tri[ins], px[ins], py[ins]
        z = (l0[ins] * Z[tri, 0] + l1[ins] * Z[tri, 1] + l2[ins] * Z[tri, 2]) * sgn
        cell = py * W + px
        o = np.lexsort((z, cell))
        cell, z, tri = cell[o], z[o], tri[o]
        first = np.ones(len(cell), bool)
        first[1:] = cell[1:] != cell[:-1]
        cell, z, tri = cell[first], z[first], tri[first]
        better = z < best[cell] * sgn
        best[cell[better]] = z[better] * sgn
        bid[cell[better]] = tri[better]
    return best.reshape(H, W), bid.reshape(H, W)


def _stack(meshes):
    mats = list(meshes)
    T = np.concatenate([meshes[m] for m in mats])
    mid = np.concatenate([np.full(len(meshes[m]), i) for i, m in enumerate(mats)])
    return mats, T, mid


def _normals(T):
    nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    return nrm / np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)


def posed(meshes, direction_or_yaw):
    """Rotate the S-facing model to an 8-way direction (same rot_y convention as frames.Scene)."""
    yaw = DIRECTION_YAW.get(direction_or_yaw, direction_or_yaw) if isinstance(direction_or_yaw, str) else direction_or_yaw
    R = rot_y(yaw)[:3, :3]
    return {m: T @ R.T for m, T in meshes.items()}


def raster(meshes, cam, size, pivot, ss=1):
    """-> dict(depth, mat (index into mats, -1 bg), normal (H,W,3), mats) at size*ss samples."""
    mats, T, mid = _stack(meshes)
    W, H = size
    k = cam.ppu * ss
    sx = (T @ cam.right) * k + pivot[0] * ss
    sy = (pivot[1] + 0.5) * ss - (T @ cam.up) * k
    P = np.stack([sx, sy], -1)
    Z = T @ cam.fwd
    depth, tid = _zbuffer(P, Z, (H * ss, W * ss))
    nrm = _normals(T)
    nrm[(nrm @ cam.to_cam) < 0] *= -1                    # two-sided: face the camera
    hit = tid >= 0
    N = np.zeros((H * ss, W * ss, 3))
    N[hit] = nrm[tid[hit]]
    M = np.where(hit, mid[np.maximum(tid, 0)], -1)
    return {"depth": depth, "mat": M, "normal": N, "mats": mats}


def _ramp_rgb(palette, m):
    ramp = palette.ramps.get(m) or EXTRA_RAMPS.get(m) or EXTRA_RAMPS["other"]
    return np.array([palette.rgb[palette.index[c]] for c in ramp], float)


def shade(buf, palette, cam, line=True, depth_jump=1.2):
    """Smooth lambert along each material's palette ramp (dark -> light), dark outline at material/depth breaks."""
    M, N, D = buf["mat"], buf["normal"], buf["depth"]
    H, W = M.shape
    img = np.empty((H, W, 3))
    img[:] = BG
    lam = N @ cam.light
    t = np.clip((lam + 0.35) / 1.2, 0, 1)
    for i, m in enumerate(buf["mats"]):
        sel = M == i
        if not sel.any():
            continue
        ramp = _ramp_rgb(palette, m)
        if len(ramp) == 1:
            ramp = np.stack([ramp[0] * 0.8, ramp[0]])
        f = t[sel] * (len(ramp) - 1)
        j = np.minimum(f.astype(int), len(ramp) - 2)
        u = (f - j)[:, None]
        img[sel] = ramp[j] * (1 - u) + ramp[j + 1] * u
    if line:
        e = np.zeros((H, W), bool)
        Df = np.where(M >= 0, D, 1e9)
        for dy, dx in ((0, 1), (1, 0)):
            a, b = (slice(0, H - dy), slice(0, W - dx)), (slice(dy, H), slice(dx, W))
            brk = (M[a] != M[b]) | (np.abs(Df[a] - Df[b]) > depth_jump)
            e[a] |= brk & (Df[a] <= Df[b])
            e[b] |= brk & (Df[b] < Df[a])
        img[e] = LINE
    return img.astype(np.uint8)


def render_shaded(meshes, palette, direction, size, pivot, ppu, elevation=16, ss=2, line=True):
    """Hi-res reference render (anti-aliased by ss box filter). `size` / `pivot` are in sprite pixels (ppu 1); the
    image is size * ppu. Returns RGB uint8 (H, W, 3)."""
    ensure_ramps(palette, meshes)
    cam = Camera(elevation, ppu)
    size = (int(round(size[0] * ppu)), int(round(size[1] * ppu)))
    pivot = (pivot[0] * ppu, (pivot[1] + 0.5) * ppu - 0.5)
    buf = raster(posed(meshes, direction), cam, size, pivot, ss)
    img = shade(buf, palette, cam, line=line, depth_jump=1.2 * ppu * ss / 8).astype(float)
    W, H = size
    return img.reshape(H, ss, W, ss, 3).mean((1, 3)).astype(np.uint8)


# ---------------------------------------------------------------- tracer for render.render_pixels
class MeshTracer:
    """Implements the `tracer` protocol of render.render_pixels (raycast / occluded over parallel rays) for a
    triangle mesh by rasterising along the ray direction on a fine grid (cell = `cell` world units).
    Primitive i == material i (group = material), so prims = tracer.prims()."""

    def __init__(self, meshes, cell=0.08):
        self.mats, self.T, self.mid = _stack(meshes)
        self.nrm = _normals(self.T)
        self.cell = cell

    def prims(self):
        return [{"name": m, "material": m, "group": m, "M": np.eye(4)} for m in self.mats]

    def _frame(self, direction):
        d = direction / np.linalg.norm(direction)
        a = np.array([0.0, 1.0, 0.0]) if abs(d[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
        e1 = np.cross(a, d)
        e1 /= np.linalg.norm(e1)
        return d, e1, np.cross(d, e1)

    def _grid(self, origins, direction, tri_mask=None, keep="min"):
        d, e1, e2 = self._frame(direction)
        T = self.T if tri_mask is None else self.T[tri_mask]
        u, v = T @ e1, T @ e2
        ou, ov = origins @ e1, origins @ e2
        lo = np.array([min(u.min(), ou.min()), min(v.min(), ov.min())]) - 2 * self.cell
        hi = np.array([max(u.max(), ou.max()), max(v.max(), ov.max())]) + 2 * self.cell
        W, H = (np.ceil((hi - lo) / self.cell).astype(int) + 1)
        P = np.stack([(u - lo[0]) / self.cell, (v - lo[1]) / self.cell], -1)
        depth, tid = _zbuffer(P, T @ d, (H, W), keep=keep)
        c = np.clip(((ou - lo[0]) / self.cell).astype(int), 0, W - 1)
        r = np.clip(((ov - lo[1]) / self.cell).astype(int), 0, H - 1)
        return depth[r, c], tid[r, c], origins @ d

    def raycast(self, prims, origins, direction):
        z, tid, oz = self._grid(origins, direction)
        hit = tid >= 0
        t = np.where(hit, z - oz, np.inf)
        pi = np.where(hit, self.mid[np.maximum(tid, 0)], -1)
        n = np.zeros((len(origins), 3))
        nn = self.nrm[tid[hit]]
        nn[(nn @ direction) > 0] *= -1                    # face the ray origin
        n[hit] = nn
        return t, pi, n

    def occluded(self, prims, origins, direction, skip_groups):
        occ = np.zeros(len(origins), bool)
        groups = np.array([p["group"] for p in prims], dtype=object)
        for i, g in enumerate(self.mats):
            far, tid, oz = self._grid(origins, direction, tri_mask=self.mid == i, keep="max")
            occ |= (tid >= 0) & (far > oz + 0.05) & (skip_groups != groups[i])
        return occ


def render_sprite(meshes, palette, direction, size=(48, 64), pivot=(24, 57), elevation=16, ppu=1.0, ss=3):
    """Pipeline-style 48x64 pixelisation: banded palette tones + inner lines (render_pixels), despeckle, outline.
    No face cels / pixel rules - the raw 3D->pixel read of the mesh."""
    ensure_ramps(palette, meshes)
    cam = Camera(elevation, ppu)
    tr = MeshTracer(posed(meshes, direction), cell=0.5 / (ss * ppu))
    pf = render_pixels(tr.prims(), palette, size, pivot, cam=cam, ss=ss, tracer=tr)
    return add_outline(despeckle(pf.idx), palette.special["outline"])
