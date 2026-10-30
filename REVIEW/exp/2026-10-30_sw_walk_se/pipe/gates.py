"""gates.py OUTDIR WORKDIR/<act>_<VIEW>.json MOTION.json GIF  (pixtools venv)  -- step 5: DESIGN_LOCK gates -> OUTDIR/gates.json
Blocking gates (lock section 6: only gates that map to the owner's words):
  line     lamet.metrics per frame, measured on the line art (the eye/brow glyphs are masked to skin: they are locked face shapes,
           not line art): zig (1-3-1 zigzags) <= 1, dbl (redundant L-corners) <= 2, gap (silhouette px not K) = 0,
           clump (2x2 K) = 0; interior K only at listed overlaps (every K is outline, a listed-overlap line or face ink) and every
           interior line piece >= 4 px.
  palette  colours per frame <= 14, every pixel one of the 14 lock keys, no material uses another material's colours.
  limbs    P's limb audit (render/pixel_chain.limb_audit / p_audit.py rules) on leg.L/R, arm.L/R, hand.L/R: VANISHED, SPLIT, THIN, DETACHED
           (3D visibility measured inside the drawn line: the 8x alpha eroded by SHRINK + 1 px).
  posture  M's motion gate (motion/scripts/mgate.py) on the re-baked motion.
  gif      loop=0, every frame >= 20 ms (render/gifcheck.py flags: NO_LOOP SHORT_FRAME GHOST_RISK GHOSTING SEAM DUP_FRAMES).
Report only: pxeval seq boil / shade_swap, temporal line pops (outline px present for a single frame), colours used."""
import os, sys, json, subprocess, re
import numpy as np
from scipy import ndimage as nd
ROOT = '/Users/waylonhuang/Documents/other/pixelart'; SK = ROOT + '/REVIEW/exp/2026-10-28_sw_skinned'
PY = ROOT + '/.models/pixtools/venv/bin/python'
sys.path.insert(0, ROOT + '/docs/team_review/2026-10-30/line_art'); sys.path.insert(0, SK + '/render')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lamet as LM  # noqa: E402
import gifcheck  # noqa: E402
import lock_chain as LC  # noqa: E402
P = 8
LIMBS = {'leg.L': ['leg.L'], 'leg.R': ['leg.R'], 'arm.L': ['arm.L'], 'arm.R': ['arm.R'], 'hand.L': ['hand.L'], 'hand.R': ['hand.R']}
GATE = {'zig': 1, 'dbl': 2, 'gap': 0, 'clump': 0}


def limb_audit(g, sub1, iline, F):
    """pixel_chain.limb_audit on the lock labels (same four rules)"""
    opaque = g != '.'; fillg = opaque & (g != 'K'); out = {}
    for name, subs in LIMBS.items():
        ids = [LC.SI[s] for s in subs]
        # visible in 3D = inside the drawn line: the lock outline sits ON the silhouette edge (traced on the alpha eroded by SHRINK),
        # so the outer 1 px of the 3D silhouette is line, not fill (P's chain drew its outline outside an eroded fill instead)
        L = fillg & np.isin(sub1, ids); hi = np.isin(F['sub'], ids) & nd.binary_erosion(F['alpha'], iterations=LC.SHRINK + P)
        hia = hi.sum() / (P * P); hl, hn = nd.label(hi, np.ones((3, 3)))
        hcomp = int(sum(1 for k in range(1, hn + 1) if (hl == k).sum() >= P * P)) if hn else 0
        Lc = L | (iline & nd.binary_dilation(L, LC.CROSS) & (g == 'K'))
        sl, sn = nd.label(Lc, np.ones((3, 3)))
        core = nd.binary_opening(np.pad(L, 1), np.ones((2, 2)))[1:-1, 1:-1]
        thin = int((L & ~nd.binary_dilation(core, LC.CROSS)).sum()); det = 0
        for k in range(1, sn + 1):
            c = (sl == k) & L
            if c.any() and not (nd.binary_dilation(c, np.ones((3, 3)), iterations=2) & fillg & ~c).any(): det += 1
        fl = []
        if hia >= 2 and L.sum() == 0: fl.append('VANISHED')
        if sn > max(1, hcomp): fl.append('SPLIT')
        if thin: fl.append('THIN')
        if det: fl.append('DETACHED')
        out[name] = {'px': int(L.sum()), 'hi_px': round(float(hia), 1), 'pieces': int(sn), 'hi_pieces': hcomp, 'thin': thin, 'flags': fl}
    return out


