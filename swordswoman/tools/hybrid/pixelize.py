"""Hi-res illustration (Gemini / paint-over / render) -> palette-locked 128-cell sprite.

  .venv/bin/python tools/hybrid/pixelize.py IN_hires.png --guide <prefix|none> --out OUT.png [--height 60]
        [--bg auto|alpha|flood|legacy] [--crop x0,y0,x1,y1] [--fit iou|joints|none] [--src-joints J.json]
        [--down box|mode] [--quant material|ramp|nearest] [--outline auto|inner|outer|keep]
        [--no-clean] [--no-guide-mat] [--baseline 104] [--pivot-x 64]
  .venv/bin/python tools/hybrid/pixelize.py --regress        # rebuild docs/palette_v1_vs_v2_terrain.png

Steps
  1. background removal (alpha if the input has it; else flood fill from the border colour, enclosed
     background holes, flat grey ground-shadow under the feet, specks)
  2. alignment to the guide: the body (sword-free) height is scaled to the guide's body height, the
     feet baseline and feet centre land on the guide's (or on --baseline / --pivot-x with no guide);
     --fit iou then searches scale +-6 % and shifts for the best silhouette IoU against the guide;
     --fit joints uses a least-squares similarity (scale + shift) on named joints (--src-joints, input
     px) vs the guide joints, then the IoU refine.
  3. BOX/area downsample (premultiplied) of the cropped figure; alpha binarized at 50 % coverage.
     --down mode: per-pixel palette quantization at hi-res, then the most covered tone per cell pixel.
  4. quantization: per material.  With a guide id pass every pixel is classified to the ramp whose
     polyline (outline -> dark -> light) is closest in Lab, with a penalty for ramps the guide's
     material does not allow (soft, so Gemini shapes that differ from the 3D guide still get the
     right ramp); without ids it is pure ramp clustering.  Then nearest tone inside the ramp
     (value-weighted).  --quant nearest = global nearest colour (legacy, for comparison).
  5. clean 1 px exterior outline with sel-out: silhouette pixels -> outline on shadow side (bottom /
     right / ground contact), material's darkest tone on the lit side (top / left; cleanup guide R9);
     steel keeps its tones (R20).  1-2 px thin parts keep their colour ('auto' adds the outline
     outside them instead).
  6. safe auto-clean: orphans (except glint / mouth / blush / buckle / lace / eye tones and the
     sword), 1 px notches and holes, 1 px hanging spurs, doubled outline bumps; alpha is binary.
  7. writes OUT.png (128 cell), OUT_4x.png (4x preview), OUT_hires.png (aligned hi-res, 512 = 4x the
     cell), OUT_dbg.png (hi-res | sprite | ramps | guide overlay) and OUT_meta.json.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hylib as H  # noqa: E402
from hylib import BASE, CELL, PIVOT, N4, N8, shift, label_cc, disk_op  # noqa: E402

ap_defaults = dict(height=60, baseline=PIVOT[1], pivot_x=PIVOT[0])


# ================================================================ 1. background removal
def _lab(rgb):
    return H.srgb_to_lab(rgb)


def bg_legacy(rgb):
    """exact mask of the design-bible terrain snippet (near-white + light neutral grey removed)."""
    a = rgb.astype(int)
    return (np.abs(a - 245).max(2) > 18) & ~((np.abs(a[..., 0] - a[..., 1]) < 8) &
                                             (np.abs(a[..., 1] - a[..., 2]) < 8) & (a[..., 0] > 150))


def bg_flood(rgb, tol=11.0, holes=True, shadow=True, speck_frac=6e-5):
    """-> opaque mask.  Background = pixels close (Lab) to the median border colour that are
    connected to the border; plus enclosed background-coloured holes >= 0.15 % of the figure;
    plus a flat neutral ground shadow touching the background in the lower 35 % of the figure."""
    from scipy import ndimage
    Hh, Ww = rgb.shape[:2]
    lab = _lab(rgb)
    border = np.concatenate([lab[:3].reshape(-1, 3), lab[-3:].reshape(-1, 3),
                             lab[:, :3].reshape(-1, 3), lab[:, -3:].reshape(-1, 3)])
    bgc = np.median(border, 0)
    cand = np.linalg.norm(lab - bgc, axis=-1) < tol
    lab_c, n = ndimage.label(cand)
    edge_ids = np.unique(np.concatenate([lab_c[0], lab_c[-1], lab_c[:, 0], lab_c[:, -1]]))
    bg = np.isin(lab_c, edge_ids[edge_ids > 0])
    fig = ~bg
    if holes and n:
        sizes = np.bincount(lab_c.ravel(), minlength=n + 1)
        fa = max(fig.sum(), 1)
        big = np.nonzero(sizes >= 0.0015 * fa)[0]
        hole = np.isin(lab_c, big[big > 0]) & ~bg
        bg |= hole
    if shadow:
        ys = np.nonzero((~bg).any(1))[0]
        if len(ys):
            y0, y1 = ys.min(), ys.max()
            low = np.zeros_like(bg)
            low[int(y1 - 0.35 * (y1 - y0)):] = True
            L = lab[..., 0]
            chroma = np.hypot(lab[..., 1], lab[..., 2])
            loc = ndimage.uniform_filter(L, 5)
            var = ndimage.uniform_filter(L * L, 5) - loc * loc
            flat = (chroma < 7) & (L > 45) & (var < 4.0) & low & ~bg
            if flat.any():
                lab_s, ns = ndimage.label(flat)
                touch = np.unique(lab_s[ndimage.binary_dilation(bg, iterations=5) & flat])
                touch = touch[touch > 0]
                sizes = np.bincount(lab_s.ravel(), minlength=ns + 1)
                best = None
                for t in touch:                  # a uniform grey blob (the blade has a gradient)
                    if sizes[t] < 0.002 * flat.size:
                        continue
                    Ls = L[lab_s == t]
                    if Ls.std() < 2.5 and (best is None or sizes[t] > sizes[best]):
                        best = t
                if best is not None:
                    sh = lab_s == best
                    shc = np.median(lab[sh], 0)
                    # grow into the anti-aliased rim of the shadow (and its soft edge to the bg)
                    near = ((np.linalg.norm(lab - shc, axis=-1) < 5) | sh) & low & ~bg
                    lab_n, _ = ndimage.label(near)
                    keep = np.unique(lab_n[sh])
                    shm = np.isin(lab_n, keep[keep > 0])
                    rim = ndimage.binary_dilation(shm, iterations=3) & ~bg & (chroma < 7) & \
                        (L > shc[0] - 3) & low
                    bg |= shm | rim
    fig = ~bg
    lab_f, nf = ndimage.label(fig)
    if nf:
        sizes = np.bincount(lab_f.ravel(), minlength=nf + 1)
        sizes[0] = 0
        fig &= sizes[lab_f] >= max(8, speck_frac * fig.size)
    # fill tiny holes (< 0.004 % of the image) inside the figure
    lab_h, nh = ndimage.label(~fig)
    if nh:
        sizes = np.bincount(lab_h.ravel(), minlength=nh + 1)
        edge_ids = np.unique(np.concatenate([lab_h[0], lab_h[-1], lab_h[:, 0], lab_h[:, -1]]))
        small = sizes < max(4, 4e-5 * fig.size)
        small[edge_ids] = False
        small[0] = False
        fig |= small[lab_h]
    return fig


def pick_figure(mask, k):
    """multi-figure sheets: group big components whose column ranges overlap into figures,
    left to right, and keep figure k (with every small component inside its bbox)."""
    from scipy import ndimage
    lab, n = ndimage.label(mask)
    if n == 0:
        return mask
    sizes = np.bincount(lab.ravel(), minlength=n + 1)
    sizes[0] = 0
    objs = ndimage.find_objects(lab)
    big = [i for i in range(1, n + 1) if sizes[i] >= 0.03 * sizes.max()]
    spans = sorted([(objs[i - 1][1].start, objs[i - 1][1].stop, i) for i in big])
    groups = []
    for x0, x1, i in spans:
        # overlap needs > 25 % of the narrower span (a sword tip poking under a neighbour is not a merge)
        if groups and min(x1, groups[-1][1]) - x0 > 0.25 * min(x1 - x0, groups[-1][1] - groups[-1][0]):
            groups[-1][1] = max(groups[-1][1], x1)
            groups[-1][2].append(i)
        else:
            groups.append([x0, x1, [i]])
    if not 0 <= k < len(groups):
        raise SystemExit(f"--pick {k}: found {len(groups)} figures")
    keep = np.isin(lab, groups[k][2])
    ys, xs = np.nonzero(keep)
    box = np.zeros_like(mask)
    box[ys.min():ys.max() + 1, xs.min():xs.max() + 1] = True
    small = np.isin(lab, [i for i in range(1, n + 1) if i not in big]) & box
    return keep | small


def remove_bg(img, mode="auto", tol=11.0):
    a = np.array(img.convert("RGBA"))
    rgb = a[..., :3]
    has_alpha = (a[..., 3] < 250).mean() > 0.01
    if mode == "alpha" or (mode == "auto" and has_alpha):
        return rgb, a[..., 3] >= 128, "alpha"
    if mode == "legacy":
        return rgb, bg_legacy(rgb), "legacy"
    return rgb, bg_flood(rgb, tol=tol), "flood"


# ================================================================ 2. alignment
def body_rows(rgb, mask):
    """hi-res body (sword-free) extent: drop steel-classified pixels (blade, + 2 % dilation) from the
    mask before measuring top / bottom / feet centre.  Classification on a reduced copy (speed)."""
    Hh, Ww = mask.shape
    k = max(1, int(round(max(Hh, Ww) / 384)))
    small = rgb[::k, ::k]
    cls, _ = H.classify(small.astype(float))
    lab = H.srgb_to_lab(small.astype(float))
    neutral = (np.hypot(lab[..., 1], lab[..., 2]) < 8) & (lab[..., 0] > 50)   # silver blade
    steel = ((cls == BASE.index("steel")) | neutral) & mask[::k, ::k]
    lab_s, sz = label_cc(steel, 8)
    keep = []
    for i in np.nonzero(sz >= max(6, 0.01 * mask[::k, ::k].sum()))[0]:
        if i == 0:
            continue
        yy, xx = np.nonzero(lab_s == i)
        ev = np.sort(np.linalg.eigvalsh(np.cov(np.stack([xx, yy]).astype(float)) + 1e-6 * np.eye(2)))
        if np.sqrt(ev[1] / max(ev[0], 1e-6)) >= 3.0:        # blade-like (long and thin)
            keep.append(i)
    big = np.isin(lab_s, keep)
    big = disk_op(big, 2)
    steel_hr = np.repeat(np.repeat(big, k, 0), k, 1)[:Hh, :Ww]
    body = mask & ~steel_hr
    if body.sum() < 0.5 * mask.sum():
        body = mask
    ys, xs = np.nonzero(body)
    y0, y1 = ys.min(), ys.max()
    band = body[max(y1 - int(0.04 * (y1 - y0)), 0):y1 + 1]
    fx = np.nonzero(band.any(0))[0]
    return dict(top=int(y0), bottom=int(y1), feet_cx=float(fx.mean()), body=body)


def guide_geom(g):
    b = g.body if g.body.any() else g.mask
    ys, xs = np.nonzero(b)
    y1 = ys.max()
    fx = np.nonzero(b[max(y1 - 1, 0):y1 + 1].any(0))[0]
    top = int(np.nonzero(g.mask.any(1))[0].min())     # bow included, sword excluded below the feet
    return dict(top=min(top, int(ys.min())), bottom=int(y1), feet_cx=float(fx.mean()),
                mx=float(xs.mean()) + 0.5)


def place(rgba_crop, s, ox, oy, premult=True):
    """resize the crop by s (BOX) and paste with its top-left at integer (ox, oy) in a 128 cell.
    -> (rgb float HxWx3, coverage float HxW) in cell space."""
    im = Image.fromarray(rgba_crop, "RGBA")
    rw, rh = max(1, int(round(im.width * s))), max(1, int(round(im.height * s)))
    if premult:
        sm = np.array(im.convert("RGBa").resize((rw, rh), Image.BOX).convert("RGBA")).astype(float)
    else:
        sm = np.array(im.resize((rw, rh), Image.BOX)).astype(float)
    cell = np.zeros((CELL, CELL, 4), float)
    x0, y0 = int(ox), int(oy)
    cx0, cy0 = max(0, x0), max(0, y0)
    cx1, cy1 = min(CELL, x0 + rw), min(CELL, y0 + rh)
    if cx1 > cx0 and cy1 > cy0:
        cell[cy0:cy1, cx0:cx1] = sm[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]
    return cell[..., :3], cell[..., 3] / 255.0


def place_alpha(mask_crop, s, ox, oy):
    im = Image.fromarray((mask_crop * 255).astype(np.uint8), "L")
    rw, rh = max(1, int(round(im.width * s))), max(1, int(round(im.height * s)))
    sm = np.array(im.resize((rw, rh), Image.BOX)) >= 128
    cell = np.zeros((CELL, CELL), bool)
    x0, y0 = int(ox), int(oy)
    cx0, cy0 = max(0, x0), max(0, y0)
    cx1, cy1 = min(CELL, x0 + rw), min(CELL, y0 + rh)
    if cx1 > cx0 and cy1 > cy0:
        cell[cy0:cy1, cx0:cx1] = sm[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]
    return cell


def iou(a, b):
    u = (a | b).sum()
    return float((a & b).sum() / u) if u else 0.0


def solve_placement(geo, crop_xy, s, target_bottom, target_cx, target_mx=None):
    """integer top-left so that the source body bottom row lands on target_bottom and the feet
    centre on target_cx."""
    cx0, cy0 = crop_xy
    # feet centre measured over the same band as the guide's (bottom 2 cell rows = 2/s src rows)
    b = geo["body"]
    band = b[max(geo["bottom"] + 1 - int(round(2 / max(s, 1e-6))), 0):geo["bottom"] + 1]
    fx = np.nonzero(band.any(0))[0]
    feet = float(fx.mean()) if len(fx) else geo["feet_cx"]
    oy = target_bottom + 1 - (geo["bottom"] + 1 - cy0) * s
    if target_mx is not None:
        # with a guide: match the body (sword-free) centroid x, more robust than 1 px tail tips
        mx = float(np.nonzero(b)[1].mean())
        return int(round(target_mx - (mx + 0.5 - cx0) * s + 0.5)), int(round(oy))
    ox = target_cx - (feet + 0.5 - cx0) * s + 0.5
    return int(round(ox)), int(round(oy))


def similarity(P, Q):
    """least-squares scale + translation (no rotation) mapping P -> Q."""
    P, Q = np.asarray(P, float), np.asarray(Q, float)
    pm, qm = P.mean(0), Q.mean(0)
    den = ((P - pm) ** 2).sum()
    s = float(((P - pm) * (Q - qm)).sum() / den) if den > 0 else 1.0
    return s, qm - s * pm


# ================================================================ 5. outline
def outline_selout(idx, cls, op, mode="auto", baseline=None, protect=None):
    """idx palette-index image (-1 transparent), cls base-class map.  Returns new idx (and op)."""
    pal = H.palette()
    OL = pal.index["outline"]
    out = idx.copy()
    if mode == "keep":
        return out, op
    tr = [~shift(op, dy, dx, False) for dy, dx in N4]          # up, down, left, right transparent
    ext = op & (tr[0] | tr[1] | tr[2] | tr[3])
    interior = op & ~ext
    steel_b = BASE.index("steel")
    protect = protect if protect is not None else np.zeros_like(op)
    thin = np.zeros_like(op)
    for y, x in zip(*np.nonzero(ext)):
        if protect[y, x] or cls[y, x] == steel_b:
            continue
        # material from the inward neighbour (opposite the outside), else any interior neighbour
        m = None
        order = []
        if tr[0][y, x]:
            order.append((1, 0))
        if tr[2][y, x]:
            order.append((0, 1))
        if tr[1][y, x]:
            order.append((-1, 0))
        if tr[3][y, x]:
            order.append((0, -1))
        order += [d for d in [(1, 0), (0, 1), (-1, 0), (0, -1)] if d not in order]
        for dy, dx in order:
            yy, xx = y + dy, x + dx
            if 0 <= yy < CELL and 0 <= xx < CELL and interior[yy, xx]:
                m = cls[yy, xx]
                break
        if m is None:
            thin[y, x] = True
            if mode == "inner":
                out[y, x] = OL
            continue
        if mode == "outer":
            continue
        mat = BASE[m]
        lit = (tr[0][y, x] or tr[2][y, x]) and not (tr[1][y, x] or tr[3][y, x])
        ground = baseline is not None and y >= baseline - 1
        tone = H.SELOUT_LIT.get(mat)
        if mat == "steel" or tone is None:
            continue
        out[y, x] = pal.index[tone] if (lit and not ground) else OL
    newop = op.copy()
    if mode in ("auto", "outer"):
        src = thin & ~protect if mode == "auto" else (ext & ~protect & (cls != steel_b))
        grow = np.zeros_like(op)
        for dy, dx in N4:
            grow |= shift(src, dy, dx, False)
        grow &= ~op
        out[grow] = OL
        newop |= grow
    return out, newop


# ================================================================ 6. cleanup
def safe_clean(idx, cls, protect, baseline=None, keep=H.ORPHAN_OK, passes=2):
    pal = H.palette()
    OL = pal.index["outline"]
    keep_ids = set(H.names_to_idx(keep))
    stats = dict(orphans=0, notches=0, spurs=0, doubles=0)
    idx = idx.copy()
    for _ in range(passes):
        op = idx != -1
        # --- orphans
        same = np.zeros(idx.shape, int)
        for dy, dx in N8:
            same += shift(idx, dy, dx, -9) == idx
        orph = op & (same == 0) & ~protect
        for y, x in zip(*np.nonzero(orph)):
            v = idx[y, x]
            if v in keep_ids:
                continue
            nb = [idx[y + dy, x + dx] for dy, dx in N8 if 0 <= y + dy < CELL and 0 <= x + dx < CELL]
            nb = [n for n in nb if n >= 0]
            if not nb:
                continue
            vb = H.name_base(pal.names[v])
            same_ramp = [n for n in nb if H.name_base(pal.names[n]) == vb and n != v]
            pool = same_ramp or nb
            vals, cnt = np.unique(pool, return_counts=True)
            idx[y, x] = vals[cnt.argmax()]
            stats["orphans"] += 1
        op = idx != -1
        # --- notches / holes: transparent px with >= 3 opaque 4-nbrs whose open side is outside
        opn = sum(shift(op, dy, dx, False).astype(int) for dy, dx in N4)
        for y, x in zip(*np.nonzero(~op & (opn >= 3))):
            if not (0 < y < CELL - 1 and 0 < x < CELL - 1):
                continue
            if opn[y, x] == 3:
                oy, ox = [(y + dy, x + dx) for dy, dx in N4 if not op[y + dy, x + dx]][0]
                if 0 < oy < CELL - 1 and 0 < ox < CELL - 1:
                    o_n = sum(op[oy + dy, ox + dx] for dy, dx in N4)
                    if o_n >= 2:          # a 1 px channel (gap between legs), not a dent
                        continue
            nb = [idx[y + dy, x + dx] for dy, dx in N4 if idx[y + dy, x + dx] >= 0]
            vals, cnt = np.unique(nb, return_counts=True)
            idx[y, x] = vals[cnt.argmax()]
            stats["notches"] += 1
        op = idx != -1
        # --- spurs: 1 px teeth hanging by a single 8-neighbour
        tr4 = sum((~shift(op, dy, dx, False)).astype(int) for dy, dx in N4)
        n8 = sum(shift(op, dy, dx, False).astype(int) for dy, dx in N8)
        sp = op & (tr4 >= 3) & (n8 <= 1) & ~protect
        if baseline is not None:
            sp[baseline - 1:] = False
        stats["spurs"] += int(sp.sum())
        idx[sp] = -1
    # --- doubled outline: interior outline px touching the exterior outline, with no interior
    #     outline neighbour (a bump, not an interior line), on cloth / skin / hair
    op = idx != -1
    ext = op & ~(shift(op, -1, 0, False) & shift(op, 1, 0, False) & shift(op, 0, -1, False) & shift(op, 0, 1, False))
    olm = idx == OL
    soft = np.isin(cls, [BASE.index(b) for b in ("red", "skin", "pink", "hair")])
    cand = olm & ~ext & soft & ~protect
    for y, x in zip(*np.nonzero(cand)):
        touches_ext_ol = any(0 <= y + dy < CELL and 0 <= x + dx < CELL and ext[y + dy, x + dx] and olm[y + dy, x + dx]
                             for dy, dx in N4)
        inner_ol = any(0 <= y + dy < CELL and 0 <= x + dx < CELL and olm[y + dy, x + dx] and not ext[y + dy, x + dx]
                       for dy, dx in N4)
        if touches_ext_ol and not inner_ol:
            nb = [idx[y + dy, x + dx] for dy, dx in N8 if 0 <= y + dy < CELL and 0 <= x + dx < CELL]
            nb = [n for n in nb if n >= 0 and n != OL]
            if nb:
                vals, cnt = np.unique(nb, return_counts=True)
                idx[y, x] = vals[cnt.argmax()]
                stats["doubles"] += 1
    return idx, stats


# ================================================================ pipeline
def pixelize(inp, guide=None, height=60, bg="auto", crop=None, fit="iou", src_joints=None, down="box",
             quant="material", outline="auto", clean=True, guide_mat=True, baseline=PIVOT[1],
             pivot_x=PIVOT[0], penalty=6.0, tol=11.0, verbose=True, pick=None):
    img = Image.open(inp)
    if crop:
        img = img.crop(crop)
    rgb, mask, bgmode = remove_bg(img, bg, tol)
    if pick is not None:
        mask = pick_figure(mask, pick)
    if not mask.any():
        raise SystemExit(f"{inp}: background removal left nothing")
    ys, xs = np.nonzero(mask)
    bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    rgba = np.dstack([rgb, mask * 255]).astype(np.uint8)
    rgba[~mask] = 0
    crop_a = rgba[by0:by1, bx0:bx1]
    geo = body_rows(rgb, mask)
    meta = dict(input=os.path.relpath(inp, H.ROOT) if os.path.isabs(inp) else inp, bg=bgmode,
                src_size=list(img.size), src_body=[geo["top"], geo["bottom"]], fit=fit)
    g = guide
    if g is not None:
        gg = guide_geom(g)
        tgt_h = gg["bottom"] - gg["top"] + 1
        tgt_bottom, tgt_cx, tgt_mx = gg["bottom"], gg["feet_cx"], gg["mx"]
    else:
        tgt_h, tgt_bottom, tgt_cx, tgt_mx = height, baseline, pivot_x, None
    s = tgt_h / (geo["bottom"] - geo["top"] + 1)
    ox, oy = solve_placement(geo, (bx0, by0), s, tgt_bottom, tgt_cx, tgt_mx)
    if fit == "joints" and g is not None and src_joints:
        J = json.load(open(src_joints))
        J = J.get("joints", J)
        common = [k for k in J if k in g.joints]
        if len(common) >= 2:
            s, t = similarity([J[k][:2] for k in common], [g.joints[k] for k in common])
            ox = int(round(t[0] + bx0 * s))
            oy = int(round(t[1] + by0 * s))
            meta["joints_used"] = common
        else:
            print(f"  --fit joints: only {common} shared with the guide; falling back to bbox fit")
    if g is not None and fit in ("iou", "joints"):
        m_crop = mask[by0:by1, bx0:bx1]
        best = (iou(place_alpha(m_crop, s, ox, oy), g.mask), s, ox, oy)
        for f in np.linspace(0.94, 1.06, 13):
            s2 = s * f
            bx, byy = solve_placement(geo, (bx0, by0), s2, tgt_bottom, tgt_cx, tgt_mx) if fit == "iou" else (ox, oy)
            for dy in (-1, 0, 1):
                for dx in range(-4, 5):
                    sc = iou(place_alpha(m_crop, s2, bx + dx, byy + dy), g.mask)
                    if sc > best[0] + 1e-9:
                        best = (sc, s2, bx + dx, byy + dy)
        _, s, ox, oy = best
    # ---- 3. downsample
    if down == "mode":
        cls_hr, C_hr = H.classify(crop_a[..., :3].astype(float))
        cls_hr = H.resolve_steel(cls_hr, C_hr, crop_a[..., :3].astype(float), crop_a[..., 3] > 0,
                                 min_px=int(6 / max(s, 1e-3) ** 2))
        idx_hr = H.quantize_tones(crop_a[..., :3].astype(float), cls_hr)
        idx_hr[crop_a[..., 3] == 0] = -1
        pal = H.palette()
        cov_best = np.zeros((CELL, CELL))
        idx = np.full((CELL, CELL), -1, int)
        for k in range(len(pal.names)):
            m = idx_hr == k
            if not m.any():
                continue
            c = np.zeros((CELL, CELL))
            _, cov = place(np.dstack([np.zeros(m.shape + (3,), np.uint8), m * 255]).astype(np.uint8), s, ox, oy, False)
            c = cov
            upd = c > cov_best
            idx[upd] = k
            cov_best = np.maximum(cov_best, c)
        rgbc, cov = place(crop_a, s, ox, oy)
        op = cov >= 0.5
        idx[~op] = -1
        cls = np.full((CELL, CELL), -1, int)
        for k in range(len(pal.names)):
            b = H.name_base(pal.names[k])
            if b in BASE:
                cls[idx == k] = BASE.index(b)
        # outline pixels: class from classification of the box colour
        c2, _ = H.classify(np.where(op[..., None], rgbc / np.maximum(cov[..., None], 1e-6), 0))
        cls[cls < 0] = c2[cls < 0]
    else:
        rgbc, cov = place(crop_a, s, ox, oy)
        op = cov >= 0.5
        col = np.clip(rgbc / np.maximum(cov[..., None], 1e-6), 0, 255)
        # ---- 4. quantize
        if quant == "nearest":
            pal = H.palette()
            P = np.array(pal.rgb, float)
            d = ((col[:, :, None, :] - P[None, None]) ** 2).sum(-1)
            idx = d.argmin(-1)
            cls = np.array([BASE.index(H.name_base(n)) if H.name_base(n) in BASE else 0 for n in pal.names])[idx]
        else:
            allowed = g.mat if (g is not None and guide_mat and quant == "material") else None
            cls, C = H.classify(col, allowed, penalty)
            cls = H.resolve_steel(cls, C, col, op, g.sword if g is not None else None)
            idx = H.quantize_tones(col, cls)
        idx[~op] = -1
    # ---- 5. outline + 6. clean
    protect = np.zeros((CELL, CELL), bool)
    steel = (cls == BASE.index("steel")) & op
    if steel.any():
        lab_s, sz = label_cc(steel, 8)
        protect = np.isin(lab_s, np.nonzero(sz >= 4)[0]) & steel
    if g is not None:
        protect |= g.sword & op
    protect_r = disk_op(protect, 1) & op
    feet_row = int(np.nonzero(op.any(1))[0].max()) if op.any() else baseline
    idx, op2 = outline_selout(idx, cls, op, outline, feet_row, protect_r)
    st = {}
    if clean:
        idx, st = safe_clean(idx, cls, protect_r, feet_row)
    out = H.rgba_of(idx)
    out[idx == -1] = 0
    meta.update(scale=round(float(s), 5), offset=[int(ox), int(oy)], downsample=down, quant=quant,
                outline=outline, clean=st, guide=getattr(g, "prefix", None))
    if g is not None:
        meta["iou"] = round(iou(idx != -1, g.mask), 4)
        meta["iou_body"] = round(iou((idx != -1) & ~disk_op(g.sword, 1), g.body), 4)
    F = H.features(out)
    meta.update(height=F.get("height"), body_height=F.get("body_height"), baseline=F.get("baseline"),
                feet_cx=F.get("feet_cx"), colours=int(len(np.unique(idx[idx >= 0]))),
                opaque=int((idx >= 0).sum()))
    # aligned hi-res at 4x cell
    hi = Image.new("RGBA", (CELL * 4, CELL * 4), (0, 0, 0, 0))
    cim = Image.fromarray(crop_a, "RGBA")
    rw, rh = max(1, int(round(cim.width * s * 4))), max(1, int(round(cim.height * s * 4)))
    big = cim.resize((rw, rh), Image.LANCZOS)
    hi.paste(big, (int(ox) * 4, int(oy) * 4), big)
    return out, cls, meta, np.array(hi)


def dbg_sheet(out, cls, hi, g, meta):
    z = 4
    tiles = []
    m = out[..., 3] > 0
    if g is not None:
        m = m | g.mask
    ys, xs = np.nonzero(m) if m.any() else (np.array([0, CELL - 1]), np.array([0, CELL - 1]))
    y0, y1 = max(ys.min() - 3, 0), min(ys.max() + 4, CELL)
    x0, x1 = max(xs.min() - 3, 0), min(xs.max() + 4, CELL)
    out = out[y0:y1, x0:x1]
    cls = cls[y0:y1, x0:x1]
    hi = hi[y0 * 4:y1 * 4, x0 * 4:x1 * 4]
    gm = g.mask[y0:y1, x0:x1] if g is not None else None
    bgc = (150, 150, 150, 255)

    def on(a, c=bgc):
        im = Image.new("RGBA", (a.shape[1], a.shape[0]), c)
        im.alpha_composite(Image.fromarray(a, "RGBA"))
        return im

    tiles.append(on(hi))
    tiles.append(on(H.up(out, z)))
    mc = np.zeros(out.shape, np.uint8)
    for i, b in enumerate(BASE):
        mc[(cls == i) & (out[..., 3] > 0)] = H.MAT_COLOR[b] + (255,)
    tiles.append(on(H.up(mc, z)))
    ov = H.up(out, z).copy()
    if gm is not None:
        e = gm & ~(shift(gm, -1, 0, False) & shift(gm, 1, 0, False) & shift(gm, 0, -1, False) & shift(gm, 0, 1, False))
        E = H.up(e, z)
        ov[E] = (0, 230, 255, 255)
    tiles.append(on(ov))
    W = sum(t.width for t in tiles) + 5 * (len(tiles) + 1)
    sheet = Image.new("RGBA", (max(W, 640), out.shape[0] * z + 40), (30, 24, 36, 255))
    x = 5
    for t, lab in zip(tiles, ["hi-res (aligned)", "sprite 4x", "ramp classes", "guide silhouette"]):
        sheet.paste(t, (x, 36))
        ImageDraw.Draw(sheet).text((x + 2, 22), lab, fill=(240, 240, 240, 255))
        x += t.width + 5
    txt = f"h={meta.get('height')} scale={meta['scale']} iou={meta.get('iou', '-')} clean={meta.get('clean')}"
    ImageDraw.Draw(sheet).text((5, 5), txt, fill=(255, 220, 120, 255))
    return sheet


def write_outputs(path, out, cls, meta, hi, g, preview=True):
    st = os.path.splitext(path)[0]
    H.save_rgba(out, path)
    if preview:
        H.save_rgba(H.up(out, 4), st + "_4x.png")
        H.save_rgba(hi, st + "_hires.png")
        dbg_sheet(out, cls, hi, g, meta).save(st + "_dbg.png")
    json.dump(meta, open(st + "_meta.json", "w"), indent=1)


# ================================================================ regression
def regress(out_dir):
    """Rebuild docs/palette_v1_vs_v2_terrain.png with this module's legacy path (bg_legacy + crop +
    BOX to 56 px + global nearest, v2 with the warm-pixel dark[1] block) and diff it pixel-exactly.
    Also writes the new per-material pipeline's version of the same strip for eyeballing."""
    R = H.ROOT
    os.makedirs(out_dir, exist_ok=True)
    src = Image.open(os.path.join(R, "concept/chibi_iso_v5.png")).convert("RGB")
    rgb = np.array(src)
    mask = bg_legacy(rgb)
    im = Image.fromarray(np.dstack([rgb.astype(int), mask * 255]).astype(np.uint8), "RGBA")
    im = im.crop(im.getbbox())
    h = 56
    w = round(im.width * h / im.height)
    sm = im.resize((w, h), Image.BOX)

    def quant(img, pal, warm_block):
        cols = sorted({c for r in pal["ramps"].values() for c in r} | {pal["outline"]})
        P = np.array([[int(c[i:i + 2], 16) for i in (1, 3, 5)] for c in cols])
        x = np.array(img).astype(int)
        rgb_, al = x[..., :3], x[..., 3] > 128
        d = ((rgb_[:, :, None, :] - P[None, None]) ** 2).sum(-1).astype(float)
        if warm_block:
            k = cols.index(pal["ramps"]["dark"][1])
            d[..., k] = np.where(rgb_[..., 0] >= rgb_[..., 2], 1e9, d[..., k])
        q = P[d.argmin(-1)]
        return Image.fromarray(np.dstack([q, al * 255]).astype(np.uint8), "RGBA")

    pals = [(json.load(open(os.path.join(R, "docs/palette_v1.json"))), False),
            (json.load(open(os.path.join(R, "docs/palette.json"))), True)]
    bgs = ["#2a2830", "#6b5440", "#4f7a3a"]

    rows = [quant(sm, p, m) for p, m in pals]
    # the original sheet is (w*3+40, h*2+30): rebuild with exactly that canvas
    canvas = Image.new("RGB", (w * 3 + 40, h * 2 + 30), "white")
    for r, q in enumerate(rows):
        for c, bgc in enumerate(bgs):
            t = Image.new("RGBA", (w + 10, h + 10), bgc)
            t.alpha_composite(q, (5, 5))
            canvas.paste(t.convert("RGB"), (c * (w + 12) + 4, r * (h + 14) + 4))
    out = canvas.resize((canvas.width * 5, canvas.height * 5), Image.NEAREST)
    p_out = os.path.join(out_dir, "regress_terrain_rebuild.png")
    out.save(p_out)
    ref = np.array(Image.open(os.path.join(R, "docs/palette_v1_vs_v2_terrain.png")).convert("RGB")).astype(int)
    A = np.array(out).astype(int)
    if A.shape != ref.shape:
        print(f"REGRESSION FAIL: shape {A.shape} vs {ref.shape}")
        return 1
    diff = int(np.any(A != ref, 2).sum())
    print(f"regression: legacy rebuild vs docs/palette_v1_vs_v2_terrain.png: {diff} differing px "
          f"of {ref.shape[0] * ref.shape[1]}  ({'PASS' if diff == 0 else 'FAIL'}) -> {os.path.relpath(p_out, R)}")
    # new pipeline, same concept, same 56 px, no guide (ramp clustering), plus legacy-bg variant
    variants = []
    for lbl, kw in [("v2 legacy", None),
                    ("new: flood bg, material ramps, sel-out, clean", dict(bg="auto")),
                    ("new: mode downsample", dict(bg="auto", down="mode"))]:
        if kw is None:
            variants.append((lbl, rows[1]))
            continue
        spr, cls, meta, hi = pixelize(os.path.join(R, "concept/chibi_iso_v5.png"), None, height=56, verbose=False, **kw)
        ys, xs = np.nonzero(spr[..., 3])
        variants.append((lbl, Image.fromarray(spr[ys.min():ys.max() + 1, xs.min():xs.max() + 1], "RGBA")))
        write_outputs(os.path.join(out_dir, f"iso_v5_{kw.get('down', 'box')}.png"), spr, cls, meta, hi, None)
    Wm = max(v.width for _, v in variants)
    Hm = max(v.height for _, v in variants)
    sheet = Image.new("RGB", ((Wm + 12) * 3 + 4, (Hm + 26) * len(variants) + 4), "white")
    d = ImageDraw.Draw(sheet)
    for r, (lbl, q) in enumerate(variants):
        d.text((4, r * (Hm + 26) + 4), lbl, fill=(0, 0, 0))
        for c, bgc in enumerate(bgs):
            t = Image.new("RGBA", (Wm + 10, Hm + 10), bgc)
            t.alpha_composite(q, (5 + (Wm - q.width) // 2, 5 + Hm - q.height))
            sheet.paste(t.convert("RGB"), (c * (Wm + 12) + 4, r * (Hm + 26) + 18))
    sheet = sheet.resize((sheet.width * 5, sheet.height * 5), Image.NEAREST)
    p2 = os.path.join(out_dir, "regress_terrain_new_vs_legacy.png")
    sheet.save(p2)
    print("new pipeline comparison ->", os.path.relpath(p2, R))
    return 0 if diff == 0 else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", nargs="?")
    ap.add_argument("--guide", default="none", help="guide prefix (see hylib.Guide) or 'none'")
    ap.add_argument("--out")
    ap.add_argument("--height", type=int, default=ap_defaults["height"], help="body height (no guide)")
    ap.add_argument("--bg", default="auto", choices=["auto", "alpha", "flood", "legacy"])
    ap.add_argument("--tol", type=float, default=11.0, help="flood background tolerance (Lab)")
    ap.add_argument("--crop", help="x0,y0,x1,y1 crop of the input before anything else")
    ap.add_argument("--pick", type=int, help="multi-figure sheet: keep figure K (0 = leftmost)")
    ap.add_argument("--fit", default="iou", choices=["iou", "joints", "none"])
    ap.add_argument("--src-joints", help="JSON {joints: {name: [x, y]}} in input px (for --fit joints)")
    ap.add_argument("--down", default="box", choices=["box", "mode"])
    ap.add_argument("--quant", default="material", choices=["material", "ramp", "nearest"])
    ap.add_argument("--outline", default="auto", choices=["auto", "inner", "outer", "keep"])
    ap.add_argument("--penalty", type=float, default=6.0, help="Lab penalty for ramps the guide material forbids")
    ap.add_argument("--no-guide-mat", action="store_true", help="ignore guide ids for quantization")
    ap.add_argument("--no-clean", action="store_true")
    ap.add_argument("--no-preview", action="store_true")
    ap.add_argument("--baseline", type=int, default=ap_defaults["baseline"])
    ap.add_argument("--pivot-x", type=int, default=ap_defaults["pivot_x"])
    ap.add_argument("--regress", action="store_true")
    ap.add_argument("--regress-dir", default=os.path.join(H.ROOT, "hybrid", "_pipeline_test"))
    a = ap.parse_args()
    if a.regress:
        sys.exit(regress(a.regress_dir))
    if not a.input or not a.out:
        ap.error("input and --out are required (or --regress)")
    g = H.load_guide(a.guide)
    crop = tuple(int(v) for v in a.crop.split(",")) if a.crop else None
    out, cls, meta, hi = pixelize(a.input, g, a.height, a.bg, crop, a.fit if g is not None else "none", a.src_joints,
                                  a.down, a.quant, a.outline, not a.no_clean, not a.no_guide_mat, a.baseline,
                                  a.pivot_x, a.penalty, a.tol, pick=a.pick)
    write_outputs(a.out, out, cls, meta, hi, g, not a.no_preview)
    print(f"pixelize {os.path.basename(a.input)} -> {a.out}  h={meta['height']} body_h={meta['body_height']} "
          f"base={meta['baseline']} feet_cx={meta['feet_cx'] and round(meta['feet_cx'], 1)} scale={meta['scale']} "
          f"iou={meta.get('iou', '-')} colours={meta['colours']} clean={meta['clean']}")


if __name__ == "__main__":
    main()
