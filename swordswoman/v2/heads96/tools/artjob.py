"""artjob.py: Opus pixel-artist jobs on small char-map crops for the layered head.
  artjob.py tilt VIEW L|R ACCOUNT         clean the procedural tilt draft of base_neutral -> layers/<V>/approved/base_tilt<L|R>.txt
  artjob.py sway VIEW PART ACCOUNT        clean the 4 sway drafts (lagL lagR lift drop) of PART -> layers/<V>/approved/<P>_<state>.txt
Each output: sprite lint (palette chars of the source, O1 outline, S4 orphans, root rows / blank face kept) -> 1 retry with fix lines;
then the composite is eyechecked + gated by accept.py. Logs in v2/heads96/art/<job>/."""
import sys, os, json, re, subprocess, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cm import *
import compose_head as CH
LD = f'{ROOT}/heads96/layers'; ART = f'{ROOT}/heads96/art'
LEG = {k: v['desc'].split(';')[0] for k, v in json.load(open(f'{ROOT}/pixelize/palette.json'))['colors'].items()}
NAMES = {'B': 'back hair mass', 'l': 'screen-left side lock (long hanging strand of hair)', 'r': 'screen-right side lock (long hanging strand of hair)',
         'w': 'half-up hair knot + red bow', 't': 'red ribbon tails (thin ribbon ends hanging from the bow)'}
STATE_TXT = {'lagL': 'LAG LEFT: the head moved right, the part trails to the LEFT; the tip/free end swings 1-2 px left, the attachment stays put; a gentle curve, not a rigid shear',
             'lagR': 'LAG RIGHT: mirror of lag left: the free end swings 1-2 px RIGHT, attachment stays put, gentle curve',
             'lift': 'LIFT (jump rise / hang time): the free end floats UP 1-2 px (the strand shortens/curls up a little, ends slightly flared)',
             'drop': 'DROP (landing): the free end drops DOWN 1-2 px (strand hangs longer/heavier, ends bunched)'}
BOW_TXT = {'lagL': 'LAG LEFT: the loops trail left (outer loop ends 1 px left, knot centre stays)', 'lagR': 'LAG RIGHT: loops trail right 1 px, knot centre stays',
           'lift': 'LIFT: loop tips flutter up 1 px, knot stays', 'drop': 'DROP: loop tips droop down 1 px, knot stays'}
def grid_txt(g, ruler=True):
    W = len(g[0]); s = '    ' + ''.join(str(i % 10) for i in range(W)) + '\n' if ruler else ''
    return s + '\n'.join(('%3d ' % y if ruler else '') + r for y, r in enumerate(g))
def parse(out, H, W):
    blocks = re.findall(r'BEGIN(?: (\S+))?\s*\n(.*?)\nEND', out, re.S); res = {}
    for name, body in blocks:
        rows = [re.sub(r'^\s*\d+\s', '', l).rstrip() for l in body.split('\n') if l.strip() and not l.strip().startswith('`')]
        rows = [r[:W].ljust(W, '.') for r in rows]
        if len(rows) >= H - 1: res[name or '_'] = (rows + ['.' * W] * H)[:H]
    return res
def nbr8(g, x, y):
    H, W = len(g), len(g[0])
    return [g[y + j][x + i] for i in (-1, 0, 1) for j in (-1, 0, 1) if (i or j) and 0 <= x + i < W and 0 <= y + j < H]
