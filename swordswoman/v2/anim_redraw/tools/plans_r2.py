"""Round-2 plans (crit r1 fixes). writes work48/<act>/plan_<ver>.json"""
import json
A = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/anim_redraw/work48'
def G(act): return json.load(open(f'{A}/{act}/guide/frames.json'))['frames']
def save(act, ver, fr, **kw):
    d = dict(action=act, ver=ver, name=f'{act}_SE_{ver}', mine=1, frames=fr); d.update(kw)
    json.dump(d, open(f'{A}/{act}/plan_{ver}.json', 'w'), indent=1)
J = lambda x, y, k=16, s=8: (x + s, y + k)

# ---- run v5: n k0, keyed trailing blade (behind body on the crossing frames), contact dust, air speed lines
g = G('run'); fr = []
for i in range(8):
    f = dict(src=f'cand/nf{i:02d}_k0.png', ms=g[i]['ms'], blade={'ang': g[i]['blade'], 'keyed': 1, 'behind': int(i in (1, 5))}, fx=[])
    if i in (0, 4): f['fx'] = [{"t": "dust", "puffs": [[18, 58, 1, 1]]}]
    if i in (1, 5): f['fx'] = [{"t": "dust", "puffs": [[14, 57, 2, 2]]}]
    if i in (3, 7): f['fx'] = [{"t": "speed", "lines": [[16, 30, 6], [13, 40, 8], [16, 50, 5]]}]
    if i in (2, 6): f['fx'] = [{"t": "speed", "lines": [[14, 36, 5], [15, 46, 4]]}]
    fr.append(f)
save('run', 'v5', fr)

# ---- walk v2: w k1, bob (contacts down, passing up), constant low blade
g = G('walk'); bob = [1, 0, -1, 0, 1, 0, -1, 0]
save('walk', 'v2', [dict(src=f'cand/wf{i:02d}_k1.png', ms=100, dy=bob[i], head='squash' if bob[i] > 0 else 'neutral',
                         bow=[0, -1] if bob[i] > 0 else ([0, 1] if bob[i] < 0 else [0, 0]),
                         blade={'ang': 150 + bob[i] * 3, 'keyed': 1}) for i in range(8)])

# ---- jump v3 (FIN_PAD=16,8)
g = G('jump')
fr = [dict(src='cand/sf00_k0.png', ms=120, vsq=2, head='squash', blade={'ang': 170, 'keyed': 1},
           fx=[{"t": "dust", "puffs": [list(J(22, 58)) + [1, 1], list(J(40, 58)) + [1, 1]]}]),
      dict(src='cand/sf01_k1.png', ms=60, vsq=-2, head='stretch', bow=[0, 2], dy=24 - 26, blade={'ang': 235, 'keyed': 1, 'behind': 1},
           fx=[{"t": "dust", "puffs": [list(J(19, 58)) + [2, 1], list(J(43, 58)) + [2, 1]]},
               {"t": "lines", "l": [[*J(28, 52), *J(28, 60), "w"], [*J(32, 54), *J(32, 63), "n"], [*J(36, 52), *J(36, 60), "w"]]}]),
      dict(src='cand/sf02_k0.png', ms=80, dy=14 - 23, bow=[0, 1], blade={'ang': 200, 'keyed': 1, 'behind': 1},
           fx=[{"t": "dust", "puffs": [list(J(15, 58)) + [3, 2], list(J(47, 58)) + [3, 2]]}]),
      dict(src='cand/sf02_k0.png', ms=140, meta=2, dy=11 - 23, bow=[0, 0], blade={'ang': 195, 'keyed': 1, 'behind': 1}),
      dict(src='cand/sf04_k0.png', ms=90, dy=13 - 25, bow=[0, -1], blade={'ang': 200, 'keyed': 1, 'behind': 1}),
      dict(src='cand/sf05_k1.png', ms=60, dy=24 - 33, bow=[0, -1], blade={'ang': 215, 'keyed': 1, 'behind': 1},
           fx=[{"t": "lines", "l": [[*J(22, 4), *J(22, 12), "n"], [*J(42, 2), *J(42, 10), "n"], [*J(32, 0), *J(32, 4), "w"]]}]),
      dict(src='cand/sf06_k1.png', ms=100, vsq=2, head='squash', bow=[0, -1], blade={'ang': 175, 'keyed': 1},
           fx=[{"t": "dust", "puffs": [list(J(18, 58)) + [2, 1], list(J(44, 58)) + [2, 1]]}]),
      dict(src='cand/sf07_k1.png', ms=90, blade={'ang': 165, 'keyed': 1}, bow=[0, 1],
           fx=[{"t": "dust", "puffs": [list(J(14, 57)) + [3, 2], list(J(48, 57)) + [3, 2]]}]),
      dict(src='cand/sf08_k0.png', ms=150, blade={'ang': 160, 'keyed': 1})]
