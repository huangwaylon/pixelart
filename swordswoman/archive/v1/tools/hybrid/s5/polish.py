"""Claude polish pass (exact pixels) on the snapped+normalized Gemini sprites:
ribbons back to pink, stray white->skin, slash 'focused' eyes, bow-cel lag, smears/FX, orphan clean.
polish.py [names]  -> sprite/<name>.png (+ _src.png = raw Gemini image, _4x.png)"""
import sys, os, shutil, math
import numpy as np
from PIL import Image
from common import *
sys.path.insert(0, f"{ROOT}/tools/hybrid")
import draw as D
from norm import steel_layer, remove_orphans

def tone(a, x, y):
    if not a[y, x, 3]: return None
    return INV.get(tuple(a[y, x, :3]))
INV = {}
for k, v in TRGB.items(): INV.setdefault(v, k)

def ribbons_pink(a, region=None):
    """free-floating 1 px strands in tan/peach/coral tones (Gemini's ribbons) -> pink_0/pink_1."""
    out = a.copy(); n = 0
    cand = {"hair_2": "pink_1", "leather_2": "pink_0", "red_3": "pink_1", "skin_0": "pink_0", "hair_1": "pink_0"}
    for y in range(1, 127):
        for x in range(1, 127):
            t = tone(a, x, y)
            if t not in cand: continue
            if region and not (region[0] <= x < region[2] and region[1] <= y < region[3]): continue
            nb = [tone(a, x+dx, y+dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dx or dy)]
            opq = [q for q in nb if q]
            if len(opq) <= 3 and "outline" not in opq:
                out[y, x, :3] = TRGB[cand[t]]; n += 1
    return out, n

def white_to_skin(a, box):
    st = steel_layer(a); x0, y0, x1, y1 = box
    for y in range(y0, y1):
        for x in range(x0, x1):
            if tone(a, x, y) in ("steel_2", "steel_1") and not st[y, x]:
                a[y, x, :3] = TRGB["skin_2" if tone(a, x, y) == "steel_2" else "skin_1"]
    return a

def stamp_edit(a, name, edits):
    x, y = head_xy(name)
    for (r, c, t) in edits: a[y + r, x + c, :3] = TRGB[t]; a[y + r, x + c, 3] = 255
    return a

FOCUS_SE = [(25, 12, "outline"), (25, 18, "outline"), (24, 13, "outline")]   # inner lids drop: focused look

def bow_shift(a, name, dx, dy):
    """move the bow cel (red cluster + its outline in the top 11 stamp rows) by (dx,dy) for lag."""
    if not (dx or dy): return a
    st = load(f"{ROOT}/hybrid/lock/pixel/head_{dir_of(name)}.png"); hx, hy = head_xy(name)
    reds = {TRGB[k] for k in ("red_0", "red_1", "red_2", "red_3")}
    h, w = st.shape[:2]; top = 11
    bm = np.zeros((h, w), bool)
    for r in range(top):
        for c in range(w):
            if st[r, c, 3] and tuple(st[r, c, :3]) in reds: bm[r, c] = True
    ring = np.zeros_like(bm)
    for r in range(top):
        for c in range(w):
            if st[r, c, 3] and tuple(st[r, c, :3]) == TRGB["outline"]:
                if any(0 <= r+u < h and 0 <= c+v < w and bm[r+u, c+v] for u, v in ((0, 1), (0, -1), (1, 0), (-1, 0))):
                    # outline belongs to the bow if it is not also touching hair
                    hairy = any(0 <= r+u < h and 0 <= c+v < w and st[r+u, c+v, 3] and INV.get(tuple(st[r+u, c+v, :3]), "").startswith("hair")
                                for u, v in ((0, 1), (0, -1), (1, 0), (-1, 0)))
                    if not hairy or r < 2: ring[r, c] = True
    bm |= ring
    out = a.copy()
    cel = [(r, c, a[hy + r, hx + c].copy()) for r in range(h) for c in range(w) if bm[r, c]]
    for r, c, _ in cel:   # vacate: hair underneath if inside the head mass, else transparent
        below = [a[hy + rr, hx + c] for rr in range(r + 1, min(h, r + 4)) if not bm[rr, c] and a[hy + rr, hx + c, 3]]
        if below and r >= 5: out[hy + r, hx + c] = below[0] if tuple(below[0][:3]) != TRGB["outline"] else (*TRGB["hair_0"], 255)
        else: out[hy + r, hx + c] = 0
    for r, c, px in cel:
        out[hy + r + dy, hx + c + dx] = px
    # re-close: transparent pixels left inside the hair under the moved bow get outline
    return out

