"""Build a 1x colour-blocked SEED sprite per test name from the 3D guide id/clay passes
(hidden guide only) + the locked pixel head stamp. The seed is what Gemini repaints on the grid."""
import sys, json, os
import numpy as np
from common import *

PART_TONES = {  # id -> (shadow, base, light)
    1: ("hair_0", "hair_0", "hair_1"), 2: ("hair_0", "hair_1", "hair_1"), 3: ("red_1", "red_2", "red_2"),
    4: ("skin_1", "skin_2", "skin_2"), 5: ("skin_1", "skin_1", "skin_2"), 6: ("red_1", "red_2", "red_3"),
    7: ("red_1", "red_2", "red_2"), 8: ("outline", "leather_1", "leather_1"), 9: ("red_1", "red_2", "red_3"),
    10: ("red_0", "red_1", "red_1"), 11: ("outline", "dark_1", "dark_1"), 12: ("red_1", "red_2", "red_3"),
    13: ("red_1", "red_2", "red_3"), 14: ("skin_0", "skin_1", "skin_2"), 15: ("skin_0", "skin_1", "skin_2"),
    16: ("skin_0", "skin_1", "skin_1"), 17: ("skin_0", "skin_1", "skin_1"), 18: ("skin_0", "skin_1", "skin_2"),
    19: ("skin_0", "skin_1", "skin_2"), 20: ("outline", "leather_1", "leather_1"), 21: ("outline", "leather_1", "leather_1"),
    22: ("pink_0", "pink_1", "pink_1"), 23: ("pink_0", "pink_1", "pink_1"), 24: ("steel_1", "steel_2", "steel_2"),
    25: ("pink_0", "pink_1", "steel_2"),
}
HEAD_IDS = {1, 2, 3, 4, 5}

def block_mode(ids, alpha, k=8):
    H = ids.shape[0] // k
    out = np.zeros((H, H), int)
    for y in range(H):
        for x in range(H):
            a = alpha[y*k:(y+1)*k, x*k:(x+1)*k] > 127
            if a.mean() < 0.4: continue
            v = ids[y*k:(y+1)*k, x*k:(x+1)*k][a]
            v = v[v > 0]
            if len(v) == 0: continue
            out[y, x] = np.bincount(v).argmax()
    return out

def build(name):
    P = guide_prefix(name)
    idimg = load(P + "_id.png"); clay = load(P + "_clay.png").astype(float)
    ids = (idimg[..., 0].astype(int) + 5) // 10
    idc = block_mode(ids, idimg[..., 3])
    lum = clay[..., :3].mean(2).reshape(128, 8, 128, 8).mean((1, 3))
    out = np.zeros((128, 128, 4), np.uint8)
    for pid, tones in PART_TONES.items():
        m = idc == pid
        if not m.any() or pid in HEAD_IDS or (pid == 25 and os.environ.get("S5_NOSMEAR")): continue
        med = np.median(lum[m])
        for yy, xx in zip(*np.nonzero(m)):
            l = lum[yy, xx]
            t = tones[0] if l < med - 12 else (tones[2] if l > med + 25 else tones[1])
            out[yy, xx, :3] = TRGB[t]; out[yy, xx, 3] = 255
    # smear helper mask (slash keys)
    if os.path.exists(P + "_mask_smear.png") and not os.environ.get("S5_NOSMEAR"):
        sm = load(P + "_mask_smear.png")
        sa = (sm[..., 3] if sm[..., 3].min() < 255 else sm[..., :3].mean(2)).astype(float)
        sa = sa.reshape(128, 8, 128, 8).mean((1, 3)) > 100
        for yy, xx in zip(*np.nonzero(sa & (out[..., 3] == 0))):
            out[yy, xx, :3] = TRGB["pink_1"]; out[yy, xx, 3] = 255
    if os.environ.get("S5_SWORD"):
        # redraw the katana from the guide joints (the id downsample breaks the 2 px blade)
        J = joints(P)
        st = np.isin(idc, [24])
        out[st] = 0
        def ln2(a, b, t1, t2):
            x0, y0 = a; x1, y1 = b
            n = int(max(abs(x1-x0), abs(y1-y0))) + 1
            ox, oy = (0, 1) if abs(x1-x0) > abs(y1-y0) else (1, 0)
            for k in range(n + 1):
                x = round(x0 + (x1-x0)*k/n); y = round(y0 + (y1-y0)*k/n)
                out[y, x, :3] = TRGB[t1]; out[y, x, 3] = 255
                if t2: out[y+oy, x+ox, :3] = TRGB[t2]; out[y+oy, x+ox, 3] = 255
        ln2(J["sword_guard"], J["sword_tip"], "steel_2", "steel_1")
        ln2(J["sword_pommel"], J["sword_guard"], "red_2", "outline")
    if name == "slash_SE_k0" and os.environ.get("S5_K0RAISE"):
        # push the anticipation: blade raised back over her right shoulder (tip toward the coil start)
        st = np.all(out[..., :3] == TRGB["steel_2"], -1) | np.all(out[..., :3] == TRGB["steel_1"], -1)
        out[st] = 0
        def ln(x0, y0, x1, y1, t, w=1):
            n = int(max(abs(x1-x0), abs(y1-y0))) + 1
            for k in range(n + 1):
                x = round(x0 + (x1-x0)*k/n); y = round(y0 + (y1-y0)*k/n)
                for dx in range(w):
                    out[y, x+dx, :3] = TRGB[t]; out[y, x+dx, 3] = 255
        ln(58, 87, 55, 82, "red_2", 2); ln(54, 82, 57, 80, "steel_0")      # handle, guard bar
        ln(54, 80, 38, 60, "steel_2"); ln(55, 80, 39, 60, "steel_1")       # 2 px blade
    # exterior outline (not on steel / smear)
    a = out[..., 3] > 0
    ring = np.zeros_like(a)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ring |= np.roll(np.roll(a, dy, 0), dx, 1)
    ring &= ~a
    out[ring, :3] = TRGB["outline"]; out[ring, 3] = 255
    # head stamp
    d = dir_of(name)
    head = load(f"{ROOT}/hybrid/lock/pixel/head_{d}.png")
    x, y = head_xy(name)
    paste(out, head, x, y)
    return out

if __name__ == "__main__":
    names = sys.argv[1:] or NAMES
    for n in names:
        save(build(n), f"{OUT}/seed/{n}.png")
        print(n, head_xy(n))
