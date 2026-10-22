"""Orthographic iso raycaster over ellipsoid primitives + pixel-art resolve pass."""
import math
import numpy as np

from .rig import ISO_ELEVATION

class Camera:
    """Orthographic camera. `elevation` is the view pitch in degrees; the key light is screen-fixed."""

    def __init__(self, elevation=ISO_ELEVATION, ppu=1.0):
        e = math.radians(elevation)
        self.elevation = elevation
        self.ppu = ppu            # screen pixels per world unit (resolution study)
        self.right = np.array([1.0, 0.0, 0.0])
        self.up = np.array([0.0, math.cos(e), -math.sin(e)])
        self.fwd = np.array([0.0, -math.sin(e), -math.cos(e)])  # view direction (into the scene)
        self.to_cam = -self.fwd
        # Screen-fixed key light: upper-left, slightly toward the viewer (AD decision).
        light = -0.55 * self.right + 0.68 * self.up + 0.48 * self.to_cam
        self.light = light / np.linalg.norm(light)

    def project(self, p, pivot):
        """World point -> continuous pixel coordinates (x right, y down)."""
        return (pivot[0] + self.ppu * float(np.dot(p, self.right)),
                pivot[1] + 0.5 - self.ppu * float(np.dot(p, self.up)))

    def depth(self, p):
        return float(np.dot(p, self.fwd)) + RAY_START


RAY_START = 300.0
ISO_CAMERA = Camera()

DIRECTION_YAW = {"S": 0, "SE": 45, "E": 90, "NE": 135, "N": 180, "NW": 225, "W": 270, "SW": 315}


def _prep(prims):
    out = []
    for p in prims:
        Minv = np.linalg.inv(p["M"])
        out.append(dict(p, Mi=Minv[:3, :3], mt=Minv[:3, 3]))
    return out


def _clip_ok(p, prim):
    ok = np.ones(p.shape[0], bool)
    for nx, ny, nz, d in prim.get("clip_all", []):
        ok &= p[:, 0] * nx + p[:, 1] * ny + p[:, 2] * nz >= d
    anyp = prim.get("clip_any", [])
    if anyp:
        a = np.zeros(p.shape[0], bool)
        for nx, ny, nz, d in anyp:
            a |= p[:, 0] * nx + p[:, 1] * ny + p[:, 2] * nz >= d
        ok &= a
    return ok


def raycast(prims, origins, direction):
    """Returns (t, prim_index, world_normal) for nearest hit along parallel rays."""
    n = origins.shape[0]
    tbest = np.full(n, np.inf)
    ibest = np.full(n, -1, int)
    nbest = np.zeros((n, 3))
    for idx, pr in enumerate(prims):
        o = origins @ pr["Mi"].T + pr["mt"]
        d = pr["Mi"] @ direction
        a = d @ d
        b = o @ d
        c = np.einsum("ij,ij->i", o, o) - 1.0
        disc = b * b - a * c
        hit = disc > 0
        if not hit.any():
            continue
        s = np.sqrt(np.where(hit, disc, 0))
        t0 = (-b - s) / a
        p0 = o + t0[:, None] * d
        ok = hit & _clip_ok(p0, pr)
        better = ok & (t0 < tbest)
        if better.any():
            tbest[better] = t0[better]
            ibest[better] = idx
            nl = p0[better] @ pr["Mi"]          # inverse-transpose normal transform
            nbest[better] = nl / np.linalg.norm(nl, axis=1, keepdims=True)
    return tbest, ibest, nbest


def occluded(prims, origins, direction, skip_groups):
    """Shadow-ray test; a primitive never shadows its own group (handled by N.L)."""
    occ = np.zeros(origins.shape[0], bool)
    for pr in prims:
        o = origins @ pr["Mi"].T + pr["mt"]
        d = pr["Mi"] @ direction
        a = d @ d
        b = o @ d
        c = np.einsum("ij,ij->i", o, o) - 1.0
        disc = b * b - a * c
        hit = (disc > 0) & (skip_groups != pr["group"])
        if not hit.any():
            continue
        s = np.sqrt(np.where(hit, disc, 0))
        for t in ((-b - s) / a, (-b + s) / a):
            p = o + t[:, None] * d
            occ |= hit & (t > 0.05) & _clip_ok(p, pr)
    return occ


