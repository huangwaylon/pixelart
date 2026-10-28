"""writes walk_SE_k{0..3}.txt: turn_SE torso cel (byte-identical, rides the head bounce) + per-key legs, arm swing,
katana sway and lagging tail / ribbons / bow (secondary motion trails against velocity, 1 key behind the body)."""
D = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools/hybrid/s1/bodies/'
TAIL = "____KRR/___KRRR/___KRRR/__KRRRr/__KRRRr/_KRRRrr/_KRRRrr/_KRRrrv/KRRrrvK/KRrvvK_/KvvKK__/KK_____"
TAIL_FLY = "____KKR/__KKRRR/_KRRRRr/KRRRRrr/KRRRrrr/KRRrrrv/_KRrrvK/_KRrvK_/KRvvK__/KvKK___/KK_____"
ARM = "_____KssK__/_____KsmmK_/____KCRRrK_/____KCRRRrK/___KCRRRRrK/__KCRRRRRrK/_KRRRRRRRrK/_KRRRRRRrrK/_KvvvvvvvvK/__KKKKKKKK_"
K = {
 # bx,by body shift | legs | near-arm swing | tail | bow lag | katana / far-arm swing | ribbon lag | lean
 0: dict(bx=1, by=1, lean=1, legs=[('s', [(62, 97), (60, 100), (58, 102)]), ('d', [(57, 103), (58, 104)]), ('s', [(70, 97), (72, 100), (73, 102)]), ('d', [(73, 103), (75, 104)])],
         arm=(3, 0), tail=(-1, -1, TAIL_FLY), bow=(0, -1), kat=(-2, -1), rib=(-2, -1), note='contact: long stride, front (left) heel strikes, back toe pushes; right arm swings forward, sword arm back; torso leans 1 px into the step'),
 1: dict(bx=1, by=3, lean=1, legs=[('s', [(62, 99), (60, 101), (59, 102)]), ('d', [(58, 103), (59, 104)]), ('s', [(70, 99), (73, 101), (72, 102)]), ('d', [(72, 103), (73, 104)])],
         arm=(2, 1), tail=(-2, -2, TAIL_FLY), bow=(0, -1), kat=(-1, 0), rib=(-2, -2), note='down: weight on the bent front knee, body 3 px lower, tail/bow/ribbons lag UP'),
 2: dict(bx=0, by=0, lean=0, legs=[('s', [(63, 96), (65, 99), (65, 100)]), ('d', [(65, 101), (66, 101)]), ('s', [(68, 96), (68, 102)]), ('d', [(68, 103), (69, 104)])],
         arm=(0, 0), tail=(-1, 1, TAIL), bow=(0, 1), kat=(0, 0), rib=(-1, 1), note='passing: support leg straight, swing leg lifted and bent; lagging parts drop'),
 3: dict(bx=0, by=-1, lean=0, legs=[('s', [(68, 95), (68, 101)]), ('d', [(68, 102), (68, 104)]), ('s', [(63, 95), (66, 98), (67, 100)]), ('d', [(67, 101), (69, 102)])],
         arm=(-3, -1), tail=(0, 1, TAIL), bow=(0, 1), kat=(2, 0), rib=(0, 1), note='up: heel off, body 1 px high, right leg reaching forward; right arm swings back, sword arm forward'),
}
for k, c in K.items():
    bx, by = c['bx'], c['by']
    L = [f"# walk_SE_k{k}: {c['note']}", 'fx: none', f'from: turn_SE {bx} {by}', f'stamp: {56 + bx} {46 + by}',
         f"bow: {c['bow'][0]} {c['bow'][1]}",
         f'clear: 50,{96 + by},84,110']
    ax, ay = c['arm']
    L.append(f'move: {56 + bx},{82 + by},{61 + bx},{93 + by} {ax},{ay}')
    if c['lean']: L.append(f'shear: {76 + by} {87 + by} {c["lean"]}')
    for tone, pts in c['legs']:
        L.append(f'limb: {tone} 2 ' + ' '.join(f'{x},{y}' for x, y in pts))
    kx, ky = c['kat']
    L.append(f'kat: katana_idle_2to1 {71 + bx + kx} {86 + by + ky} under')
    L += [f'top: {74 + bx + kx} {90 + by}', '_KKK_', 'KsssK', 'KmssK', '_KKK_']
    tx, ty, shape = c['tail']
    L.append(f'opb: stamp {56 + bx + tx},{90 + by + ty} {shape}')
    rx, ry = c['rib']
    L.append(f'opb: curve {60 + bx},{80 + by} {54 + bx + rx},{84 + by + ry} {56 + bx + rx},{89 + by + ry} P')
    L.append(f'opb: curve {56 + bx + rx},{89 + by + ry} {58 + bx + rx * 2},{93 + by + ry} {54 + bx + rx * 2},{96 + by + ry} p')
    L.append(f'opb: stamp {72 + bx + kx // 2},{81 + by} {ARM}')
    open(D + f'walk_SE_k{k}.txt', 'w').write('\n'.join(L) + '\n')
print('ok')
