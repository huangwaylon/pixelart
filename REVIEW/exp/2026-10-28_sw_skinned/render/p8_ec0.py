"""p8_ec0.py (P, round 7 experiment): the masters' exact E2 recipe EC0 (swordswoman/v2/pixelize/tools/pz.py: k-centroid C0 ->
material-locked palette snap -> outline_sil -> cleanup() incl. its programmatic face pass) applied to R's whole 8x COLOUR render
(--preview with PVS=8: body PV colours + unlit illustration head), at the fixed game scale (8 hi-res px per sprite px, 128 cell, the
chain's align.json placement) instead of re-scaling each frame to 96 px.  pz.py finds the face itself (face_hull: skin hull of the head
from the source colours), so no face boxes or anchors are needed.
    p8_ec0.py <clip json> ...   -> <clip dir>/<stem>_ec0/fNN.{txt,png,json}
importable: ec0_frame(rgba_hi_1024, h_hint=None) -> 128x128 char grid"""
import sys, os, json, numpy as np
from PIL import Image
from scipy import ndimage as nd
ROOT = '/Users/waylonhuang/Documents/other/pixelart/'
sys.path.insert(0, ROOT + 'swordswoman/v2/pixelize/tools')
import pzlib as Z, pz as PZ  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
P, N, OFF = 8, 128, 256
KEYS, RGB, _ = Z.load_pal(Z.PAL18)


def ec0_frame(hi):
    """hi: (1024, 1024, 4) uint8 RGBA, the 128 cell at 8x (already placed).  Returns the EC0 grid in the same cell."""
    al = hi[..., 3] > 127; x = hi[..., :3].astype(float); x[~al] = 255
    a = hi[..., 3].reshape(N, P, N, P).mean((1, 3)) > 127
    ys, xs = np.nonzero(a); oy, y1, ox, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1; h, w = y1 - oy, x1 - ox
    pad = 2; y0p, x0p = max(0, oy - pad), max(0, ox - pad); y1p, x1p = min(N, y1 + pad), min(N, x1 + pad)
    hp = x[y0p * P:y1p * P, x0p * P:x1p * P]
    lo = PZ.kcentroid(hp, 3, line=False, prefilter=False)                       # C0
    am = a[y0p:y1p, x0p:x1p]
    lab, n = nd.label(am)                                                         # finish(): drop specks off the main body
    if n > 1:
        sz = nd.sum(am, lab, range(1, n + 1)); am = np.isin(lab, 1 + np.where(sz >= max(3, sz.max() * 0.01))[0])
    sub = Z.snap(lo, am, KEYS, RGB, True)                                         # material-locked palette snap (seg2)
    sub = Z.outline_sil(sub)
    g = np.full((N, N), '.', dtype='<U1'); g[y0p:y1p, x0p:x1p] = sub
    # cleanup(): face pass + orphans + skin specks + outline gaps, on the figure bbox source (x, m) at this scale
    xf = x[oy * P:y1 * P, ox * P:x1 * P].copy(); mf = al[oy * P:y1 * P, ox * P:x1 * P]
    g = PZ.cleanup(g, xf, mf, h, ox, oy, KEYS, RGB)
    return g


def run_clip(jp):
    info = json.load(open(jp)); stem = jp[:-5]; view = info['view']
    import pixel_chain as pc
    sh = pc.align(stem, view); od = stem + '_ec0'; os.makedirs(od, exist_ok=True); out = []
    for f in info['frames']:
        im = np.array(Image.open(f"{stem}_f{f['i']:02d}_pv.png").convert('RGBA'))
        hi = pc.crop(im.astype(float), sh['dx'], sh['dy']).astype(np.uint8)
        g = ec0_frame(hi)
        Z.save(g, f"{od}/f{f['i']:02d}", KEYS, RGB, {'method': 'EC0-render', 'view': view}); out.append(g)
    print('EC0', os.path.basename(stem), len(out))
    return out


if __name__ == '__main__':
    sys.argv, args = sys.argv[:1], sys.argv[1:]
    for jp in args: run_clip(jp)
