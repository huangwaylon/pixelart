"""temporal.py CLIP [METHODS] -> out/temporal_<clip>.json + gifs/<clip>_<method>.gif (4x, grey) + gifs/<clip>_grid.gif
static cell (t -> t+1) = its 8x8 hi-res block is unchanged in the render (same matid in every px, mean |dlum| < .01, alpha same).
flicker = output pixel changes on static cells / static cells.  chg = all changed px per transition (raw boiling + real motion).
boil = cells whose 1x material vote is the same at t and t+1 (and opaque) but whose output char changed / such cells (shading+line churn).
chg_sh = changed px after the best global integer shift (|d|<=2) of frame t onto t+1 (removes the whole-body bob)."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hx, run
from PIL import Image, ImageDraw


def static_masks(clip, n, sh):
    Fs = [hx.load(clip, i, sh['dx'], sh['dy']) for i in range(n)]; M = []
    for i in range(n):
        a, b = Fs[i], Fs[(i + 1) % n]
        same = hx.cells((a['mid'] == b['mid']).astype(float)).min((2, 3)) > 0.5
        dl = hx.cells(np.abs(a['lum'][..., 0] - b['lum'][..., 0])).mean((2, 3)) < 0.01
        anyf = hx.cells(((a['mid'] >= 0) | (b['mid'] >= 0)).astype(float)).max((2, 3)) > 0
        M.append(same & dl & anyf)
    return M, Fs


def gif(frames, ms, path, s=4):
    ims = [hx.render(g[14:128, 22:106], s) for g in frames]; ims[0].save(path, save_all=True, append_images=ims[1:], duration=ms, loop=0, disposal=1)


if __name__ == '__main__':
    clip = sys.argv[1]; view = clip.split('_')[1]; sh = run.align(view)
    meta = json.load(open(hx.EXP + f'big/{clip}/{clip}.json')); n = len(meta['frames']); ms = [f['ms'] for f in meta['frames']]
    methods = sys.argv[2].split(',') if len(sys.argv) > 2 else [m + s for m in run.ALL for s in ('', '_hs')]
    M, Fs = static_masks(clip, n, sh); MG = [hx.mat_grid(F) for F in Fs]; res = {'static_cells': [int(m.sum()) for m in M]}
    os.makedirs(hx.EXP + 'gifs', exist_ok=True)
    for m in methods:
        G = [hx.read_grid(hx.EXP + f'out/{clip}/{m}/f{i:02d}.txt') for i in range(n)]
        fl, ch, bo, bn, cs = [], [], 0, 0, []
        for i in range(n):
            j = (i + 1) % n; d = G[i] != G[j]; fl.append(int((d & M[i]).sum())); ch.append(int(d.sum()))
            sm = (MG[i] == MG[j]) & (MG[i] >= 0); bo += int((d & sm).sum()); bn += int(sm.sum())
            cs.append(min(int((np.roll(np.roll(G[i], dy, 0), dx, 1) != G[j]).sum()) for dy in range(-2, 3) for dx in range(-2, 3)))
        res[m] = {'flicker_px': fl, 'flicker_rate': round(sum(fl) / max(1, sum(res['static_cells'])), 4), 'chg_px_mean': round(float(np.mean(ch)), 1),
                  'boil': round(bo / max(1, bn), 4), 'band_churn': hx.band_churn(G), 'chg_sh_mean': round(float(np.mean(cs)), 1)}
        gif(G, ms, hx.EXP + f'gifs/{clip}_{m}.gif')
    json.dump(res, open(hx.EXP + f'out/temporal_{clip}.json', 'w'), indent=0)
    print('static cells/transition', res['static_cells'])
    print('method flicker_rate boil band_churn chg chg_sh')
    for m in methods: print(m.ljust(16), res[m]['flicker_rate'], res[m]['boil'], res[m]['band_churn'], res[m]['chg_px_mean'], res[m]['chg_sh_mean'])
