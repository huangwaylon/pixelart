"""geom.py VIEW OUTDIR [--iters N] [--srcdir DIR]: cross-view geometry unification (geom_targets.json).
1) per-view pz figure height H so crown->sole spans the target rows; 2) piecewise-linear vertical warp of the illustration so
the landmark rows (qc_gate.parts + eye lash row) hit the targets; 3) horizontal head-band scale to the target head width.
Writes OUTDIR/src_<VIEW>.png (warped illustration), OUTDIR/EC0_<VIEW>_96.{txt,png,json} (auto master), OUTDIR/geom_<VIEW>.json."""
import sys, os, json, subprocess, numpy as np, cv2
R = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/'; M96 = R + 'v2/m96/'
sys.path.insert(0, R + 'v2/pixelize/tools'); sys.path.insert(0, M96 + 'tools'); sys.path.insert(0, R + 'v2/qc'); sys.path.insert(0, R + 'v2/anim_cut/tools')
import pzlib as Z, eyes as EY, colorcheck as CC
import qc_gate as QC
PY = R + '.scratch/pixelize/pixeloe/venv/bin/python'
TG = json.load(open(M96 + 'geom_targets.json')); PAL = CC.load(R + 'v2/pixelize/palette.json')
NAMES = ['crown', 'eye', 'chin', 'shoulder', 'waist', 'obi_bot', 'hem', 'sock_top', 'boot_top']


def run_pz(v, H, src, stem):
    subprocess.run([PY, '-I', M96 + 'tools/pzh.py', v, str(H), src, stem], check=True, capture_output=True)


def measure(stem, v):
    g, meta = Z.read(stem); P = QC.parts([''.join(r) for r in g], PAL)
    L = {k: P.get(k) for k in NAMES}
    try:
        d = EY.detect(g, meta, v); L['eye'] = d['eyes'][0]['y0'] + 1 if d['eyes'] else None
    except Exception: L['eye'] = None
    if v in ('NE', 'N'): L['eye'] = None
    return L, P['head'], meta


def fig_bbox(img):
    m = Z.fgmask(img.astype(float)); ys, xs = np.where(m)
    return ys.min(), ys.max(), xs.min(), xs.max()


def main():
    a = sys.argv[1:]; v, od = a[0], os.path.abspath(a[1]); iters = int(a[a.index('--iters') + 1]) if '--iters' in a else 3
    os.makedirs(od, exist_ok=True)
    src0 = Z.srcpath(v); img = cv2.cvtColor(cv2.imread(src0), cv2.COLOR_BGR2RGB)
    cur = f'{od}/src_{v}.png'; cv2.imwrite(cur, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    stem = f'{od}/EC0_{v}_96'; log = dict(view=v, src0=src0, it=[])
    # 1) H from the crown fraction (start at 96)
    H = 96
    for _ in range(2):
        run_pz(v, H, cur, stem); L, hd, meta = measure(stem, v)
        f = (L['crown'] - meta['oy']) / meta['h']; H2 = int(round((TG['rows']['sole'] + 1 - TG['rows']['crown']) / (1 - f)))
        if H2 == H: break
        H = H2
    log['H'] = H
    best = None
    for it in range(iters):
        run_pz(v, H, cur, stem); L, hd, meta = measure(stem, v)
        log['it'].append(dict(L=L, head_w=hd['w'], head_h=hd['h']))
        img = cv2.cvtColor(cv2.imread(cur), cv2.COLOR_BGR2RGB)
        e0 = max([abs(L[k] - TG['rows'][k]) for k in NAMES if L.get(k) is not None] + [abs(TG['head_w'].get(v, hd['w']) - hd['w'])])
        if best is None or e0 < best[0]: best = (e0, img.copy())
        by0, by1, bx0, bx1 = fig_bbox(img); Hh = by1 - by0 + 1; Ww = bx1 - bx0 + 1
        ill = lambda y: by0 + (y - meta['oy'] + 0.5) * Hh / meta['h'] - 0.5
        illx = lambda x: bx0 + (x - meta['ox'] + 0.5) * Ww / meta['w'] - 0.5
        src_r = [ill(meta['oy'] - 0.5)]; dst_r = [ill(meta['oy'] - 0.5)]
        for k in NAMES:
            if L.get(k) is None or k not in TG['rows']: continue
            s, t = ill(L[k]), ill(TG['rows'][k])
            if s <= src_r[-1] + 1 or t <= dst_r[-1] + 1: continue
            src_r.append(s); dst_r.append(t)
        end = ill(meta['oy'] + meta['h'] - 0.5); src_r.append(end); dst_r.append(end)
        Hi, Wi = img.shape[:2]
        yo = np.arange(Hi, dtype=np.float32)
        yi = np.interp(yo, dst_r, src_r)
        yi = np.where(yo < dst_r[0], yo - dst_r[0] + src_r[0], np.where(yo > dst_r[-1], yo - dst_r[-1] + src_r[-1], yi)).astype(np.float32)
        sx = 1.0
        if v in TG['head_w'] and hd['w']: sx = 1 + 0.5 * (TG['head_w'][v] / hd['w'] - 1)
        cx = illx((hd['x0'] + hd['x1']) / 2); chin_o = ill(TG['rows']['chin']); sh_o = ill(TG['rows']['chin'] + 3)
        s_row = np.where(yo <= chin_o, sx, np.where(yo >= sh_o, 1.0, sx + (1 - sx) * (yo - chin_o) / max(1, sh_o - chin_o)))
        xo = np.arange(Wi, dtype=np.float32)
        mapx = (cx + (xo[None, :] - cx) / s_row[:, None]).astype(np.float32)
        mapy = np.repeat(yi[:, None], Wi, 1).astype(np.float32)
        out = cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
        cv2.imwrite(cur, cv2.cvtColor(out, cv2.COLOR_RGB2BGR))
        err = max([abs(L[k] - TG['rows'][k]) for k in NAMES if L.get(k) is not None] + [abs(TG['head_w'].get(v, hd['w']) - hd['w'])])
        log['it'][-1]['maxerr'] = err
        if err <= 0.5 and it > 0: break
    run_pz(v, H, cur, stem); L, hd, meta = measure(stem, v)
    e0 = max([abs(L[k] - TG['rows'][k]) for k in NAMES if L.get(k) is not None] + [abs(TG['head_w'].get(v, hd['w']) - hd['w'])])
    if best is not None and best[0] < e0:
        cv2.imwrite(cur, cv2.cvtColor(best[1], cv2.COLOR_RGB2BGR)); run_pz(v, H, cur, stem); L, hd, meta = measure(stem, v)
    log['final'] = dict(L=L, head_w=hd['w'], head_h=hd['h'], x0=hd['x0'], x1=hd['x1'])
    json.dump(log, open(f'{od}/geom_{v}.json', 'w'), indent=1, default=int)
    print(v, 'H', H, 'final', {k: L[k] for k in NAMES}, 'head', hd['w'], 'x', hd['h'])


main()
