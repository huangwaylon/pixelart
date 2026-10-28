#!/usr/bin/env python3
"""pxeval_backtest.py: reproduce the 2026-10-28 pxeval back-test (REVIEW/exp/2026-10-28_pxeval/NOTES.md).

  .models/pixtools/venv/bin/python -I pipeline/tools/pxeval_backtest.py [--out REVIEW/exp/2026-10-28_pxeval]

1. seq on the swordswoman pilot (anim96 GIFs + 1x strips), mocap / unarmed / throw GIFs, 3d_motion previews
   (negative control: AA renders, not pixel art) and every row of the snowpeak S4_hd_actions_v1 idle/walk/run sheets.
2. still on swordswoman top1 + m96 masters vs the turnE_final illustrations (and masters vs their geo/ warped source),
   top1 vs masters; if scikit-image + the swordswoman metrics.py import, cross-check every shared key (must be equal).
3. writes backtest_seq.json, backtest_still.json, tables.md and viz/board PNGs into --out.
"""
import argparse, glob, json, os, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
PX = os.path.join(ROOT, 'pipeline', 'tools', 'pxeval.py')
SW = os.path.join(ROOT, 'swordswoman', 'v2')
ILL = {'S': 'iso_S.png', 'SE': 'iso_SE_fixed.png', 'E': 'iso_E.png', 'NE': 'iso_NE.png', 'N': 'iso_N.png'}
VIEWS = ['S', 'SE', 'E', 'NE', 'N']


def px(*args):
    r = subprocess.run([sys.executable, '-I', PX, *args, '--compact'], capture_output=True, text=True, cwd=ROOT)
    if r.returncode: raise SystemExit(f'pxeval failed: {args}\n{r.stderr}')
    return json.loads(r.stdout)


def rel(p): return os.path.relpath(p, ROOT)


def seq_set(out):
    vz = os.path.join(out, 'viz'); os.makedirs(vz, exist_ok=True)
    items = []
    A = 'REVIEW/swordswoman/anim96'
    items += [('sw pilot anim96', 'idle_SE gif', [f'{A}/idle_SE.gif'], 'motion 5 (Opus/Argon r2), "virtually zero motion", no_boiling 4'),
              ('sw pilot anim96', 'idle_SE 1x', ['swordswoman/v2/animate96/gifs/idle_SE_1x.png', '--cell', '128', '128', '--ms', '300', '150', '150', '300', '150', '150'], 'same, 6 frames incl. 2 exact holds'),
              ('sw pilot anim96', 'walk_SE gif', [f'{A}/walk_SE.gif'], 'motion 3 (Opus), legs never swap, face/hair boil, no_boiling 4'),
              ('sw pilot anim96', 'walk_SE 1x', ['swordswoman/v2/animate96/gifs/walk_SE_1x.png', '--cell', '128', '128', '--ms', '110', '100', '110', '110', '100', '110'], 'same')]
    for grp in ('mocap', 'unarmed', 'throw'):
        for g in sorted(glob.glob(os.path.join(ROOT, f'REVIEW/swordswoman/{grp}/*_SE.gif'))):
            items.append((f'sw {grp} 64px', os.path.basename(g)[:-4], [rel(g)], {'unarmed': 'Argon ~8/7/7', 'throw': 'Opus 5-6', 'mocap': 'pose tables kept'}[grp]))
    for g in sorted(glob.glob(os.path.join(ROOT, 'REVIEW/swordswoman/3d_motion/*_SE.gif'))):
        items.append(('sw 3d_motion preview (control)', os.path.basename(g)[:-4], [rel(g)], 'AA 3D render, not pixels'))
    rows = []
    for grp, name, args, crit in items:
        tag = (grp.split()[1] + '_' + name).replace(' ', '_')
        d = px('seq', *args, '--viz', os.path.join(vz, tag + '.png'))
        rows.append({'group': grp, 'name': name, 'critic': crit, **{k: v for k, v in d.items() if k not in ('pxeval', 'cmd')}})
    for clip in ('idle', 'walk', 'run'):
        sh = f'releases/S4_hd_actions_v1/{clip}/{clip}_sheet.png'
        d = px('seq', sh, '--row', 'all')
        for i, r in enumerate(d['rows']):
            rows.append({'group': 'snowpeak S4_hd v1 (shipped)', 'name': f"{clip}_{r['row_name']}", 'critic': 'released', **r})
        px('seq', sh, '--row', 'SE', '--viz', os.path.join(vz, f'snowpeak_{clip}_SE.png'), '--viz-scale', '4')
    json.dump(rows, open(os.path.join(out, 'backtest_seq.json'), 'w'), indent=1)
    return rows