def line_pops(lines, subs):
    """outline px that exist in a single frame only: no line px within 1 px in the previous AND the next frame after moving that
    frame's line part by part (best integer shift of each body part, as the chain's temporal hysteresis does)"""
    n = len(lines); pops = []
    for t in range(n):
        a = lines[t]; cnt = np.zeros_like(a, int)
        for u in ((t - 1) % n, (t + 1) % n):
            by_part, _, _ = LC.part_motion(subs[u], lines[u], np.zeros(a.shape, np.int8), subs[t])
            m = np.zeros_like(a)
            for pts in by_part.values():
                if len(pts): m[pts[:, 0], pts[:, 1]] = True
            cnt += nd.binary_dilation(m, np.ones((3, 3)))
        pops.append(int((a & (cnt == 0)).sum()))
    return pops


def line_pops_flow(lines, Fs):
    """the same, but each neighbour frame's line is moved by the surface-point motion from the rest-position pass (per cell), so a
    swinging leg's line is compared with where that leg's surface really went (a pop = line that does not follow the body)"""
    n = len(lines); pops = []
    for t in range(n):
        a = lines[t]; cnt = np.zeros_like(a, int)
        for u in ((t - 1) % n, (t + 1) % n):
            m = np.zeros_like(a); w = LC.warp_pts(lines[u], LC.flow(Fs[u], Fs[t]))
            if len(w): m[w[:, 0], w[:, 1]] = True
            cnt += nd.binary_dilation(m, np.ones((3, 3)))
        pops.append(int((a & (cnt == 0)).sum()))
    return pops