class PixelFrame:
    """Result of rendering one frame: palette-index image (-1 transparent) + aux buffers."""

    def __init__(self, idx, depth, group, material):
        self.idx, self.depth, self.group, self.material = idx, depth, group, material


def render_pixels(prims, palette, size, pivot, cam=ISO_CAMERA, ss=3, inner_line_depth=2.2, cast_shadows=True,
                  smooth=0.0, line_min_run=1, no_face_lines=False, hair_style=None, tracer=None):
    """`tracer`: module with raycast/occluded (pipeline.sdf for "model": "hd"); None = analytic ellipsoids."""
    W, H = size
    prims = _prep(prims)
    rc, occ_fn = (raycast, occluded) if tracer is None else (tracer.raycast, tracer.occluded)
    # Subsample grid
    u = (np.arange(ss) + 0.5) / ss
    xs = (np.arange(W)[:, None] + u[None, :]).reshape(-1)
    ys = (np.arange(H)[:, None] + u[None, :]).reshape(-1)
    gx, gy = np.meshgrid(xs, ys)               # (H*ss, W*ss)
    sx = (gx - pivot[0]) / cam.ppu
    sy = (pivot[1] + 0.5 - gy) / cam.ppu
    origins = sx.reshape(-1, 1) * cam.right + sy.reshape(-1, 1) * cam.up + RAY_START * cam.to_cam
    t, pi, nrm = rc(prims, origins, cam.fwd)
    hit = pi >= 0
    lam = np.einsum("ij,j->i", nrm, cam.light)
    if hair_style and hit.any():
        lam = _stylize_hair(prims, origins, t, pi, hit, lam, cam, hair_style)
    if cast_shadows and hit.any():
        groups = np.array([p["group"] for p in prims], dtype=object)
        hp = origins[hit] + t[hit, None] * cam.fwd + nrm[hit] * 0.35
        sh = occ_fn(prims, hp, cam.light, groups[pi[hit]])
        lam_h = lam[hit]
        lam_h[sh] = np.minimum(lam_h[sh], -0.2)
        lam[hit] = lam_h

    if smooth > 0 and hit.any():
        hit, pi, t, lam = _smooth_field(prims, hit, pi, t, lam, H * ss, W * ss, smooth * ss)

    # Reshape into (H, W, ss*ss)
    def blocks(a, fill):
        a = a.reshape(H * ss, W * ss)
        return a.reshape(H, ss, W, ss).transpose(0, 2, 1, 3).reshape(H, W, ss * ss)

    T = blocks(np.where(hit, t, np.inf), np.inf)
    P = blocks(pi, -1)
    Lm = blocks(lam, 0)
    nprim = len(prims)
    mats = sorted({p["material"] for p in prims})
    mat_id = {m: i for i, m in enumerate(mats)}
    prim_mat = np.array([mat_id[p["material"]] for p in prims] + [-1])
    prim_grp_names = sorted({p["group"] for p in prims})
    gid = {g: i for i, g in enumerate(prim_grp_names)}
    prim_grp = np.array([gid[p["group"]] for p in prims] + [-1])
    Msub = prim_mat[np.where(P >= 0, P, nprim)]
    Gsub = prim_grp[np.where(P >= 0, P, nprim)]

    cover = (P >= 0).sum(axis=2)
    opaque = cover * 2 > ss * ss                # majority coverage
    center = (ss * ss) // 2
    # Material: majority among hit samples, tie -> center sample
    counts = np.stack([(Msub == m).sum(axis=2) for m in range(len(mats))], axis=2) if mats else None
    best = counts.max(axis=2)
    cmat = Msub[:, :, center]
    mat = np.argmax(counts, axis=2)
    use_center = (cmat >= 0) & (np.take_along_axis(counts, np.maximum(cmat, 0)[..., None], 2)[..., 0] == best)
    mat = np.where(use_center, cmat, mat)
    sel = Msub == mat[..., None]
    lam_mean = np.where(sel, Lm, 0).sum(axis=2) / np.maximum(sel.sum(axis=2), 1)
    depth = np.where(sel, T, np.inf).min(axis=2)
    # Group of the nearest sample of the chosen material
    near_k = np.argmin(np.where(sel, T, np.inf), axis=2)
    grp = np.take_along_axis(Gsub, near_k[..., None], 2)[..., 0]

    # Banded tones
    idx = np.full((H, W), -1, int)
    tone = np.zeros((H, W), int)
    ramps = palette.ramps
    for m, mi in mat_id.items():
        ramp = ramps[m]
        mb = palette.data.get("material_bands", {})
        th = mb.get(m) or mb.get(m.split("_")[0]) or palette.bands[str(len(ramp))]   # hair_espresso -> hair
        mask = opaque & (mat == mi)
        tn = np.zeros((H, W), int)
        for k, v in enumerate(th):
            tn[lam_mean >= v] = k + 1
        tone[mask] = tn[mask]
    tone = _clean_orphan_tones(tone, mat, opaque)

    # Selective inner lines at depth breaks between different groups (front part's darkest tone)
    line = np.zeros((H, W), bool)
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        qd = np.full((H, W), np.inf)
        qo = np.zeros((H, W), bool)
        qg = np.full((H, W), -2)
        ys0, ys1 = max(dy, 0), H + min(dy, 0)
        xs0, xs1 = max(dx, 0), W + min(dx, 0)
        qd[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx] = depth[ys0:ys1, xs0:xs1]
        qo[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx] = opaque[ys0:ys1, xs0:xs1]
        qg[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx] = grp[ys0:ys1, xs0:xs1]
        gap = np.where(qo & opaque, qd - np.where(opaque, depth, 0), 0)
        line |= opaque & qo & (qg != grp) & (gap > inner_line_depth)
    if no_face_lines:
        line &= ~(mat == mat_id.get("skin", -99))       # never draw interior lines across the face
    if line_min_run > 1:
        line = _drop_small_components(line, line_min_run)  # interior lines only as continuous runs
    tone[line] = 0

    for m, mi in mat_id.items():
        ramp_idx = [palette.index[c] for c in ramps[m]]
        mask = opaque & (mat == mi)
        lut = np.array(ramp_idx)
        idx[mask] = lut[np.minimum(tone[mask], len(lut) - 1)]

    mat_names = np.array(mats + [None], dtype=object)
    material = np.where(opaque, mat_names[np.where(opaque, mat, len(mats))], None)
    depth = np.where(opaque, depth, np.inf)
    pf = PixelFrame(idx, depth, np.where(opaque, grp, -1), material)
    pf.group_names = prim_grp_names
    return pf


