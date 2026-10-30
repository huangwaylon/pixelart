"""compare.py OUTDIR  -- step 6: board round-10 walk SE vs the locked build, and (once they exist) f00/f02 vs the gold frames.
  OUTDIR/compare/r10_vs_lock_strip1x.png   two rows (round 10 | lock), 8 frames, 1x
  OUTDIR/compare/r10_vs_lock_4x.png        same, 4x nearest, labelled
  OUTDIR/compare/r10_vs_lock_4x.gif        side by side animation (gifio, motion timing)
Gold (../gold/walk_SE_contact.png -> f00, ../gold/walk_SE_passing.png -> f02; another teammate makes them):
  pxeval still fNN.png --ref gold --json OUTDIR/compare/pxeval_fNN_vs_gold.json
  OUTDIR/compare/gold_diff_fNN.json  every pixel where the build differs from the gold frame (after the best +-6 px alignment),
      classified silhouette / outline / interior_line / face / fill, = the candidate override pixels {x, y, key, reason}
  OUTDIR/compare/gold_board_fNN.png  build | gold | diff (6x)"""
import sys, os, json, subprocess
import numpy as np
from PIL import Image, ImageDraw
ROOT = '/Users/waylonhuang/Documents/other/pixelart'; PY = ROOT + '/.models/pixtools/venv/bin/python'
R10 = ROOT + '/REVIEW/exp/2026-10-28_sw_skinned/release/out/20261030_66119a7/work/walk/SE/final'
GOLD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'gold')
sys.path.insert(0, ROOT + '/REVIEW/exp/2026-10-28_sw_skinned/render'); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gifio import write_gif  # noqa: E402
import lock_chain as LC  # noqa: E402
BG = (110, 110, 110, 255)
PALL = {k: v for k, v in json.load(open(ROOT + '/swordswoman/v2/pixelize/palette.json'))['colors'].items()}
PRGB = {k: tuple(int(v['hex'][i:i + 2], 16) for i in (1, 3, 5)) for k, v in PALL.items()}


def frames(d, n=8): return [Image.open(os.path.join(d, f'f{i:02d}.png')).convert('RGBA') for i in range(n)]


def strip_rows(rows, box, s=1, labels=None):
    x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0; lab = 14 if labels else 0
    out = Image.new('RGBA', (w * len(rows[0]) * s, (h * s + lab) * len(rows)), BG)
    d = ImageDraw.Draw(out)
    for r, row in enumerate(rows):
        for i, im in enumerate(row):
            out.alpha_composite(im.crop(box).resize((w * s, h * s), Image.NEAREST), (i * w * s, r * (h * s + lab) + lab))
        if labels: d.text((3, r * (h * s + lab)), labels[r], fill=(255, 255, 0, 255))
    return out


def keygrid(im):
    a = np.asarray(im.convert('RGBA')).astype(int); g = np.full(a.shape[:2], '.', dtype='<U1')
    keys = list(PRGB); cols = np.array([PRGB[k] for k in keys])
    op = a[..., 3] > 127; d = ((a[..., None, :3] - cols[None, None]) ** 2).sum(-1); g[op] = np.array(keys)[d.argmin(-1)][op]
    return g


