# compare.py ACT VIEW OURS_DIR OUT.png : blind A/B sheet, A = hy3d frames_preview (m12 baseline), B = pose strand (both 1x 64 cell, matid + sil, 3x)
import sys, os, json, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import metrics as MX
act, view, ours, outp = sys.argv[1:5]
def to1x(path, piv):
    a = np.asarray(Image.open(path).convert("RGBA")); k = a.shape[0] // 96
    cov = (a[..., 3] > 127).reshape(96, k, 96, k).mean((1, 3)) > 0.5
    b = a.reshape(96, k, 96, k, 4).transpose(0, 2, 1, 3, 4).reshape(96, 96, k * k, 4); m = np.zeros((96, 96, 3), np.uint8)
    for y, x in zip(*np.where(cov)):
        px = b[y, x][b[y, x, :, 3] > 127][:, :3]; v, c = np.unique(px, axis=0, return_counts=True); m[y, x] = v[c.argmax()]
    y0 = piv[1] - 60; x0 = piv[0] - 32
    return cov[y0:y0 + 64, x0:x0 + 64], m[y0:y0 + 64, x0:x0 + 64]
B0 = f"/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/hy3d/frames_preview/{act}_{view}/s48"
fa = json.load(open(os.path.join(B0, "frames.json"))); A = [to1x(os.path.join(B0, f"f{i:02d}_matid.png"), fa["pivot_1x"]) for i in range(len(fa["frames"]))]
mj = json.load(open(os.path.join(ours, f"{act}_{view}", "metrics.json"))); n = len(mj["frames"])
Bf = [to1x(os.path.join(ours, f"{act}_{view}", f"f{i:02d}_matid4x.png"), (48, 76)) for i in range(n)]
s = 3; cw = 64 * s + 6; W = max(len(A), n) * cw + 40; H = 2 * (16 + 70 + 64 * s * 2 + 8) + 20
O = Image.new("RGB", (W, H), MX.BG); dr = ImageDraw.Draw(O)
def row(fr, names, ms, y, lab):
    dr.text((4, y), lab, fill=(255, 255, 255))
    for i, (al, m) in enumerate(fr):
        mat = np.where(al[..., None], m, np.array(MX.BG)).astype(np.uint8); sil = np.where(al[..., None], np.array([20, 20, 24]), np.array(MX.BG)).astype(np.uint8)
        O.paste(Image.fromarray(mat), (40 + i * 140, y + 14)); O.paste(Image.fromarray(sil), (40 + i * 140 + 68, y + 14))
        dr.text((40 + i * cw, y + 84), f"{i} {names[i]} {ms[i]}ms", fill=(255, 255, 160))
        O.paste(Image.fromarray(mat).resize((64 * s, 64 * s), Image.NEAREST), (40 + i * cw, y + 98))
        O.paste(Image.fromarray(sil).resize((64 * s, 64 * s), Image.NEAREST), (40 + i * cw, y + 98 + 64 * s + 2))
    return y + 98 + 2 * 64 * s + 12
y = row(A, [f["name"] for f in fa["frames"]], [f["ms"] for f in fa["frames"]], 4, "A")
row(Bf, [f["name"] for f in mj["frames"]], [f["ms"] for f in mj["frames"]], y, "B")
O.save(outp); print(outp, O.size)