def _clean_orphan_tones(tone, mat, opaque):
    """A pixel whose tone matches none of its 4 same-material neighbours takes the majority neighbour tone."""
    H, W = tone.shape
    out = tone.copy()
    for y in range(H):
        for x in range(W):
            if not opaque[y, x]:
                continue
            nb = []
            for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and opaque[yy, xx] and mat[yy, xx] == mat[y, x]:
                    nb.append(tone[yy, xx])
            if len(nb) >= 3 and tone[y, x] not in nb:
                out[y, x] = max(set(nb), key=lambda v: (nb.count(v), -v))
    return out


def add_outline(idx, outline_index):
    """1px outer outline (4-neighbourhood) around all opaque pixels."""
    opaque = idx >= 0
    grow = np.zeros_like(opaque)
    grow[1:, :] |= opaque[:-1, :]
    grow[:-1, :] |= opaque[1:, :]
    grow[:, 1:] |= opaque[:, :-1]
    grow[:, :-1] |= opaque[:, 1:]
    out = idx.copy()
    out[grow & ~opaque] = outline_index
    return out


def remove_lone_pixels(idx):
    """Drop single opaque pixels with no opaque 4-neighbours (sub-pixel slivers)."""
    op = idx >= 0
    nb = np.zeros(op.shape, int)
    nb[1:, :] += op[:-1, :]
    nb[:-1, :] += op[1:, :]
    nb[:, 1:] += op[:, :-1]
    nb[:, :-1] += op[:, 1:]
    out = idx.copy()
    out[op & (nb == 0)] = -1
    return out


