"""p8_eval.py (P): EC0-on-render vs the current chain on render/out/p8 (rig r10).  Per frame:
  full figure vs the m96 master (pxeval still --ref, feet-aligned): ssim_b, same_px;  head crop (top 42 % of the figure) vs the master head: ssim_b;
  vs the illustration (pxeval --illus, alpha bbox): face_ssim;  head speckle (pixels with no same-colour 8-neighbour);
  limb audit: the chain's limb_audit run on each grid, with the chain's per-cell limb labels of the same frame.
-> render/out/p8/eval.json + a markdown table on stdout."""
import os, sys, glob, json, subprocess, numpy as np
from PIL import Image
EXP = '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned'; ROOT = '/Users/waylonhuang/Documents/other/pixelart/'
PY = ROOT + '.models/pixtools/venv/bin/python'; PAL = ROOT + 'swordswoman/v2/pixelize/palette.json'
MAST = ROOT + 'swordswoman/v2/m96/masters/EC0_{}_96.png'; P8 = EXP + '/render/out/p8'
sys.argv = sys.argv[:1]
sys.path.insert(0, EXP + '/render'); sys.path.insert(0, ROOT + 'swordswoman/v2/pixelize/tools')
import pzlib as Z  # noqa: E402
import pixel_chain as pc, hx  # noqa: E402
HEADF = 0.42
FR = [('rest', 'S', [0]), ('rest', 'SE', [0]), ('rest', 'E', [0]), ('walk', 'SE', [0, 3]), ('walk', 'E', [0, 3]), ('idle', 'SE', [0, 6])]


def headcrop(png, out):
    a = np.array(Image.open(png).convert('RGBA')); op = a[..., 3] > 0; ys = np.nonzero(op.any(1))[0]
    y1 = ys[0] + int(HEADF * (ys[-1] - ys[0])); b = a.copy(); b[y1 + 1:] = 0; Image.fromarray(b).save(out); return b


def speck(b):
    op = b[..., 3] > 0; k = np.where(op, (b[..., :3].astype(int) * [65536, 256, 1]).sum(-1), -1); H, W = op.shape
    p = np.pad(k, 1, constant_values=-2)
    same = sum((p[1 + dy:1 + dy + H, 1 + dx:1 + dx + W] == k).astype(int) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
    return int((op & (same == 0)).sum())


def still(c, ref=None, illus=None):
    cmd = [PY, '-I', ROOT + 'pipeline/tools/pxeval.py', 'still', c, '--pal', PAL, '--compact', '--align', 'feet'] + \
          (['--ref', ref] if ref else []) + (['--illus', illus, '--meta', 'none'] if illus else [])
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT); return json.loads(r.stdout) if r.stdout.strip() else {}


tmp = P8 + '/eval_tmp'; os.makedirs(tmp, exist_ok=True); rows = []
for act, V, fis in FR:
    stem = f'{P8}/{act}/{act}_{V}'; info = json.load(open(stem + '.json'))
    G, sts, sh, aud = pc.run(stem, info, {'temporal': True, 'protect': True, 'sep': True})
    os.environ['COLOR'] = 'ec0'; import importlib; importlib.reload(pc)
    Gh, stsh, _, _ = pc.run(stem, info, {'temporal': True, 'protect': True, 'sep': True})
    os.environ['COLOR'] = 'vote'; os.environ['PZCLEAN'] = '1'; importlib.reload(pc)
    Gc, stsc, _, _ = pc.run(stem, info, {'temporal': True, 'protect': True, 'sep': True})
    os.environ['PZCLEAN'] = '0'; importlib.reload(pc)
    cd_ = f'{stem}_pzc'; os.makedirs(cd_, exist_ok=True)
    for f_, g_ in zip(info['frames'], Gc): hx.save(g_, f"{cd_}/f{f_['i']:02d}", V)
    hd = f'{stem}_hyb'; os.makedirs(hd, exist_ok=True)
    for f_, g_ in zip(info['frames'], Gh): hx.save(g_, f"{hd}/f{f_['i']:02d}", V)
    Fs = None
    for fi in fis:
        k = [f['i'] for f in info['frames']].index(fi)
        F = pc.load(stem, fi, sh['dx'], sh['dy'], f'{P8}/{act}/parts')
        hm = headcrop(MAST.format(V), f'{tmp}/m_{V}.png')
        for meth, png in (('chain', f'{stem}_px/f{fi:02d}.png'), ('EC0', f'{stem}_ec0/f{fi:02d}.png'), ('chain+EC0 colour', f'{stem}_hyb/f{fi:02d}.png'), ('chain+pz cleanup', f'{stem}_pzc/f{fi:02d}.png')):
            g = hx.read_grid(png[:-4] + '.txt')
            a = still(png, ref=MAST.format(V)).get('vs_ref', {}); hc = headcrop(png, f'{tmp}/{meth}_{act}_{V}_{fi}.png')
            hb = still(f'{tmp}/{meth}_{act}_{V}_{fi}.png', ref=f'{tmp}/m_{V}.png').get('vs_ref', {})
            il = still(png, illus=Z.srcpath(V)).get('vs_illus', {})
            la = pc.limb_audit(g, (stsh if meth == 'chain+EC0 colour' else stsc if meth == 'chain+pz cleanup' else sts)[k], F); fl = {l: v['flags'] for l, v in la.items() if v['flags']}
            rows.append({'frame': f'{act} {V} f{fi:02d}', 'method': meth, 'ssim_b': a.get('ssim_b'), 'same_px': a.get('same_px'),
                         'head_ssim_b': hb.get('ssim_b'), 'face_ssim': il.get('face_ssim'), 'speckle': speck(hc), 'master_speckle': speck(hm),
                         'limbs': 'PASS' if not fl else json.dumps(fl)})
json.dump(rows, open(P8 + '/eval.json', 'w'), indent=0)
f4 = lambda v: '-' if v is None else f'{v:.3f}'
print('| frame | method | ssim_b | same_px | head ssim_b | face_ssim | speckle (master) | limbs |\n|---|---|---|---|---|---|---|---|')
for r in rows:
    print(f"| {r['frame']} | {r['method']} | {f4(r['ssim_b'])} | {f4(r['same_px'])} | {f4(r['head_ssim_b'])} | {f4(r['face_ssim'])} | {r['speckle']} ({r['master_speckle']}) | {r['limbs']} |")
for m in ('chain', 'EC0', 'chain+EC0 colour', 'chain+pz cleanup'):
    R = [r for r in rows if r['method'] == m]
    mean = lambda k: np.mean([r[k] for r in R if r[k] is not None])
    print(f"MEAN {m}: ssim_b {mean('ssim_b'):.3f} same_px {mean('same_px'):.3f} head_ssim_b {mean('head_ssim_b'):.3f} face_ssim {mean('face_ssim'):.3f} "
          f"speckle {mean('speckle'):.1f} (masters {mean('master_speckle'):.1f}) limb-pass {sum(r['limbs'] == 'PASS' for r in R)}/{len(R)}")
