"""Pixel lint (detector only: it REPORTS, humans decide).

  .venv/bin/python tools/pixel/lint.py --anim idle [--dir S] [--src clean|base] [--frame K] [--quiet]

Checks per frame (flag type -> meaning):
  off_palette     opaque pixel whose RGB is not in docs/palette.json
  semi_alpha      alpha not in {0, 255}
  orphan          opaque pixel with no same-colour 8-neighbour (eye glints etc. are legit - judge)
  outline_gap     silhouette-edge pixel (4-touches transparency) in a mid/light tone, i.e. not
                  outline / a selective-outline dark tone (SELOUT) / the pink rim -> hole in the 1px outline
  notch           transparent pixel with >= 3 opaque 4-neighbours (1px dent in the silhouette)
  spur            opaque pixel with >= 3 transparent 4-neighbours (1px tooth sticking out)
  double          outline-colour silhouette pixel forming an L-corner whose removal keeps the line
                  8-connected ("pixel-perfect" doubles / thick stair corners)
  jaggy           irregular stair on the silhouette profile: a run 2+ px shorter/longer than both
                  neighbouring runs of a monotone slope (e.g. 3-1-3 or 1-4-1)
  banding         >= 5 connected px of a 1px band of one ramp tone sandwiched between the outline
                  and another tone of the same ramp (tone lines parallel to the outline)
  inner_break     1px gap between two end-points of an interior outline-colour line
  flicker         pixel that toggles A -> B -> A over consecutive frames while its 5x5
                  neighbourhood is static (loops wrap around)
  pivot           per-frame feet baseline (lowest body row, sword excluded) / feet centre x;
                  direction summary reports drift (max - min) and offset from the pivot (64, 104)
  colours         colour count per frame (summary only)
Region tags come from the object-ID pass (pixel/base/<anim>/_id) when present.  Sword / kagi
pixels are excluded from spur / jaggy / double / orphan (thin diagonal blade by design) and
reported as 'info' only.
Writes pixel/lint/<anim>_<src>.json (+ prints a per-direction table).
"""
import argparse
import json
import os
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pxlib import PIVOT, PIXEL, Palette, anim_loops, dirs_of, frame_path, frames_of, load_rgba, rel  # noqa: E402