def render_smooth(prims, palette, size, pivot, px_per_unit, cam=ISO_CAMERA, tracer=None):
    """High-res smooth-shaded 3D reference render (no pixel pass) -> RGBA uint8 array."""
    W, H = size
    prims = _prep(prims)
    raycast_, occluded_ = (raycast, occluded) if tracer is None else (tracer.raycast, tracer.occluded)
    gx, gy = np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5)
    sx = (gx - pivot[0]) / px_per_unit
    sy = (pivot[1] - gy) / px_per_unit
    origins = sx.reshape(-1, 1) * cam.right + sy.reshape(-1, 1) * cam.up + RAY_START * cam.to_cam
    t, pi, nrm = raycast_(prims, origins, cam.fwd)
    hit = pi >= 0
    lam = np.einsum("ij,j->i", nrm, cam.light)
    groups = np.array([p["group"] for p in prims], dtype=object)
    if hit.any():
        hp = origins[hit] + t[hit, None] * cam.fwd + nrm[hit] * 0.35
        sh = occluded_(prims, hp, cam.light, groups[pi[hit]])
        lh = lam[hit]
        lh[sh] = np.minimum(lh[sh], -0.2)
        lam[hit] = lh
    rgba = np.zeros((H * W, 4), np.uint8)
    for i, p in enumerate(prims):
        m = pi == i
        if not m.any():
            continue
        ramp = [np.array(palette.rgb[palette.index[c]], float) for c in palette.ramps[p["material"]]]
        lo, mid, hi = ramp[0], ramp[1], ramp[-1]
        v = np.clip((lam[m] + 0.3) / 1.3, 0, 1)[:, None]
        col = np.where(v < 0.4, lo + (mid - lo) * (v / 0.4), mid + (hi - mid) * ((v - 0.4) / 0.6))
        rgba[m, :3] = np.clip(col, 0, 255).astype(np.uint8)
        rgba[m, 3] = 255
    return rgba.reshape(H, W, 4), t.reshape(H, W), pi.reshape(H, W)


def _despeckle_once(idx, keep=(), max_island=2, material=None):
    """Merge same-colour islands of <= max_island pixels (4-connected) into the dominant neighbouring
    colour (style rule: bands are chunky shapes, no orphan/speckle pixels). `keep` colours are untouched."""
    H, W = idx.shape
    out = idx.copy()
    keep = set(keep)
    seen = np.zeros((H, W), bool)
    for y in range(H):
        for x in range(W):
            v = out[y, x]
            if seen[y, x] or v < 0:
                continue
            comp, stack = [], [(y, x)]
            seen[y, x] = True
            while stack:
                cy, cx = stack.pop()
                comp.append((cy, cx))
                for yy, xx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= yy < H and 0 <= xx < W and not seen[yy, xx] and out[yy, xx] == v:
                        seen[yy, xx] = True
                        stack.append((yy, xx))
            if len(comp) > max_island or v in keep:
                continue
            nb = []
            cs = set(comp)
            own = material[comp[0]] if material is not None else None
            for cy, cx in comp:
                for yy, xx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= yy < H and 0 <= xx < W and (yy, xx) not in cs and out[yy, xx] >= 0:
                        # material-aware: a tone island merges into its OWN part's tones, so small parts
                        # (mitten, scarf tip) are never swallowed by a neighbouring material
                        if material is None or material[yy, xx] == own:
                            nb.append(int(out[yy, xx]))
            pref = [c for c in nb if c not in keep] or nb    # never grow protected (face) colours
            if pref:
                new = max(sorted(set(pref)), key=pref.count)
                for cy, cx in comp:
                    out[cy, cx] = new
    return out


def despeckle(idx, keep=(), max_island=2, passes=4, material=None):
    """Iterate island merging until stable (merges can expose new islands)."""
    for _ in range(passes):
        new = _despeckle_once(idx, keep, max_island, material)
        if np.array_equal(new, idx):
            break
        idx = new
    return idx


