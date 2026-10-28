"""p_audit.py [out_dir ...]  (P): limb-audit gate report over every <clip>_limbs.json written by pixel_chain.py.
Gate per frame: every limb (leg.L/R, arm.L/R = sleeve tube + bag, hand.L/R) is ONE connected piece (or no more pieces than the
visible 3D limb has), >= 2 px wide (2x2 core + 1 px fringe), attached to the figure, and not vanished when visible in 3D.
Prints a markdown table (clip | frames | failed | failing frames: limb flags) and exits 1 if any frame fails.
Default dir: render/out/p5.  Writes <dir>/limb_audit.md."""
import sys, os, glob, json
EXP = '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned'
dirs = sys.argv[1:] or [EXP + '/render/out/p5']
bad = 0
for d in dirs:
    rows = ['| clip | frames | failed | fails |', '|---|---|---|---|']
    for f in sorted(glob.glob(os.path.join(d, '*', '*_limbs.json'))):
        s = json.load(open(f))['summary']; bad += s['failed_frames'] > 0
        fl = '; '.join(f"{k}: " + ', '.join(f"{l} {'/'.join(v)}" for l, v in lv.items()) for k, lv in s['fails'].items())
        rows.append(f"| {os.path.basename(f)[:-11]} | {s['frames']} | {s['failed_frames']} | {fl or 'PASS'} |")
    open(os.path.join(d, 'limb_audit.md'), 'w').write('\n'.join(rows) + '\n'); print('\n'.join(rows))
sys.exit(1 if bad else 0)
