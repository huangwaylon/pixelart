"""p7_eval.py <tag> (P, round 7): run the current chain (env knobs) on render/out/p7/{rest,walk} passes (rig r10, illustration-textured head) into
render/out/p7/<tag>/, then score the HEAD against the m96 master and the illustration with pxeval still:
  head crop = top HEADF (0.42) of the figure height for both candidate and master; --ref (feet-aligned crop) -> ssim / ssim_b / same_px;
  full frame --illus -> face_ssim; speckle = head pixels with no same-colour 8-neighbour.  Prints a table, writes <tag>/eval.json."""
import os, sys, glob, json, subprocess, numpy as np
from PIL import Image
EXP = '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned'; ROOT = '/Users/waylonhuang/Documents/other/pixelart/'
PY = ROOT + '.models/pixtools/venv/bin/python'; PAL = ROOT + 'swordswoman/v2/pixelize/palette.json'
MAST = ROOT + 'swordswoman/v2/m96/masters/EC0_{}_96.png'
sys.path.insert(0, ROOT + 'swordswoman/v2/pixelize/tools'); import pzlib as Z
tag = sys.argv[1]; P7 = f'{EXP}/render/out/p7'; OUT = f'{P7}/{tag}'; HEADF = 0.42
CLIPS = [('rest', 'S', 0), ('rest', 'SE', 0), ('rest', 'E', 0), ('walk', 'SE', 0), ('walk', 'SE', 3)]


def headcrop(png, out):
    a = np.array(Image.open(png).convert('RGBA')); op = a[..., 3] > 0; ys = np.nonzero(op.any(1))[0]
    y1 = ys[0] + int(HEADF * (ys[-1] - ys[0])); b = a.copy(); b[y1 + 1:] = 0; Image.fromarray(b).save(out); return b


def speck(b):
    op = b[..., 3] > 0; k = (b[..., :3].astype(int) * [65536, 256, 1]).sum(-1); H, W = op.shape
    p = np.pad(np.where(op, k, -1), 1, constant_values=-2)
    same = sum((p[1 + dy:1 + dy + H, 1 + dx:1 + dx + W] == np.where(op, k, -1)).astype(int) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
    return int((op & (same == 0)).sum())


def still(c, ref=None, illus=None):
    cmd = [PY, '-I', ROOT + 'pipeline/tools/pxeval.py', 'still', c, '--pal', PAL, '--compact', '--align', 'feet'] + (['--ref', ref] if ref else []) + (['--illus', illus, '--meta', 'none'] if illus else [])
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT); return json.loads(r.stdout) if r.stdout.strip() else {'err': r.stderr[-300:]}


rows = []
done = set()
for act, V, fi in CLIPS:
    d = f'{OUT}/{act}'; os.makedirs(d, exist_ok=True); stem = f'{act}_{V}'
    if (act, V) not in done:
        for f in glob.glob(f'{P7}/{act}/{stem}_f??_*.png') + glob.glob(f'{P7}/{act}/{stem}_rest_*.png') + [f'{P7}/{act}/{stem}.json']:
            t = f'{d}/{os.path.basename(f)}'
            if not os.path.lexists(t): os.symlink(f, t)
        if not os.path.lexists(f'{d}/parts'): os.symlink(f'{P7}/{act}/parts', f'{d}/parts')
        r = subprocess.run([PY, f'{EXP}/render/pixel_chain.py', f'{d}/{stem}.json'], capture_output=True, text=True)
        if r.returncode: print(r.stderr[-500:]); sys.exit(1)
        done.add((act, V))
    c = f'{d}/{stem}_px/f{fi:02d}.png'
    hc = headcrop(c, f'{d}/head_{V}_f{fi:02d}.png'); hm = headcrop(MAST.format(V), f'{d}/mhead_{V}.png')
    a = still(f'{d}/head_{V}_f{fi:02d}.png', ref=f'{d}/mhead_{V}.png')
    b = still(c, illus=Z.srcpath(V))
    vr = a.get('vs_ref', {}); vi = b.get('vs_illus', {})
    rows.append({'clip': f'{stem} f{fi:02d}', 'head_ssim': vr.get('ssim'), 'head_ssim_b': vr.get('ssim_b'), 'head_same_px': vr.get('same_px'),
                 'face_ssim_illus': vi.get('face_ssim'), 'ssim_b_illus': vi.get('ssim_b'), 'speckle': speck(hc), 'master_speckle': speck(hm)})
json.dump(rows, open(f'{OUT}/eval.json', 'w'), indent=0)
print(f'{tag}:'); [print('  ', r) for r in rows]
k = ['head_ssim_b', 'head_same_px', 'face_ssim_illus', 'speckle']
print(f'{tag} MEAN', {x: round(float(np.mean([r[x] for r in rows if r[x] is not None])), 4) for x in k})