def _gauss1d(sigma):
    r = max(1, int(round(sigma * 2.5)))
    x = np.arange(-r, r + 1)
    k = np.exp(-0.5 * (x / sigma) ** 2)
    return k / k.sum()


def _blur(a, k):
    """Separable convolution (zero padding) without scipy."""
    r = len(k) // 2
    p = np.pad(a, ((r, r), (r, r)))
    tmp = sum(k[i] * p[:, i:i + a.shape[1]] for i in range(len(k)))
    return sum(k[i] * tmp[i:i + a.shape[0], :] for i in range(len(k)))


def _smooth_field(prims, hit, pi, t, lam, Hs, Ws, sigma):
    """Line-art pass 1: smooth the silhouette and the part regions at subsample resolution before quantizing,
    so the union of ellipsoids becomes a clean curve (removes 1px bumps / irregular runs)."""
    k = _gauss1d(sigma)
    hit2 = hit.reshape(Hs, Ws)
    pi2 = pi.reshape(Hs, Ws)
    t2 = np.where(hit, t, 0).reshape(Hs, Ws)
    lam2 = np.where(hit, lam, 0).reshape(Hs, Ws)
    alpha = _blur(hit2.astype(float), k)
    new_hit = alpha >= 0.5
    # per-primitive weighted vote -> smooth part boundaries (also assigns parts to newly filled samples)
    ids = np.unique(pi2[hit2])
    best = np.full((Hs, Ws), -1.0)
    new_pi = np.full((Hs, Ws), -1, int)
    for i in ids:
        v = _blur((pi2 == i).astype(float), k)
        better = v > best
        best[better] = v[better]
        new_pi[better] = i
    new_pi[~new_hit] = -1
    w = _blur(hit2.astype(float), k) + 1e-9
    t_s = _blur(t2, k) / w
    lam_s = _blur(lam2, k) / w
    keep_t = np.where(hit2 & (new_pi == pi2), t2, t_s)          # original depth where the part didn't change
    keep_l = np.where(hit2 & (new_pi == pi2), lam2, lam_s)
    return new_hit.reshape(-1), new_pi.reshape(-1), np.where(new_hit, keep_t, np.inf).reshape(-1), keep_l.reshape(-1)


def _drop_small_components(mask, min_size):
    H, W = mask.shape
    out = mask.copy()
    seen = np.zeros_like(mask)
    for y in range(H):
        for x in range(W):
            if not mask[y, x] or seen[y, x]:
                continue
            comp, st = [], [(y, x)]
            seen[y, x] = True
            while st:
                cy, cx = st.pop()
                comp.append((cy, cx))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        yy, xx = cy + dy, cx + dx
                        if 0 <= yy < H and 0 <= xx < W and mask[yy, xx] and not seen[yy, xx]:
                            seen[yy, xx] = True
                            st.append((yy, xx))
            if len(comp) < min_size:
                for cy, cx in comp:
                    out[cy, cx] = False
    return out