def layer_smear(a, ops, front_y=None):
    """draw ops on an empty layer, composite: behind the body, except rows >= front_y (passes in front)."""
    L = np.zeros_like(a); cv = D.Canvas(L)
    for op in ops: D.run_op(cv, op, ".")
    m = L[..., 3] > 0
    for y, x in zip(*np.nonzero(m)):
        if not a[y, x, 3] or (front_y is not None and y >= front_y):
            a[y, x] = L[y, x]
    return a

def star(a, x, y):
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, 2), (0, -2)):
        a[y+dy, x+dx, :3] = TRGB["steel_2"]; a[y+dy, x+dx, 3] = 255
    for dx, dy in ((2, 2), (-2, -2), (2, -2), (-2, 2), (3, 0), (-3, 0)):
        a[y+dy, x+dx, :3] = TRGB["pink_1"]; a[y+dy, x+dx, 3] = 255
    return a

def ribbons_shift(a, dy, dx=0):
    """secondary motion: move the pink ribbon pixels (lag/float/overshoot) into free space."""
    pk = {TRGB["pink_0"], TRGB["pink_1"]}
    ys, xs = np.nonzero(a[..., 3] > 0)
    pts = [(y, x) for y, x in zip(ys, xs) if tuple(a[y, x, :3]) in pk]
    out = a.copy()
    for y, x in pts: out[y, x] = 0
    for y, x in pts:
        Y, X = y + dy, x + dx
        if 0 <= Y < 128 and 0 <= X < 128 and (not out[Y, X, 3]): out[Y, X] = a[y, x]
        elif not out[y, x, 3]: out[y, x] = a[y, x]
    return out

