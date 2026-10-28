"""Write work48/<act>/plan_<ver>.json for walk/jump/dash/slash from tag-s candidates + FX keys."""
import json, sys
A = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/anim_redraw'
ver = sys.argv[1]
P = {}
P['walk'] = dict(pick=[1] * 8, fx={})
P['jump'] = dict(pick=[0, 1, 0, 0, 0, 1, 0, 1, 0], fx={
    0: [{"t": "dust", "puffs": [[22, 58, 1, 1], [40, 58, 1, 1]]}],
    1: [{"t": "dust", "puffs": [[20, 58, 2, 1], [42, 58, 2, 1]]}, {"t": "lines", "l": [[27, 60, 27, 63, "w"], [31, 61, 31, 63, "n"], [35, 60, 35, 63, "w"]]}],
    2: [{"t": "dust", "puffs": [[18, 58, 2, 2], [44, 58, 2, 2]]}],
    6: [{"t": "dust", "puffs": [[19, 58, 2, 1], [43, 58, 2, 1]]}],
    7: [{"t": "dust", "puffs": [[16, 57, 2, 2], [46, 57, 2, 2]]}]})
P['dash'] = dict(pick=[0, 1, 1, 0, 0, 0], fx={
    1: [{"t": "afterimage", "ghosts": [[-6, 0, "E", 0], [-12, 0, "R", 1]]}, {"t": "speed", "lines": [[14, 36, 9], [12, 44, 12], [15, 52, 8]]}],
    2: [{"t": "afterimage", "ghosts": [[-5, 0, "R", 1]]}, {"t": "speed", "lines": [[13, 34, 7], [11, 42, 11], [14, 50, 9]]},
        {"t": "dust", "puffs": [[16, 58, 1, 1]]}],
    3: [{"t": "dust", "puffs": [[44, 58, 2, 1], [38, 58, 1, 1]]}, {"t": "lines", "l": [[18, 59, 26, 59, "u"], [16, 57, 22, 57, "U"]]}],
    4: [{"t": "dust", "puffs": [[47, 57, 2, 2]]}]})
P['slash'] = dict(pick=[1, 1, 1, 1, 1, 1, 1, 1], fx={
    2: [{"t": "smear", "c": [31, 38], "r": 20, "a0": -150, "a1": 30, "th": 5, "flat": 0.85}],
    3: [{"t": "smear", "c": [31, 38], "r": 20, "a0": -40, "a1": 35, "th": 3, "flat": 0.85}, {"t": "spark", "x": 49, "y": 49, "r": 3}],
    4: [{"t": "smear", "c": [31, 38], "r": 20, "a0": 0, "a1": 40, "th": 2, "flat": 0.85}]},
    extra={3: {"shake": [1, 0]}, 4: {"shake": [-1, 0]}})
for act, d in P.items():
    gf = json.load(open(f'{A}/work48/{act}/guide/frames.json'))['frames']
    fr = []
    for i, k in enumerate(d['pick']):
        f = dict(src=f'cand/sf{i:02d}_k{k}.png', fx=d['fx'].get(i, []))
        f.update(d.get('extra', {}).get(i, {}))
        fr.append(f)
    if act == 'jump':                      # FIN_PAD=16,8 cell: shift FX coords
        def sh(e):
            e = json.loads(json.dumps(e))
            if 'puffs' in e: e['puffs'] = [[x + 8, y + 16, r, st] for x, y, r, st in e['puffs']]
            if 'l' in e: e['l'] = [[a + 8, b + 16, c + 8, d + 16, col] for a, b, c, d, col in e['l']]
            return e
        for f in fr: f['fx'] = [sh(e) for e in f['fx']]
    plan = dict(action=act, ver=ver, name=f'{act}_SE_{ver}', mine=1, decrawl=0, frames=fr)
    json.dump(plan, open(f'{A}/work48/{act}/plan_{ver}.json', 'w'), indent=1)
