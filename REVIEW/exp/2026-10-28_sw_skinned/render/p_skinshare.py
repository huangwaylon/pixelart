"""p_skinshare.py <clip json> ... (P): dark-skin share = S cells / all skin-material cells, for the head part and for all skin, per frame (mean).
Masters for comparison: share of S among s/S/m/k skin chars in the head rows of EC0_<V>_96."""
import sys, json, numpy as np
sys.argv, args = sys.argv[:1], sys.argv[1:]
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned/render')
import pixel_chain as pc, hx
for jp in args:
    if jp.startswith('master:'):
        v = jp.split(':')[1]; g = hx.read_grid(pc.MAST.format(v)); ys = np.nonzero((g != '.').any(1))[0]; h = g[ys[0]:ys[0] + int(.4 * (ys[-1] - ys[0]))]
        sk = np.isin(h, list('sSmk')); print(f'master {v}: head dark-skin share {(h == "S").sum() / max(1, sk.sum()):.3f}'); continue
    info = json.load(open(jp)); stem = jp[:-5]
    G, sts, sh, aud = pc.run(stem, info, {'temporal': True, 'protect': True, 'sep': True})
    hs, al = [], []
    for g, st in zip(G, sts):
        lab = st['lab']; M_ = pc._mat(lab); P_ = pc._part(lab); skin = (M_ == pc.MI['skin']) & (g != 'K') & (g != '.')
        head = skin & (P_ == pc.PI['head'])
        hs.append((g[head] == 'S').sum() / max(1, head.sum())); al.append((g[skin] == 'S').sum() / max(1, skin.sum()))
    print(f"{info['action']} {info['view']}: head dark-skin share mean {np.mean(hs):.3f} (max {np.max(hs):.3f}), all skin {np.mean(al):.3f}")