def lint(g, src, kind, view, attach=None):
    """fix lines for an artist sprite. src = draft (same canvas)."""
    fx = []; H, W = len(g), len(g[0]); allowed = {c for r in src for c in r} | {'K', '.'}
    bad = [(x, y, c) for y, r in enumerate(g) for x, c in enumerate(r) if c not in allowed]
    if bad: fx.append('PAL chars %s not allowed here (use only %s): %s' % (''.join(sorted({b[2] for b in bad})), ''.join(sorted(allowed - {'.'})), bad[:8]))
    orph = [(x, y) for y, r in enumerate(g) for x, c in enumerate(r) if c != '.' and all(n == '.' for n in nbr8(g, x, y))]
    if orph: fx.append('S4 floating pixels (no neighbours) at %s: remove or connect' % orph[:8])
    lab = CH.meta(view)[0]; rest = CH.rest_union(view)
    def o1(G):
        return [(x, y) for y, r in enumerate(G) for x, c in enumerate(r) if c not in '.K' and any(
            (not (0 <= x + i < W and 0 <= y + j < H)) or (G[y + j][x + i] == '.' and (x + i, y + j) not in attach_ok)
            for i, j in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    attach_ok = attach or set()
    e0, e1 = o1(src), o1(g)
    if len(e1) > len(e0) + 2: fx.append('O1 %d edge pixels are not K outline (draft had %d): %s; every edge pixel facing empty space is K' % (len(e1), len(e0), [p for p in e1 if p not in set(e0)][:10]))
    if kind == 'tilt':
        fm = [(x, y) for y, r in enumerate(lab) for x, c in enumerate(r) if c == 'f']
        ink = [(x, y, g[y][x]) for x, y in fm if g[y][x] in 'KWLg' and src[y][x] not in 'KWLg']
        if ink: fx.append('FACE the blank face area must stay plain skin (no eyes/brows/mouth drawn; the face layer is pasted on top): %s' % ink[:8])
    n0, n1 = sum(c != '.' for r in src for c in r), sum(c != '.' for r in g for c in r)
    if abs(n1 - n0) > max(6, 0.15 * n0): fx.append('SIZE %d px vs draft %d: keep the same mass (only redraw the lean/sway cleanly)' % (n1, n0))
    return fx
def call(acc, prompt, log):
    t = time.time()
    with open(log + '.prompt.txt', 'w') as f: f.write(prompt)
    r = subprocess.run(['zsh', '-ic', 'claude-as %s --dangerously-skip-permissions --model claude-opus-5-5 -p "$(cat %s)"' % (acc, log + '.prompt.txt')],
                       capture_output=True, text=True, timeout=1500)
    open(log, 'w').write(r.stdout + '\n---stderr---\n' + r.stderr[-2000:]); return r.stdout, time.time() - t
HEAD = ('You are a professional pixel artist (SNES/GBA chibi sprites). Work ONLY on the char-maps below (1 char = 1 pixel, "." = transparent). '
        'Palette chars: ' + '; '.join('%s=%s' % (k, v) for k, v in LEG.items()) + '. Light from the upper left. Clean 1-px K outline on every edge facing empty space, '
        'no orphan pixels, no rotation blur / dithering / new colours, clusters >= 2 px, smooth stepping (equal step lengths). Do not use tools; reply directly.\n')
def tilt_job(v, side, acc):
    d = -1 if side == 'L' else 1; jd = f'{ART}/{v}_tilt{side}'; os.makedirs(jd, exist_ok=True)
    base = CH.lib(v, 'base_neutral')[0]; draft = load(f'{LD}/{v}/draft/base_tilt{side}.txt')[0]; lab = CH.meta(v)[0]
    mk = [''.join('#' if c == 'f' else '.' for c in r) for r in lab]
    full = CH.compose_stamp(v, {})[0]
    P = HEAD + f'''TASK: a {v}-view chibi girl head BASE layer (skull, bangs, hair framing the face; the face features are a separate layer, so the face area here is blank skin).
Draw a clean pre-drawn HEAD TILT of about 8-10 degrees, crown leaning to screen {"LEFT" if d < 0 else "RIGHT"} (like a cute curious head tilt).
DRAFT below = a crude row-shear of the neutral base (crown already shifted ~3 px {"left" if d < 0 else "right"}, jaw ~1 px the other way): it has broken stair-step outlines and torn bangs/strand lines.
Redraw it as a clean tilted head: keep the draft's overall placement (same canvas, same face position: the blank face skin area marked # in the MASK must stay plain skin at exactly those pixels, so the face layer lands on skin), smooth the tilted skull outline,
re-flow the bangs strands (h lines on H, the L sheen band) so they follow the tilt, keep the jaw/cheek outline clean. Keep the same chars and the same overall size.

NEUTRAL BASE (reference, untilted):
{grid_txt(base)}

FULL HEAD AT REST (reference with face, bow, hair parts; for context only):
{grid_txt(full)}

MASK (# = blank face area, must stay skin s/S):
{grid_txt(mk)}

DRAFT TO CLEAN (tilt {side}):
{grid_txt(draft)}

Reply with the cleaned {len(draft[0])}x{len(draft)} grid (no row numbers) between a line "BEGIN" and a line "END".'''
    return run(jd, acc, P, draft, 'tilt', v, f'{LD}/{v}/approved/base_tilt{side}.txt', {'_': f'base_tilt{side}'})
def sway_job(v, p, acc):
    jd = f'{ART}/{v}_{p}'; os.makedirs(jd, exist_ok=True); rest = CH.lib(v, f'{p}_rest')[0]
    drafts = {s: load(f'{LD}/{v}/draft/{p}_{s}.txt')[0] for s in ('lagL', 'lagR', 'lift', 'drop')}
    full = CH.compose_stamp(v, {})[0]; T = BOW_TXT if p == 'w' else STATE_TXT
    P = HEAD + f'''TASK: secondary-motion sway states for the {NAMES[p]} of a {v}-view chibi girl head (96 px figure). The part is a separate layer composited over/under the head.
REST sprite of the part (same canvas as the full head):
{grid_txt(rest)}

FULL HEAD AT REST (context):
{grid_txt(full)}

Draw 4 clean pre-drawn sway states. The top attachment rows (where the part meets the head/knot) must stay pixel-identical to REST so it stays attached; motion grows toward the free end (secondary motion, natural hair/ribbon physics, soft S-curves, tips taper to points). Keep the same chars, shading clusters and strand lines as REST, re-flowed along the new curve. Crude procedural DRAFTS are given as a starting point (they are rigid shears with stair-steps; fix them):
''' + '\n'.join(f'STATE {s}: {T[s]}\nDRAFT {s}:\n{grid_txt(g)}\n' for s, g in drafts.items()) + f'''
Reply with 4 grids ({len(rest[0])}x{len(rest)} each, no row numbers), each between a line "BEGIN <state>" (state = lagL, lagR, lift, drop) and a line "END".'''
    return run(jd, acc, P, drafts, 'sway', v, {s: f'{LD}/{v}/approved/{p}_{s}.txt' for s in drafts}, {s: f'{p}_{s}' for s in drafts}, rest=rest)
def run(jd, acc, P, src, kind, v, outp, names, rest=None):
    srcs = src if isinstance(src, dict) else {'_': src}; outs = outp if isinstance(outp, dict) else {'_': outp}
    H, W = len(next(iter(srcs.values()))), len(next(iter(srcs.values()))[0]); res = {}; logs = []
    attach = CH.rest_union(v) - {(x, y) for g in srcs.values() for y, r in enumerate(g) for x, c in enumerate(r) if c != '.'}   # neighbours that belong to other layers
    for attempt in range(2):
        out, dt = call(acc, P, f'{jd}/log{attempt}.txt'); got = parse(out, H, W); fixes = []
        for k in srcs:
            g = got.get(k) or (got.get('_') if len(srcs) == 1 else None)
            if g is None: fixes.append(f'{k}: grid missing/unparsable'); continue
            if rest is not None:   # root rows (top 2 rows of the rest bbox) identical
                ys = [y for y, r in enumerate(rest) if r.strip('.')]; y0 = ys[0]
                for y in (y0, y0 + 1):
                    if g[y] != rest[y]: g[y] = rest[y]
            f = lint(g, srcs[k], kind, v, attach)
            if not f or attempt == 1: res[k] = (g, f)
            fixes += [f'{k}: {x}' for x in f]
        logs.append(dict(attempt=attempt, sec=round(dt), fixes=fixes))
        if not fixes: break
        P = P + '\n\nYOUR PREVIOUS ANSWER HAD THESE PROBLEMS, fix them and reply again in the same format:\n' + '\n'.join(fixes[:20]) + '\nPREVIOUS ANSWER:\n' + out[-6000:]
    os.makedirs(os.path.dirname(next(iter(outs.values()))), exist_ok=True); acc_ = {}
    for k, (g, f) in res.items():
        p = outs[k].replace('/approved/', '/artist/'); os.makedirs(os.path.dirname(p), exist_ok=True)
        save(p, g, {'origin': list(map(int, load(f'{LD}/{v}/labels.txt')[1]['origin'])), 'view': [v], 'lint': [len(f)]}); acc_[k] = dict(path=p, lint=f)
    json.dump(dict(logs=logs, out=acc_), open(f'{jd}/result.json', 'w'), indent=1)
    print(os.path.basename(jd), 'attempts', len(logs), 'secs', [l['sec'] for l in logs], 'lint left', {k: len(v['lint']) for k, v in acc_.items()})
if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'tilt': tilt_job(a[1], a[2], a[3])
    elif a[0] == 'sway': sway_job(a[1], a[2], a[3])
