"""Hi-res render -> pixelate experiment library (read-only use of pipeline/*).

* setup(variant, anim)          -> (scene, palette) exactly as pipeline.build.main constructs them (no files written)
* trace(scene, i, d, k)         -> hi-res buffers (k x sprite PPU, same camera/pivot grid): t, prim, normal, lam,
                                   material id, group id, band tone, smooth RGB, flat-band RGB, edge masks
* resolve_*(buf, ...)           -> native 48x64 PixelFrame (idx, depth, group, material) via one downscale method
* patched(scene, fn)            -> context manager: Scene.render_base runs its full native FIX chain (despeckle, face
                                   cels, pixel rules, outline + sel-out, ring trim, bow shine, final orphans) on the
                                   PixelFrame from `fn` instead of the native supersampled render_pixels
"""
import contextlib
import json
import os
import sys

import numpy as np

ROOT = "/Users/waylonhuang/Documents/other/pixelart"
sys.path.insert(0, ROOT)
from pipeline import build as B          # noqa: E402  (read-only)
from pipeline import frames as F         # noqa: E402
from pipeline import render as R         # noqa: E402
from pipeline.palette import Palette     # noqa: E402

EXP = os.path.join(ROOT, "REVIEW/exp/2026-10-28_snowpeak_hires")


def setup(variant, anim_name):
    spec = B.load_variant(variant)
    _, pal_path = B.variant_inputs(spec)
    palette = Palette(pal_path)
    if spec.get("material_bands"):
        palette.data.setdefault("material_bands", {}).update(spec["material_bands"])
    for mat, names in spec.get("ramp_overrides", {}).items():
        palette.ramps[mat] = names
    with open(os.path.join(ROOT, "data", "animations", f"{anim_name}.json")) as f:
        anim = json.load(f)
    from pipeline.chargen import build as gen_character
    character = gen_character(spec)
    if "frame" in spec:
        anim["frame_size"], anim["pivot"] = spec["frame"]["size"], spec["frame"]["pivot"]
    for k, v in spec.get("anim", {}).items():
        anim[k] = v
    patch = spec.get("anim_patch", {})
    if patch:
        from pipeline.rig import deep_merge
        if "rest" in patch:
            anim["rest"] = deep_merge(anim["rest"], patch["rest"])
        for fr in anim["frames"]:
            if fr["name"] in patch.get("frames", {}):
                fr.update(deep_merge(fr, patch["frames"][fr["name"]]))
    scene = F.Scene(character, anim, palette)
    return scene, palette


# ----------------------------------------------------------------------------------------------- hi-res trace
def hs_for(scene, i, d, prims, worlds):
    rnd = scene.char.get("render", {})
    if not rnd.get("hair_style"):
        return None
    hs = dict(rnd["hair_style"])
    face = scene.char["face"]
    hs.update(head_M=worlds[face["bone"]], center=face["center"], radius=face["radii"][0], ppu=scene.cam.ppu,
              materials={p_["material"] for p_ in prims if p_["material"].startswith("hair")})
    return hs