save('jump', 'v3', fr)

# ---- dash v2
g = G('dash')
fr = [dict(src='cand/sf00_k0.png', ms=120, vsq=2, shear=-2, head='back', blade={'ang': 175, 'keyed': 1}),
      dict(src='cand/sf01_k1.png', ms=45, shear=2, head='lean', bow=[-2, 0],
           fx=[{"t": "afterimage", "ghosts": [[-7, 0, "E", 0], [-14, 0, "R", 0]]}, {"t": "speed", "lines": [[13, 34, 9], [11, 43, 13], [14, 52, 8]]}]),
      dict(src='cand/sf02_k1.png', ms=45, dx=3, shear=2, head='lean', bow=[-2, 0],
           fx=[{"t": "afterimage", "ghosts": [[-9, 0, "R", 0]]}, {"t": "speed", "lines": [[12, 32, 11], [10, 41, 14], [13, 50, 10]]},
               {"t": "dust", "puffs": [[17, 58, 1, 1]]}]),
      dict(src='cand/sf03_k0.png', ms=110, shear=-3, head='back', bow=[2, 0], blade={'ang': 160, 'keyed': 1},
           fx=[{"t": "dust", "puffs": [[45, 57, 3, 1], [38, 58, 2, 1]]}, {"t": "lines", "l": [[16, 59, 27, 59, "u"], [18, 57, 24, 57, "U"]]}]),
      dict(src='cand/sf04_k0.png', ms=90, shear=-1, bow=[1, 0], blade={'ang': 140, 'keyed': 1},
           fx=[{"t": "dust", "puffs": [[48, 56, 3, 2], [40, 57, 2, 2]]}]),
      dict(src='cand/sf05_k0.png', ms=150)]
save('dash', 'v2', fr)

# ---- slash v3
def S(src, meta, ms, **kw): d = dict(src=f'cand/sf{src:02d}_k1.png', meta=meta, ms=ms); d.update(kw); return d
fr = [S(0, 0, 120),
      S(1, 1, 170, head='back', bow=[1, -1], blade={'ang': 235, 'hilt': [24, 25], 'behind': 1, 'len': 19}),
      S(3, 3, 45, head='lean', bow=[-2, 0], blade={'ang': 15, 'keyed': 1},
        fx=[{"t": "smear", "c": [31, 40], "r": 25, "a0": -175, "a1": 25, "th": 9, "flat": 0.85, "over": 1, "dith": 0.12}]),
      S(3, 3, 110, head='lean', bow=[-1, 1], vsq=1, shear=1, blade={'ang': 35, 'keyed': 1, 'flash': 1}, shake=[2, 0],
        fx=[{"t": "smear", "c": [31, 40], "r": 25, "a0": -10, "a1": 40, "th": 4, "flat": 0.85, "over": 1, "dith": 0}, {"t": "spark", "x": 51, "y": 54, "r": 6}]),
      S(4, 4, 90, bow=[1, 1], fx=[{"t": "smear", "c": [31, 40], "r": 25, "a0": 25, "a1": 50, "th": 2, "flat": 0.85, "dith": 0}]),
      S(7, 7, 120, bow=[0, -1]),
      S(0, 0, 160)]
save('slash', 'v3', fr)
