"""Build the S4 textured-3D STANDARD TEST SET base sprites (pass A: automatic).

  .venv/bin/python tools/hybrid/s4/build_set.py OUT_DIR [--sx 1.05 --sy 1.22]

Writes OUT_DIR/hires/<name>.png (the cel-shaded textured guide render, 512) and
OUT_DIR/base/<name>.png (128 cell, before hand polish) + OUT_DIR/base/<name>_meta.json (joints in
cell space after the body scale, head stamp placement).
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import celrender as CR  # noqa: E402
import fx as FX  # noqa: E402

G = os.path.join(CR.ROOT, "hybrid/guide/p2")
SET = {}
for d in ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]:
    SET[f"turn_{d}"] = (f"turn/{d}/f00", d)
for i in range(4):
    SET[f"walk_SE_k{i}"] = (f"walk_SE_keys/SE/f0{i}", "SE")
    SET[f"slash_SE_k{i}"] = (f"slash_SE_keys/SE/f0{i}", "SE")
for i, k in enumerate(["crouch", "apex", "land"]):
    SET[f"jump_E_{k}"] = (f"jump_E_keys/E/f0{i}", "E")

STAMP_BOTTOM = {"N": 29}
NS = os.path.join(CR.ROOT, "hybrid/S4_textured3d/r1/_work/guide_noskirt")
STAMPS = os.path.join(CR.ROOT, "hybrid/S4_textured3d/r1/stamps")


def build(name, out, sx, sy, head_dir=None, stamp_dir=STAMPS, head_dy=0, hem_dy=0, R=None):
    R = R or {}
    head_dy = R.get("head_dy", head_dy)
    rel, d = SET[name]
    if "scale" in R:
        sx, sy = sx * R["scale"][0], sy * R["scale"][1]
    fr = CR.Frame(os.path.join(G, rel), sx, sy)
    J = fr.joints
    hem = min(J["knee_L"][1], J["knee_R"][1]) - 3.0 + R.get("hem_dy", hem_dy)
    if "hem_hips" in R:
        hem = J["hips"][1] + R["hem_hips"]
    CR.reveal_legs(fr, os.path.join(NS, rel), hem)
    hi, L = CR.cel_hires(fr, drop_head=False)
    rib = [CR.ribbon_paths(fr, 22), CR.ribbon_paths(fr, 23)]
    ids_saved = fr.ids.copy()
    fr.ids[np.isin(fr.ids, [22, 23])] = 0
    ci, cl = CR.reduce_cell(fr, L)
    fr.ids = ids_saved
    ci, cl = CR.absorb_small_parts(ci, cl)
    # skirt tails never hang below the soles (in back views they project under the feet = reads as sinking)
    foot_y = max(J[k][1] for k in ("toe_L", "toe_R", "heel_L", "heel_R"))
    lim = int(round(foot_y)) + 2
    sh_ = np.isin(ci, [20, 21])
    if sh_.any():
        lim = int(np.nonzero(sh_)[0].max()) + 1
    tail = np.isin(ci, [9, 10, 12, 13])
    tail[:lim + 1] = False
    ci[tail] = 0
    if "skirt_cut" in R:
        # hand edit: short front panel (iso_v5) so the legs read in deep squash poses
        cy_, cx_ = R["skirt_cut"]
        hx_, hy_ = J["hips"][:2]
        yy, xx = np.mgrid[0:128, 0:128]
        cut = np.isin(ci, [9, 10, 18, 19, 20, 21, 11]) & (yy > hy_ + cy_) & (xx > hx_ + cx_)
        ci[cut] = 0
    ci = CR.despike(ci, 2)
    ci = CR.smooth_hem(ci, 3)
    img = CR.paint_cells(ci, cl)
    img = CR.majority_clean(img, ci)
    img = CR.cluster_clean(img, ci, 5)
    img = CR.polish_parts(img, ci)
    img = CR.strappy_heels(img, ci)
    img = CR.outline(img, ci)
    if "legs" in R:
        R["legs"](fr, img, ci)
    body = img[..., 3] > 0
    # only ribbon parts outside the body (plus the root) are drawn: lines over the dress read as straps
    body_in = body.copy()
    for r in rib:
        CR.draw_ribbon(img, r, body=body_in if R.get("ribbon_clip", True) else None, keep_root=R.get("ribbon_root", 5))
    vis = CR.guide_sword_visible(fr)
    if "katana" in R:
        kp = R["katana"](fr)
        vm = np.ones_like(vis) if kp.get("vis") == "all" else (vis if kp.get("vis", True) else np.zeros_like(vis))
        CR.draw_katana(fr, img, vm, pommel=kp["pommel"],
                       guard=kp["guard"], tip=kp["tip"])
    else:
        CR.draw_katana(fr, img, vis)
    hx, hy = fr.joints["hand_L"][:2]
    hand_front = fr.joints["hand_L"][3]
    if hand_front:
        CR.draw_fist(img, hx, hy)
    # head stamp: chin row on the guide chin, centre on the head joint
    hd = head_dir or d
    st = CR.load_stamp(f"head_{hd}", stamp_dir)
    if R.get("face") == "focus":
        st = FX.focus_face(st, hd)
    if "bow" in R:
        st = FX.shift_bow(st, *R["bow"])
    sh, sw = st.shape[:2]
    cx = fr.joints["head"][0]
    chin = fr.joints["chin"][1]
    if hd == "N":
        # no chin: align the skull top with the other directions' skull top
        y0 = int(round(chin)) + 1 - 33 + head_dy
    else:
        y0 = int(round(chin)) + 1 - (sh - 1) + head_dy
    x0 = int(round(cx - 12.5))
    keep = vis.copy()
    if "pre_head" in R:
        R["pre_head"](fr, img)
    CR.paste_stamp(img, st, x0, y0)
    CR.collar_band(img, st, x0, y0, hd)
    head_mask = np.zeros((128, 128), bool)
    hm = st[..., 3] > 0
    for yy, xx in zip(*np.nonzero(hm)):
        if 0 <= y0 + yy < 128 and 0 <= x0 + xx < 128:
            head_mask[y0 + yy, x0 + xx] = True
    # ground lock: the lowest shoe row sits 1 px under the pivot (y 105) on grounded frames
    shoe = np.isin(ci, [20, 21])
    if R.get("ground", True):
        low = np.nonzero(shoe)[0].max() if shoe.any() else np.nonzero(ci)[0].max() - 1
        dy = int(105 - low)
        if dy:
            img = np.roll(img, dy, 0)
            head_mask = np.roll(head_mask, dy, 0)
            fr.id = np.roll(fr.id, dy * 8, 0)
            fr.ids = np.roll(fr.ids, dy * 8, 0)
            fr.joints = {k: (v[0], v[1] + dy, v[2], v[3]) for k, v in fr.joints.items()}
            fr.raw = {k: (v[0], v[1] + dy) for k, v in fr.raw.items()}
            y0 = int(y0 + dy)
    if "post" in R:
        R["post"](fr, img, head_mask)
    # final safe clean (pixelize.safe_clean): orphans, notches, spurs, doubled outline on the body;
    # the head stamp, katana/steel, smears and ribbons (pink) are protected
    import pixelize as PZ
    import hylib as HL
    idx = HL.index_of(img)
    pal = HL.palette()
    cls = np.full(idx.shape, -1)
    for i, nm in enumerate(pal.names):
        b = HL.name_base(nm)
        if b in HL.BASE:
            cls[idx == i] = HL.BASE.index(b)
    prot = head_mask | HL.base_mask(idx, "steel", "pink")
    idx, _st = PZ.safe_clean(idx, cls, prot, baseline=106, passes=2)
    img = HL.rgba_of(idx)
    os.makedirs(os.path.join(out, "hires"), exist_ok=True)
    os.makedirs(os.path.join(out, "base"), exist_ok=True)
    Image.fromarray(hi).resize((512, 512), Image.LANCZOS).save(os.path.join(out, "hires", name + ".png"))
    Image.fromarray(img).save(os.path.join(out, "base", name + ".png"))
    meta = {"guide": rel, "dir": d, "sx": sx, "sy": sy, "head": f"head_{hd}", "head_at": [x0, y0],
            "joints": {k: [round(v[0], 2), round(v[1], 2), bool(v[3])] for k, v in fr.joints.items()}}
    json.dump(meta, open(os.path.join(out, "base", name + "_meta.json"), "w"), indent=1)
    # scaled guide (hidden) for metrics: id + mask + joints in cell space
    gd = os.path.join(out, "guide")
    os.makedirs(gd, exist_ok=True)
    Image.fromarray(fr.id).save(os.path.join(gd, name + "_id.png"))
    m = np.zeros((1024, 1024, 4), np.uint8)
    m[fr.ids > 0] = 255
    Image.fromarray(m).save(os.path.join(gd, name + "_mask.png"))
    json.dump({"space": "cell", "joints": {k: [v[0], v[1]] for k, v in fr.joints.items()}},
              open(os.path.join(gd, name + "_joints.json"), "w"))
    json.dump({"groups": json.load(open(os.path.join(CR.ROOT, "hybrid/guide/id_legend.json")))["groups"]},
              open(os.path.join(gd, "id_groups.json"), "w"))
    return img


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--sx", type=float, default=1.0)
    ap.add_argument("--sy", type=float, default=1.04)
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    for n in SET:
        if a.only and a.only not in n:
            continue
        import recipes
        build(n, a.out, a.sx, a.sy, R=recipes.RECIPES.get(n))
        print("built", n)