def load_gold(p):
    im = Image.open(p).convert('RGBA')
    if im.size != (128, 128):
        for k in (2, 3, 4, 5, 6, 8):
            if im.size[0] % k == 0 and im.size[1] % k == 0 and (im.size[0] // k, im.size[1] // k) == (128, 128): im = im.resize((128, 128), Image.NEAREST); break
    if im.size != (128, 128):  # a cropped sprite: centre it by its alpha bbox on a 128 cell
        c = Image.new('RGBA', (128, 128), (0, 0, 0, 0)); bb = im.getbbox(); sp = im.crop(bb); c.alpha_composite(sp, ((128 - sp.width) // 2, 128 - 6 - sp.height)); im = c
    return im


def gold_diff(i, name, outd, cmpd, lab):
    gp = os.path.join(GOLD, name)
    if not os.path.exists(gp): return {'frame': f'f{i:02d}', 'gold': os.path.relpath(gp, outd), 'status': 'pending (gold frame not there yet)'}
    ours = keygrid(Image.open(os.path.join(outd, f'f{i:02d}.png'))); gold = keygrid(load_gold(gp))
    best = (1 << 30, 0, 0)
    for dy in range(-6, 7):
        for dx in range(-6, 7):
            v = int((np.roll(np.roll(gold, dy, 0), dx, 1) != ours).sum())
            if v < best[0]: best = (v, dy, dx)
    gold = np.roll(np.roll(gold, best[1], 0), best[2], 1)
    line = lab[f'line{i:02d}']; il = lab[f'iline{i:02d}']; ink = lab[f'ink{i:02d}']; sub1 = lab[f'sub1{i:02d}']
    px = []
    for y, x in zip(*np.nonzero(ours != gold)):
        o, g = ours[y, x], gold[y, x]
        if (o == '.') != (g == '.'): why = 'silhouette'
        elif ink[y, x] or (sub1[y, x] == LC.SI['face'] and (g in 'KgWh' or o in 'KgWh')): why = 'face'
        elif line[y, x] or (g == 'K' and (ours[max(y - 1, 0):y + 2, max(x - 1, 0):x + 2] == '.').any()): why = 'outline'
        elif il[y, x] or o == 'K' or g == 'K': why = 'interior_line'
        else: why = 'fill'
        px.append({'x': int(x), 'y': int(y), 'ours': str(o), 'key': str(g), 'reason': why})
    cnt = {}
    for p in px: cnt[p['reason']] = cnt.get(p['reason'], 0) + 1
    band = {}
    for p in px:
        b = 'head (y<62)' if p['y'] < 62 else 'body (62-90)' if p['y'] < 91 else 'legs (>=91)'; band[b] = band.get(b, 0) + 1
    res = {'frame': f'f{i:02d}', 'gold': os.path.relpath(gp, outd), 'align_dy_dx': [best[1], best[2]], 'diff_px': len(px), 'by_reason': cnt, 'by_band': band,
           'figure_px': {'build': int((ours != '.').sum()), 'gold': int((gold != '.').sum())},
           'candidate_overrides': px}
    json.dump(res, open(os.path.join(cmpd, f'gold_diff_f{i:02d}.json'), 'w'), indent=0)
    r = subprocess.run([PY, '-I', ROOT + '/pipeline/tools/pxeval.py', 'still', os.path.join(os.path.abspath(outd), f'f{i:02d}.png'), '--ref', os.path.abspath(gp),
                        '--json', os.path.join(os.path.abspath(cmpd), f'pxeval_f{i:02d}_vs_gold.json'), '--compact'], capture_output=True, text=True, cwd=ROOT)
    try: res['pxeval'] = json.loads(r.stdout)['vs_ref']
    except Exception: res['pxeval'] = {'error': r.stderr[-300:]}
    # board: ours | gold | diff
    def img(gr):
        a = np.zeros((128, 128, 4), np.uint8)
        for k, c in PRGB.items(): a[gr == k, :3] = c
        a[gr != '.', 3] = 255; return Image.fromarray(a)
    dm = np.zeros((128, 128, 4), np.uint8); col = {'silhouette': (0, 220, 255), 'outline': (255, 60, 60), 'interior_line': (255, 160, 0), 'face': (255, 0, 255), 'fill': (255, 255, 0)}
    for p in px: dm[p['y'], p['x']] = (*col[p['reason']], 255)
    ys, xs = np.nonzero((ours != '.') | (gold != '.')); box = (max(xs.min() - 3, 0), max(ys.min() - 3, 0), min(xs.max() + 4, 128), min(ys.max() + 4, 128))
    b = strip_rows([[img(ours), img(gold), Image.fromarray(dm)]], box, s=6)
    ImageDraw.Draw(b).text((4, 4), f'build f{i:02d} | gold {name} | diff: cyan silhouette red outline orange interior magenta face yellow fill', fill=(255, 255, 255, 255))
    b.save(os.path.join(cmpd, f'gold_board_f{i:02d}.png'))
    return {k: v for k, v in res.items() if k != 'candidate_overrides'}


def main(outd):
    cmpd = os.path.join(outd, 'compare'); os.makedirs(cmpd, exist_ok=True)
    info = json.load(open(os.path.join(outd, 'chain.json'))); ms = info['ms']
    A, B = frames(R10), frames(outd)
    boxes = [im.getbbox() for im in A + B]; box = (min(b[0] for b in boxes) - 2, min(b[1] for b in boxes) - 2, max(b[2] for b in boxes) + 2, max(b[3] for b in boxes) + 2)
    strip_rows([A, B], box, 1).save(os.path.join(cmpd, 'r10_vs_lock_strip1x.png'))
    strip_rows([A, B], box, 4, ['round 10 (20261030_66119a7) walk SE', 'DESIGN LOCK build walk SE']).save(os.path.join(cmpd, 'r10_vs_lock_4x.png'))
    sbs = []
    for a, b in zip(A, B):
        c = Image.new('RGBA', ((box[2] - box[0]) * 2 + 4, box[3] - box[1]), BG); c.alpha_composite(a.crop(box), (0, 0)); c.alpha_composite(b.crop(box), (box[2] - box[0] + 4, 0)); sbs.append(c)
    write_gif(os.path.join(cmpd, 'r10_vs_lock_4x.gif'), sbs, ms, bg=BG[:3], scale=4)
    lab = np.load(os.path.join(outd, 'labels.npz'))
    gold = [gold_diff(0, 'walk_SE_contact.png', outd, cmpd, lab), gold_diff(2, 'walk_SE_passing.png', outd, cmpd, lab)]
    json.dump({'r10_vs_lock': ['r10_vs_lock_strip1x.png', 'r10_vs_lock_4x.png', 'r10_vs_lock_4x.gif'], 'gold': gold}, open(os.path.join(cmpd, 'compare.json'), 'w'), indent=1)
    print('COMPARE', json.dumps(gold))


if __name__ == '__main__':
    main(sys.argv[1])
