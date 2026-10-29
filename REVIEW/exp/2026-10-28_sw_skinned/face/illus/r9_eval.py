"""r9_eval.py <tag> [<tag2>] (F round 9): face_ssim of the pixelized head vs the m96 master (S/SE rest, walk SE every frame) + head board.
face_ssim = SSIM (RGB, palette render) over the master's face box (eyes/brows/nose/mouth/blush rows, from heads/anchor.json), the frame aligned to the
master by the best integer shift within +-4 px on the head silhouette (removes the placement/lift offset)."""
import os, sys, json, glob
import numpy as np
from PIL import Image, ImageDraw
from skimage.metrics import structural_similarity as ssim
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts')
import hx
D = os.path.dirname(os.path.abspath(__file__)); M96 = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/'
ANC = json.load(open(M96 + 'heads/anchor.json'))['views']; BG = (110, 110, 110)
FB = {'S': (54, 46, 75, 60), 'SE': (59, 47, 79, 61)}   # face box x0 y0 x1 y1 (master cell coords)


def rgb(g): return np.array(hx.render(g, 1, BG)).astype(float)


def score(g, V):
    m = hx.read_grid(f'{M96}masters/EC0_{V}_96.txt'); x0, y0, x1, y1 = FB[V]; best = (-9, 0, 0)
    hm = (m[20:66] != '.'); 
    for dy in range(-5, 6):
        for dx in range(-5, 6):
            gs = np.roll(np.roll(g, dy, 0), dx, 1); iou = ((gs[20:66] != '.') & hm).sum() / max(1, ((gs[20:66] != '.') | hm).sum())
            if iou > best[0]: best = (iou, dy, dx)
    gs = np.roll(np.roll(g, best[1], 0), best[2], 1)
    a, b = rgb(gs)[y0:y1, x0:x1], rgb(m)[y0:y1, x0:x1]
    return float(ssim(a, b, channel_axis=2, data_range=255, win_size=7)), gs, m


def main():
    tags = sys.argv[1:]; rows = []; rep = {}
    for T in tags:
        res = {}; tl = []
        for a, V in (('rest', 'S'), ('rest', 'SE'), ('walk', 'SE'), ('idle', 'SE')):
            fs = sorted(glob.glob(f'{D}/r9/{T}/{a}/{a}_{V}_px/f*.txt'))
            sc = []
            for f in fs:
                s, gs, m = score(hx.read_grid(f), V); sc.append(s)
                if len(tl) < 16:
                    x0, y0, x1, y1 = FB[V]; t = hx.render(gs[y0 - 8:y1 + 3, x0 - 4:x1 + 4], 6, BG).convert('RGB')
                    ImageDraw.Draw(t).text((3, 2), f'{T} {a} {V} {os.path.basename(f)[:3]} {s:.3f}', fill=(255, 255, 150)); tl.append(t)
            res[f'{a}_{V}'] = round(float(np.mean(sc)), 4) if sc else None
        for V in ('S', 'SE'):
            m = hx.read_grid(f'{M96}masters/EC0_{V}_96.txt'); x0, y0, x1, y1 = FB[V]
            t = hx.render(m[y0 - 8:y1 + 3, x0 - 4:x1 + 4], 6, BG).convert('RGB'); ImageDraw.Draw(t).text((3, 2), f'm96 {V}', fill=(150, 220, 255)); tl.insert(0, t)
        rep[T] = res; rows.append(tl); print(T, res)
    W = max(sum(t.width + 4 for t in r) for r in rows); H = sum(max(t.height for t in r) + 4 for r in rows)
    B = Image.new('RGB', (W, H), (36, 36, 40)); y = 0
    for r in rows:
        x = 0
        for t in r: B.paste(t, (x, y)); x += t.width + 4
        y += max(t.height for t in r) + 4
    B.save(f'{D}/r9/board_{"_vs_".join(tags)}.png'); json.dump(rep, open(f'{D}/r9/face_ssim_{"_vs_".join(tags)}.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