def still_set(out):
    res = []
    pal = 'swordswoman/v2/pixelize/palette.json'
    for v in VIEWS:
        ill = f'swordswoman/v2/hair/turnE_final/{ILL[v]}'
        t = f'swordswoman/v2/pixelize/top1/EC0_{v}_96.png'; m = f'swordswoman/v2/m96/masters/EC0_{v}_96.png'
        geo = json.load(open(os.path.join(ROOT, m[:-4] + '.json')))['src']
        res.append(('top1 vs illus', v, px('still', t, '--ref', m, '--illus', ill, '--pal', pal, '--save-illus-grid', os.path.join(out, 'viz', f'illus_grid_{v}.png'))))
        res.append(('masters vs illus', v, px('still', m, '--illus', ill, '--pal', pal)))
        res.append(('masters vs geo src', v, px('still', m, '--illus', geo, '--pal', pal)))
    json.dump([{'case': c, 'view': v, **d} for c, v, d in res], open(os.path.join(out, 'backtest_still.json'), 'w'), indent=1)
    return res


def crosscheck(res):
    """compare with swordswoman/v2/pixelize/tools/metrics.py (needs scikit-image)."""
    try:
        sys.path.insert(0, os.path.join(SW, 'pixelize', 'tools'))
        import metrics as M, pzlib as Z  # noqa
    except Exception as e:
        return f'skipped ({e.__class__.__name__}: {e})', []
    import shutil, tempfile
    tmp = tempfile.mkdtemp(prefix='pxeval_xc_')
    keys = ['ssim', 'ssim_b', 'dE', 'sil', 'bloat', 'iou_hair', 'iou_red', 'iou_skin', 'iou_obi', 'iou_boot', 'iou_socks', 'line_f', 'kcomp', 'orph', 'face_ssim']
    worst = 0.0; rows = []
    for case, v, d in res:
        cand = os.path.join(ROOT, d['candidate'])
        stem = os.path.join(tmp, f'{case.replace(" ", "_")}_{v}')
        for ext in ('.txt', '.png'): shutil.copy(cand[:-4] + ext, stem + ext)
        meta = json.load(open(cand[:-4] + '.json'))
        meta['src'] = os.path.join(ROOT, d['illus']) if not os.path.isabs(d['illus']) else d['illus']
        meta['pal'] = os.path.join(ROOT, 'swordswoman', meta['pal']) if not os.path.isabs(meta['pal']) else meta['pal']
        json.dump(meta, open(stem + '.json', 'w'))
        o = M.metrics(stem)
        diff = {}
        for k in keys:
            a, b = o.get(k), d['vs_illus'].get(k)
            if isinstance(a, float) and a != a: a = None
            if a is None or b is None:
                if a != b: diff[k] = (a, b)
                continue
            dd = abs(float(a) - float(b)); worst = max(worst, dd if k not in ('kcomp', 'orph') else 0)
            if dd > 1e-4 + (0 if k in ('kcomp', 'orph') else 0): diff[k] = (a, b)
        rows.append((case, v, diff))
    shutil.rmtree(tmp)
    return f'max |diff| {worst:.2e} over {len(rows)} sprites x {len(keys)} keys', rows