# selective-outline tones allowed on the silhouette edge besides the outline (sprite_post LIT side)
SELOUT = {"outline", "skin_0", "red_0", "red_1", "steel_0", "hair_0", "pink_0", "leather_1", "dark_1", "purple_0"}
THIN_GROUPS = {"sword", "kagi"}
N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
N4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def shift(m, dy, dx, fill=0):
    """out[y, x] = m[y + dy, x + dx]"""
    H, W = m.shape[:2]
    out = np.full_like(m, fill)
    ys0, ys1 = max(0, -dy), min(H, H - dy)
    xs0, xs1 = max(0, -dx), min(W, W - dx)
    out[ys0:ys1, xs0:xs1] = m[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
    return out


def index_image(a, pal):
    """-> int image: palette index, -1 transparent, -2 off-palette"""
    H, W = a.shape[:2]
    idx = np.full((H, W), -1, int)
    op = a[..., 3] > 0
    lut = {c: i for i, c in enumerate(pal.rgb)}
    for y, x in zip(*np.nonzero(op)):
        idx[y, x] = lut.get(tuple(int(v) for v in a[y, x, :3]), -2)
    return idx


def load_groups(anim, d, k):
    p = os.path.join(PIXEL, "base", anim, "_id", d, f"f{k:02d}.png")
    gp = os.path.join(PIXEL, "base", anim, "_id", "id_groups.json")
    if not os.path.exists(p) or not os.path.exists(gp):
        return None, {}
    names = {v: g for g, v in json.load(open(gp))["groups"].items()}
    a = load_rgba(p)
    ids = np.rint(a[..., 0] / 10.0).astype(int)
    ids[a[..., 3] < 128] = 0
    # the outline ring is added after the ID pass: give ring pixels the id of an adjacent body pixel
    for _ in range(2):
        z = ids == 0
        for dy, dx in N4:
            s = shift(ids, dy, dx)
            ids = np.where(z & (s > 0), s, ids)
            z = ids == 0
    return ids, names


def comp_sizes(mask):
    H, W = mask.shape
    lab = np.zeros((H, W), int)
    sizes = [0]
    n = 0
    for y, x in zip(*np.nonzero(mask)):
        if lab[y, x]:
            continue
        n += 1
        st = [(y, x)]
        lab[y, x] = n
        c = 0
        while st:
            cy, cx = st.pop()
            c += 1
            for dy, dx in N8:
                yy, xx = cy + dy, cx + dx
                if 0 <= yy < H and 0 <= xx < W and mask[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n
                    st.append((yy, xx))
        sizes.append(c)
    return lab, np.array(sizes)


def runs(p):
    """profile array (nan = no pixel) -> list of (value, start, length) runs of equal values"""
    out = []
    i = 0
    while i < len(p):
        if np.isnan(p[i]):
            i += 1
            continue
        j = i
        while j + 1 < len(p) and p[j + 1] == p[i]:
            j += 1
        out.append((p[i], i, j - i + 1))
        i = j + 1
    return out


def stair_flags(p, axis_is_y):
    """irregular run in a monotone unit-step staircase of a silhouette profile"""
    res = []
    rs = runs(p)
    for (v1, s1, l1), (v2, s2, l2), (v3, s3, l3) in zip(rs, rs[1:], rs[2:]):
        if s2 != s1 + l1 or s3 != s2 + l2:
            continue                       # gap in the profile
        d1, d2 = v2 - v1, v3 - v2
        if d1 == 0 or d2 == 0 or np.sign(d1) != np.sign(d2) or abs(d1) != 1 or abs(d2) != 1:
            continue
        if (l2 + 2 <= min(l1, l3)) or (l2 >= max(l1, l3) + 2):
            for t in range(s2, s2 + l2):
                res.append((int(v2), t) if axis_is_y else (t, int(v2)))
            # report the middle run as (x, y) list
    return res, rs


def lint_frame(a, pal, ids=None, gnames=None):
    H, W = a.shape[:2]
    gnames = gnames or {}
    alpha = a[..., 3]
    op = alpha > 0
    idx = index_image(a, pal)
    OL = pal.index["outline"]
    flags = []
    if ids is not None and gnames:
        # The ID pass tags hand-painted steel (e.g. the inner, background-facing side of the kagi
        # crescent, drawn where the render had skirt) by the part it replaced.  A steel-coloured
        # 8-connected cluster that touches a sword/kagi-tagged pixel is sword/kagi: retag the whole
        # cluster so R22 (hook outlined on its outer side only) does not read as outline_gap.
        # Isolated steel elsewhere (buckles, eye glints, strays) keeps its own tag.
        thin_ids = {v for v, g in gnames.items() if g in THIN_GROUPS}
        steel = np.isin(idx, [pal.index[n] for n in pal.names if n.startswith("steel_")])
        if thin_ids and steel.any():
            ids = ids.copy()
            lab_s, _ = comp_sizes(steel)
            for k in range(1, int(lab_s.max()) + 1):
                m = lab_s == k
                hit = [v for v in np.unique(ids[m]).tolist() if v in thin_ids]
                if hit:
                    ids[m & ~np.isin(ids, list(thin_ids))] = hit[0]

    def region(x, y):
        if ids is None:
            return None
        return gnames.get(int(ids[y, x]))

    def add(t, x, y, detail="", sev="warn"):
        r = region(x, y)
        if r in THIN_GROUPS and t in ("spur", "jaggy", "double", "orphan", "notch", "outline_gap"):
            sev = "info"
        f = {"type": t, "x": int(x), "y": int(y), "sev": sev}
        if detail:
            f["detail"] = detail
        if r:
            f["region"] = r
        flags.append(f)

    for y, x in zip(*np.nonzero(idx == -2)):
        add("off_palette", x, y, "#%02x%02x%02x" % tuple(a[y, x, :3]), "error")
    for y, x in zip(*np.nonzero((alpha > 0) & (alpha < 255))):
        add("semi_alpha", x, y, f"alpha={int(alpha[y, x])}", "error")
    # orphans
    same = np.zeros((H, W), int)
    for dy, dx in N8:
        same += (shift(idx, dy, dx, -9) == idx)
    for y, x in zip(*np.nonzero(op & (same == 0))):
        add("orphan", x, y, pal.names[idx[y, x]] if idx[y, x] >= 0 else "off")
    # silhouette tests
    tr4 = np.zeros((H, W), int)
    opn4 = np.zeros((H, W), int)
    for dy, dx in N4:
        tr4 += ~shift(op, dy, dx, False)
        opn4 += shift(op, dy, dx, False)
    edge = op & (tr4 > 0)
    for y, x in zip(*np.nonzero(edge)):
        v = idx[y, x]
        if v >= 0 and pal.names[v] not in SELOUT:
            add("outline_gap", x, y, pal.names[v])
    for y, x in zip(*np.nonzero(~op & (opn4 >= 3))):
        if 0 < x < W - 1 and 0 < y < H - 1:
            add("notch", x, y, f"{int(opn4[y, x])} opaque 4-nbrs")
    for y, x in zip(*np.nonzero(op & (tr4 >= 3))):
        add("spur", x, y, pal.names[idx[y, x]] if idx[y, x] >= 0 else "off")
    # doubles: outline L-corners on the silhouette
    olm = idx == OL
    for y, x in zip(*np.nonzero(olm & edge)):
        for hx_ in (-1, 1):
            for vy in (-1, 1):
                h_ok = 0 <= x + hx_ < W and olm[y, x + hx_]
                v_ok = 0 <= y + vy < H and olm[y + vy, x]
                if not (h_ok and v_ok):
                    continue
                dy_, dx_ = y + vy, x + hx_
                inner = 0 <= dy_ < H and 0 <= dx_ < W and op[dy_, dx_] and not olm[dy_, dx_]
                # opposite sides of P must be transparent (P is the outer corner of the L)
                ox, oy = x - hx_, y - vy
                outer = (not (0 <= ox < W) or not op[y, ox]) and (not (0 <= oy < H) or not op[oy, x])
                if inner and outer:
                    add("double", x, y, "L-corner; removable without breaking the 8-connected line")
    # jaggies on the silhouette profiles (left/right per row, top/bottom per column)
    rows = np.nonzero(op.any(axis=1))[0]
    cols = np.nonzero(op.any(axis=0))[0]
    L = np.full(H, np.nan)
    R = np.full(H, np.nan)
    T = np.full(W, np.nan)
    B = np.full(W, np.nan)
    for y in rows:
        xs = np.nonzero(op[y])[0]
        L[y], R[y] = xs.min(), xs.max()
    for x in cols:
        ys = np.nonzero(op[:, x])[0]
        T[x], B[x] = ys.min(), ys.max()
    seen = set()
    for prof, axis_is_y in ((L, True), (R, True), (T, False), (B, False)):
        pts, _ = stair_flags(prof, axis_is_y)
        for x, y in pts:
            if (x, y) not in seen:
                seen.add((x, y))
                add("jaggy", x, y, "irregular stair run")
    # banding: 1px tone band between the outline and another tone of the same ramp
    band = np.zeros((H, W), bool)
    for y, x in zip(*np.nonzero(op & ~olm & (idx >= 0))):
        nm = pal.names[idx[y, x]]
        rp = pal.ramp_of.get(nm, (None,))[0]
        if rp is None:
            continue
        for dy, dx in N4:
            y1, x1, y2, x2 = y + dy, x + dx, y - dy, x - dx
            if not (0 <= y1 < H and 0 <= x1 < W and 0 <= y2 < H and 0 <= x2 < W):
                continue
            if idx[y1, x1] == OL and idx[y2, x2] >= 0 and idx[y2, x2] != idx[y, x] and idx[y2, x2] != OL:
                n2 = pal.names[idx[y2, x2]]
                if pal.ramp_of.get(n2, (None,))[0] == rp:
                    band[y, x] = True
                    break
    lab, sz = comp_sizes(band)
    for k in range(1, len(sz)):
        if sz[k] >= 5:
            ys, xs = np.nonzero(lab == k)
            j = len(ys) // 2
            add("banding", xs[j], ys[j], f"{sz[k]} px band of {pal.names[idx[ys[j], xs[j]]]} along the outline")
    # inner outline breaks: endpoints of interior outline lines, 1px apart
    interior_ol = olm & (tr4 == 0)
    nb = np.zeros((H, W), int)
    for dy, dx in N8:
        nb += shift(olm, dy, dx, False)
    ends = list(zip(*np.nonzero(interior_ol & (nb == 1))))
    done = set()
    for i, (y1, x1) in enumerate(ends):
        for (y2, x2) in ends[i + 1:]:
            if max(abs(y1 - y2), abs(x1 - x2)) == 2:
                my, mx = (y1 + y2) // 2, (x1 + x2) // 2
                if op[my, mx] and not olm[my, mx] and (mx, my) not in done:
                    done.add((mx, my))
                    add("inner_break", mx, my, f"gap between line ends ({x1},{y1}) and ({x2},{y2})")
    # pivot / feet
    body = op.copy()
    if ids is not None:
        for g, nm in gnames.items():
            if nm in THIN_GROUPS:
                body &= ids != g
    piv = None
    if body.any():
        by = int(np.nonzero(body.any(axis=1))[0].max())
        xs = np.nonzero(body[max(by - 1, 0):by + 1].any(axis=0))[0]
        piv = {"baseline_y": by, "feet_x0": int(xs.min()), "feet_x1": int(xs.max()), "feet_cx": round(float(xs.mean()), 1)}
    colours = sorted(pal.names[v] for v in set(np.unique(idx[idx >= 0]).tolist()))
    return flags, {"pivot": piv, "colours": colours, "n_colours": len(colours) + int((idx == -2).any()),
                   "opaque_px": int(op.sum())}, idx


def flicker(idxs, loop):
    """idxs: list of index images (consecutive frames). -> {k: [(x, y, A, B)]}"""
    n = len(idxs)
    out = {k: [] for k in range(n)}
    if n < 3:
        return out
    ks = range(n) if loop else range(1, n - 1)
    for k in ks:
        p, c, nx = idxs[(k - 1) % n], idxs[k], idxs[(k + 1) % n]
        tog = (p == nx) & (c != p)
        if not tog.any():
            continue
        H, W = c.shape
        for y, x in zip(*np.nonzero(tog)):
            y0, y1, x0, x1 = max(y - 2, 0), min(y + 3, H), max(x - 2, 0), min(x + 3, W)
            pw, cw, nw = p[y0:y1, x0:x1], c[y0:y1, x0:x1], nx[y0:y1, x0:x1]
            if (pw != nw).any():
                continue                       # neighbourhood moving between k-1 and k+1
            if (cw != pw).sum() > 2:
                continue                       # more than a 1-2 px blink: real motion
            out[k].append((int(x), int(y), int(p[y, x]), int(c[y, x])))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anim", default="idle")
    ap.add_argument("--dir")
    ap.add_argument("--frame", type=int)
    ap.add_argument("--src", default="clean", choices=["clean", "base"])
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    pal = Palette()
    src = a.src
    dirs = [a.dir] if a.dir else dirs_of(a.anim, src)
    if not dirs and src == "clean":
        print("no clean frames (run px.py apply); linting base")
        src = "base"
        dirs = [a.dir] if a.dir else dirs_of(a.anim, src)
    report = {"anim": a.anim, "src": src, "dirs": {}}
    loop = anim_loops(a.anim)
    for d in dirs:
        ks = frames_of(a.anim, d, src)
        fr, idxs = {}, []
        for k in ks:
            img = load_rgba(frame_path(src, a.anim, d, k))
            ids, gn = load_groups(a.anim, d, k)
            flags, info, idx = lint_frame(img, pal, ids, gn)
            idxs.append(idx)
            fr[k] = {"flags": flags, **info}
        for k, lst in flicker(idxs, loop).items():
            for x, y, A, B in lst:
                nm = lambda v: "clear" if v == -1 else (pal.names[v] if v >= 0 else "off")
                fr[ks[k]]["flags"].append({"type": "flicker", "x": x, "y": y, "sev": "warn",
                                           "detail": f"{nm(A)} -> {nm(B)} -> {nm(A)} (f{ks[(k - 1) % len(ks)]:02d}..f{ks[(k + 1) % len(ks)]:02d})"})
        pv = [fr[k]["pivot"] for k in ks if fr[k]["pivot"]]
        piv = {}
        if pv:
            bys = [p["baseline_y"] for p in pv]
            cxs = [p["feet_cx"] for p in pv]
            piv = {"baseline_min": min(bys), "baseline_max": max(bys), "baseline_drift": max(bys) - min(bys),
                   "baseline_offset_from_pivot": max(bys) - PIVOT[1],
                   "feet_cx_min": min(cxs), "feet_cx_max": max(cxs), "feet_cx_drift": round(max(cxs) - min(cxs), 1),
                   "feet_cx_offset_from_pivot": round(sum(cxs) / len(cxs) - PIVOT[0], 1)}
        tot = Counter()
        for k in ks:
            for f in fr[k]["flags"]:
                if f["sev"] != "info":
                    tot[f["type"]] += 1
            tot["info"] += sum(f["sev"] == "info" for f in fr[k]["flags"])
        report["dirs"][d] = {"frames": {f"f{k:02d}": fr[k] for k in ks}, "totals": dict(tot), "pivot": piv,
                             "colours_per_frame": [fr[k]["n_colours"] for k in ks]}
    os.makedirs(os.path.join(PIXEL, "lint"), exist_ok=True)
    outp = os.path.join(PIXEL, "lint", f"{a.anim}_{src}.json") if not a.dir else os.path.join(PIXEL, "lint", f"{a.anim}_{src}_{a.dir}.json")
    json.dump(report, open(outp, "w"), indent=1)
    types = ["off_palette", "semi_alpha", "orphan", "outline_gap", "notch", "spur", "double", "jaggy", "banding",
             "inner_break", "flicker"]
    hdr = f"{'dir':<4}" + "".join(f"{t[:9]:>10}" for t in types) + f"{'info':>6}{'colours':>9}{'base_y':>8}{'y_drift':>8}{'cx_drift':>9}"
    print(f"lint {a.anim} [{src}]  (warn/error counts; info = sword/kagi thin-line flags)")
    print(hdr)
    grand = Counter()
    for d, r in report["dirs"].items():
        t = r["totals"]
        grand.update(t)
        cpf = r["colours_per_frame"]
        p = r["pivot"]
        print(f"{d:<4}" + "".join(f"{t.get(x, 0):>10}" for x in types) + f"{t.get('info', 0):>6}"
              f"{f'{min(cpf)}-{max(cpf)}':>9}{p.get('baseline_max', '-'):>8}{p.get('baseline_drift', '-'):>8}{p.get('feet_cx_drift', '-'):>9}")
    print(f"{'ALL':<4}" + "".join(f"{grand.get(x, 0):>10}" for x in types) + f"{grand.get('info', 0):>6}")
    if not a.quiet and a.frame is not None:
        for d, r in report["dirs"].items():
            for f in r["frames"].get(f"f{a.frame:02d}", {}).get("flags", []):
                print(f"  {d} f{a.frame:02d} {f['type']:<12} ({f['x']},{f['y']}) {f.get('region', '')} {f.get('detail', '')}")
    print("report:", rel(outp))


if __name__ == "__main__":
    main()
