#!/usr/bin/env python3
"""QC: flag frames whose head part bbox differs from the reference head by >1px, or that use off-palette chars,
or that hide the head/bun. usage: qc.py [action ...]  (default: all actions/*_SE*.json and *_E*.json)"""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cm
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OK = set(cm.PAL) | {'.'}


def bbox(g):
    pts = [(x, y) for y, r in enumerate(g) for x, c in enumerate(r) if c != '.']
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return max(xs) - min(xs) + 1, max(ys) - min(ys) + 1


def part(pd, n):
    for d in (pd, 'parts/common'):
        p = os.path.join(ROOT, d, n + '.txt')
        if os.path.exists(p):
            return cm.read_cm(p)[0]


def check(path):
    a = json.load(open(path)); pd = a['partdir']; name = a['name']; bad = []
    ref = bbox(part(pd, a['rig']['head']['part']))
    for i, fr in enumerate(a['frames']):
        st = fr.get('set', {}); hide = fr.get('hide', [])
        if 'head' in hide or 'bun' in hide:
            bad.append(f'f{i:02d} hides head/bun')
        hp = st.get('head', {}).get('part', a['rig']['head']['part'])
        g = part(pd, hp)
        if g is None:
            bad.append(f'f{i:02d} missing head part {hp}'); continue
        w, h = bbox(g)
        if abs(w - ref[0]) > 1 or abs(h - ref[1]) > 1:
            bad.append(f'f{i:02d} head {hp} bbox {w}x{h} vs ref {ref[0]}x{ref[1]}')
        ft = os.path.join(ROOT, 'frames', name, f'f{i:02d}.txt')
        if os.path.exists(ft):
            chars = set(open(ft).read()) - {'\n'}
            if chars - OK:
                bad.append(f'f{i:02d} off-palette {sorted(chars - OK)}')
    print(('OK   ' if not bad else 'FAIL ') + name)
    for b in bad:
        print('   ', b)
    return not bad


if __name__ == '__main__':
    acts = sys.argv[1:] or sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, 'actions', '*_[SE]*.json'))
                                  if not os.path.basename(p).startswith(('test', 'stand')))
    res = [check(os.path.join(ROOT, 'actions', a + '.json')) for a in acts]
    sys.exit(0 if all(res) else 1)