def pixel_perfect_outline(idx, outline_colors, exterior=None):
    """Line-art pass 2: remove L-shaped 'doubles' from the outline so it is a clean 8-connected 1px line.
    A corner outline pixel is removed when it has outline neighbours on two orthogonal sides and removing it
    exposes no fill pixel to the background through a 4-neighbour."""
    out = idx.copy()
    H, W = out.shape
    # exterior = pixels that are outline *by position* (no fill material); colour alone is not enough because
    # a material ramp may legitimately contain the outline colour
    ext = np.ones_like(out, bool) if exterior is None else exterior
    is_ol = lambda y, x: 0 <= y < H and 0 <= x < W and out[y, x] in outline_colors and ext[y, x]
    for _ in range(3):
        changed = False
        for y in range(H):
            for x in range(W):
                if out[y, x] not in outline_colors or not ext[y, x]:
                    continue
                for (ay, ax), (by, bx) in (((0, -1), (1, 0)), ((0, 1), (1, 0)), ((0, -1), (-1, 0)), ((0, 1), (-1, 0))):
                    if is_ol(y + ay, x + ax) and is_ol(y + by, x + bx) and is_ol(y + ay + by, x + ax + bx) is False:
                        # the pixel is the outer corner of an L; check it shields no fill pixel
                        shields = any(0 <= y + dy < H and 0 <= x + dx < W and out[y + dy, x + dx] >= 0
                                      and not ext[y + dy, x + dx]
                                      for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                        if not shields:
                            out[y, x] = -1
                            changed = True
                            break
        if not changed:
            break
    return out


def selout_outline(idx, material, palette, pivot_row_bottom=None, mode="selout"):
    """Line-art pass 3 (色トレス): exterior line colour follows the material it wraps. Lit (top/left-facing)
    edges use the material's darkest tone; shadow-side (right/bottom-facing) edges and the feet use the
    near-black outline colour."""
    out = idx.copy()
    H, W = out.shape
    ol = palette.special["outline"]
    rows = np.nonzero((idx >= 0).any(axis=1))[0]
    bottom = rows.max() if len(rows) else H
    line_cols = palette.data.get("line_colors", {})
    for y in range(H):
        for x in range(W):
            if idx[y, x] != ol or material[y, x] is not None:
                continue                       # only exterior outline pixels (no material underneath)
            # fill neighbours and the direction from them to this outline pixel
            cand = []
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and material[yy, xx] is not None:
                    cand.append((material[yy, xx], -dy, -dx))
            if not cand:
                continue
            mat, fy, fx = cand[0]
            lit_side = (fy < 0 or fx < 0) and not (fy > 0 or fx > 0)
            if mat not in palette.ramps:
                continue
            if mode == "colored":          # every exterior edge takes the wrapped material's darkest tone
                out[y, x] = palette.index[line_cols.get(mat) or palette.ramps[mat][0]]
                continue
            if y >= bottom - 1 or not lit_side:
                continue
            if mode == "open":             # lit edges have no line at all: the shape is defined by its fill
                out[y, x] = -1
                continue
            name = line_cols.get(mat) or palette.ramps[mat][0]
            out[y, x] = palette.index[name]
    return _even_outline_runs(out, material, palette)


def _even_outline_runs(out, material, palette):
    """Outline colour runs must be continuous: an exterior outline pixel whose colour matches none of its outline
    neighbours (8-connected along the contour) takes the neighbours' colour (no speckled sel-out)."""
    H, W = out.shape
    ext = (out >= 0) & np.equal(material, None)
    res = out.copy()
    for _ in range(2):
        changed = False
        for y in range(H):
            for x in range(W):
                if not ext[y, x]:
                    continue
                nb = [int(res[y + a, x + b]) for a in (-1, 0, 1) for b in (-1, 0, 1)
                      if (a or b) and 0 <= y + a < H and 0 <= x + b < W and ext[y + a, x + b]]
                if nb and res[y, x] not in nb:
                    res[y, x] = max(sorted(set(nb)), key=nb.count)
                    changed = True
        if not changed:
            break
    return res


def _extent_spikes(e):
    """Count single-sample spikes in an extent profile (a value that differs from both neighbours, which agree)."""
    n = 0
    for k in range(1, len(e) - 1):
        if e[k - 1] is None or e[k] is None or e[k + 1] is None:
            continue
        if e[k - 1] == e[k + 1] and e[k] != e[k - 1]:
            n += 1
    return n


def jaggy_count(idx):
    """QA metric: 1px bumps/notches on the outer silhouette (left/right per row, top/bottom per column)."""
    op = idx >= 0
    H, W = op.shape
    total = 0
    for axis in (0, 1):
        m = op if axis == 0 else op.T
        lo = [int(np.argmax(r)) if r.any() else None for r in m]
        hi = [int(len(r) - 1 - np.argmax(r[::-1])) if r.any() else None for r in m]
        total += _extent_spikes(lo) + _extent_spikes(hi)
    return total


def regularize_silhouette(idx, protect=None):
    """Line-art pass 4 (ジャギ取り): remove 1-row bumps/notches from the silhouette by median-filtering the
    left/right extents of each row and top/bottom extents of each column. Added pixels copy the colour of the
    adjacent fill pixel; removed pixels become transparent. `protect` (bool mask) is never removed."""
    out = idx.copy()
    for axis in (0, 1):
        a = out if axis == 0 else out.T.copy()
        pr = None if protect is None else (protect if axis == 0 else protect.T)
        rows = [r for r in range(a.shape[0]) if (a[r] >= 0).any()]
        for side in (0, 1):
            ext = {}
            for r in rows:
                nz = np.nonzero(a[r] >= 0)[0]
                ext[r] = nz.min() if side == 0 else nz.max()
            for r in rows:
                if r - 1 in ext and r + 1 in ext and ext[r - 1] == ext[r + 1] and ext[r] != ext[r - 1]:
                    target = ext[r - 1]
                    cur = ext[r]
                    inward = (target > cur) if side == 0 else (target < cur)
                    if inward:      # bump sticking out: remove it
                        xs = range(cur, target) if side == 0 else range(target + 1, cur + 1)
                        if pr is not None and any(pr[r, x] for x in xs):
                            continue
                        for x in xs:
                            a[r, x] = -1
                    else:           # notch: fill from the row's own edge colour
                        col = a[r, cur]
                        xs = range(target, cur) if side == 0 else range(cur + 1, target + 1)
                        for x in xs:
                            a[r, x] = col
                    ext[r] = target
        out = a if axis == 0 else a.T.copy()
    return out



def _stylize_hair(prims, origins, t, pi, hit, lam, cam, hs):
    """Designed anime-style hair shading in head space (consistent in every view).
    Parameters (render.hair_style): clump_deg, clump_offset, line_start, line_px, line_az_min, ring_y, ring_w,
    ring_az, under_band.
    * clump lines: dark separations at fixed azimuths around the head, starting below the crown and running down
      to the tips, so the hair reads as a few deliberate locks (毛束) instead of random strands;
    * one highlight ring (天使の輪) at a fixed height on the crown, broken at the clump lines;
    * a soft shadow under the crown so the mass has one clean light-to-dark read."""
    hair_ids = [k for k, p in enumerate(prims) if p["material"] in hs["materials"]]
    if not hair_ids:
        return lam
    m = hit & np.isin(pi, hair_ids)
    if not m.any():
        return lam
    Hm = np.linalg.inv(hs["head_M"])
    pts = origins[m] + t[m, None] * cam.fwd
    loc = pts @ Hm[:3, :3].T + Hm[:3, 3]
    c = np.asarray(hs["center"], float)
    r = float(hs["radius"])
    rel = (loc - c) / r                                  # head-local, unit = head radius
    az = np.degrees(np.arctan2(rel[:, 0], rel[:, 2]))    # 0 = front, +90 = her left
    y = rel[:, 1]                                        # +1 crown ... -1 chin, below = long hair
    out = lam.copy()
    sub = out[m]
    spacing = hs.get("clump_deg", 36.0)
    off = hs.get("clump_offset", 18.0)
    # line half-width in degrees ~ 0.5 px at the head silhouette, widening slightly as locks hang
    # line half-width: ~0.5 px measured at the head radius; long hair hanging lower is further from the head axis,
    # so convert using the actual horizontal distance to keep a constant ~1px line all the way down
    rad = np.maximum(np.hypot(rel[:, 0], rel[:, 2]), 0.35) * r * hs.get("ppu", 1.0)
    halfw = np.degrees(hs.get("line_px", 0.5) / rad)
    d = np.abs(((az - off) + spacing / 2) % spacing - spacing / 2)
    start = hs.get("line_start", 0.35)                   # lines begin below this height (crown stays clean)
    line = (d < halfw) & (y < start) & (np.abs(az) > hs.get("line_az_min", 50.0))   # keep the face frame clean
    sub[line] = -1.0
    ring_y, ring_w = hs.get("ring_y", 0.62), hs.get("ring_w", 0.1)
    ring = (np.abs(y - ring_y) < ring_w) & ~line & (np.abs(az) < hs.get("ring_az", 110))
    sub[ring] = 1.0
    under = (y < ring_y - ring_w) & (y > ring_y - ring_w - hs.get("under_band", 0.16)) & ~line
    sub[under] = np.minimum(sub[under], 0.2)             # crisp shade just under the ring
    out[m] = sub
    return out
