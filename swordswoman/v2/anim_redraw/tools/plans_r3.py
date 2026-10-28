"""Round-3 plans (crit r2 fixes): walk v3, run v6, dash v3, slash v4 (jump stays v3)."""
import json
A = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/anim_redraw/work48'
def G(act): return json.load(open(f'{A}/{act}/guide/frames.json'))['frames']
def save(act, ver, fr, **kw):
    d = dict(action=act, ver=ver, name=f'{act}_SE_{ver}', mine=1, frames=fr); d.update(kw)
    json.dump(d, open(f'{A}/{act}/plan_{ver}.json', 'w'), indent=1)

# walk v3: bob via waist squash (feet stay planted), blade sways 1 frame behind the bob
vs = [1, 2, 0, -1, 1, 2, 0, -1]; ba = [149, 150, 153, 151, 149, 150, 153, 151]
save('walk', 'v3', [dict(src=f'cand/wf{i:02d}_k1.png', ms=[110, 100, 90, 100][i % 4], vsq=vs[i],
                         head='squash' if vs[i] == 2 else ('stretch' if vs[i] < 0 else 'neutral'),
                         bow=[0, -1] if vs[i] < 0 else ([0, 1] if vs[i] == 2 else [0, 0]),
                         blade={'ang': ba[i], 'keyed': 1}) for i in range(8)])

# run v6: one trailing blade angle (in front, never hidden), continuous speed lines, no floating dust
g = G('run'); fr = []
L = [[[16, 31, 6], [13, 41, 9], [16, 51, 5]], [[14, 33, 5], [12, 43, 8], [15, 52, 6]]]
for i in range(8):
    fr.append(dict(src=f'cand/nf{i:02d}_k0.png', ms=g[i]['ms'], blade={'ang': 166 + (2 if i % 4 in (1, 2) else 0), 'keyed': 1},
                   fx=[{"t": "speed", "lines": L[i % 2]}]))
save('run', 'v6', fr)

# dash v3
fr = [dict(src='cand/sf00_k0.png', ms=130, vsq=3, shear=-3, head='back', bow=[1, 1], blade={'ang': 175, 'keyed': 1}),
      dict(src='cand/sf01_k1.png', ms=45, shear=2, head='lean', bow=[-2, 0],
           fx=[{"t": "afterimage", "ghosts": [[-7, 0, "n", "outline"], [-14, 0, "m", "outline"]]}, {"t": "speed", "lines": [[13, 34, 9], [11, 43, 13], [14, 52, 8]]}]),
      dict(src='cand/sf02_k1.png', ms=45, dx=3, shear=2, head='lean', bow=[-2, 0],
           fx=[{"t": "afterimage", "ghosts": [[-9, 0, "n", "outline"]]}, {"t": "speed", "lines": [[12, 32, 11], [10, 41, 14], [13, 50, 10]]},
               {"t": "dust", "puffs": [[17, 58, 1, 1]]}]),
      dict(src='cand/sf03_k0.png', ms=120, vsq=2, shear=-4, head='back', bow=[2, 0], blade={'ang': 162, 'keyed': 1},
           fx=[{"t": "dust", "puffs": [[45, 57, 3, 1], [39, 58, 2, 1]]}, {"t": "lines", "l": [[16, 59, 28, 59, "u"], [18, 57, 25, 57, "U"]]}]),
      dict(src='cand/sf04_k0.png', ms=90, vsq=1, shear=-1, bow=[1, 0], blade={'ang': 165, 'keyed': 1},
           fx=[{"t": "dust", "puffs": [[47, 56, 3, 1]]}]),
      dict(src='cand/sf05_k0.png', ms=150, blade={'ang': 150, 'keyed': 1})]
save('dash', 'v3', fr)

# slash v4 (everything 4px left so blade/smear/spark stay in the cell)
def S(src, meta, ms, **kw):
    d = dict(src=f'cand/sf{src:02d}_k1.png', meta=meta, ms=ms, dx=-4); d.update(kw); return d
fr = [S(0, 0, 130),
      S(1, 1, 170, head='back', bow=[1, -1], blade={'ang': 215, 'hilt': [20, 25], 'len': 18}),
      S(3, 3, 45, head='lean', bow=[-2, 0], blade={'ang': 15, 'keyed': 1},
        fx=[{"t": "smear", "c": [27, 42], "r": 24, "a0": -170, "a1": 25, "th": 9, "flat": 0.8, "over": 1, "dith": 0.1}]),
      S(3, 3, 80, head='lean', bow=[-1, 1], vsq=1, shear=1, blade={'ang': 35, 'keyed': 1, 'flash': 1}, shake=[2, 0],
        fx=[{"t": "smear", "c": [27, 42], "r": 24, "a0": -5, "a1": 40, "th": 5, "flat": 0.8, "over": 1, "dith": 0}, {"t": "spark", "x": 47, "y": 55, "r": 7}]),
      S(4, 4, 90, bow=[1, 1]),
      S(7, 7, 100, bow=[0, -1]),
      S(0, 0, 150)]
save('slash', 'v4', fr)
