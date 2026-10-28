import json, sys, numpy as np
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/prop/tools')
from landmarks import *
T = {'_doc': 'Section template from official Pokemon female battle sprites (front 3/4, standing). Rows: fraction of figure height H from crown (top of skull/hair mass, hats/buns/bows excluded) to sole (0..1). Widths: fraction of H. Measured by eye on char-map dumps, +-1 px (~0.015 H). Source: prop/tools/landmarks.py',
     'refs': {}, 'rows': {}, 'widths': {}, 'derived': {}}
F = {}
for n, (p, r, w) in REFS.items():
    H, fr_, fw = fr(r, w); F[n] = (fr_, fw); T['refs'][n] = {'file': p, 'H_px': H, 'rows': fr_, 'widths': fw}
for kind, keys, idx in [('rows', ROWS, 0), ('widths', WIDS, 1)]:
    for k in keys:
        v = np.array([F[n][idx][k] for n in F]); T[kind][k] = {'mean': float(round(v.mean(), 3)), 'min': float(round(v.min(), 3)), 'max': float(round(v.max(), 3))}
# derived
d = {}
for n in F:
    r, w = F[n]
    d.setdefault('heads_tall', []).append(1 / r['chin']); d.setdefault('legs_crotch_to_sole', []).append(1 - r['crotch'])
    d.setdefault('neck_gap_chin_to_shoulder', []).append(r['shoulder'] - r['chin'])
    d.setdefault('shoulder_over_headw', []).append(w['shoulder'] / w['head']); d.setdefault('waist_over_headw', []).append(w['waist'] / w['head'])
    d.setdefault('hip_over_headw', []).append(w['hip'] / w['head']); d.setdefault('eye_down_head', []).append(r['eye'] / r['chin'])
    d.setdefault('head_h_frac_of_H', []).append(r['chin']); d.setdefault('head_w_frac_of_H', []).append(w['head'])
    d.setdefault('head_w_over_head_h', []).append(w['head'] / r['chin']); d.setdefault('head_w_over_shoulder', []).append(w['head'] / w['shoulder'])
    d.setdefault('head_h_over_legs', []).append(r['chin'] / (1 - r['crotch'])); d.setdefault('head_w_over_hip', []).append(w['head'] / w['hip'])
for k, v in d.items(): v = np.array(v); T['derived'][k] = {'mean': float(round(v.mean(), 3)), 'min': float(round(v.min(), 3)), 'max': float(round(v.max(), 3))}
T['px48'] = {'_doc': 'template mean (and range) in px for a 48 px figure (crown row 14, sole line 62 in a 64 cell)',
             'rows': {k: [float(round(14 + 48 * T['rows'][k]['mean'], 1)), float(round(14 + 48 * T["rows"][k]["min"], 1)), float(round(14 + 48 * T["rows"][k]["max"], 1))] for k in ROWS},
             'widths': {k: [float(round(48 * T['widths'][k]['mean'], 1)), float(round(48 * T["widths"][k]["min"], 1)), float(round(48 * T["widths"][k]["max"], 1))] for k in WIDS}}
hh, hw = T['derived']['head_h_frac_of_H'], T['derived']['head_w_frac_of_H']
T['head_latitude'] = {'_doc': 'Head size range of the real refs (crown excl. hats/buns/bows to chin; width = hair mass). The new anime head (HAIR/FACE strands) may use any size inside this range; large eyes -> use the upper end. Body sections stay fixed. At the max, the chin line moves down and the neck/shoulder must follow (shoulder line max 0.33 H).',
  'head_h_frac': hh, 'head_w_frac': hw, 'px48_head_h': [round(48 * hh['min'], 1), round(48 * hh['mean'], 1), round(48 * hh['max'], 1)],
  'px48_head_w': [round(48 * hw['min'], 1), round(48 * hw['mean'], 1), round(48 * hw['max'], 1)],
  'blockout_head_px': {'h': 14, 'w': 15}, 'latitude_from_blockout_px': {'h': '+%.1f / -%.1f' % (48 * hh['max'] + 0.5 - 14, 14 - 48 * hh['min'] + 0.5), 'w': '+%.1f / -%.1f' % (48 * hw['max'] + 0.5 - 15, 15 - 48 * hw['min'] + 0.5)},
  'upper_end_recommendation_px48': {'head_h': 15, 'head_w': 16, 'heads_tall': round(48 / 15, 2), 'chin_line_row': 29, 'shoulder_line_row': 30, 'note': 'heads_tall then 3.2 (Rosa-like, the biggest-headed ref). Eye line (centre) range 0.18-0.20 H = rows 22.5-23.7 for refs with small eyes; big anime eyes may extend 1-2 rows lower but keep eye centre <= 0.66 of head height down.'}}
T['tolerance'] = 'blockout check: value within [min, max] widened by 0.5 px of a 48 px figure (pixel quantisation)'
json.dump(T, open('/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/prop/template.json', 'w'), indent=1)
for kind in ['rows', 'widths']:
    print(kind, ' '.join(f"{k}={T[kind][k]['mean']:.3f}[{T[kind][k]['min']:.2f}-{T[kind][k]['max']:.2f}]" for k in T[kind]))
print('derived', ' '.join(f"{k}={v['mean']:.2f}[{v['min']:.2f}-{v['max']:.2f}]" for k, v in T['derived'].items()))
print('px48', T['px48'])
