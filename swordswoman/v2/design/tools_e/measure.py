"""measure.py img... : rough Level E proportion metrics on a FRONT/BACK view (white bg).
heads = (sole-crown)/(chin-crown); crown = first row where hair width >= 50% of max hair width (skips bow/bun)."""
import sys, numpy as np
from PIL import Image
for p in sys.argv[1:]:
    x = np.array(Image.open(p).convert('RGB')).astype(int); r, g, b = x[..., 0], x[..., 1], x[..., 2]
    v = x.max(-1); s = v - x.min(-1)
    fig = (x.min(-1) < 215) | (s > 30)
    hair = (v < 95) & (s < 40)
    red = (r > 110) & (r > g + 50) & (r > b + 30)
    skin = (r > 200) & (g > 150) & (b > 110) & (r > b + 20) & (s > 15)
    ys = np.where(fig.any(1))[0]; top, sole = ys.min(), ys.max(); Hh = sole - top
    hw = hair.sum(1); hmax = hw.max(); crown = np.where(hw >= 0.5 * hmax)[0].min()
    redrows = np.where(red.sum(1) > 0.15 * red.sum(1).max())[0]
    # red mass below head: first red row after crown + 0.15H
    rr = redrows[redrows > crown + 0.15 * Hh]; dress_top, hem = rr.min(), rr.max()
    # chin: last row above dress_top with skin in the centre band
    cx = int(np.where(fig[int(sole - 0.05 * Hh)])[0].mean()) if False else int(np.where(fig[crown:dress_top].any(0))[0].mean())
    band = skin[:, cx - 6:cx + 7].any(1); sk = np.where(band[crown:dress_top])[0] + crown
    # neck = skin rows in centre band directly above dress top; chin = where skin width jumps (face) - approximate as last row where skin width > 2.2 * neck width
    sw = skin[:, cx - 80:cx + 80].sum(1)
    neckw = np.median(sw[dress_top - 6:dress_top]) if dress_top > 6 else 0
    face = [y for y in range(crown, dress_top) if sw[y] > max(2.0 * neckw, 1)]
    chin = max(face) if face else dress_top
    head_h = chin - crown; headW = hmax
    def width(m, y): w = np.where(m[y])[0]; return (w.max() - w.min() + 1) if len(w) else 0
    sh = max(width(red, y) for y in range(dress_top, dress_top + int(0.06 * Hh)))
    obi = (v < 110) & (s < 50) & ~hair | hair
    waist = min(width(fig & ~skin, y) for y in range(dress_top + int(0.08 * Hh), dress_top + int(0.2 * Hh)))
    hemw = width(red, hem - 3)
    fullH = sole - crown
    print(f"{p.split('/')[-1]}: heads {fullH/head_h:.2f} | head% {head_h/fullH:.2f} | legs% {(sole-hem)/fullH:.2f} | neck rows% {(dress_top-chin)/fullH:.3f} | shoulder/headW {sh/headW:.2f} | waist(min torso incl sleeves?)/headW {waist/headW:.2f} | hem/headW {hemw/headW:.2f}")