def main(outd, jp, motion, gif):
    lab = np.load(os.path.join(outd, 'labels.npz')); info = json.load(open(jp)); n = len(info['frames']); stem = jp[:-5]
    LC.RPOS_BOX = info.get('rpos_box'); Fs = []
    grids = [LM.load_txt(os.path.join(outd, f'f{i:02d}.txt')) for i in range(n)]
    res = {'frames': n, 'line': [], 'palette': [], 'limbs': [], 'interior': []}
    for i, g in enumerate(grids):
        ink = lab[f'ink{i:02d}']; line = lab[f'line{i:02d}']; il = lab[f'iline{i:02d}']; mat1 = lab[f'mat1{i:02d}']; sub1 = lab[f'sub1{i:02d}']
        gl = g.copy(); gl[ink] = 's'  # line art only
        m = LM.metrics(gl); res['line'].append({k: m[k] for k in ('zig', 'dbl', 'gap', 'clump', 'mono', 'irr', 'kink', 'intK', 'orphK', 'K')})
        K = g == 'K'; stray = K & ~line & ~il & ~ink
        lb, nl = nd.label(il & K, np.ones((3, 3))); short = [int((lb == k).sum()) for k in range(1, nl + 1) if (lb == k).sum() < LC.MINLEN]
        kinds = lab[f'kind{i:02d}']; per = {k: int(((kinds == k) & K).sum()) for k in sorted(set(LC.PAIRS.values()))}
        res['interior'].append({'stray_K': int(stray.sum()), 'short_pieces': short, 'px_by_overlap': per})
        used = sorted(set(g[g != '.'].tolist())); off = [c for c in used if c not in LC.LOCK14]
        cross = 0; cross_ex = {}
        for mname, allow in LC.ALLOW.items():
            sel = (mat1 == LC.MI[mname]) & (g != '.') & ~ink & ~np.isin(g, list(allow))
            if sel.any(): cross += int(sel.sum()); cross_ex[mname] = sorted(set(g[sel].tolist()))
        res['palette'].append({'colours': len(used), 'used': ''.join(used), 'off_lock': off, 'cross_material_px': cross, 'cross': cross_ex})
        F = LC.load(stem, info['frames'][i]['i'], info['align']); Fs.append(F)
        res['limbs'].append(limb_audit(g, sub1, il, F))
    res['line_pops_flow'] = line_pops_flow([lab[f'line{i:02d}'] for i in range(n)], Fs)
    res['line_pops'] = line_pops([lab[f'line{i:02d}'] for i in range(n)], [lab[f'sub1{i:02d}'] for i in range(n)])
    # posture (M's gate on the re-baked motion)
    md = os.path.dirname(os.path.abspath(motion)); mn = os.path.splitext(os.path.basename(motion))[0]
    r = subprocess.run([PY, SK + '/motion/scripts/mgate.py', mn, '--dir', md], capture_output=True, text=True)
    res['posture'] = {'pass': 'GATE PASS' in r.stdout, 'out': r.stdout.strip().splitlines()[0] if r.stdout.strip() else r.stderr[-300:]}
    # gif
    gflags = sorted(gifcheck.check(gif, oneshot=()).get('flags', []))
    from PIL import Image
    im = Image.open(gif); durs = []
    for k in range(getattr(im, 'n_frames', 1)): im.seek(k); durs.append(im.info.get('duration', 0))
    res['gif'] = {'path': os.path.relpath(gif, outd), 'flags': gflags, 'loop': Image.open(gif).info.get('loop'), 'ms': durs, 'min_ms': min(durs)}
    # report only: pxeval seq
    ms = [f['ms'] for f in info['frames']]
    r = subprocess.run([PY, '-I', ROOT + '/pipeline/tools/pxeval.py', 'seq', os.path.join(os.path.abspath(outd), 'f??.png'), '--ms', *map(str, ms), '--loop', 'yes', '--compact'], capture_output=True, text=True, cwd=ROOT)
    try:
        q = json.loads(r.stdout); res['report'] = {k: q[k] for k in q if any(s in k for s in ('boil', 'shade_swap', 'flicker', 'seam'))}
    except Exception:
        res['report'] = {'pxeval_error': r.stderr[-400:]}
    # verdicts
    L = res['line']; lim = res['limbs']
    G = {
        'zigzags_le_1': max(x['zig'] for x in L) <= GATE['zig'], 'L_corners_le_2': max(x['dbl'] for x in L) <= GATE['dbl'],
        'gaps_0': max(x['gap'] for x in L) == 0, 'clumps_0': max(x['clump'] for x in L) == 0,
        'interior_K_listed_only': all(x['stray_K'] == 0 and not x['short_pieces'] for x in res['interior']),
        'palette_le_14': max(x['colours'] for x in res['palette']) <= 14, 'palette_on_lock': all(not x['off_lock'] for x in res['palette']),
        'palette_no_cross_material': all(x['cross_material_px'] == 0 for x in res['palette']),
        'limbs_connected': all(not v['flags'] for a in lim for v in a.values()),
        'posture': res['posture']['pass'], 'gif_loop_timing': res['gif']['loop'] == 0 and res['gif']['min_ms'] >= 20 and not res['gif']['flags']}
    res['gates'] = G; res['pass'] = all(G.values())
    res['summary'] = {'zig_max': max(x['zig'] for x in L), 'zig_mean': round(float(np.mean([x['zig'] for x in L])), 2),
                      'dbl_max': max(x['dbl'] for x in L), 'gap_max': max(x['gap'] for x in L), 'clump_max': max(x['clump'] for x in L),
                      'mono_mean': round(float(np.mean([x['mono'] for x in L])), 3), 'stray_K': sum(x['stray_K'] for x in res['interior']),
                      'colours_max': max(x['colours'] for x in res['palette']), 'cross_px': sum(x['cross_material_px'] for x in res['palette']),
                      'limb_fail_frames': [i for i, a in enumerate(lim) if any(v['flags'] for v in a.values())],
                      'line_pops_total': int(sum(res['line_pops'])), 'line_pops_flow_total': int(sum(res['line_pops_flow']))}
    json.dump(res, open(os.path.join(outd, 'gates.json'), 'w'), indent=1, default=lambda o: o.tolist() if hasattr(o, 'tolist') else str(o))
    return res


if __name__ == '__main__':
    r = main(*sys.argv[1:5])
    print('GATES', 'PASS' if r['pass'] else 'FAIL', json.dumps(r['gates']), json.dumps(r['summary']), json.dumps(r.get('report')))
