"""Snap a Gemini pixel-native pose to its exact grid (pitch detect + per-cell majority vote), flip it back out of
mirror space, quantize per material (locked palette), and fit it into the 128 cell (feet on y=104, head width
normalised to the S3 cel head) -> a POSE REF sprite for the Claude retrace (never shipped below the collar).
snap.py GEMPNG OUT.png [--pitch P] [--nomirror] [--pick K]"""
import sys, json
import numpy as np
from PIL import Image
sys.path.insert(0, "/Users/waylonhuang/Documents/other/pixelart/swordswoman/archive/v1/tools/hybrid/s5")
sys.path.insert(0, "/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools/hybrid")
from snap import detect, edge_profile, vote, is_bg
import hylib as H
from scipy import ndimage as ndi

def main(src, out, pitch=None, mirror=True, pick=None):
    a = np.array(Image.open(src).convert("RGB"))
    bg = is_bg(a)
    if pitch is None:
        sx, px, ox = detect(edge_profile(a, 1), 10.67)
        sy, py, oy = detect(edge_profile(a, 0), 10.67)
        # try other plausible pitches, keep the best edge score
        for e in (8.0, 9.0, 12.0, 13.0):
            s2, p2, o2 = detect(edge_profile(a, 1), e)
            if s2 > sx * 1.05: sx, px, ox = s2, p2, o2
            s3, p3, o3 = detect(edge_profile(a, 0), e)
            if s3 > sy * 1.05: sy, py, oy = s3, p3, o3
    else:
        px = py = pitch; sx = sy = 0
        _, _, ox = detect(edge_profile(a, 1), pitch); _, _, oy = detect(edge_profile(a, 0), pitch)
    g, agree = vote(a, bg, px, ox, py, oy)
    if mirror: g = g[:, ::-1].copy()
    m = g[..., 3] > 0
    lab, n = ndi.label(m)
    if n > 1:
        sizes = ndi.sum(m, lab, range(1, n + 1))
        keep = np.argmax(sizes) + 1 if pick is None else pick
        # keep the largest blob + blobs within 3 cells of it (sword pieces)
        big = lab == keep
        near = ndi.binary_dilation(big, iterations=3)
        ids = set(np.unique(lab[near])) - {0}
        m = np.isin(lab, list(ids))
        g[~m] = 0
    ys, xs = np.nonzero(m)
    g = g[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    alpha = g[..., 3] > 0
    cls, _ = H.classify(g[..., :3], allowed=None, penalty=6.0)
    q = H.quantize_tones(g[..., :3], cls); q[~alpha] = -1
    spr = H.rgba_of(q)
    h, w = spr.shape[:2]
    cell = np.zeros((128, 128, 4), np.uint8)
    # feet on 104 (bottom of the main body); centre x on 64 by the bottom-third centroid
    bot = alpha[int(h * 0.66):]
    cx = int(round(np.nonzero(bot)[1].mean())) if bot.any() else w // 2
    y0 = 105 - h; x0 = 64 - cx
    for j in range(h):
        for i in range(w):
            if spr[j, i, 3] and 0 <= y0 + j < 128 and 0 <= x0 + i < 128: cell[y0 + j, x0 + i] = spr[j, i]
    Image.fromarray(cell).save(out)
    Image.fromarray(cell).resize((512, 512), Image.NEAREST).save(out[:-4] + "_4x.png")
    meta = dict(src=src, pitch=[float(px), float(py)], offset=[float(ox), float(oy)], agree=agree, grid_h=int(h), grid_w=int(w), mirror=mirror)
    json.dump(meta, open(out[:-4] + "_meta.json", "w"), indent=1)
    print(json.dumps(meta))

if __name__ == "__main__":
    a = sys.argv[1:]; p = None; mir = True; pick = None
    if "--pitch" in a: i = a.index("--pitch"); p = float(a[i + 1]); del a[i:i + 2]
    if "--pick" in a: i = a.index("--pick"); pick = int(a[i + 1]); del a[i:i + 2]
    if "--nomirror" in a: a.remove("--nomirror"); mir = False
    main(a[0], a[1], p, mir, pick)