def trace_prims(prims, palette, size, pivot, cam, k, hair_style=None, tracer=None):
    """Same rays as render_pixels(ss=k) but kept per sample (one hi-res pixel per sample)."""
    W, H = size
    prims = R._prep(prims)
    rc, occ_fn = (R.raycast, R.occluded) if tracer is None else (tracer.raycast, tracer.occluded)
    gx, gy = np.meshgrid((np.arange(W * k) + 0.5) / k, (np.arange(H * k) + 0.5) / k)
    sx = (gx - pivot[0]) / cam.ppu
    sy = (pivot[1] + 0.5 - gy) / cam.ppu
    origins = sx.reshape(-1, 1) * cam.right + sy.reshape(-1, 1) * cam.up + R.RAY_START * cam.to_cam
    t, pi, nrm = rc(prims, origins, cam.fwd)
    hit = pi >= 0
    lam = np.einsum("ij,j->i", nrm, cam.light)
    lam_raw = lam.copy()
    if hair_style and hit.any():
        lam = R._stylize_hair(prims, origins, t, pi, hit, lam, cam, hair_style)
    shadow = np.zeros_like(hit)
    if hit.any():
        groups = np.array([p["group"] for p in prims], dtype=object)
        hp = origins[hit] + t[hit, None] * cam.fwd + nrm[hit] * 0.35
        sh = occ_fn(prims, hp, cam.light, groups[pi[hit]])
        lh = lam[hit]
        lh[sh] = np.minimum(lh[sh], -0.2)
        lam[hit] = lh
        s2 = shadow[hit]; s2[sh] = True; shadow[hit] = s2
    Hk, Wk = H * k, W * k
    mats = sorted({p["material"] for p in prims})
    mat_id = {m: j for j, m in enumerate(mats)}
    grp_names = sorted({p["group"] for p in prims})
    gid = {g: j for j, g in enumerate(grp_names)}
    pm = np.array([mat_id[p["material"]] for p in prims] + [-1])
    pg = np.array([gid[p["group"]] for p in prims] + [-1])
    P = np.where(hit, pi, len(prims))
    M = pm[P].reshape(Hk, Wk)
    G = pg[P].reshape(Hk, Wk)
    lam2 = np.where(hit, lam, 0).reshape(Hk, Wk)
    # band tone per sample (same thresholds as render_pixels)
    tone = np.zeros((Hk, Wk), int)
    mb = palette.data.get("material_bands", {})
    for m, mi in mat_id.items():
        ramp = palette.ramps[m]
        th = mb.get(m) or mb.get(m.split("_")[0]) or palette.bands[str(len(ramp))]
        sel = M == mi
        tn = np.zeros((Hk, Wk), int)
        for j, v in enumerate(th):
            tn[lam2 >= v] = j + 1
        tone[sel] = np.minimum(tn[sel], len(ramp) - 1)
    return dict(k=k, size=(W, H), t=np.where(hit, t, np.inf).reshape(Hk, Wk), prim=pi.reshape(Hk, Wk),
                nrm=nrm.reshape(Hk, Wk, 3), lam=lam2, lam_raw=np.where(hit, lam_raw, 0).reshape(Hk, Wk),
                shadow=shadow.reshape(Hk, Wk), mat=M, grp=G, tone=tone, mats=mats, grp_names=grp_names)