KEEP = {"steel_2", "steel_1", "steel_0", "eye_0", "eye_1", "pink_0", "pink_1", "skin_2"}
def merge_orphans(a, name, passes=2):
    """single pixels with no same-tone 4-neighbour -> the dominant 8-neighbour tone (outside the head stamp).
    Outline pixels are kept when they continue a line (>= 2 outline 8-neighbours)."""
    hx, hy = head_xy(name); st = load(f"{ROOT}/hybrid/lock/pixel/head_{dir_of(name)}.png")
    hh, hw = st.shape[:2]
    for _ in range(passes):
        out = a.copy()
        for y in range(1, 127):
            for x in range(1, 127):
                t = tone(a, x, y)
                if not t or t in KEEP: continue
                if hy <= y < hy + hh and hx <= x < hx + hw and st[y - hy, x - hx, 3]: continue
                n4 = [tone(a, x+dx, y+dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                if t in n4: continue
                n8 = [tone(a, x+dx, y+dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dx or dy)]
                if t == "outline" and (n8.count("outline") >= 2 or None in n8): continue
                if None in n4: continue          # silhouette edge pixel: leave the contour alone
                cand = [q for q in n4 if q and q not in KEEP]
                if len(cand) < 2: continue
                best = max(set(cand), key=cand.count)
                out[y, x, :3] = TRGB[best]
        a = out
    return a

def blade_clean(a):
    """dotted outline beside the blade (Gemini AA debris): drop K pixels touching steel with <= 1 K 8-neighbour
    and no non-steel colour neighbour."""
    st = steel_layer(a); out = a.copy()
    for y in range(1, 127):
        for x in range(1, 127):
            if tone(a, x, y) != "outline": continue
            n8 = [(tone(a, x+dx, y+dy), st[y+dy, x+dx]) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dx or dy)]
            if not any(s for _, s in n8): continue
            kk = sum(1 for t, _ in n8 if t == "outline")
            other = any(t and t != "outline" and not s for t, s in n8)
            if kk <= 1 and not other: out[y, x] = 0
    return out

def dust(a, pts):
    for (x, y, t) in pts: a[y, x, :3] = TRGB[t]; a[y, x, 3] = 255
    return a

BOW = {"walk_SE_k1": (0, -1), "walk_SE_k3": (0, 1), "slash_SE_k0": (1, 0), "slash_SE_k1": (-1, 0),
       "slash_SE_k3": (1, 1), "jump_E_crouch": (0, -1), "jump_E_apex": (-1, -1), "jump_E_land": (0, 1)}
ELL = "74,86 38,14"

def polish(name):
    src = f"{OUT}/work/legs_{name}.png" if os.path.exists(f"{OUT}/work/legs_{name}.png") else f"{OUT}/work/norm_{name}.png"
    a = load(src)
    a, n = ribbons_pink(a)
    if name == "slash_SE_k0": a = white_to_skin(a, (50, 88, 80, 106))
    if name.startswith("slash"): a = stamp_edit(a, name, FOCUS_SE)
    if name in BOW: a = bow_shift(a, name, *BOW[name])
    if name == "slash_SE_k1":
        a = layer_smear(a, [f"streak 64,86 74,90 3 tones=r,v"], None)                     # stretched sleeves
        a = layer_smear(a, [f"cluster 71,88 s XX/XX"], None)                                 # hand echo
        a = layer_smear(a, [f"smear {ELL} -168 -328 6 tones=w,P,p taper=lead grow=in"], front_y=87)
    if name == "slash_SE_k2":
        a = layer_smear(a, [f"smear {ELL} -300 -362 2 tones=P,p taper=lead grow=in"], front_y=87)
        a = star(a, 106, 84)
    if name == "slash_SE_k3":
        a = layer_smear(a, [f"smear {ELL} -330 -372 1 tones=p taper=both grow=in"], front_y=87)
    if name == "jump_E_land":
        ys, xs = np.nonzero(a[100:107, :, 3]); x0, x1 = xs.min(), xs.max()
        a = dust(a, [(x0-2, 105, "steel_1"), (x0-3, 104, "steel_1"), (x0-5, 103, "skin_2"), (x0-4, 105, "steel_1"),
                     (x1+2, 105, "steel_1"), (x1+3, 104, "steel_1"), (x1+5, 103, "skin_2"), (x1+4, 105, "steel_1")])
    RIB = {"jump_E_crouch": (-1, 0), "jump_E_apex": (-2, -1), "jump_E_land": (2, 0), "walk_SE_k1": (-1, 0), "walk_SE_k3": (1, 0)}
    if name in RIB: a = ribbons_shift(a, *RIB[name])
    a = blade_clean(a)
    a = merge_orphans(a, name)
    a = remove_orphans(a, 3)
    return a

if __name__ == "__main__":
    names = sys.argv[1:] or NAMES
    os.makedirs(f"{OUT}/sprite", exist_ok=True); os.makedirs(f"{OUT}/hires", exist_ok=True)
    import re
    picks = dict(re.findall(r"(\w+):(\w+)", open(f"{ROOT}/tools/hybrid/s5/picks.sh").read().split("PICKS=")[1]))
    for n in names:
        a = polish(n)
        save(a, f"{OUT}/sprite/{n}.png")
        Image.fromarray(a).resize((512, 512), Image.NEAREST).save(f"{OUT}/sprite/{n}_4x.png")
        raw = f"{OUT}/gem/{n}_1x_{picks[n]}.png"
        shutil.copy(raw, f"{OUT}/hires/{n}.png"); shutil.copy(raw, f"{OUT}/sprite/{n}_src.png")
        print(n, "ok")
