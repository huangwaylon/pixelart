"""face2build.py IN_DIR OUT_DIR [OLD_SPEC OLD_ANCHOR]: face round 2 (faithful face) pass on finished masters.
1) remove the previous neutral face marks (old eye_spec + old heads/anchor.json: eye/brow/wing template px, nose, mouth, blush -> skin)
2) geometry from face_measure.json (GEO below): S softer/rounder chin, SE far-cheek bulge removed, E profile nose/lip
3) new anchor (ANC below; wing_bg recorded from the cleaned master) -> heads/anchor.json
4) stamp.py face neutral (cat-eye, raised eyes, oval blush) -> OUT_DIR/EC0_<V>_96.{txt,png,json}
Defaults: OLD_SPEC/OLD_ANCHOR = snap/v11_preface2/{eye_spec.json,heads/anchor.json}."""
import sys, os, json, shutil
R = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/'; M = R + 'v2/m96/'
sys.path.insert(0, M + 'tools'); sys.path.insert(0, R + 'v2/pixelize/tools')
import eyetmpl as ET, stamp as ST

# new anchors (128-cell coords; measured targets, face_measure.json)
ANC = {
 'S':  dict(eyes=[dict(kind='front_left', x0=56, y0=49), dict(kind='front_right', x0=66, y0=49)], mouth=[62, 56],
            blush=[[57, 55, 'front'], [67, 55, 'front']], nose=[[63, 54, 'S'], [63, 55, 'S']]),
 'SE': dict(eyes=[dict(kind='front_left', x0=62, y0=50), dict(kind='far', x0=72, y0=50)], mouth=[67, 57],
            blush=[[62, 56, 'front'], [72, 56, 'far']], nose=[[71, 55, 'S'], [71, 56, 'S']]),
 'E':  dict(eyes=[dict(kind='profile', x0=72, y0=49)], mouth=[74, 56], blush=[[72, 55, 'front']],
            nose=[[78, 54, 's'], [79, 54, 'K'], [78, 55, 's'], [79, 55, 'K'], [78, 56, 'K']]),
 'NE': dict(blush=[[74, 58, 'ne']]),
}
# geometry px (x, y, char) from the illustration contours (face_measure.json spr.contour)
GEO = {
 'S': [(58, 57, 's'), (69, 57, 's'),                                  # jaw row 57: skin 58-69 (K 57/70)
       (58, 58, 'K'), (59, 58, 's'), (68, 58, 's'), (69, 58, 'K'),    # row 58: skin 59-68
       (59, 59, 'K'), (60, 59, 's'), (67, 59, 's'), (68, 59, 'K'),    # row 59: skin 60-67
       (60, 60, 'K'), (62, 60, 's'), (65, 60, 's'), (67, 60, 'K'),    # row 60: rounder chin bottom skin 62-65 (stair K 60-61 / 66-67)
       (54, 54, 'H'), (55, 54, 'H'), (72, 54, 'H'), (73, 54, 'H'),
       (54, 51, 'H'), (54, 52, 'H'), (54, 53, 'H'), (73, 51, 'H'), (73, 52, 'H'), (73, 53, 'H')],   # eye round: side-hair px beside the outer lash flicks h -> H (qc eye blob)                                 # side-hair px next to the lower lash: h -> H (qc eye blob stays the eye)                                 # row 60: rounder chin bottom skin 62-65
 'SE': [(75, 55, 'K'), (76, 55, 'H'), (77, 55, 'K'),
        (75, 56, 'K'), (76, 56, 'H'), (77, 56, 'K')],
 'E': [(77, 57, 's'), (78, 57, 'K')],                                 # upper lip at the profile (nose = anchor px)
}


def rd(p): return [list(l.rstrip('\n')) for l in open(p) if l.strip() and not l.startswith(';')]


def clean(g, v, osp, oan):
    a = oan['views'][v]
    fl = osp['front_left']['neutral']
    def tmpl(kind):
        if kind == 'front_left': return fl
        fr = ET.mirror(fl) if kind != 'far' else None
        if kind == 'front_right': return fr
        return [''.join(r[i] for i in (1, 2, 3, 5)) for r in ET.mirror(fl)]
    for ey in a.get('eyes', []):
        t = tmpl(ey['kind'])
        for j, r in enumerate(t):
            for i, c in enumerate(r):
                if c != '.': g[ey['y0'] + j][ey['x0'] + i] = 's'
        for j in range(-4, 0):   # old brow-window shade remnants (S) -> skin
            for i in (range(-1, 4) if ey['kind'] == 'far' else range(0, 6)):
                if g[ey['y0'] + j][ey['x0'] + i] == 'S': g[ey['y0'] + j][ey['x0'] + i] = 's'
        b = osp['brow']['front_left']['neutral'] if ey['kind'] != 'far' else osp['brow']['far']['neutral']
        if ey['kind'] == 'front_right': b = [r[::-1] for r in b]
        for j, r in enumerate(b):
            for i, c in enumerate(r):
                y, x = ey['y0'] - len(b) + j, ey['x0'] + i
                if c == 'h' and g[y][x] == osp['brow'].get('char', 'h'): g[y][x] = 's'
    if a.get('mouth'):
        mx, my = a['mouth']
        for j, r in enumerate(osp['mouth']['neutral']):
            for i, c in enumerate(r):
                if c not in '._' and g[my + j][mx + i] == c: g[my + j][mx + i] = 's'
    for bx, by, n in a.get('blush', []):
        for y in (by, by + 1):
            for x in range(bx - 1, bx + max(n, 2) + 1):
                if g[y][x] == 'k': g[y][x] = 's'
    for x, y, c in a.get('nose', []):
        if c == 'S': g[y][x] = 's'


def main():
    a = sys.argv[1:]; I, O = a[0], a[1]
    osp = json.load(open(a[2] if len(a) > 2 else M + 'snap/v11_preface2/eye_spec.json'))
    oan = json.load(open(a[3] if len(a) > 3 else M + 'snap/v11_preface2/heads/anchor.json'))
    import pzlib as Z
    keys, rgb, _ = Z.load_pal(R + 'v2/pixelize/palette.json')
    os.makedirs(O, exist_ok=True)
    anc = json.load(open(ST.ANC))
    for v in ['S', 'SE', 'E', 'NE', 'N']:
        g = rd(f'{I}/EC0_{v}_96.txt'); meta = json.load(open(f'{I}/EC0_{v}_96.json'))
        clean(g, v, osp, oan)
        for x, y, c in GEO.get(v, []): g[y][x] = c
        if v in ANC:
            anc['views'][v].update(json.loads(json.dumps(ANC[v])))
            for ey in anc['views'][v].get('eyes', []):
                ey['wing_bg'] = {'%d,%d' % (dx, dy): g[ey['y0'] + dy][ey['x0'] + dx] for dx, dy in ET.all_wings(ey['kind'])}
        if v != 'N': g = ST.face(g, v, 'neutral', anc)
        import numpy as np
        Z.save(np.array(g), f'{O}/EC0_{v}_96', keys, rgb, meta)
    anc['_doc'] = anc['_doc'].split(' FACE ROUND 2')[0] + (' FACE ROUND 2: eyes[i].wing_bg = master px under each cat-eye wing position (restored before drawing the expression wing);'
                  ' blush = [x, y, kind] oval patch origin (eye_spec blush[kind] templates); eye rows per eye_spec eye_dy (S 20, SE 21, E 20). Built by tools/face2build.py.')
    json.dump(anc, open(ST.ANC, 'w'), indent=1)
    print('face2build ->', O)


if __name__ == '__main__':
    main()