def colorize(buf, palette):
    """(smooth RGBA, flat-band RGBA, band palette-index image) at hi-res."""
    M, tone, lam = buf["mat"], buf["tone"], buf["lam"]
    Hk, Wk = M.shape
    smooth = np.zeros((Hk, Wk, 4), np.uint8)
    flat = np.zeros((Hk, Wk, 4), np.uint8)
    bidx = np.full((Hk, Wk), -1, int)
    for mi, m in enumerate(buf["mats"]):
        sel = M == mi
        if not sel.any():
            continue
        ramp_i = [palette.index[c] for c in palette.ramps[m]]
        ramp = [np.array(palette.rgb[j], float) for j in ramp_i]
        lo, mid, hi = ramp[0], ramp[len(ramp) // 2] if len(ramp) > 2 else ramp[min(1, len(ramp) - 1)], ramp[-1]
        v = np.clip((lam[sel] + 0.3) / 1.3, 0, 1)[:, None]
        col = np.where(v < 0.4, lo + (mid - lo) * (v / 0.4), mid + (hi - mid) * ((v - 0.4) / 0.6))
        smooth[sel, :3] = np.clip(col, 0, 255).astype(np.uint8)
        smooth[sel, 3] = 255
        bi = np.array(ramp_i)[tone[sel]]
        bidx[sel] = bi
        flat[sel, :3] = np.array(palette.rgb)[bi]
        flat[sel, 3] = 255
    return smooth, flat, bidx


def edges(buf, depth_gap=2.2, crease_deg=50.0, mat_lines=False):
    """Hi-res line masks from buffer discontinuities, marked on ONE side so lines stay 1 hi-res px:
    depth: near side of a jump > depth_gap between different groups (the native inner-line rule, at hi-res)
    crease: normal angle > crease_deg inside a part, marked on the darker side
    material: material change at small depth gap (optional)."""
    t, G, M, n, lam = buf["t"], buf["grp"], buf["mat"], buf["nrm"], buf["lam"]
    op = M >= 0
    dep = np.zeros_like(op); cre = np.zeros_like(op); mat = np.zeros_like(op)
    cosT = np.cos(np.radians(crease_deg))
    for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        def sh(a, fill):
            o = np.full_like(a, fill)
            Hh, Ww = a.shape[:2]
            ys0, ys1 = max(dy, 0), Hh + min(dy, 0)
            xs0, xs1 = max(dx, 0), Ww + min(dx, 0)
            o[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx] = a[ys0:ys1, xs0:xs1]
            return o
        qt, qG, qM, qop, ql = sh(t, np.inf), sh(G, -2), sh(M, -2), sh(op, False), sh(lam, 0.0)
        qn = sh(n, 0.0)
        both = op & qop
        dep |= both & (qG != G) & (qt - t > depth_gap)
        dotn = (n * qn).sum(-1)
        cre |= both & (qG == G) & (np.abs(qt - t) < depth_gap) & (dotn < cosT) & (lam <= ql)
        if mat_lines:
            mat |= both & (qM != M) & (np.abs(qt - t) <= depth_gap) & (M < qM)
    return dep, cre, mat


# ----------------------------------------------------------------------------------------------- downscale
def blocks(a, k):
    Hk, Wk = a.shape[:2]
    H, W = Hk // k, Wk // k
    rest = a.shape[2:]
    return a.reshape(H, k, W, k, *rest).transpose(0, 2, 1, 3, *range(4, 4 + len(rest))).reshape(H, W, k * k, *rest)


def cell_material(buf, center_tiebreak=True):
    """render_pixels' material rule at ss=k: majority coverage -> opaque; majority material (tie -> centre)."""
    k = buf["k"]
    Mb = blocks(buf["mat"], k)
    Tb = blocks(buf["t"], k)
    Gb = blocks(buf["grp"], k)
    nm = len(buf["mats"])
    cover = (Mb >= 0).sum(-1)
    opaque = cover * 2 > k * k
    counts = np.stack([(Mb == m).sum(-1) for m in range(nm)], -1)
    best = counts.max(-1)
    mat = counts.argmax(-1)
    if center_tiebreak:
        c = (k // 2) * k + k // 2
        cm = Mb[..., c]
        use = (cm >= 0) & (np.take_along_axis(counts, np.maximum(cm, 0)[..., None], 2)[..., 0] == best)
        mat = np.where(use, cm, mat)
    sel = Mb == mat[..., None]
    depth = np.where(sel, Tb, np.inf).min(-1)
    nk = np.argmin(np.where(sel, Tb, np.inf), -1)
    grp = np.take_along_axis(Gb, nk[..., None], 2)[..., 0]
    return opaque, mat, sel, depth, grp


def _native_lines(depth, grp, opaque, inner_line_depth=2.2):
    """render_pixels' selective inner-line rule on the native grid."""
    H, W = depth.shape
    line = np.zeros((H, W), bool)
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        qd = np.full((H, W), np.inf); qo = np.zeros((H, W), bool); qg = np.full((H, W), -2)
        ys0, ys1 = max(dy, 0), H + min(dy, 0)
        xs0, xs1 = max(dx, 0), W + min(dx, 0)
        qd[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx] = depth[ys0:ys1, xs0:xs1]
        qo[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx] = opaque[ys0:ys1, xs0:xs1]
        qg[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx] = grp[ys0:ys1, xs0:xs1]
        gap = np.where(qo & opaque, qd - np.where(opaque, depth, 0), 0)
        line |= opaque & qo & (qg != grp) & (gap > inner_line_depth)
    return line


def _pixelframe(idx, depth, grp, opaque, mat, mats, grp_names):
    names = np.array(list(mats) + [None], dtype=object)
    material = np.where(opaque, names[np.where(opaque, mat, len(mats))], None)
    pf = R.PixelFrame(idx, np.where(opaque, depth, np.inf), np.where(opaque, grp, -1), material)
    pf.group_names = grp_names
    return pf


def lab(rgb):
    x = np.asarray(rgb, float) / 255.
    x = np.where(x > 0.04045, ((x + 0.055) / 1.055) ** 2.4, x / 12.92)
    Mx = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = x @ Mx.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def lock_to_ramp(rgb, mat, opaque, mats, palette, ramp_only=True):
    """Palette lock in Lab: each pixel snaps to the nearest colour of its cell material's ramp (or whole palette).
    Returns (idx, tone) with tone = ramp position (needed by the native chain for inner lines etc.)."""
    H, W = mat.shape
    idx = np.full((H, W), -1, int)
    tone = np.zeros((H, W), int)
    L = lab(rgb[..., :3])
    prgb = np.array(palette.rgb, float)
    plab = lab(prgb)
    for mi, m in enumerate(mats):
        sel = opaque & (mat == mi)
        if not sel.any():
            continue
        ramp_i = [palette.index[c] for c in palette.ramps[m]]
        cand = np.array(ramp_i) if ramp_only else np.arange(len(prgb))
        d = ((L[sel][:, None, :] - plab[cand][None]) ** 2).sum(-1)
        j = d.argmin(1)
        idx[sel] = cand[j]
        if ramp_only:
            tone[sel] = j
    return idx, tone


def _apply_lines(idx, line, mat, opaque, mats, palette):
    out = idx.copy()
    for mi, m in enumerate(mats):
        sel = line & opaque & (mat == mi)
        out[sel] = palette.index[palette.ramps[m][0]]
    return out


def edge_cells(buf, emask, frac=0.75):
    """native cells crossed by a hi-res line: >= frac*k edge samples in the cell."""
    k = buf["k"]
    return blocks(emask, k).sum(-1) >= frac * k


# method: native-equivalent vote at ss=k, mean lambert -> band (render_pixels logic, more samples)
def resolve_vote_mean(buf, palette, lines="native", edge=None):
    opaque, mat, sel, depth, grp = cell_material(buf)
    k = buf["k"]
    Lb = blocks(buf["lam"], k)
    lam_mean = np.where(sel, Lb, 0).sum(-1) / np.maximum(sel.sum(-1), 1)
    H, W = mat.shape
    tone = np.zeros((H, W), int)
    mb = palette.data.get("material_bands", {})
    for mi, m in enumerate(buf["mats"]):
        ramp = palette.ramps[m]
        th = mb.get(m) or mb.get(m.split("_")[0]) or palette.bands[str(len(ramp))]
        msk = opaque & (mat == mi)
        tn = np.zeros((H, W), int)
        for j, v in enumerate(th):
            tn[lam_mean >= v] = j + 1
        tone[msk] = tn[msk]
    return _finish_tone(buf, palette, opaque, mat, depth, grp, tone, lines, edge)


# method: majority material, then majority BAND among that material's samples
def resolve_vote_mode(buf, palette, lines="native", edge=None):
    opaque, mat, sel, depth, grp = cell_material(buf)
    k = buf["k"]
    Tb = blocks(buf["tone"], k)
    nt = int(buf["tone"].max()) + 1
    cnt = np.stack([((Tb == j) & sel).sum(-1) for j in range(nt)], -1)
    tone = cnt.argmax(-1)
    return _finish_tone(buf, palette, opaque, mat, depth, grp, tone, lines, edge)


def _finish_tone(buf, palette, opaque, mat, depth, grp, tone, lines, edge):
    tone = R._clean_orphan_tones(tone, mat, opaque)
    H, W = mat.shape
    line = np.zeros((H, W), bool)
    if lines in ("native", "both"):
        line |= _native_lines(depth, grp, opaque)
    if edge is not None:
        line |= edge
    tone = tone.copy()
    tone[line & opaque] = 0
    idx = np.full((H, W), -1, int)
    for mi, m in enumerate(buf["mats"]):
        msk = opaque & (mat == mi)
        lut = np.array([palette.index[c] for c in palette.ramps[m]])
        idx[msk] = lut[np.minimum(tone[msk], len(lut) - 1)]
    return _pixelframe(idx, depth, grp, opaque, mat, buf["mats"], buf["grp_names"])


def kcentroid(rgb, k, nclus=3, valid=None):
    """Per-cell k-means (swordswoman pz.kcentroid, numpy port, no prefilter): dominant cluster centre per cell.
    `valid` (hi-res bool) restricts clustering to foreground samples."""
    img = rgb[..., :3].astype(float)
    Hk, Wk = img.shape[:2]
    H, W = Hk // k, Wk // k
    b = blocks(img, k).reshape(H * W, k * k, 3)
    v = np.ones((H * W, k * k), bool) if valid is None else blocks(valid, k).reshape(H * W, k * k)
    lum = b @ np.array([.299, .587, .114])
    lum_s = np.where(v, lum, np.inf)
    o = np.argsort(lum_s, 1)
    nv = np.maximum(v.sum(1), 1)
    rows = np.arange(len(b))
    c = np.stack([b[rows, o[rows, np.minimum((q * (nv - 1)).astype(int), k * k - 1)]]
                  for q in np.linspace(0, 1, nclus)], 1)
    for _ in range(8):
        d = ((b[:, :, None] - c[:, None]) ** 2).sum(-1)
        a = d.argmin(-1)
        a = np.where(v, a, -1)
        for j in range(nclus):
            s = (a == j)[..., None]
            n = s.sum(1)
            c[:, j] = np.where(n > 0, (b * s).sum(1) / np.maximum(n, 1), c[:, j])
    cnt = np.stack([(a == j).sum(1) for j in range(nclus)], 1)
    pick = cnt.argmax(1)
    return c[np.arange(len(pick)), pick].reshape(H, W, 3)


def resolve_rgb(buf, palette, low_rgb, lines="native", edge=None):
    """Any RGB downscale -> palette lock to the cell material's ramp -> PixelFrame."""
    opaque, mat, sel, depth, grp = cell_material(buf)
    idx, tone = lock_to_ramp(low_rgb, mat, opaque, buf["mats"], palette)
    tone = R._clean_orphan_tones(tone, mat, opaque)
    H, W = mat.shape
    line = np.zeros((H, W), bool)
    if lines in ("native", "both"):
        line |= _native_lines(depth, grp, opaque)
    if edge is not None:
        line |= edge
    tone[line & opaque] = 0
    for mi, m in enumerate(buf["mats"]):
        msk = opaque & (mat == mi)
        lut = np.array([palette.index[c] for c in palette.ramps[m]])
        idx[msk] = lut[np.minimum(tone[msk], len(lut) - 1)]
    return _pixelframe(idx, depth, grp, opaque, mat, buf["mats"], buf["grp_names"])


def area_avg(rgba, k):
    a = blocks(rgba[..., :3].astype(float), k)
    w = blocks((rgba[..., 3] > 0).astype(float), k)[..., None]
    return (a * w).sum(2) / np.maximum(w.sum(2), 1e-9)


# ----------------------------------------------------------------------------------------------- native-chain hook
@contextlib.contextmanager
def patched(fn):
    """Within the block, Scene.render_base gets its PixelFrame from fn(prims, palette, size, pivot, cam, hair_style,
    tracer) -> PixelFrame, and runs the rest of the shipped FIX chain unchanged."""
    orig = F.render_pixels

    def hook(prims, palette, size, pivot, cam=R.ISO_CAMERA, ss=3, inner_line_depth=2.2, cast_shadows=True,
             smooth=0.0, line_min_run=1, no_face_lines=False, hair_style=None, tracer=None):
        return fn(prims, palette, size, pivot, cam, hair_style, tracer)
    F.render_pixels = hook
    try:
        yield
    finally:
        F.render_pixels = orig

