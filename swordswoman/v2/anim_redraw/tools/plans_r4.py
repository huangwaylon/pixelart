"""Lead round 2: Opus legs (walk/run), locked head stamps, katana sprites with smooth angle sequences."""
import json
A = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/anim_redraw/work48'
def load(act, v): return json.load(open(f'{A}/{act}/plan_{v}.json'))
def save(d, act, ver):
    d['ver'] = ver; d['name'] = f'{act}_SE_{ver}'; d['kat'] = 1
    json.dump(d, open(f'{A}/{act}/plan_{ver}.json', 'w'), indent=1)
def key(f, ang, **kw):
    b = f.get('blade') if isinstance(f.get('blade'), dict) else {}
    b = {k: v for k, v in b.items() if k in ('hilt', 'behind', 'flash')}; b.update(ang=ang, keyed=1); b.update(kw); f['blade'] = b

d = load('walk', 'k1')                     # walk: Opus legs, neutral head, blade d9 throughout
for i, f in enumerate(d['frames']):
    f['legs'] = f'legs/f{i:02d}.txt'; f['head'] = 'neutral'; key(f, 153, behind=1)
d['head_lock'] = 1
VS = [2, 3, 1, 0, 1, 0, 0, 0]; BOB = [0, 1, 0, -1, 0, 1, 0, -1]
for i, f in enumerate(d['frames']):
    f['vsq'] = VS[i]; f['head'] = 'neutral'; key(f, 153, behind=1, hilt=[29, 49 + BOB[i]])
save(d, 'walk', 'v5')

d = load('run', 'k1')                      # run: Opus legs, lean head, blade d9 throughout
for i, f in enumerate(d['frames']):
    f['legs'] = f'legs/f{i:02d}.txt'; f['head'] = 'lean'; key(f, 180 if i % 4 in (2, 3) else 153, behind=1)
d['head_lock'] = 1
SP = [[[18 - 3 * (i % 4), 31, 6 - (i % 2)], [15 - 3 * ((i + 2) % 4), 41, 9], [18 - 3 * ((i + 1) % 4), 51, 5]] for i in range(8)]
MS = [70, 80, 50, 60, 70, 80, 50, 60]                    # hold contact/down, snap through push-off/air
HY = [45, 48, 50, 47, 45, 48, 50, 47]; HX = [28, 29, 30, 29, 28, 29, 30, 29]
for i, f in enumerate(d['frames']):
    f['fx'] = [{"t": "speed", "lines": SP[i]}]; f['ms'] = MS[i]; key(f, 153, behind=1, hilt=[HX[i], HY[i]])
save(d, 'run', 'v8')

d = load('jump', 'v3')                     # d8 d6 d7 d7 d8 d8 d8 d9 d9 (f1,f4,f5 behind the body)
H = ['squash', 'up', 'up', 'up', 'neutral', 'neutral', 'squash', 'neutral', 'neutral']
for i, (f, a) in enumerate(zip(d['frames'], [180, 225, 207, 207, 180, 180, 180, 153, 153])):
    f['head'] = H[i]; key(f, a, behind=int(i in (1, 4, 5)))
save(d, 'jump', 'v4')

d = load('dash', 'v3')                     # d8 d8 d8 d9 d9 d9
H = ['neutral', 'lean', 'lean', 'neutral', 'neutral', 'neutral']
for i, (f, a) in enumerate(zip(d['frames'], [180, 180, 180, 153, 153, 153])):
    f['head'] = H[i]; key(f, a)
save(d, 'dash', 'v4')

d = load('slash', 'v4')                    # ready d1, windup d7, smear/impact d15, follow d14, recover d0, ready d1
H = ['neutral', 'neutral', 'lean', 'lean', 'neutral', 'neutral', 'neutral']
for i, (f, a) in enumerate(zip(d['frames'], [333, 207, 27, 27, 45, 0, 333])):
    f['head'] = H[i]; key(f, a)
save(d, 'slash', 'v5')