def boards(out):
    vz = os.path.join(out, 'viz')
    rr = []
    for v in VIEWS:
        rr += ['--row', f'{v}:' + ','.join([os.path.join(vz, f'illus_grid_{v}.png'), f'swordswoman/v2/pixelize/top1/EC0_{v}_96.png', f'swordswoman/v2/m96/masters/EC0_{v}_96.png'])]
    px('board', os.path.join(out, 'board_still.png'), '--scale', '2', '--title', 'per view: illustration area-downsampled (the still --illus reference) | top1 E2@96 | m96 master  (1x + 2x)', *rr)
    px('board', os.path.join(out, 'board_pilot_vs_snowpeak.png'), '--scale', '2', '--title', 'pilot (anim96, 96px) vs shipped snowpeak (48px), SE, 1x + 2x',
       '--row', 'pilot idle (STIFF):swordswoman/v2/animate96/gifs/idle_SE_1x.png@128x128',
       '--row', 'pilot walk (BOILING):swordswoman/v2/animate96/gifs/walk_SE_1x.png@128x128',
       '--row', 'snowpeak idle SE (STIFF):releases/S4_hd_actions_v1/idle/idle_sheet.png@48x64rSE',
       '--row', 'snowpeak walk SE (ok):releases/S4_hd_actions_v1/walk/walk_sheet.png@48x64rSE')
    px('gif', os.path.join(out, 'pilot_walk_SE_x3.gif'), 'swordswoman/v2/animate96/gifs/walk_SE_1x.png', '--cell', '128', '128', '--scale', '3', '--ms', '110')


def plot(out, seq):
    """boil vs articulation/s scatter (log-log), one marker shape + colour per group, gate lines. PIL only."""
    import math
    from PIL import Image, ImageDraw, ImageFont
    sys.path.insert(0, os.path.dirname(PX)); import pxeval as X
    G = [('pilot', 'sw pilot anim96 (rejected)', '#2a78d6', 'o'), ('snowpeak', 'snowpeak S4_hd v1 (shipped)', '#1baf7a', 's'),
         ('64px', 'sw 64px mocap/unarmed/throw (3D-guide pixels)', '#eda100', '^'), ('3d_motion', 'sw 3d_motion AA preview (control)', '#eb6834', 'd')]
    W, H, l, r, t, b = 900, 600, 80, 30, 50, 70
    img = Image.new('RGB', (W, H), '#fcfcfb'); d = ImageDraw.Draw(img)
    try: f = ImageFont.load_default(size=13); fs = ImageFont.load_default(size=11)
    except TypeError: f = fs = ImageFont.load_default()
    x0, x1, y0, y1 = math.log10(0.01), math.log10(10), math.log10(0.0005), math.log10(0.5)
    X_ = lambda v: l + (math.log10(max(v, 1e-9)) - x0) / (x1 - x0) * (W - l - r)
    Y_ = lambda v: H - b - (math.log10(max(v, 1e-9)) - y0) / (y1 - y0) * (H - t - b)
    for v in (0.01, 0.1, 1, 10):
        d.line([(X_(v), t), (X_(v), H - b)], fill='#ebeae6'); d.text((X_(v) - 10, H - b + 6), f'{v:g}', fill='#52514e', font=fs)
    for v in (0.001, 0.01, 0.1):
        d.line([(l, Y_(v)), (W - r, Y_(v))], fill='#ebeae6'); d.text((l - 42, Y_(v) - 6), f'{v:g}', fill='#52514e', font=fs)
    bx, by = X.THRESH['stiff_articulation_per_s'], X.THRESH['boil_max']
    d.line([(l, Y_(by)), (W - r, Y_(by))], fill='#52514e', width=1); d.text((l + 6, Y_(by) - 16), f'boil gate {by}', fill='#52514e', font=fs)
    d.line([(X_(bx), t), (X_(bx), H - b)], fill='#52514e', width=1); d.text((X_(bx) + 4, t + 2), f'STIFF < {bx}/s', fill='#52514e', font=fs)
    def mark(x, y, c, sh, sz=5):
        if sh == 'o': d.ellipse([x - sz, y - sz, x + sz, y + sz], fill=c, outline='#fcfcfb', width=2)
        elif sh == 's': d.rectangle([x - sz, y - sz, x + sz, y + sz], fill=c, outline='#fcfcfb', width=2)
        elif sh == '^': d.polygon([(x, y - sz - 1), (x - sz - 1, y + sz), (x + sz + 1, y + sz)], fill=c, outline='#fcfcfb')
        else: d.polygon([(x, y - sz - 1), (x + sz + 1, y), (x, y + sz + 1), (x - sz - 1, y)], fill=c, outline='#fcfcfb')
    for key, lab, c, sh in G:
        for rr in seq:
            if key in rr['group'] and rr.get('articulation_per_s') is not None:
                x, y = X_(rr['articulation_per_s']), Y_(max(rr['boil'], 0.0005))
                mark(x, y, c, sh)
                if key == 'pilot' and '1x' in rr['name']: d.text((x + 8, y - 6), 'pilot ' + rr['name'].split()[0], fill='#0b0b0b', font=fs)
    for i, (key, lab, c, sh) in enumerate(G):
        mark(l + 10 + i * 205, 22, c, sh); d.text((l + 20 + i * 205, 15), lab.split(' (')[0], fill='#0b0b0b', font=fs)
    d.text((l, H - 30), 'articulation per second (non-rigid coherent motion, figure fraction / s, log)', fill='#0b0b0b', font=f)
    d.text((6, t - 18), 'boil (log)', fill='#0b0b0b', font=f)
    img.save(os.path.join(out, 'plot_boil_vs_articulation.png'))


