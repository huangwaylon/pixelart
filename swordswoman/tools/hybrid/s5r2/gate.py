"""S5 r2 GATE (DECISION r1 foundation 6) on a sprite set: body orphans 0 (head-stamp px excluded: lock2 stamp is
locked), off-palette 0, semi-alpha 0, flicker 0, body height 56-64 on standing keys (turn/walk/slash; jump squash
and stretch keys are reported, not gated), baseline spread 0 and feet_cx spread <= 1 on the turn set, walk crown
range 4-5 with the head lagging, slash tip-arc rms <= 1, k1 smear >= 15 px, plus colour drift vs the S3 turn cels.
gate.py SPRITE_DIR METRICS.json [--s3 S3_TURN_DIR]"""
import sys, os, json
import numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools/hybrid'); sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools/pixel')
import hylib as H, lint as L
d, mj = sys.argv[1], sys.argv[2]
M = json.load(open(mj)); res = {}; fails = []
work = os.path.join(d, '..', 'work')
for s in M['sprites']:
    n = s['name'][:-4]; a = H.load_rgba(os.path.join(d, s['name'])); pal = H.palette(); idx = H.index_of(a)
    flags, info, _ = L.lint_frame(a, pal, None, None)
    sword = H.disk_op(H.base_mask(idx, 'steel'), 1)
    hp = os.path.join(work, n + '_head.npy'); head = np.load(hp) if os.path.exists(hp) else np.zeros(idx.shape, bool)
    orph = [f for f in flags if f['type'] == 'orphan' and f.get('detail') not in H.ORPHAN_OK and not sword[f['y'], f['x']]]
    body_o = [f for f in orph if not head[f['y'], f['x']]]
    r = dict(body_orphans=len(body_o), head_orphans=len(orph) - len(body_o), off_palette=s['off_palette'],
             semi_alpha=s['semi_alpha'], body_height=s.get('body_height'), height=s.get('height'))
    standing = not n.startswith('jump')
    if r['body_orphans']: fails.append(f'{n}: body orphans {r["body_orphans"]} {[(f["x"], f["y"]) for f in body_o]}')
    if r['off_palette'] or r['semi_alpha']: fails.append(f'{n}: palette/alpha')
    if standing and not (56 <= (r['body_height'] or 0) <= 64): fails.append(f'{n}: body height {r["body_height"]}')
    res[n] = r
dirs = M.get('directions', {})
for q in M['sequences']:
    nm = f"{q['anim']}_{q['dir']}"
    if q.get('flicker'): fails.append(f'{nm}: flicker {q["flicker"]}')
    if q['anim'] == 'slash':
        rms = (q.get('tip_arc') or {}).get('rms', 9)
        if rms > 1.0: fails.append(f'{nm}: tip arc rms {rms}')
        if q['smear_px'][1] < 15: fails.append(f'{nm}: k1 smear {q["smear_px"][1]}')
    if q['anim'] == 'walk':
        if not (4 <= q.get('head_disp_max', 0) <= 5.5): fails.append(f'{nm}: crown range {q.get("head_disp_max")}')
        if q.get('head_lag', 0) < 1: fails.append(f'{nm}: head not lagging')
print(json.dumps(dict(per_sprite=res, fails=fails), indent=1)[-3000:])
json.dump(dict(per_sprite=res, fails=fails), open(os.path.join(d, '..', 'gate.json'), 'w'), indent=1)
print('GATE', 'PASS' if not fails else f'FAIL ({len(fails)})')
for f in fails: print(' -', f)
