"""decompose.py: split each view master head (+ m96 stamps) into layers -> v2/heads96/layers/<V>/labels.txt, base_neutral.txt, ...
Labels: b base (skull+bangs+face skin), f face mask (subset of b; replaced by the expression face layer), B back hair,
l/r side locks (screen left/right), w knot+bow, t ribbon tails, '.' = not head (body/empty).
Canvas = head box BOX[V] in master coords (x0,y0,x1,y1 exclusive)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cm import *
HAIR = set('KhHgL'); RED = set('eER'); SKIN = set('sSmk')
BOX = {'S': (48, 27, 80, 71), 'SE': (43, 26, 82, 68), 'E': (44, 24, 84, 66), 'NE': (42, 25, 82, 66), 'N': (47, 27, 80, 66)}
NECK = {'S': 61, 'SE': 61, 'E': 63, 'NE': 64, 'N': 65}   # rows >= NECK: only hair-layer (l/r/B/t) pixels belong to the head
# rules: (label, x0, y0, x1, y1 inclusive, chars) applied in order (later wins); default for head pixels = 'b'
R = {
 'S': [('w', 48, 27, 80, 37, RED), ('w', 60, 28, 68, 31, HAIR),
       ('l', 50, 54, 58, 70, HAIR), ('r', 70, 54, 78, 70, HAIR)],
 'SE': [('w', 44, 27, 59, 43, RED | HAIR), ('t', 44, 44, 51, 52, RED | HAIR),
        ('B', 50, 44, 57, 61, HAIR), ('l', 54, 55, 62, 66, HAIR), ('r', 73, 54, 79, 66, HAIR)],
 'E': [('w', 49, 25, 64, 39, RED), ('w', 49, 29, 55, 39, HAIR), ('t', 44, 42, 53, 63, RED | HAIR),
       ('B', 52, 42, 63, 63, HAIR), ('l', 64, 50, 70, 64, HAIR)],
 'NE': [('w', 45, 26, 66, 44, RED), ('w', 51, 28, 58, 37, HAIR), ('t', 43, 48, 49, 64, RED | HAIR), ('t', 56, 40, 61, 64, RED),
        ('B', 49, 43, 68, 64, HAIR), ('r', 69, 52, 77, 64, HAIR)],
 'N': [('w', 52, 28, 74, 45, RED), ('w', 58, 28, 68, 35, HAIR), ('t', 56, 45, 62, 55, RED), ('t', 65, 45, 70, 55, RED),
       ('B', 48, 46, 80, 61, HAIR), ('l', 48, 58, 58, 65, HAIR), ('r', 69, 58, 76, 65, HAIR)],
}
def face_mask(v, box):
    """union over expressions of pixels differing from neutral + anchor feature boxes, inside the neutral skin bbox (+1)"""
    hd = f'{ROOT}/m96/heads'; nt, nm = load(f'{hd}/{v}_neutral.txt'); ox, oy = map(int, nm['origin'])
    M = set(); DIFF = set()
    for fn in os.listdir(hd):
        if fn.startswith(v + '_') and fn.endswith('.txt'):
            st, _ = load(f'{hd}/{fn}')
            DIFF |= {(ox + x, oy + y) for y, r in enumerate(st) for x, c in enumerate(r) if c != nt[y][x]}
    a = json.load(open(f'{hd}/anchor.json'))['views'][v]
    for e in a.get('eyes', []):
        w = 6 if e['kind'] != 'far' else 4
        M |= {(x, y) for x in range(e['x0'] - 1, e['x0'] + w + 1) for y in range(e['y0'] - 3, e['y0'] + 6)}
    if a.get('mouth'): mx, my = a['mouth']; M |= {(x, y) for x in range(mx, mx + 4) for y in range(my, my + 3)}
    for x, y, c in a.get('nose', []): M.add((x, y))
    for bx, by, k in a.get('blush', []): M |= {(x, y) for x in range(bx, bx + 4) for y in range(by, by + 2)}
    for x, y in a.get('ne_lash', []): M.add((x, y))
    sp = [(ox + x, oy + y) for y, r in enumerate(nt) for x, c in enumerate(r) if c in SKIN]
    if not sp: return set(), DIFF
    x0, y0, x1, y1 = min(p[0] for p in sp) - 1, min(p[1] for p in sp) - 1, max(p[0] for p in sp) + 1, max(p[1] for p in sp) + 1
    return {(x, y) for x, y in M if x0 <= x <= x1 and y0 <= y <= y1}, DIFF
def labels(v):
    G, _ = load(f'{ROOT}/m96/masters/EC0_{v}_96.txt'); X0, Y0, X1, Y1 = BOX[v]
    lab = {}
    for y in range(Y0, Y1):
        for x in range(X0, X1):
            c = G[y][x]
            if c == '.': continue
            l = None
            for L_, a, b, cc, d, cs in R[v]:
                if a <= x <= cc and b <= y <= d and c in cs: l = L_
            if l is None and y < NECK[v] and c in HAIR | SKIN | RED | {'W'}: l = 'b'
            if l: lab[(x, y)] = l
    # K outline pixels: re-assign to the majority non-K neighbour layer (skin side -> base)
    for it in range(2):
        for (x, y), l in list(lab.items()):
            if G[y][x] != 'K': continue
            nb = [lab.get((x + dx, y + dy)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if G[y + dy][x + dx] != 'K']
            nb = [n for n in nb if n]
            if nb:
                lab[(x, y)] = max(set(nb), key=lambda n: (nb.count(n), n != 'b'))
            elif y >= NECK[v] and l == 'b': del lab[(x, y)]
    # isolated K below NECK with no head neighbours were dropped; K in neck rows adjacent only to body stay body
    FM, DIFF = face_mask(v, BOX[v])
    for (x, y) in FM:
        if lab.get((x, y)) == 'b' or (x, y) not in lab: lab[(x, y)] = 'f'
    for (x, y) in DIFF: lab[(x, y)] = 'f'   # every expression delta px belongs to the face layer
    rows = [''.join(lab.get((x, y), '.') for x in range(X0, X1)) for y in range(Y0, Y1)]
    return G, rows
if __name__ == '__main__':
    from PIL import Image
    views = sys.argv[1:] or ['S', 'SE', 'E', 'NE', 'N']
    COL = {'b': (150, 150, 150), 'f': (255, 230, 0), 'B': (60, 90, 255), 'l': (0, 200, 0), 'r': (0, 230, 230), 'w': (255, 40, 40), 't': (255, 0, 255)}
    S = int(os.environ.get("SC", 5)); tiles = []
    for v in views:
        G, rows = labels(v); X0, Y0, X1, Y1 = BOX[v]
        os.makedirs(f'{ROOT}/heads96/layers/{v}', exist_ok=True)
        save(f'{ROOT}/heads96/layers/{v}/labels.txt', rows, {'origin': [X0, Y0], 'view': [v]})
        im = to_img(crop(G, X0, Y0, X1, Y1), S, '#6e6e6e').convert('RGB'); ov = im.copy(); px = ov.load()
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                if c in COL:
                    for i in range(S):
                        for j in range(S):
                            o = px[x * S + i, y * S + j]; px[x * S + i, y * S + j] = tuple((a + b) // 2 for a, b in zip(o, COL[c]))
        t = Image.new('RGB', (im.width * 2 + 4, im.height), (0, 0, 0)); t.paste(im, (0, 0)); t.paste(ov, (im.width + 4, 0)); tiles.append(t)
    W = sum(t.width for t in tiles) + 6 * len(tiles); H = max(t.height for t in tiles)
    out = Image.new('RGB', (W, H), (30, 30, 30)); x = 0
    for t in tiles: out.paste(t, (x, 0)); x += t.width + 6
    out.save(sys.argv[0].replace('decompose.py', '') + '../work_labels.png' if False else '/tmp/h96_labels.png'); print(out.size)
