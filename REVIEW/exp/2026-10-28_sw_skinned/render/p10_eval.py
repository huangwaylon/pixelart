"""p10_eval.py (P, round 10): default chain (R10=1) vs round-9 behaviour (R10=0) on render/out/p10 (rig r13): face_ssim / head ssim_b vs master+illus,
limb audit, hair light specks, cheek W specks, eye W pixels (W touching iris/lash), plus idle SE blink frames (closed-eye dark pixels kept)."""
import os, sys, json, glob, subprocess, numpy as np
from scipy import ndimage as nd
EXP = '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned'; ROOT = '/Users/waylonhuang/Documents/other/pixelart/'
PY = ROOT + '.models/pixtools/venv/bin/python'; P10 = EXP + '/render/out/p10'
sys.path.insert(0, EXP + '/render'); sys.path.insert(0, ROOT + 'swordswoman/v2/pixelize/tools')
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts'); import hx, pzlib as Z
exec(open(EXP + '/render/p8_eval.py').read().split('tmp = P8')[0].split("sys.argv = sys.argv[:1]")[0])  # MAST, PAL, headcrop/speck/still helpers
src = open(EXP + '/render/p8_eval.py').read(); ns = {}
exec(src[src.index('def headcrop'):src.index('tmp = P8')], {**globals(), 'Image': __import__('PIL.Image', fromlist=['Image']), 'HEADF': 0.42}, ns); globals().update(ns)
CL = [('rest', 'S'), ('rest', 'SE'), ('rest', 'E'), ('walk', 'SE'), ('walk', 'E'), ('idle', 'SE')]
FR = {('rest', 'S'): [0], ('rest', 'SE'): [0], ('rest', 'E'): [0], ('walk', 'SE'): [0, 3], ('walk', 'E'): [0, 3], ('idle', 'SE'): [0, 6]}


def specks(g):
    H, W = g.shape; p = np.pad(g, 2, constant_values='.')
    skin = sum(np.isin(p[2 + dy:2 + dy + H, 2 + dx:2 + dx + W], list('sSmk')) for dy in range(-2, 3) for dx in range(-2, 3)) > 0
    dk = sum(np.isin(p[2 + dy:2 + dy + H, 2 + dx:2 + dx + W], list('KhHg')) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx) > 0
    light = np.isin(g, list('WQL')); cl, n = nd.label(light, np.ones((3, 3)))
    small = np.isin(cl, [k for k in range(1, n + 1) if (cl == k).sum() <= 2]) if n else light & False
    return int((light & small & ~skin).sum()), int(((g == 'W') & ~dk & skin).sum()), int(((g == 'W') & dk & skin).sum())


res = {}
for tag, env in (('r9', '0'), ('r10', '1')):
    rows = []; tot = np.zeros(3, int); lim = []
    for act, V in CL:
        stem = f'{P10}/{act}/{act}_{V}'; e = dict(os.environ, R10=env)
        r = subprocess.run([PY, EXP + '/render/pixel_chain.py', stem + '.json'], capture_output=True, text=True, env=e)
        lim.append([l for l in r.stdout.splitlines() if l.startswith('LIMB_AUDIT')][0][:140])
        od = f'{P10}/{tag}/{act}_{V}'; os.makedirs(od, exist_ok=True); subprocess.run(['cp', '-R', stem + '_px/.', od])
        for f in sorted(glob.glob(od + '/f*.txt')): tot += np.array(specks(hx.read_grid(f)))
        for fi in FR[(act, V)]:
            png = f'{od}/f{fi:02d}.png'; tmp = f'{od}/head_f{fi:02d}.png'; headcrop(png, tmp); hm = f'{P10}/mhead_{V}.png'; headcrop(MAST.format(V), hm)
            il = still(png, illus=Z.srcpath(V)).get('vs_illus', {}); hb = still(tmp, ref=hm).get('vs_ref', {})
            rows.append((f'{act} {V} f{fi:02d}', il.get('face_ssim'), hb.get('ssim_b')))
    res[tag] = rows
    print(f"{tag}: face_ssim {np.mean([r[1] for r in rows if r[1] is not None]):.3f} head_ssim_b {np.mean([r[2] for r in rows]):.3f} | all frames: hair light specks {tot[0]}, cheek W specks {tot[1]}, eye W {tot[2]}")
    for l in lim: print('   ', l)
# blinks: idle SE frames with blink=1 in the motion: dark (K/h) pixels in the face of the r10 output
mot = json.load(open(EXP + '/motion/idle.json'))['frames']
bl = [i for i, f in enumerate(mot) if f.get('blink') == 1]
for i in bl:
    for tag in ('r9', 'r10'):
        g = hx.read_grid(f'{P10}/{tag}/idle_SE/f{i:02d}.txt'); ys = np.nonzero((g != '.').any(1))[0]; h = g[ys[0]:ys[0] + int(.42 * (ys[-1] - ys[0]))]
        print(f'idle SE blink f{i:02d} {tag}: face dark px (K/h on skin rows) {int(np.isin(h, list("Kh")).sum())}, W {int((h == "W").sum())}')
