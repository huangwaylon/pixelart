import sys, json
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/prop/tools')
from overlay import *
pairs = [('Dawn DPPt', 'S'), ('Hilda BW', 'SE'), ('Lyra HGSS', 'E'), ('Rosa B2W2', 'NE'), ('Dawn DPPt', 'N'), ('Hilda BW', 'designE front'), ('Rosa B2W2', 'designE isoSE')]
rows_out = []; lines = ['deviation = ours - template mean (fraction of H; x48 = px at 48px figure); * = outside ref range']
hdr = 'section      ' + ' '.join(f'{v[:9]:>10}' for _, v in pairs); lines.append(hdr)
D = {}
for v in dict.fromkeys(p[1] for p in pairs):
    H, r, w = fr(OURS[v][1], OURS[v][2]); D[v] = (r, w)
def cell(val, t):
    if val is None: return '        - '
    dv = val - t['mean']; flag = '*' if (val < t['min'] - 0.0105 or val > t['max'] + 0.0105) else ' '
    return f'{dv:+.3f}{flag}{dv*48:+3.0f}'[:10].rjust(10)
for k in ROWS[1:-1]: lines.append(f'row {k:9}' + ' '.join(cell(D[v][0][k], T['rows'][k]) for _, v in pairs))
for k in WIDS:
    lines.append(f'w   {k:9}' + ' '.join(cell(D[v][1][k], T['widths'][k]) for _, v in pairs))
lines.append('heads tall   ' + ' '.join(f'{1/D[v][0]["chin"]:10.2f}' for _, v in pairs) + f'   ref {T["derived"]["heads_tall"]["mean"]:.2f} [{T["derived"]["heads_tall"]["min"]:.2f}-{T["derived"]["heads_tall"]["max"]:.2f}]')
lines.append('E view widths are side-on (depth), not comparable to front refs. Masters: silhouette widths (sleeves merge with body). design: silhouette incl. hanging sleeves (body-only obi 0.16-0.17H, skirt 0.21-0.27H)')
open(R + 'prop/compare.txt', 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
p1 = panel([(a,) + REFS[a] for a, _ in pairs[:4]] and [x for a, b in pairs[:4] for x in [(a,) + REFS[a], (b,) + OURS[b]]], 200)
p2 = panel([x for a, b in pairs[4:] for x in [(a,) + REFS[a], (b,) + OURS[b]]], 200)
tb = Image.new('RGB', (1000, 14 * len(lines) + 8), (30, 30, 34)); d = ImageDraw.Draw(tb)
for i, l in enumerate(lines): d.text((4, 4 + 14 * i), l, fill=(255, 120, 120) if '*' in l else (230, 230, 230), font=Fn)
stack([p1, p2, tb], R + 'prop/compare.png')
