"""board.py VIEW CLIP FRAME OUT.png [METHODS]: illustration | m96 master | candidates; 4x nearest tiles (crop x22..106 y14..128) + 1x strip, mid-grey bg"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hx
from PIL import Image, ImageDraw
X0, X1, Y0, Y1 = 22, 106, 14, 128; S = 4; TW, TH = (X1 - X0) * S, (Y1 - Y0) * S


def tile(g, lab):
    im = hx.render(g[Y0:Y1, X0:X1], S); c = Image.new('RGB', (TW, TH + 16), (40, 40, 40)); c.paste(im, (0, 16)); ImageDraw.Draw(c).text((3, 2), lab, fill=(255, 255, 255)); return c


def illus(view):
    x, m = hx.Z.load(view); h = 96 * S; w = int(x.shape[1] * h / x.shape[0])
    im = Image.fromarray(x.astype(np.uint8)).resize((w, h), Image.LANCZOS); c = Image.new('RGB', (max(TW, w), TH + 16), (255, 255, 255))
    c.paste(im, ((c.width - w) // 2, 16 + TH - h - 4 * S)); ImageDraw.Draw(c).text((3, 2), 'illustration', fill=(0, 0, 0)); return c


def build(view, clip, i, out, methods, ncol=8):
    gm = hx.read_grid(hx.SW + f'v2/m96/masters/EC0_{view}_96.txt')
    T = [illus(view), tile(gm, 'm96 master')]; ones = [gm]
    for m in methods:
        p = hx.EXP + f'out/{clip}/{m}/f{i:02d}.txt'
        if os.path.exists(p): g = hx.read_grid(p); T.append(tile(g, m)); ones.append(g)
    cols = min(ncol, len(T)); rows = (len(T) + cols - 1) // cols; W = max(t.width for t in T)
    B = Image.new('RGB', (cols * (W + 6), rows * (TH + 22) + 130), (110, 110, 110))
    for k, t in enumerate(T): B.paste(t, ((k % cols) * (W + 6), (k // cols) * (TH + 22)))
    y = rows * (TH + 22) + 4
    for k, g in enumerate(ones): B.paste(hx.render(g[Y0:Y1, X0:X1]), (4 + k * 90, y))
    B.save(out); return out


if __name__ == '__main__':
    v, c, i, o = sys.argv[1:5]; ms = sys.argv[5].split(',') if len(sys.argv) > 5 else None
    if ms is None:
        import run; ms = run.ALL
    build(v, c, int(i), o, ms)
