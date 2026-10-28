"""f_mirror_test.py (F, round 4) -- validates the mirrored-view face path (W/SW/NW) before R's native renders exist.
For a clip in E/SE/NE: mirror P's frames, the faceless head pass and the face json (x -> 128 - x, head turn sign flipped), run face_layer
with view W/SW/NW, and compare with the mirror of the E/SE/NE result.  Differences are expected ONLY where the spec keeps the iris unmirrored
(catchlight top-left in every view).  -> face/out/mirror/<act>_<W>_vs_<E>.png + a printed diff count."""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); EXP = os.path.dirname(HERE); sys.path.insert(0, HERE)
import face_layer as FLY, face_lib as FL
hx = FLY.hx; BG = (110, 110, 110)
INV = {v: k for k, v in FL.MIRROR.items()}


def run(act, src):
    V = INV[src]; od = f'{EXP}/face/out/mirror'; os.makedirs(od, exist_ok=True)
    fj = f'{EXP}/face/out/{act}/{act}_{src}_face.json'; d = json.load(open(fj)); m = json.loads(json.dumps(d))
    m['view'] = V; m['align'] = {'dx': -d['align']['dx'], 'dy': d['align']['dy']}; m['tex_off'] = [-d['tex_off'][0], d['tex_off'][1]]
    m['anchors_rest'] = {k: [128 - xy[0], xy[1]] for k, xy in d['anchors_rest'].items()}
    for f in m['frames']:
        for a in f['anchors'].values(): a['xy'][0] = 128 - a['xy'][0]
        f['head']['turn'] = -f['head']['turn']; f['head']['roll'] = -f['head']['roll']
    mj = f'{od}/{act}_{V}_face.json'; json.dump(m, open(mj, 'w'))
    pd = f'{EXP}/face/out/p2cur/{act}/{act}_{src}_px'
    tiles = []; ndiff = []
    for k, f in enumerate(d['frames']):
        i = f['i']; g = hx.read_grid(f'{pd}/f{i:02d}.txt')
        tex = FLY.load_ftex(f'{EXP}/face/out/{act}/{act}_{src}_f{i:02d}_tex.png', d['align']['dx'], d['align']['dy'])
        gs = FLY.face_layer({'action': act, 'view': src, 'i': i}, g, {'ftex': tex})
        T, gn = FLY.tex_cells(tex)   # texel phase is found on the native render (flipping hi-res turns a phase-4 tie into a 1 px shift)
        gm = FLY.face_layer({'action': act, 'view': V, 'i': i, 'face_json': mj}, g[:, ::-1].copy(), {'ftex_cells': (T[:, ::-1].copy(), gn[:, ::-1].copy())})
        ref = gs[:, ::-1]; dm = gm != ref; ndiff.append(int(dm.sum()))
        ys, xs = np.nonzero(gm[:72] != '.'); x0, y0 = max(0, int(np.median(xs)) - 20), max(0, ys.min() - 1)
        a = hx.render(ref[y0:y0 + 40, x0:x0 + 40], 5, BG).convert('RGB'); b = hx.render(gm[y0:y0 + 40, x0:x0 + 40], 5, BG).convert('RGB')
        dr = ImageDraw.Draw(b)
        for y, x in zip(*np.nonzero(dm[y0:y0 + 40, x0:x0 + 40])): dr.rectangle([x * 5, y * 5, x * 5 + 4, y * 5 + 4], outline=(0, 255, 0))
        t = Image.new('RGB', (200, 404), (36, 36, 40)); t.paste(a, (0, 0)); t.paste(b, (0, 204)); tiles.append(t)
    B = Image.new('RGB', (200 * len(tiles), 420), (36, 36, 40)); dr = ImageDraw.Draw(B)
    for k, t in enumerate(tiles): B.paste(t, (k * 200, 16))
    dr.text((4, 2), f'{act}: top = mirror of {src} result | bottom = {V} face path on mirrored inputs (green = differing px; expected only at the iris/catchlight)', fill=(230, 230, 120))
    B.save(f'{od}/{act}_{V}_vs_{src}.png'); print(act, V, 'diff px per frame', ndiff)


if __name__ == '__main__':
    for av in sys.argv[1:]:
        a, v = av.split(':'); run(a, v)
