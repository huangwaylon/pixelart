"""make_tex.py (R, rounds 2-3): per-view head projection textures rig/tex/tex_<V>.png = the m96 master EC0_<V>_96 (128x128, exact palette
pixels) with every transparent pixel filled by its nearest opaque master pixel (so a hull overshoot of 1-2 px still gets head colours).
ROUND 3: the FACE is masked out (F draws eyes, brows, mouth and blush as pixel parts on R's 3D face anchors). In each anchor box from
v2/m96/heads/anchor.json the eye block (brow rows y0-3 .. lower lash y0+5, cols x0-1 .. x0+6), the mouth block and the blush patches are
cleared to skin base 's', except for (a) hair pixels whose 4-connected hair component reaches outside the box (bangs), (b) the head
outline (K next to transparent) and (c) the nose pixels. The cleared pixels are written to rig/tex/face_mask_<V>.png (white = cleared)
and tex_<V>_face.png keeps the unmasked version for reference."""
import os, json, numpy as np
from PIL import Image
from scipy import ndimage as nd
H = os.path.dirname(os.path.abspath(__file__)); SW = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/'
M = SW + 'masters/EC0_{}_96.png'; MT = SW + 'masters/EC0_{}_96.txt'
A = json.load(open(SW + 'heads/anchor.json'))['views']
PAL = {k: v['hex'] for k, v in json.load(open('/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/palette.json'))['colors'].items()}
def rgb(k): h = PAL[k]; return [int(h[i:i + 2], 16) for i in (1, 3, 5)]
HAIR = set('hHgL')
for v in ('S', 'SE', 'E', 'NE', 'N'):
    a = np.asarray(Image.open(M.format(v)).convert('RGBA')).copy(); op = a[..., 3] > 127
    g = np.array([list(l.rstrip('\n')) for l in open(MT.format(v)) if l.strip() and not l.startswith(';')])
    an = A[v]; box = np.zeros(g.shape, bool)
    for e in an.get('eyes', []): box[e['y0'] - 3:e['y0'] + 6, e['x0'] - 1:e['x0'] + 7] = True
    if an.get('mouth'): mx, my = an['mouth']; box[my - 1:my + 4, mx - 1:mx + 5] = True
    for bx, by, kind in an.get('blush', []): box[by - 1:by + 3, bx - 1:bx + (5 if kind == 'front' else 4 if kind == 'far' else 2)] = True
    for x_, y_ in an.get('ne_lash', []): box[y_ - 1:y_ + 2, x_ - 1:x_ + 2] = True
    hair = np.isin(g, list(HAIR)); lab, _ = nd.label(hair); keep_hair = np.zeros_like(hair)
    for l in np.unique(lab[hair]):
        comp = lab == l
        if (comp & ~box).any(): keep_hair |= comp  # reaches outside the face boxes -> bangs / side hair
    outline = (g == 'K') & nd.binary_dilation(g == '.', iterations=1)
    nose = np.zeros_like(box)
    for x_, y_, _ in an.get('nose', []): nose[y_, x_] = True
    clear = box & (g != '.') & ~keep_hair & ~outline & ~nose
    face = a.copy(); a[clear, :3] = rgb('s')
    _, (iy, ix) = nd.distance_transform_edt(~op, return_indices=True)
    for arr, nm in ((a, f'tex_{v}.png'), (face, f'tex_{v}_face.png')):
        b = arr[iy, ix]; b[..., 3] = 255; Image.fromarray(b, 'RGBA').save(os.path.join(H, 'tex', nm))
    Image.fromarray((clear * 255).astype(np.uint8)).save(os.path.join(H, 'tex', f'face_mask_{v}.png'))
    print(v, 'cleared', int(clear.sum()), 'px')
