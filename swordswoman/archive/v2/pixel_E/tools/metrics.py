#!/usr/bin/env python3
"""Frame-to-frame consistency metrics for a redrawn sequence vs its master.
Usage: metrics.py MASTER.png f0.png f1.png ... > report
Per frame: material pixel counts (hair, red, skin, obi/boots, steel, outline), head bbox (hair+bow) size/top,
colour count; deltas vs master in %; head-mask IoU between consecutive frames after aligning the head bbox."""
import sys, json
import numpy as np
from PIL import Image

PAL = json.load(open('/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixel/palette.json'))['colors']
GROUPS = {'hair': 'hHj', 'red': 'rREe', 'skin': '123p', 'obi': 'Dd', 'steel': 'mnw', 'iris': 'iI', 'outline': '#'}
HEX = {c: v[0].lower() for c, v in PAL.items()}


def load(p):
    a = np.array(Image.open(p).convert('RGBA'))
    keys = np.full(a.shape[:2], '.', dtype='<U1')
    for c, h in HEX.items():
        rgb = [int(h[i:i + 2], 16) for i in (1, 3, 5)]
        keys[(a[..., 3] >= 128) & (a[..., :3] == rgb).all(-1)] = c
    return keys


def stats(k):
    s = {g: int(np.isin(k, list(cs)).sum()) for g, cs in GROUPS.items()}
    head = np.isin(k, list('hHj'))   # hair mass only (bow/red would pick up sleeves when the head tilts)
    obi_rows = np.nonzero((np.isin(k, list('Dd')).sum(1) >= 5))[0]
    if len(obi_rows):
        head[obi_rows.min():] = False   # boots quantize to hair-dark: keep only hair above the obi
    ys, xs = np.nonzero(head)
    s['head_w'] = int(xs.max() - xs.min() + 1); s['head_h'] = int(ys.max() - ys.min() + 1); s['head_top'] = int(ys.min())
    s['colors'] = int(len(set(k[k != '.'].tolist())))
    return s, head[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def headline(k):
    hair = np.isin(k, list('hHj'))
    rows = np.nonzero(hair.any(1))[0]
    return rows.max() if len(rows) else k.shape[0]


def iou(a, b):
    H = max(a.shape[0], b.shape[0]); W = max(a.shape[1], b.shape[1])
    A = np.zeros((H, W), bool); B = np.zeros((H, W), bool)
    A[:a.shape[0], :a.shape[1]] = a; B[:b.shape[0], :b.shape[1]] = b
    return (A & B).sum() / max(1, (A | B).sum())


m, mh = stats(load(sys.argv[1]))
rows = []
prev = None
for p in sys.argv[2:]:
    s, h = stats(load(p))
    d = {g: round(100 * (s[g] - m[g]) / max(1, m[g]), 1) for g in ('hair', 'red', 'skin', 'obi', 'steel')}
    rows.append({'frame': p.split('/')[-1], **{f'd_{g}%': v for g, v in d.items()},
                 'head_wh': (s['head_w'], s['head_h']), 'head_top': s['head_top'], 'colors': s['colors'],
                 'iou_head_prev': float(round(iou(prev, h), 3)) if prev is not None else None,
                 'iou_head_master': float(round(iou(mh, h), 3))})
    prev = h
print('master', {k: m[k] for k in ('hair', 'red', 'skin', 'obi', 'steel', 'head_w', 'head_h', 'colors')})
for r in rows:
    print(r)
hair = [abs(r['d_hair%']) for r in rows]
ious = [r['iou_head_prev'] for r in rows if r['iou_head_prev'] is not None]
print('SUMMARY mean|d_hair|=%.1f%%  max|d_hair|=%.1f%%  mean head IoU(prev)=%.3f  min=%.3f  head_w range=%s' % (
    np.mean(hair), np.max(hair), np.mean(ious) if ious else 0, np.min(ious) if ious else 0,
    (min(r['head_wh'][0] for r in rows), max(r['head_wh'][0] for r in rows))))
