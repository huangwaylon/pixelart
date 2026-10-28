"""p6_bench.py <tag> [acts] [views]  (P, round 6): re-run the CURRENT pixel chain on the latest release build's cached inputs
(release/out/latest/work/<act>/<V>: R passes + P part passes, symlinked, read-only) into render/out/p6/<tag>/<act>_<V>/, then
pxeval seq + limb audit + orphan count per clip -> render/out/p6/<tag>/bench.json and a summary line.  Chain knobs via env (HYS, LOCK, ...).
Parallel: env JOBS (default 6)."""
import os, sys, glob, json, subprocess
from concurrent.futures import ThreadPoolExecutor
EXP = '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned'; ROOT = '/Users/waylonhuang/Documents/other/pixelart/'
PY = ROOT + '.models/pixtools/venv/bin/python'; LW = os.path.realpath(EXP + '/release/out/latest/work')
tag = sys.argv[1]; acts = sys.argv[2].split() if len(sys.argv) > 2 else None; views = sys.argv[3].split() if len(sys.argv) > 3 else None
OUT = f'{EXP}/render/out/p6/{tag}'; os.makedirs(OUT, exist_ok=True)


def orphans(d):
    sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts'); import hx, numpy as np
    n = 0
    for f in sorted(glob.glob(d + '/f??.txt')):
        g = hx.read_grid(f); H, W = g.shape; p = np.pad(g, 1, constant_values='.')
        same = np.zeros((H, W), int)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy or dx: same += (p[1 + dy:1 + dy + H, 1 + dx:1 + dx + W] == g)
        n += int(((g != '.') & (g != 'K') & (same == 0)).sum())
    return n


def one(src):
    act, V = src.split('/')[-2:]; d = f'{OUT}/{act}_{V}'; os.makedirs(d, exist_ok=True)
    stem = json.load(open(f'{src}/clip.json')).get('stem', f'{act}_{V}') if os.path.exists(f'{src}/clip.json') else f'{act}_{V}'
    for f in glob.glob(f'{src}/{stem}_f??_*.png') + glob.glob(f'{src}/{stem}_rest_*.png') + [f'{src}/{stem}.json']:
        t = f'{d}/{os.path.basename(f)}'
        if not os.path.lexists(t): os.symlink(os.path.realpath(f), t)
    if not os.path.lexists(f'{d}/parts'): os.symlink(os.path.realpath(f'{src}/parts'), f'{d}/parts')
    r = subprocess.run([PY, f'{EXP}/render/pixel_chain.py', f'{d}/{stem}.json'], capture_output=True, text=True)
    if r.returncode: return {'clip': stem, 'error': r.stderr.strip().splitlines()[-1][:200]}
    info = json.load(open(f'{d}/{stem}.json')); ms = [str(f['ms']) for f in info['frames']]
    loop = 'no' if act.startswith(('jump', 'dash', 'hurt')) else 'yes'
    o = json.loads(subprocess.run([PY, '-I', ROOT + 'pipeline/tools/pxeval.py', 'seq', f'{d}/{stem}_px/f*.png', '--ms', *ms, '--loop', loop],
                                  capture_output=True, text=True, cwd=ROOT).stdout)
    la = json.load(open(f'{d}/{stem}_limbs.json'))['summary']
    return {'clip': stem, 'boil': o['boil'], 'shade_swap': o['shade_swap'], 'flags': o['flags'], 'limbs_pass': la['pass'], 'limb_fails': la['fails'],
            'orphans': orphans(f'{d}/{stem}_px'), 'frames': la['frames']}


srcs = sorted(d for d in glob.glob(LW + '/*/*') if os.path.isdir(d) and (not acts or d.split('/')[-2] in acts) and (not views or d.split('/')[-1] in views)
              and os.path.exists(f"{d}/clip.json"))
with ThreadPoolExecutor(int(os.environ.get('JOBS', '6'))) as ex: res = list(ex.map(one, srcs))
json.dump(res, open(f'{OUT}/bench.json', 'w'), indent=0)
ok = [r for r in res if 'error' not in r]
import statistics as S
print(f"{tag}: {len(ok)}/{len(res)} clips | limbs pass {sum(r['limbs_pass'] for r in ok)} | shade_swap<=.015 {sum(r['shade_swap'] <= .015 for r in ok)} "
      f"mean {S.mean(r['shade_swap'] for r in ok):.4f} median {S.median(r['shade_swap'] for r in ok):.4f} | boil<=.02 {sum(r['boil'] <= .02 for r in ok)} "
      f"mean {S.mean(r['boil'] for r in ok):.4f} | orphans/frame {sum(r['orphans'] for r in ok) / max(1, sum(r['frames'] for r in ok)):.2f}")
for r in res:
    if 'error' in r: print('ERR', r['clip'], r['error'])
