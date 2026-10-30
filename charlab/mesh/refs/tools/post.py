#!/usr/bin/env python3
"""Post-process Gemini reference renders into image->3D inputs.

usage: post.py <id>            (reads refs/<id>/src.json, writes refs/<id>/*.png, 512/, meta.json, checks.json, sheet.png)

src.json: {"views": [{"view": "front", "src": "raw/x.png", "fig": 0, "flip": false, "group": "body"}, ...],
           "yaw": {"front": 0, ...}, "notes": "..."}
- Sheets are split into figures left-to-right by empty-column gaps in the matte; "fig" picks one.
- Matte: flood-fill of near-white pixels connected to the border (keeps interior whites like a tank top),
  cross-checked against rembg u2net (IoU logged). "matte": "rembg" in a view entry forces rembg.
- Body views: identical scale (body height = BODY_H of the canvas), feet on a shared baseline, x centred on the
  lower-leg/foot band. Head views: one shared scale for the group (largest head fits HEAD_H), shared baseline.
"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 1024
BODY_H, FEET_Y = 0.86, 0.93      # fraction of canvas
HEAD_H, HEAD_BASE = 0.84, 0.93

_rembg = None


def rembg_mask(rgb):
    global _rembg
    from rembg import new_session, remove
    if _rembg is None:
        _rembg = new_session("u2net")
    out = remove(Image.fromarray(rgb), session=_rembg)
    return np.array(out)[..., 3] > 127


def flood_mask(rgb, tol_min=232, tol_chroma=14):
    mn = rgb.min(-1).astype(int); mx = rgb.max(-1).astype(int)
    white = (mn >= tol_min) & ((mx - mn) <= tol_chroma)
    lab, n = ndi.label(white)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    bg = np.isin(lab, border[border > 0])
    fg = ~bg
    fg = ndi.binary_opening(fg, iterations=1)
    lab, n = ndi.label(fg)
    if n > 1:  # drop specks (< 0.05% of the image)
        sizes = ndi.sum(fg, lab, range(1, n + 1))
        keep = np.isin(lab, 1 + np.nonzero(sizes >= fg.size * 5e-4)[0])
        fg = keep
    return fg


def soft_alpha(mask):
    m = ndi.binary_erosion(mask, iterations=1).astype(np.float32)
    a = ndi.gaussian_filter(m, 0.8)
    return np.clip(a * 1.15, 0, 1)


def split_figures(mask):
    """Connected components of the matte; big ones (>=8% of fg) are figures, ordered by centroid x.
    Small blobs are attached to the nearest figure. Returns a list of full-size boolean masks."""
    lab, n = ndi.label(mask)
    if n == 0:
        return []
    sizes = ndi.sum(mask, lab, range(1, n + 1))
    cents = ndi.center_of_mass(mask, lab, range(1, n + 1))
    big = [i for i in range(n) if sizes[i] >= 0.08 * sizes.sum()]
    big.sort(key=lambda i: cents[i][1])
    figs = [lab == (i + 1) for i in big]
    for i in range(n):
        if i in big:
            continue
        j = int(np.argmin([abs(cents[i][1] - cents[k][1]) + abs(cents[i][0] - cents[k][0]) for k in big]))
        figs[j] |= lab == (i + 1)
    return figs


def iou(a, b):
    return float((a & b).sum() / max(1, (a | b).sum()))


def bbox(m):
    ys, xs = np.nonzero(m)
    return ys.min(), ys.max() + 1, xs.min(), xs.max() + 1


def place(rgb, alpha, scale, anchor_src, anchor_dst):
    """Scale RGBA by `scale`, put src point anchor_src (x,y) at anchor_dst on an SxS canvas."""
    ys, xs = np.nonzero(alpha > 0.01)
    y0, y1, x0, x1 = max(0, ys.min() - 2), ys.max() + 3, max(0, xs.min() - 2), xs.max() + 3
    rgb, alpha = rgb[y0:y1, x0:x1], alpha[y0:y1, x0:x1]
    anchor_src = (anchor_src[0] - x0, anchor_src[1] - y0)
    h, w = alpha.shape
    rgba = np.dstack([rgb, (alpha * 255).astype(np.uint8)])
    im = Image.fromarray(rgba, "RGBA")
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    im = im.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", (S, S), (255, 255, 255, 0))
    ox = round(anchor_dst[0] - anchor_src[0] * scale)
    oy = round(anchor_dst[1] - anchor_src[1] * scale)
    canvas.alpha_composite(im, (ox, oy)) if (ox >= 0 and oy >= 0) else canvas.paste(im, (ox, oy), im)
    clipped = ox < 0 or oy < 0 or ox + nw > S or oy + nh > S
    return canvas, clipped


def band_widths(alpha, nb=24):
    m = alpha > 127
    y0, y1, _, _ = bbox(m)
    edges = np.linspace(y0, y1, nb + 1).astype(int)
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        rows = m[a:b]
        w = [(np.nonzero(r)[0].max() - np.nonzero(r)[0].min() + 1) if r.any() else 0 for r in rows]
        out.append(float(np.mean(w)))
    return np.array(out)


def neck_y(alpha):
    """Row of minimum silhouette width between 12% and 40% of body height (neck/shoulder line)."""
    m = alpha > 127
    y0, y1, _, _ = bbox(m)
    H = y1 - y0
    best, by = 1e9, None
    for y in range(y0 + int(0.12 * H), y0 + int(0.40 * H)):
        xs = np.nonzero(m[y])[0]
        if len(xs) and xs.max() - xs.min() < best:
            best, by = xs.max() - xs.min(), y
    return int(by), int(best)


def main(cid):
    d = os.path.join(ROOT, cid)
    cfg = json.load(open(os.path.join(d, "src.json")))
    os.makedirs(os.path.join(d, "512"), exist_ok=True)
    cache, items, log, chk_frac = {}, [], {}, {}
    for v in cfg["views"]:
        src = os.path.join(ROOT, v["src"])
        if src not in cache:
            rgb = np.array(Image.open(src).convert("RGB"))
            cache[src] = (rgb, flood_mask(rgb, cfg.get("tol_min", 232), cfg.get("tol_chroma", 14)))
        rgb, fm = cache[src]
        figs = split_figures(fm)
        fmask = figs[v.get("fig", 0)]
        _, _, x0, x1 = bbox(fmask)
        pad = 6
        x0, x1 = max(0, x0 - pad), min(rgb.shape[1], x1 + pad)
        crgb, cm = rgb[:, x0:x1].copy(), fmask[:, x0:x1].copy()
        crgb[~ndi.binary_dilation(cm, iterations=3)] = 255   # blank out neighbouring figures
        rm = rembg_mask(crgb)
        mi = iou(cm, rm)
        mode = v.get("matte", cfg.get("matte", "flood"))
        if mode == "rembg":
            cm = rm
        elif mode == "union":   # white-on-white subjects: flood fill OR rembg
            cm = ndi.binary_fill_holes(cm | rm)
        # enclosed background pockets (e.g. between touching legs): pure-white blobs inside the figure that
        # rembg also calls background are removed
        mn = crgb.min(-1).astype(int); mx = crgb.max(-1).astype(int)
        pw = (mn >= 248) & ((mx - mn) <= 6) & cm
        lab, n = ndi.label(pw)
        holes = 0
        for i in range(1, n + 1):
            comp = lab == i
            if comp.sum() > 150 and rm[comp].mean() < 0.3:
                cm &= ~ndi.binary_dilation(comp, iterations=2); holes += 1
        if v.get("flip"):
            crgb, cm = crgb[:, ::-1].copy(), cm[:, ::-1].copy()
        items.append(dict(v=v, rgb=crgb, mask=cm, figs=len(figs), iou_rembg=round(mi, 4), holes=holes))

    for group, H_frac, base in (("body", BODY_H, FEET_Y), ("head", HEAD_H, HEAD_BASE)):
        g = [it for it in items if it["v"].get("group", "body") == group]
        if not g:
            continue
        if group == "head":
            hmax = max(bbox(it["mask"])[1] - bbox(it["mask"])[0] for it in g)
            wmax = max(bbox(it["mask"])[3] - bbox(it["mask"])[2] for it in g)
            H_frac = min(H_frac, 0.94 * hmax / wmax)
        else:   # shrink the shared body height if the widest view (relative to its feet anchor) would not fit
            need = []
            for it in g:
                m = it["mask"]; y0, y1, bx0, bx1 = bbox(m); h = y1 - y0
                xs = np.nonzero(m[y1 - int(0.2 * h):y1].any(0))[0]; ax = (xs.min() + xs.max() + 1) / 2
                need.append(max(ax - bx0, bx1 - ax) / h)
            H_frac = min(H_frac, 0.47 / max(need))
        chk_frac[group] = round(H_frac, 4)
        for it in g:
            m = it["mask"]; y0, y1, bx0, bx1 = bbox(m)
            h = y1 - y0
            scale = H_frac * S / (hmax if group == "head" else h)
            if group == "body":   # x anchor: centre of the bottom 20% (feet / lower legs)
                low = m[y1 - int(0.2 * h):y1]
                xs = np.nonzero(low.any(0))[0]
                ax = (xs.min() + xs.max() + 1) / 2
            else:                 # head: centre of the bbox of the top 60% (skull, not the shoulders)
                top = m[y0:y0 + int(0.6 * h)]
                xs = np.nonzero(top.any(0))[0]
                ax = (xs.min() + xs.max() + 1) / 2
            alpha = soft_alpha(m)
            canvas, clipped = place(it["rgb"], alpha, scale, (ax, y1), (S / 2, base * S))
            name = it["v"]["view"]
            canvas.save(os.path.join(d, name + ".png"))
            canvas.resize((512, 512), Image.LANCZOS).save(os.path.join(d, "512", name + ".png"))
            it["out"] = np.array(canvas)[..., 3]
            log[name] = dict(src=it["v"]["src"], fig=it["v"].get("fig", 0), flip=bool(it["v"].get("flip")),
                             src_height_px=int(h), scale=round(scale, 4), clipped=clipped,
                             matte_iou_flood_vs_rembg=it["iou_rembg"], pockets_removed=it["holes"], matte=it["v"].get("matte", cfg.get("matte", "flood")))

    # checks
    out = {it["v"]["view"]: it["out"] for it in items}
    chk = {"views": log, "height_frac": chk_frac}
    def mirror_iou(a):
        m = a > 127
        xs = np.nonzero(m)[1]; cx = xs.mean()
        sh = int(round(S / 2 - cx))
        m2 = np.roll(m, sh, 1)
        return round(iou(m2, m2[:, ::-1]), 4)
    sym = {k: mirror_iou(out[k]) for k in ("front", "back") if k in out}
    chk["symmetry_mirror_iou"] = sym
    bw = {k: band_widths(out[k]) for k in out if log[k] and items[[i["v"]["view"] for i in items].index(k)]["v"].get("group", "body") == "body"}
    def rel(a, b):
        return round(float(np.mean(np.abs(a - b)) / max(1, np.mean((a + b) / 2))), 4)
    pairs = [("front", "back"), ("left", "right"), ("fl34", "fr34")]
    chk["band_width_rel_diff"] = {f"{a}~{b}": rel(bw[a], bw[b]) for a, b in pairs if a in bw and b in bw}
    chk["band_widths_px"] = {k: [round(x) for x in v] for k, v in bw.items()}
    chk["neck_y_px"] = {k: neck_y(out[k])[0] for k in bw}
    if "front" in out and "back" in out:
        chk["front_vs_mirrored_back_iou"] = round(iou(out["front"] > 127, (out["back"] > 127)[:, ::-1]), 4)
    if "left" in out and "right" in out:
        chk["left_vs_mirrored_right_iou"] = round(iou(out["left"] > 127, (out["right"] > 127)[:, ::-1]), 4)
    json.dump(chk, open(os.path.join(d, "checks.json"), "w"), indent=1)

    meta = {"id": cid, "canvas": S, "copies_512": "512/",
            "convention": "yaw = camera azimuth around the character, degrees. 0 = camera in front (she faces the viewer); "
                          "+90 = camera at HER LEFT side (she faces screen-left); 180 = back; -90 = camera at her right (she faces screen-right). "
                          "Same convention as swordswoman/v2/hy3d/inputsD (2mv 'left' = she faces screen-left). "
                          "Orthographic-ish, camera at mid-height, elevation 0.",
            "framing": f"body views: same scale, body height = {chk_frac.get('body')} of canvas, feet baseline y = {FEET_Y} (from top), x centred on the feet band. "
                       f"head views: shared scale within the head group, baseline y = {HEAD_BASE}.",
            "views": {}, "hunyuan_mv": {k: k + ".png" for k in ("front", "left", "back", "right") if k in out},
            "notes": cfg.get("notes", "")}
    for k in out:
        meta["views"][k] = {"file": k + ".png", "yaw": cfg["yaw"].get(k), **{x: log[k][x] for x in ("src", "flip")}}
        if k in cfg.get("yaw_note", {}):
            meta["views"][k]["yaw_note"] = cfg["yaw_note"][k]
    json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=1)

    # contact sheet: all views on light grey (to show the matte), labels underneath
    from PIL import ImageDraw
    order = [k for k in ("front", "fl34", "left", "back", "right", "fr34", "head_front", "head_side") if k in out]
    cw = 384
    sheet = Image.new("RGB", (cw * 4, (cw + 28) * ((len(order) + 3) // 4)), (205, 208, 214))
    dr = ImageDraw.Draw(sheet)
    for i, k in enumerate(order):
        im = Image.open(os.path.join(d, k + ".png")).resize((cw, cw), Image.LANCZOS)
        x, y = (i % 4) * cw, (i // 4) * (cw + 28)
        sheet.paste(im, (x, y), im)
        if log[k]["src"] and items[[j["v"]["view"] for j in items].index(k)]["v"].get("group", "body") == "body":
            yb = int(FEET_Y * cw); dr.line([(x, y + yb), (x + cw, y + yb)], fill=(255, 80, 80))
            yt = int((FEET_Y - chk_frac["body"]) * cw); dr.line([(x, y + yt), (x + cw, y + yt)], fill=(255, 80, 80))
            ny = int(chk["neck_y_px"][k] * cw / S); dr.line([(x, y + ny), (x + cw, y + ny)], fill=(80, 140, 255))
        dr.text((x + 6, y + cw + 6), f"{k}  yaw {cfg['yaw'].get(k)}{'  (mirror)' if log[k]['flip'] else ''}", fill=(20, 20, 30))
    sheet.save(os.path.join(d, "sheet.png"))
    print(json.dumps({k: chk[k] for k in chk if k not in ("band_widths_px", "views")}, indent=1))
    print({k: (log[k]["matte_iou_flood_vs_rembg"], log[k]["clipped"]) for k in log})


if __name__ == "__main__":
    main(sys.argv[1])
