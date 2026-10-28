"""accept.py WORKDIR OUTDIR JOBS.txt [ARTDIR]: greedy per-job acceptance of artist crops. A job is kept if, vs the running
result, ssim_b >= -0.0015, dE <= +0.06, sil >= -0.002 and lint (O1+S4+O3) does not rise. Face boxes are protected."""
import sys, os, json, shutil, subprocess
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/tools'); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pzlib as Z, m96 as M, metrics as MT
W, O, J = sys.argv[1:4]; A = sys.argv[4] if len(sys.argv) > 4 else os.path.dirname(J)
PB = {'S': (54, 49, 80, 60), 'SE': (60, 49, 80, 60), 'E': (70, 49, 82, 60)}
os.makedirs(O, exist_ok=True)
for f in os.listdir(W):
    if f.startswith('EC0_'): shutil.copy(os.path.join(W, f), O)
keys, rgb, _ = Z.load_pal(M.PAL)
def lint(stem):
    out = subprocess.run(['python3', M.ROOT + 'v2/anim_cut/tools/lint_style.py', stem + '.txt', '--palette', M.PAL, '--pivot', '64', '124'], capture_output=True, text=True).stdout
    n = 0
    for l in out.splitlines()[1:]:
        t = l.split()
        if not t: continue
        if t[0] in ('O1', 'S4'): n += int(t[1])
        if t[0] == 'O3': n += l.count("('")
    return n
log = []
for line in open(J):
    n, v, x0, y0, x1, y1, r = line.split()[:7]; x0, y0 = int(x0), int(y0)
    crop = os.path.join(A, n, 'out.txt')
    if not os.path.exists(crop): log.append((n, 'missing')); continue
    stem = f'{O}/EC0_{v}_96'; g, meta = Z.read(stem); b0 = MT.metrics(stem); l0 = lint(stem)
    rows = [l.rstrip('\n') for l in open(crop) if l.strip()]
    g2 = g.copy(); pb = PB.get(v)
    for j, rr in enumerate(rows):
        for i, c in enumerate(rr):
            y, x = y0 + j, x0 + i
            if pb and pb[0] <= x < pb[2] and pb[1] <= y < pb[3]: continue
            if c in keys or c == '.': g2[y, x] = c
    Z.save(g2, '/tmp/m96acc', keys, rgb, meta); b1 = MT.metrics('/tmp/m96acc'); l1 = lint('/tmp/m96acc')
    d = dict(ssim_b=b1['ssim_b'] - b0['ssim_b'], dE=b1['dE'] - b0['dE'], sil=b1['sil'] - b0['sil'], lint=l1 - l0)
    ok = d['ssim_b'] >= -0.0015 and d['dE'] <= 0.06 and d['sil'] >= -0.0025 and (d['lint'] <= 0 or (d['lint'] <= 2 and d['dE'] < 0))
    if ok: Z.save(g2, stem, keys, rgb, meta)
    log.append((n, 'KEEP' if ok else 'drop', {k: round(x, 4) for k, x in d.items()}))
    print(n, 'KEEP' if ok else 'drop', {k: round(x, 4) for k, x in d.items()}, flush=True)
for e in ('.txt', '.png', '.json'):
    if os.path.exists('/tmp/m96acc' + e): os.remove('/tmp/m96acc' + e)
json.dump(log, open(f'{O}/accept_log.json', 'w'), indent=0)