def fmt(v, n=3):
    if v is None: return '-'
    if isinstance(v, float): return f'{v:.{n}f}'
    return str(v)


def tables(out, seq, still, xc):
    L = ['## seq back-test', '', '| group | clip | n | changed | resid | flicker | boil | shade_swap | motion_px | articulation | artic/s | rigid_share | pose_range | feet_rng | height_rng | seam_ratio | flags | critic |',
         '|' + '---|' * 18]
    for r in seq:
        L.append('| ' + ' | '.join([r['group'], r['name'], str(r['n_frames'])] + [fmt(r.get(k)) for k in
                 ('changed_mean', 'resid_mean', 'flicker', 'boil', 'shade_swap', 'motion_px', 'articulation', 'articulation_per_s', 'rigid_share', 'pose_range', 'feet_range', 'height_range', 'seam_ratio')]
                 + [' '.join(r['flags']) or 'ok', str(r['critic'])]) + ' |')
    L += ['', '## still back-test (vs_illus = metrics.py definitions)', '',
          '| case | view | ssim | ssim_b | dE | sil | bloat | line_f | face_ssim | orph | jaggies | colours | off_pal | outline_cov | l_corners | vs master ssim_b | vs master same_px |', '|' + '---|' * 17]
    for c, v, d in still:
        vi, cl, vr = d['vs_illus'], d['clean'], d.get('vs_ref', {})
        L.append('| ' + ' | '.join([c, v] + [fmt(vi.get(k)) for k in ('ssim', 'ssim_b', 'dE', 'sil', 'bloat', 'line_f', 'face_ssim', 'orph')]
                 + [fmt(cl.get(k)) for k in ('jaggies', 'colours', 'off_palette_px', 'outline_cov', 'l_corners')] + [fmt(vr.get('ssim_b')), fmt(vr.get('same_px'))]) + ' |')
    L += ['', f'metrics.py cross-check: {xc[0]}', '']
    for c, v, dd in xc[1]:
        if dd: L.append(f'- DIFF {c} {v}: {dd}')
    open(os.path.join(out, 'tables.md'), 'w').write('\n'.join(L) + '\n')
    return '\n'.join(L)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default=os.path.join(ROOT, 'REVIEW/exp/2026-10-28_pxeval'))
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    seq = seq_set(a.out); still = still_set(a.out); xc = crosscheck(still); boards(a.out); plot(a.out, seq)
    print(tables(a.out, seq, still, xc))
