#!/usr/bin/env python3
"""qc_gate.py: ONE consistency gate for the pixel-art sprites (masters, expression stamps, clips, all clips).

  qc_gate.py masters [MDIR]                         5-view masters (default: first of v2/m96/{final,masters}, v2/pixelize/top1)
  qc_gate.py stamps  SDIR [--masters MDIR]          expression stamps <VIEW>_<expr>.txt (vs <VIEW>_neutral.txt + master)
  qc_gate.py clip    CDIR [--view SE] [--masters MDIR] [--stamp S.txt] [--rest 0,4] [--contacts 0,4] [--noloop]
  qc_gate.py all     ROOT|CDIR... [--masters MDIR]   every clip dir under ROOT (has frames.json or fNN/cNN.txt) + cross-clip
  qc_gate.py frame   F.txt --view SE [--master M.txt] [--stamp S.txt] [--rest-frame]   single frame (fix lines only)
  common: --palette P.json (default v2/pixelize/palette.json) --out DIR (default v2/qc/out/<mode>_<name>; '-' = none)
          --json (print JSON instead of text) --quiet (only the verdict + fix lists) --no-overlay
  exit 0 = PASS, 1 = FAIL.   Outputs in OUT: report.txt, report.json, ov_<item>_<check>.png (<=800px) per failure.

Clip dir: cNN.txt (post.py clean output) else fNN.txt, optional frames.json (dir/view, cell, pivot, palette, frames[i].key,
  air, stamp, rest, contact, overlap, deliberate=[[x0,y0,x1,y1],..]). Frame meta lines: '; air', '; rest', '; contact',
  '; overlap' (hair/bow overlap motion: skips bow-shape + hair diffs), '; shift x0 y0 x1 y1' (deliberate change rect).
  rest frames = --rest | frames[i].rest | key contains idle/contact/stand/rest/neutral; contacts = --contacts | key 'contact'.
Checks (item -> FAIL with fix lines; WARN lines never fail):
  palette  off-palette chars; material ramp swaps (colorcheck.material_lint vs the view master; masters: vs nothing)
  eyes     eye blobs / catchlights (W) / lash / iris chars: same across views (rel. head) and frames (screen space, after
           the head offset); m96/tools/eyecheck.py qc_hook(grid, view, ref_grid, pal_path) -> (metrics, fixes) is called
           when present (else built-in stub)
  head     head window == the view stamp (or master head) pixel-for-pixel (minus expression stamp / shift / occlusion);
           head bbox w,h == master (+-0); cross-view: head h equal +-1, w S~N, SE~NE +-1
  bow      knot/bow centred on the head midline in S/N (|left-right| <= 1px); SE/NE/E offset == master +-1; bow shape == master
  sections crown/eye/chin/shoulder/waist/hem/skin/sock/knee*/boot/sole rows +-1 vs the view master in rest frames
           (masters: across views); skin band + sock band present wherever the legs are visible
  outline  O1 outline continuous K, S4 orphan pixels, floating islands, no colours absent from the view master/stamp
           (R1 interior K / O3 jaggies = WARN)
  xview    table S SE E NE N of head size, eye pos, bow pos, rows, palette usage per material; outliers marked '*'
  continuity (clips) colorcheck.clip_report flicker (head, obi, boots) + socks flicker, sole on pivot row, both feet down
           on contacts, pivot drift (obi centre x vs master)
Pipeline hooks (final gate; one line each, not applied - owners of those files paste them):
  ff_redraw.py validate(), just before 'return fx' (per-frame artist retry then receives the QC fix list):
      sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/qc'); import qc_gate; fx += qc_gate.validate_hook(path, fj, stamp, master)
  post.py main dispatch (new command 'post.py qc S ACT [qc_gate clip options]'):
      elif c == 'qc': sys.path.insert(0, V2 + '/qc'); import qc_gate; sys.exit(qc_gate.main(['clip', wdir(sys.argv[2], sys.argv[3])] + sys.argv[4:]))
  shell (any stage): .venv/bin/python v2/qc/qc_gate.py clip <workdir> --masters <MDIR> --out -    (exit 1 = FAIL)
h96 LAYERED HEADS (v2/heads96/tools/compose_head.py; backup qc_gate.py.bak_h96): a frame whose stamp file carries '; layered'
  (composed by compose_head.write_stamp) is compared against master_ref (the master with its rest head layers replaced by the
  composite), and chk_layered adds head FAILs LAYERFACE (face layer != approved stamp), LAYERHAIR (head px not from the approved
  sprites), LAYERLIB (face library != m96 stamps), LAYERSTAMP (composed stamp != composite of its head_spec).
"""
import glob, json, os, re, sys
from collections import Counter, deque

V2 = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2'
sys.path.insert(0, V2 + '/anim_cut/tools')
import colorcheck as CC, lint_style as LS

VIEWS = ['S', 'SE', 'E', 'NE', 'N']; MIRROR = {'SW': 'SE', 'W': 'E', 'NW': 'NE'}
DEF_PAL = V2 + '/pixelize/palette.json'
DEF_MASTERS = [V2 + '/m96/final', V2 + '/m96/masters', V2 + '/pixelize/top1']
EYEHOOK = [V2 + '/m96/tools/eyecheck.py', V2 + '/m96/eyecheck.py']
SPEC = dict(row_tol=1, head_bbox_tol=0, head_h_x=1, head_w_pairs=(('S', 'N'), ('SE', 'NE')), head_w_tol=1, bow_sym=1,
            bow_off_tol=1, bow_shape_px=2, head_px=0, eye_row_x=1, pivot_drift=1, socks_px=4,
            eyes_expected={'S': 2, 'SE': 2, 'E': 1, 'NE': 0, 'N': 0})
CHECKS = ['palette', 'eyes', 'head', 'bow', 'sections', 'outline', 'continuity', 'xview']
ROWS = ['crown', 'eye', 'chin', 'shoulder', 'waist', 'obi_bot', 'hem', 'skin_top', 'sock_top', 'knee', 'boot_top', 'sole']
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1)); N8 = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b]


# ---------------------------------------------------------------- io
def read(p):
    g, meta = LS.read(p); return g, meta


def view_of(name):
    m = re.findall(r'(?:^|[_/.\-])(SE|SW|NE|NW|S|E|N|W)(?=[_/.\-]|$)', name)
    return m[-1] if m else None


def mirror(g): return [r[::-1] for r in g]


def ref_with_stamp(M, sp):
    """a96: expression-aware reference = view master with the frame's expression stamp pasted at its '; origin'
    (eyes/bow/eye-row checks of non-neutral frames otherwise compare against the neutral face -> false FAILs)."""
    if M is None or not sp or not os.path.exists(sp): return M
    st, meta = read(sp); o = meta.get('origin') if isinstance(meta, dict) else None
    if not o: return M
    if isinstance(meta, dict) and 'layered' in meta:   # h96: layered head -> master with its rest head layers replaced by the composite
        CH = heads96(); v = (meta.get('view') or [None])[0]
        if CH and v: return CH.master_ref(M, v, st, [int(o[0]), int(o[1])])
    g = [list(r) for r in M]
    for r, row in enumerate(st):
        for c, ch in enumerate(row):
            Y, X = o[1] + r, o[0] + c
            if ch != '.' and 0 <= Y < len(g) and 0 <= X < len(g[0]): g[Y][X] = ch
    return [''.join(r) for r in g]


def find_masters(mdir=None):
    for d in ([mdir] if mdir else DEF_MASTERS):
        if d and os.path.isdir(d):
            out = {}
            for p in sorted(glob.glob(d + '/*.txt')):
                v = view_of(os.path.basename(p)[:-4])
                if v in VIEWS and v not in out: out[v] = p
            if out: return d, out
    return None, {}


def master_grid(masters, view):
    if view in masters: return read(masters[view])[0]
    if view in MIRROR and MIRROR[view] in masters: return mirror(read(masters[MIRROR[view]])[0])
    return None


# ---------------------------------------------------------------- measurement
def parts(g, pal):
    """material+location parse of a full-figure grid -> dict of rows, head box, bow, legs, eyes, usage."""
    H, W = len(g), len(g[0]); op = [(x, y) for y, r in enumerate(g) for x, c in enumerate(r) if c != '.']
    if not op: return None
    lab, comps = CC.components(g, pal)
    top = min(y for _, y in op); sole = max(y for _, y in op); fh = sole - top + 1
    has = lambda C, m: m in C['label']
    hb = [C for C in comps if has(C, 'hair') or has(C, 'boots')]
    red = [C for C in comps if has(C, 'dress') or has(C, 'bow')]
    skin = [C for C in comps if has(C, 'skin')]
    obi = [C for C in comps if has(C, 'obi') and C['n'] >= 4]
    up = top + 0.45 * fh
    hu = [C for C in hb if C['cen'][1] < up and C['n'] >= 4]
    hcy = sum(C['cen'][1] * C['n'] for C in hu) / max(1, sum(C['n'] for C in hu)) if hu else top + 0.2 * fh
    redc = {c for C in red for c in C['chars']} or set(pal.ramps.get('dress', [])) - pal.univ
    ocx = [x for C in obi for x, _ in C['px']]; bcx = (min(ocx) + max(ocx)) / 2 if ocx else sum(x for x, _ in op) / len(op)
    shoulder = None  # first row in the shoulder band with >=5 red px (and the next row too) within 7 px of the body centre (collar / dress top)
    for y in range(int(top + 0.25 * fh), int(top + 0.5 * fh) + 1):
        cnt = lambda yy: sum(1 for x in range(int(bcx) - 7, int(bcx) + 8) if 0 <= x < W and g[yy][x] in redc)
        if cnt(y) >= 5 and cnt(y + 1) >= 5: shoulder = y; break
    if shoulder is None: shoulder = int(top + 0.35 * fh)
    bowpx = {p for C in red for p in C['px'] if p[1] < shoulder}
    bow = [C for C in red if C['cen'][1] < shoulder]
    dress = [C for C in red if C not in bow or C['bbox'][3] >= shoulder]
    P = dict(top=top, sole=sole, W=W, H=H, lab=lab, comps=comps)
    P['waist'] = min((C['bbox'][1] for C in obi), default=None); P['obi_bot'] = max((C['bbox'][3] for C in obi), default=None)
    opx = [p for C in obi for p in C['px']]
    P['obi_cx'] = (min(p[0] for p in opx) + max(p[0] for p in opx)) / 2 if opx else None
    cx = P['obi_cx'] if P['obi_cx'] is not None else sum(x for x, _ in op) / len(op)
    dset = {p for C in dress for p in C['px'] if abs(p[0] - cx) <= 4 and p[1] >= shoulder}; hem = None
    if dset:  # last row of the first run of rows (from the obi / dress top down) with dress px in the centre columns
        y = P['obi_bot'] if P['obi_bot'] is not None else min(p[1] for p in dset)
        y0 = y
        while y <= sole and (any((x, y) in dset for x in range(int(cx) - 4, int(cx) + 5)) or y == y0): hem = y; y += 1
    P['hem'] = hem
    lim = shoulder if shoulder is not None else top + 0.4 * fh
    hair = [C for C in hb if C['bbox'][1] < lim]
    boots = [C for C in hb if C not in hair and C['bbox'][1] > (hem if hem is not None else top + 0.6 * fh)]
    hpx = [p for C in hair for p in C['px']]
    crown = min((p[1] for p in hpx), default=top)
    face = [C for C in skin if C['cen'][1] < (shoulder if shoulder is not None else up) + 2 and C['bbox'][1] < lim]
    fpx = [p for C in face for p in C['px'] if shoulder is None or p[1] < shoulder]
    chin = max((p[1] for p in fpx), default=(shoulder - 1 if shoulder is not None else int(up)))
    bset = bowpx
    hd = [(x, y) for (x, y) in op if crown <= y <= chin and (x, y) not in bset and (
        lab[y][x] < 0 or comps[lab[y][x]] in hair or comps[lab[y][x]] in face or 'eyes' in comps[lab[y][x]]['label'])]
    hd = [p for p in hd if not (g[p[1]][p[0]] in pal.univ and not any(
        0 <= p[0] + a < W and 0 <= p[1] + b < H and lab[p[1] + b][p[0] + a] >= 0 and comps[lab[p[1] + b][p[0] + a]] in hair + face for a, b in N8))]
    hx0, hx1 = (min(p[0] for p in hd), max(p[0] for p in hd)) if hd else (0, 0)
    P['head'] = dict(x0=hx0, x1=hx1, y0=crown, y1=chin, w=hx1 - hx0 + 1, h=chin - crown + 1)
    hh = chin - crown + 1
    upx = [p for p in hpx if p[1] <= crown + int(0.6 * hh)]
    mid = (min(p[0] for p in upx) + max(p[0] for p in upx)) / 2 if upx else (hx0 + hx1) / 2
    P['mid'] = mid
    knot = set(); rest = set(bset)  # knot/bow = 4-connected red groups (>=4 px) above the shoulder starting in the top 40% of the head
    while rest:
        q = [rest.pop()]; grp = set(q)
        while q:
            a, b = q.pop()
            for dx, dy in N4:
                n = (a + dx, b + dy)
                if n in rest: rest.discard(n); grp.add(n); q.append(n)
        if len(grp) >= 4 and min(p[1] for p in grp) <= crown + 0.4 * hh: knot |= grp
    if knot:
        bx0, bx1 = min(p[0] for p in knot), max(p[0] for p in knot); by0, by1 = min(p[1] for p in knot), max(p[1] for p in knot)
        P['bow'] = dict(x0=bx0, x1=bx1, y0=by0, y1=by1, n=len(knot), cx=(bx0 + bx1) / 2, off=round((bx0 + bx1) / 2 - mid, 1),
                        asym=(bx1 - mid) - (mid - bx0), px=sorted(knot), all=sorted(bset))
    else: P['bow'] = None
    # legs
    below = hem if hem is not None else top + 0.6 * fh
    skc = set(pal.ramps.get('skin', [])) - pal.univ; soc = set(pal.ramps.get('socks', [])) - pal.univ
    leg_skin = [(x, y) for (x, y) in op if y > below and g[y][x] in skc]
    leg_sock = [(x, y) for (x, y) in op if y > below and g[y][x] in soc]
    bpx = [p for C in boots for p in C['px']]
    P['skin_top'] = min((p[1] for p in leg_skin), default=None)
    P['sock_top'] = min((p[1] for p in leg_sock), default=None)
    P['boot_top'] = min((p[1] for p in bpx), default=None)
    P['knee'] = (P['sock_top'] + P['boot_top']) // 2 if P['sock_top'] is not None and P['boot_top'] is not None else None
    P['legs_visible'] = sum(1 for (x, y) in op if y > below + 1) >= 8
    P['n_leg_skin'], P['n_leg_sock'] = len(leg_skin), len(leg_sock)
    P['boots'] = boots
    P.update(crown=crown, chin=chin, shoulder=shoulder)
    P['face_px'] = fpx; P['bow_set'] = bset
    P['eyes'] = eyes_stub(g, pal, P)
    P['eye'] = min((e['y0'] for e in P['eyes']['list']), default=None)
    # usage per material
    use = {}
    for y, r in enumerate(g):
        for x, c in enumerate(r):
            if c == '.': continue
            k = lab[y][x]; m = '/'.join(comps[k]['label']) if k >= 0 else ('outline' if c in pal.univ else '?')
            if k >= 0 and comps[k] in bow: m = 'bow'
            elif k >= 0 and comps[k] in boots: m = 'boots'
            elif k >= 0 and comps[k] in hair: m = 'hair'
            elif k >= 0 and comps[k] in dress: m = 'dress'
            use.setdefault(m, Counter())[c] += 1
    P['usage'] = use
    P['rows'] = {k: P.get(k) for k in ROWS}
    return P


def eyes_stub(g, pal, P):
    """eye blobs inside the face skin span (rows crown..chin): non-skin pixels, grouped 8-conn, kept if they hold W or a
    foreign (non eye-ramp) char. catchlight = W pixel with >=5 of 8 neighbours non-W non-skin (inside the iris)."""
    H, W = len(g), len(g[0]); skc = set(pal.ramps.get('skin', [])) - pal.univ
    eyec = set(pal.ramps.get('eyes', [])) | pal.univ; hairc = set(pal.ramps.get('hair', [])) - pal.univ
    hl = 'W' if 'W' in pal.colors else (sorted(pal.eyes)[-1] if pal.eyes else 'W')
    span = {}
    for x, y in P['face_px']: a = span.get(y, (x, x)); span[y] = (min(a[0], x), max(a[1], x))
    if not span: return dict(list=[], foreign=[], hl=hl)
    f0 = min(span)
    def inside(x, y):
        for yy in (y - 1, y, y + 1):
            if yy in span and span[yy][0] <= x <= span[yy][1]: return True
        return False
    cand = set(); hon = hairc - eyec; ylim = P['crown'] + 0.75 * (P['chin'] - P['crown'] + 1)
    for y in range(max(P['crown'], f0 + 1), min(P['chin'] + 1, int(ylim) + 1)):
        for x in range(W):
            c = g[y][x]
            if c == '.' or c in skc or (x, y) in P['bow_set'] or not inside(x, y) or (c in hairc and c not in eyec): continue
            if c in pal.univ and any(not (0 <= x + a < W and 0 <= y + b < H) or g[y + b][x + a] == '.' for a, b in N4): continue
            if c != hl and any(0 <= x + a < W and 0 <= y + b < H and g[y + b][x + a] in hon for a, b in N8): continue
            cand.add((x, y))
    seen = set(); out = []; foreign = []
    for p in sorted(cand, key=lambda q: (q[1], q[0])):
        if p in seen: continue
        q = deque([p]); seen.add(p); blob = []
        while q:
            a, b = q.popleft(); blob.append((a, b))
            for dx, dy in N8:
                n = (a + dx, b + dy)
                if n in cand and n not in seen: seen.add(n); q.append(n)
        chars = Counter(g[y][x] for x, y in blob)
        fr = [c for c in chars if c not in eyec]
        ik = sum(1 for x, y in blob if g[y][x] in pal.univ)
        if hl not in chars and not fr and ik < 2: continue
        if len(blob) < 3 or len(blob) > 60: continue
        xs, ys = [b[0] for b in blob], [b[1] for b in blob]
        cl = []
        for x, y in blob:
            if g[y][x] != hl: continue
            nb = [g[y + b][x + a] for a, b in N8 if 0 <= x + a < W and 0 <= y + b < H]
            if sum(1 for c in nb if c != hl and c not in skc and c != '.') >= 5: cl.append((x, y))
        y0 = min(ys)
        out.append(dict(x0=min(xs), y0=y0, x1=max(xs), y1=max(ys), w=max(xs) - min(xs) + 1, h=max(ys) - y0 + 1, n=len(blob),
                        catch=cl, white=chars.get(hl, 0), iris=''.join(sorted(c for c in chars if c not in pal.univ and c != hl)),
                        lash=any(g[y0][x] in pal.univ for x in range(min(xs), max(xs) + 1)), foreign=''.join(sorted(fr)), px=blob))
        if fr: foreign.append((''.join(sorted(fr)), [b for b in blob if g[b[1]][b[0]] in fr]))
    out.sort(key=lambda e: e['x0'])
    return dict(list=out, foreign=foreign, hl=hl)


_EH = None
_H96 = None
def heads96():
    """h96: layered-head composer (v2/heads96/tools/compose_head.py) or None"""
    global _H96
    if _H96 is None:
        try:
            sys.path.insert(0, V2 + '/heads96/tools'); import compose_head as _ch; _H96 = _ch
        except Exception as e: print('heads96 load failed: %s' % e); _H96 = False
    return _H96 or None


def chk_layered(it, g, sp):
    """h96 LAYERED HEAD: face layer == the approved stamp for its expression (at the nod/turn offset, minus hair occlusion),
    every other head px == the approved layer sprites (base/tilt/sway), the face library == the m96 stamps."""
    if not sp or not os.path.exists(sp): return
    st, meta = read(sp)
    if not (isinstance(meta, dict) and 'layered' in meta): return
    CH = heads96()
    if not CH: it.warn('head', 'LAYERED head stamp but heads96 composer unavailable'); return
    v = meta['view'][0]; spec = CH.spec_of(meta); m, n, ox, oy = CC.anchor(g, st)
    if m < 0.5 * n: return   # chk_frame_vs_ref reports the missing head
    it.metrics['layered'] = dict(spec=spec, at=(ox, oy))
    for f in CH.verify(g, v, spec, (ox, oy)) + CH.library_check(v): it.fail('head', f, pts_of(f))
    rows = CH.compose_stamp(v, spec)[0]
    if rows != st: it.fail('head', 'LAYERSTAMP %s is not the composite of its head_spec (stale or hand-edited composed stamp): recompose it' % os.path.basename(sp))


def eyehook():
    global _EH
    if _EH is None:
        _EH = False
        for p in EYEHOOK:
            if os.path.exists(p):
                import importlib.util
                try:
                    sp = importlib.util.spec_from_file_location('eyecheck', p); m = importlib.util.module_from_spec(sp)
                    sys.path.insert(0, os.path.dirname(p)); sp.loader.exec_module(m)
                    if hasattr(m, 'qc_hook'): _EH = m; break
                except Exception as e: print('eyecheck hook load failed (%s): %s' % (p, e))
    return _EH or None


# ---------------------------------------------------------------- result model
class Item:
    def __init__(self, name, path=None, grid=None, ref=None):
        self.name, self.path, self.grid, self.ref = name, path, grid, ref; self.iss = []; self.metrics = {}

    def fail(self, check, msg, pts=()): self.iss.append(dict(check=check, sev='FAIL', msg=msg, pts=[tuple(p[:2]) for p in pts][:400]))
    def warn(self, check, msg, pts=()): self.iss.append(dict(check=check, sev='WARN', msg=msg, pts=[tuple(p[:2]) for p in pts][:400]))
    @property
    def ok(self): return not any(i['sev'] == 'FAIL' for i in self.iss)


def pts_of(msg):
    return [(int(a), int(b)) for a, b in re.findall(r'\((-?\d+), ?(-?\d+)', msg)]


# ---------------------------------------------------------------- per-grid checks
def chk_palette(it, g, pal, master=None, stamp=None, P=None):
    for m in CC.off_palette(g, pal): it.fail('palette', m, [(x, y) for y, r in enumerate(g) for x, c in enumerate(r) if c != '.' and c not in pal.colors])
    if master is not None:
        for m in CC.material_lint(g, pal, master, stamp): it.fail('palette', m, pts_of(m))
        return
    # no reference (masters): every region may only use its own ramp; eye chars allowed in the head box; enclosures = WARN
    lab, comps = CC.components(g, pal); hb = P['head'] if P else None
    inh = lambda x, y: hb and hb['x0'] <= x <= hb['x1'] and hb['y0'] <= y <= hb['y1']
    for C in comps:
        lb = set(C['label']); bad = {}
        for x, y in C['px']:
            c = g[y][x]
            if pal.m(c) & lb or ('eyes' in pal.m(c) and inh(x, y)): continue
            bad.setdefault(c, []).append((x, y))
        if bad:
            pts = [p for v in bad.values() for p in v]; ch = ''.join(sorted(bad))
            it.fail('palette', 'MAT %d px of %s (%s ramp) inside the %s area at %s: %s may only use its own ramp %s' % (
                len(pts), ch, '/'.join(sorted({m for c in bad for m in pal.m(c)})), '/'.join(C['label']), pts[:8], '/'.join(C['label']), pal.ramp_str(C['label'])), pts)
    HM = {'skin', 'eyes', 'hair', 'mouth', 'bow', 'dress'}
    if hb:
        fp = [(x, y) for y in range(hb['y0'], hb['y1'] + 1) for x in range(hb['x0'], hb['x1'] + 1)
              if g[y][x] != '.' and g[y][x] not in pal.univ and not (pal.m(g[y][x]) & HM)]
        if fp:
            ch = ''.join(sorted({g[y][x] for x, y in fp}))
            it.fail('palette', 'MAT %d px of %s (%s ramp) inside the head at %s: head/face may only use hair, skin, eye and bow ramps (%s)' % (
                len(fp), ch, '/'.join(sorted({m for c in ch for m in pal.m(c)})), fp[:8], ' '.join(c for c in pal.colors if pal.m(c) & HM)), fp)
    for C, D in CC.enclosed(g, pal, lab, comps, small=12, rel=0):
        if C['n'] > 12 or any('eyes' in pal.m(c) for c in C['chars']): continue
        x, y = C['cen']; msg = 'MAT %d px of %s (%s ramp) enclosed in the %s area at (%d,%d)-(%d,%d)' % (
            C['n'], ''.join(sorted(C['chars'])), '/'.join(sorted(C['mats'])), '/'.join(D['label']), *C['bbox'])
        if inh(x, y) and not (C['mats'] & HM): continue  # reported by the head check above
        it.warn('palette', msg, C['px'])


def outline_pts(g, pal):
    """{'O1': {(x,y,c)}, 'S4': {...}} full point sets (lint_style rules, uncapped)."""
    H, W = len(g), len(g[0]); op = lambda x, y: 0 <= x < W and 0 <= y < H and g[y][x] != '.'; o1, s4 = set(), set()
    out = next(iter(sorted(pal.univ)), 'K'); eye = set(pal.ramps.get('eyes', [])) | {'W'}
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            if c == '.': continue
            if c != out and any(not op(x + a, y + b) for a, b in N4): o1.add((x, y, c))
            if c != out and c not in eye and not any(0 <= x + a < W and 0 <= y + b < H and g[y + b][x + a] == c for a, b in N8): s4.add((x, y, c))
    return {'O1': o1, 'S4': s4}


def chk_outline(it, g, pal, ref_cols=None, P=None, ref=None):
    """ref = reference grid (view master): outline faults already present there at the same pixel are not repeated."""
    cur = outline_pts(g, pal); old = outline_pts(ref, pal) if ref is not None and len(ref) == len(g) else {'O1': set(), 'S4': set()}
    txt = {'O1': 'O1 %d silhouette-edge pixels are not outline colour (outline must be continuous)%s: %s',
           'S4': 'S4 %d orphan pixels (single-pixel clusters)%s: %s'}
    if ref is not None and (old['O1'] or old['S4']):  # align the master's faults to the frame (body may be shifted)
        al = set().union(*cur.values()); ol = set().union(*old.values())
        best = max(((dx, dy) for dx in range(-4, 5) for dy in range(-4, 5)),
                   key=lambda d: (len({(x + d[0], y + d[1], c) for x, y, c in ol} & al), -abs(d[0]) - abs(d[1])))
        old = {k: {(x + best[0], y + best[1], c) for x, y, c in v} for k, v in old.items()}
    for k in ('O1', 'S4'):
        new = sorted(cur[k] - old[k], key=lambda p: (p[1], p[0]))
        if new: it.fail('outline', txt[k] % (len(new), ' (new vs the master)' if ref is not None else '', new[:12]), new)
    for f in LS.lint(g, {}, None, (0, 0), air=True, max_colors=99, palette=pal):
        if f.startswith(('R1', 'O3')) and ref is None: it.warn('outline', f, pts_of(f))
    H, W = len(g), len(g[0]); seen = set()
    for y in range(H):
        for x in range(W):
            if g[y][x] == '.' or (x, y) in seen: continue
            q = deque([(x, y)]); seen.add((x, y)); cc = []
            while q:
                a, b = q.popleft(); cc.append((a, b))
                for dx, dy in N8:
                    X, Y = a + dx, b + dy
                    if 0 <= X < W and 0 <= Y < H and g[Y][X] != '.' and (X, Y) not in seen: seen.add((X, Y)); q.append((X, Y))
            if len(cc) < 6: it.fail('outline', 'ISLAND %d floating px detached from the silhouette at %s: delete them or join them to the outline' % (len(cc), cc[:6]), cc)
    if ref_cols is not None:
        new = {c for r in g for c in r} - set(ref_cols) - {'.'}
        if new:
            pp = [(x, y) for y, r in enumerate(g) for x, c in enumerate(r) if c in new]
            it.fail('outline', 'NEWCOL colours %s not used in the view master/stamp (%d px at %s): use only the master colours' % (''.join(sorted(new)), len(pp), pp[:8]), pp)


def eye_compare(it, E, R, dx, dy, where='vs master'):
    """frame eyes E vs reference eyes R (screen space, R shifted by the head offset dx,dy)."""
    a, b = E['list'], R['list']
    if len(a) != len(b):
        it.fail('eyes', 'EYES %d eye blobs vs %d in the reference (%s); keep both eyes exactly as the stamp' % (len(a), len(b), where),
                [p for e in a for p in e['px']]); return
    for k, (e, r) in enumerate(zip(a, b)):
        sh = lambda p: (p[0] + dx, p[1] + dy)
        if (e['x0'], e['y0'], e['w'], e['h']) != (r['x0'] + dx, r['y0'] + dy, r['w'], r['h']):
            it.fail('eyes', 'EYE%d box (%d,%d) %dx%d, reference (%d,%d) %dx%d (%s, head offset %+d,%+d): eye must not move/resize relative to the head' % (
                k, e['x0'], e['y0'], e['w'], e['h'], r['x0'] + dx, r['y0'] + dy, r['w'], r['h'], where, dx, dy), e['px'])
        if sorted(e['catch']) != sorted(sh(p) for p in r['catch']):
            it.fail('eyes', 'EYE%d catchlight(s) at %s, reference %s (screen space): same count and pixel position in every view/frame' % (
                k, e['catch'], [sh(p) for p in r['catch']]), e['catch'] + [sh(p) for p in r['catch']])
        if e['iris'] != r['iris']: it.fail('eyes', 'EYE%d iris colours %s vs reference %s' % (k, e['iris'], r['iris']), e['px'])
        if e['lash'] != r['lash']: it.fail('eyes', 'EYE%d lash line %s vs reference %s' % (k, 'present' if e['lash'] else 'missing', 'present' if r['lash'] else 'missing'), e['px'])


def chk_eyes_single(it, g, pal, P, view, single=True):
    """single=False (frames with a reference): count/catchlight/lash rules are left to eye_compare vs the master."""
    E = P['eyes']
    for fr, pp in E['foreign']: it.fail('eyes', 'EYE uses non-eye colours %s (%d px at %s): eyes = %s only (%s = catchlight/white)' % (
        fr, len(pp), pp[:6], pal.ramp_str(('eyes',)), E['hl']), pp)
    exp = SPEC['eyes_expected'].get(MIRROR.get(view, view)) if single else None
    if exp is not None and len(E['list']) != exp and exp:
        it.fail('eyes', 'EYES %d eye blobs found, %s view needs %d' % (len(E['list']), view, exp), [p for e in E['list'] for p in e['px']])
    for k, e in enumerate(E['list'] if single else []):
        if not e['catch']: it.fail('eyes', 'EYE%d at (%d,%d) has no catchlight (%s pixel inside the iris)' % (k, e['x0'], e['y0'], E['hl']), e['px'])
        if not e['lash']: it.warn('eyes', 'EYE%d at (%d,%d) has no outline-colour lash pixel on its top row' % (k, e['x0'], e['y0']), e['px'])
    h = eyehook()
    if h:
        try:
            m, fx = h.qc_hook(g, view, it.ref, pal.path); it.metrics['eyecheck'] = m
            for f in fx: it.fail('eyes', 'eyecheck: ' + f, pts_of(f))
        except Exception as ex: it.warn('eyes', 'eyecheck hook error: %s' % ex)


def head_window(g, P, pad=1):
    h = P['head']; x0 = max(0, h['x0'] - pad); x1 = min(P['W'] - 1, h['x1'] + pad)
    y0 = min(h['y0'], P['bow']['y0']) if P['bow'] else h['y0']
    return [r[x0:x1 + 1] for r in g[y0:h['y1'] + 1]], (x0, y0)


def excluded(x, y, rects): return any(a <= x <= c and b <= y <= d for a, b, c, d in rects)


def chk_frame_vs_ref(it, g, pal, P, M, PM, stamp=None, rest=False, overlap=False, rects=(), view=None):
    """head / bow / eyes / sections of a frame vs the view master (M grid, PM parts) and stamp."""
    st, so = (stamp, None) if stamp else head_window(M, PM)
    m, n, ox, oy = CC.anchor(g, st)
    if so is None: so = CC.anchor(M, st)[2:]
    dx, dy = ox - so[0], oy - so[1]; it.metrics['head_offset'] = (dx, dy)
    if m < 0.5 * n: it.fail('head', 'HEAD stamp not found (%d/%d px match): paste the view head stamp' % (m, n)); return
    smats = set().union(*[pal.m(c) for r in st for c in r])
    diff = []
    for y, r in enumerate(st):
        for x, c in enumerate(r):
            X, Y = x + ox, y + oy
            if c == '.' or not (0 <= X < P['W'] and 0 <= Y < P['H']): continue
            f = g[Y][X]
            if f == c or excluded(X, Y, rects): continue
            if f != '.' and pal.m(f) and not (pal.m(f) & smats): continue  # occluded by another material (arm, blade)
            if overlap and (pal.m(c) & {'hair', 'bow', 'dress'}) and f != '.': continue
            diff.append((X, Y, c, f))
    if len(diff) > SPEC['head_px']:
        it.fail('head', 'HEAD %d px differ from the %s (head at offset %+d,%+d): %s; restore those pixels' % (
            len(diff), 'stamp' if stamp else 'master head', dx, dy, ', '.join('(%d,%d) %s->%s' % q for q in diff[:10])), diff)
    hm, hf = PM['head'], P['head']
    if abs(hm['w'] - hf['w']) > SPEC['head_bbox_tol'] or abs(hm['h'] - hf['h']) > SPEC['head_bbox_tol']:
        it.fail('head', 'HEAD bbox %dx%d vs master %dx%d (must be +-%dpx): box (%d,%d)-(%d,%d)' % (
            hf['w'], hf['h'], hm['w'], hm['h'], SPEC['head_bbox_tol'], hf['x0'], hf['y0'], hf['x1'], hf['y1']),
            [(hf['x0'], hf['y0']), (hf['x1'], hf['y1'])])
    # eyes in screen space
    eye_compare(it, P['eyes'], PM['eyes'], dx, dy)
    # bow
    bm, bf = PM['bow'], P['bow']
    if bm and not bf: it.fail('bow', 'BOW missing (master has %d px at (%d,%d)-(%d,%d))' % (bm['n'], bm['x0'], bm['y0'], bm['x1'], bm['y1']))
    elif bm and bf:
        if abs(bf['off'] - bm['off']) > SPEC['bow_off_tol']:
            it.fail('bow', 'BOW centre is %+.1fpx from the head midline, master %+.1f (tol %d): move the knot back over the midline offset of the master' % (
                bf['off'], bm['off'], SPEC['bow_off_tol']), bf['px'])
        if not overlap:
            A = {(x - dx, y - dy) for x, y in bf['all']}; B = set(bm['all']); xo = sorted(A ^ B)
            if len(xo) > SPEC['bow_shape_px']:
                it.fail('bow', 'BOW shape differs from the master by %d px (after the head offset %+d,%+d) at %s; mark "; overlap" only for deliberate overlap motion' % (
                    len(xo), dx, dy, [(x + dx, y + dy) for x, y in xo[:8]]), [(x + dx, y + dy) for x, y in xo])
    # sections
    if rest:
        for k in ROWS:
            a, b = PM['rows'].get(k), P['rows'].get(k)
            if a is None and b is None: continue
            if a is None or b is None or abs(a - b) > SPEC['row_tol']:
                it.fail('sections', 'ROW %s at %s, master %s (rest frame, tol +-%d)' % (k, b, a, SPEC['row_tol']),
                        [(x, b) for x in range(0, P['W'], 4)] if b is not None else [])
    legs(it, P)


def legs(it, P):
    if P['legs_visible']:
        if P['n_leg_sock'] == 0: it.fail('sections', 'SOCKS band missing below the hem (legs visible): draw the D/d sock band')
        if P['n_leg_skin'] == 0: it.fail('sections', 'SKIN band missing between hem and socks (legs visible): keep the thigh skin band')


# ---------------------------------------------------------------- modes
def do_masters(mdir, pal, items, data):
    d, ms = find_masters(mdir)
    if not ms: raise SystemExit('no masters found in %s' % (mdir or DEF_MASTERS))
    data['masters_dir'] = d; Ps = {}; G = {}
    for v in VIEWS:
        if v not in ms: continue
        g = read(ms[v])[0]; G[v] = g; P = parts(g, pal); Ps[v] = P
        it = Item('master_' + v, ms[v], g); items.append(it)
        chk_palette(it, g, pal, None, None, P); chk_outline(it, g, pal, None, P); chk_eyes_single(it, g, pal, P, v); legs(it, P)
        chk_bow_single(it, P, v)
    xview(items, Ps, G, pal, data)
    return Ps


def chk_bow_single(it, P, v):
    b = P['bow']
    if not b: it.fail('bow', 'BOW not found above the hair centre'); return
    if v in ('S', 'N') and abs(b['asym']) > SPEC['bow_sym']:
        it.fail('bow', 'BOW not centred: spans x %d..%d, head midline %.1f (left %.1f / right %.1f px, need |diff| <= %d); shift it %+dpx' % (
            b['x0'], b['x1'], P['mid'], P['mid'] - b['x0'], b['x1'] - P['mid'], SPEC['bow_sym'], -round(b['asym'] / 2)), b['px'])


def xview(items, Ps, G, pal, data):
    """cross-view table + outliers; failures attached to an 'xview' item."""
    it = Item('xview', grid=None); it.strip = G; vs = [v for v in VIEWS if v in Ps]
    med = lambda L: sorted(L)[len(L) // 2] if L else None
    T = []; hdr = ['metric'] + vs; T.append(hdr)
    def row(name, vals, bad=()):
        T.append([name] + [('*' if v in bad else '') + str(vals.get(v, '-')) for v in vs])
    hw = {v: Ps[v]['head']['w'] for v in vs}; hh = {v: Ps[v]['head']['h'] for v in vs}
    mh = med(list(hh.values())); badh = {v for v in vs if abs(hh[v] - mh) > SPEC['head_h_x']}
    for v in badh: it.fail('xview', 'HEAD %s height %d vs median %d across views (tol %d)' % (v, hh[v], mh, SPEC['head_h_x']), [(v, 0)])
    badw = set()
    for a, b in SPEC['head_w_pairs']:
        if a in hw and b in hw and abs(hw[a] - hw[b]) > SPEC['head_w_tol']:
            badw |= {a, b}; it.fail('xview', 'HEAD width %s %d vs %s %d (tol %d)' % (a, hw[a], b, hw[b], SPEC['head_w_tol']), [(a, 0), (b, 0)])
    row('head WxH', {v: '%dx%d' % (hw[v], hh[v]) for v in vs}, badh | badw)
    for k in ROWS:
        vals = {v: Ps[v]['rows'][k] for v in vs if Ps[v]['rows'][k] is not None}
        vv = [vals[v] for v in vals if not (k == 'eye')] if k != 'eye' else list(vals.values())
        m = med(list(vals.values())); bad = {v for v in vals if m is not None and abs(vals[v] - m) > SPEC['row_tol']}
        for v in bad: it.fail('xview', 'ROW %s %s=%d vs median %d across views (tol %d)' % (v, k, vals[v], m, SPEC['row_tol']), [(v, vals[v])])
        row(k, vals, bad)
    # eyes
    ev = {v: Ps[v]['eyes']['list'] for v in vs}
    row('eyes n', {v: len(ev[v]) for v in vs}, {v for v in vs if len(ev[v]) != SPEC['eyes_expected'].get(v, len(ev[v]))})
    rel = {}
    for v in vs:
        if ev[v]:
            e = max(ev[v], key=lambda e: e['n'])  # near/main eye
            rel[v] = dict(y=e['y0'] - Ps[v]['crown'], dx=round(e['x0'] - Ps[v]['mid'], 1), wh='%dx%d' % (e['w'], e['h']),
                          cl=[(x - e['x0'], y - e['y0']) for x, y in e['catch']], iris=e['iris'], ncl=[len(x['catch']) for x in ev[v]])
    if rel:
        m = med([r['y'] for r in rel.values()]); bad = {v for v in rel if abs(rel[v]['y'] - m) > SPEC['eye_row_x']}
        for v in bad: it.fail('xview', 'EYES %s eye top %d rows below the crown vs median %d (tol %d)' % (v, rel[v]['y'], m, SPEC['eye_row_x']), [(v, 0)])
        row('eye y-crown', {v: r['y'] for v, r in rel.items()}, bad)
        row('eye x-mid', {v: r['dx'] for v, r in rel.items()})
        ref = rel.get('S') or max(rel.values(), key=lambda r: sum(r['ncl']))  # S (front) is the eye reference
        mw = ref['wh']
        badw = {v for v in rel if rel[v]['wh'] != mw}
        for v in badw: it.fail('xview', 'EYES %s main eye size %s vs %s in the reference view' % (v, rel[v]['wh'], mw), [(v, 0)])
        row('eye WxH', {v: r['wh'] for v, r in rel.items()}, badw)
        mc = Counter(str(r['ncl']) for r in rel.values()).most_common(1)[0][0]
        clp = str(ref['cl'])
        badc = {v for v in rel if str(rel[v]['cl']) != clp or not rel[v]['cl']}
        for v in badc: it.fail('xview', 'EYES %s catchlights %s (per eye %s) at %s rel. eye box vs %s in the reference view: same count + position everywhere' % (
            v, sum(rel[v]['ncl']), rel[v]['ncl'], rel[v]['cl'], clp), [(v, 0)])
        row('catchlights', {v: '%s@%s' % (r['ncl'], r['cl']) for v, r in rel.items()}, badc)
        mi = ref['iris']
        badi = {v for v in rel if rel[v]['iris'] != mi}
        for v in badi: it.fail('xview', 'EYES %s iris colours %s vs %s' % (v, rel[v]['iris'], mi), [(v, 0)])
        row('iris', {v: r['iris'] for v, r in rel.items()}, badi)
    bw = {v: Ps[v]['bow'] for v in vs if Ps[v]['bow']}
    row('bow off/asym', {v: '%+.1f/%+.0f' % (b['off'], b['asym']) for v, b in bw.items()},
        {v for v in bw if v in ('S', 'N') and abs(bw[v]['asym']) > SPEC['bow_sym']})
    row('bow WxH', {v: '%dx%d' % (b['x1'] - b['x0'] + 1, b['y1'] - b['y0'] + 1) for v, b in bw.items()})
    # palette usage per material: chars used + share
    mats = sorted({m for v in vs for m in Ps[v]['usage']} - {'?'})
    for mt in mats:
        vals = {}; sets = {}
        for v in vs:
            c = Ps[v]['usage'].get(mt)
            if not c: continue
            tot = sum(c.values()); sets[v] = {k for k, n in c.items() if n / tot >= 0.03}
            vals[v] = ''.join('%s%d' % (k, round(100 * n / tot)) for k, n in c.most_common(5))
        if not sets: continue
        common = Counter(k for s in sets.values() for k in s); maj = {k for k, n in common.items() if n > len(sets) / 2}
        bad = {v for v in sets if (sets[v] - maj) or (maj - sets[v] and len(sets) >= 3)}
        for v in bad:
            ex, mi = ''.join(sorted(sets[v] - maj)), ''.join(sorted(maj - sets[v]))
            it.warn('xview', 'COLOR %s %s uses %s%s vs the other views (>=3%% share chars)' % (v, mt, ('extra ' + ex) if ex else '', (' lacks ' + mi) if mi else ''), [(v, 0)])
        row('use ' + mt + ' %', vals, bad)
    w0 = [max(len(r[i]) for r in T) for i in range(len(hdr))]
    data['xview_table'] = T
    it.table = '\n'.join('  '.join(c.ljust(w0[i]) for i, c in enumerate(r)) for r in T)
    items.append(it)
    return it


def do_stamps(sdir, mdir, pal, items, data):
    _, ms = find_masters(mdir); files = sorted(glob.glob(sdir + '/*.txt')); neutral = {}
    for p in files:
        v = view_of(os.path.basename(p)[:-4])
        if 'neutral' in os.path.basename(p) and v: neutral[v] = p
    for p in files:
        b = os.path.basename(p); v = view_of(b[:-4]); st, meta = read(p); it = Item('stamp_' + b[:-4], p, st); items.append(it)
        M = master_grid(ms, v) if v else None
        if M: [it.fail('palette', x, pts_of(x)) for x in CC.stamp_check(p, M, pal)]
        else: [it.fail('palette', x) for x in CC.off_palette(st, pal)]
        cols = None
        if M: cols = {c for r in M for c in r} | ({c for r in read(neutral[v])[0] for c in r} if v in neutral else set())
        if cols: (lambda new: new and it.fail('outline', 'NEWCOL stamp colours %s not in the master/neutral' % ''.join(sorted(new))))({c for r in st for c in r} - cols - {'.'})
        if v in neutral and neutral[v] != p:
            nt = read(neutral[v])[0]
            if (len(nt), len(nt[0])) != (len(st), len(st[0])):
                it.fail('head', 'SIZE stamp %dx%d vs neutral %dx%d: stamps of a view must share the canvas' % (len(st[0]), len(st), len(nt[0]), len(nt))); continue
            s4 = sorted(outline_pts(st, pal)['S4'] - outline_pts(nt, pal)['S4'])
            if s4: it.fail('outline', 'S4 %d new orphan pixels vs the neutral stamp: %s' % (len(s4), s4[:10]), s4)
            skc = set(pal.ramps.get('skin', [])) - pal.univ  # face rect = skin bbox of the neutral (+1)
            sp = [(x, y) for y, r in enumerate(nt) for x, c in enumerate(r) if c in skc]
            fr = (min(p[0] for p in sp) - 1, min(p[1] for p in sp) - 1, max(p[0] for p in sp) + 1, max(p[1] for p in sp) + 1) if sp else (0, 0, len(nt[0]) - 1, len(nt) - 1)
            x0, y0, x1, y1 = fr; d = [(x, y) for y in range(len(st)) for x in range(len(st[0])) if st[y][x] != nt[y][x] and not (x0 <= x <= x1 and y0 <= y <= y1)]
            if d: it.fail('head', 'HEAD %d px outside the face rect (%d,%d)-(%d,%d) differ from the neutral stamp at %s: the expression delta must stay in the face' % (len(d), x0, y0, x1, y1, d[:8]), d)
            hl = 'W' if 'W' in pal.colors else None
            ca = sorted((x, y) for y, r in enumerate(st) for x, c in enumerate(r) if c == hl)
            cb = sorted((x, y) for y, r in enumerate(nt) for x, c in enumerate(r) if c == hl)
            if ca and ca != cb and not re.search(r'blink|closed|joy|wince|squint', b):
                it.fail('eyes', 'EYES catchlight/white pixels %s vs neutral %s: open-eye expressions keep the neutral catchlights' % (ca[:8], cb[:8]), ca + cb)


def clip_frames(cdir):
    fj = json.load(open(cdir + '/frames.json')) if os.path.exists(cdir + '/frames.json') else {}
    fs = sorted(glob.glob(cdir + '/c[0-9][0-9].txt')) or sorted(glob.glob(cdir + '/f[0-9][0-9].txt'))
    return fj, fs


def do_clip(cdir, a, pal, items, data, ms):
    fj, fs = clip_frames(cdir)
    if not fs: return None
    view = a.get('view') or fj.get('dir') or fj.get('view') or view_of(os.path.basename(cdir.rstrip('/')))
    M = read(a['master'])[0] if a.get('master') else master_grid(ms, view)
    if M is None: print('no master for view %s (%s)' % (view, cdir)); return None
    PM = parts(M, pal); fr = fj.get('frames', [])
    rest_l = [int(x) for x in a['rest'].split(',')] if a.get('rest') else None
    con_l = [int(x) for x in a['contacts'].split(',')] if a.get('contacts') else None
    G, keys, stamps, Ps, rests, cons, airs, fdn = [], [], [], [], [], [], [], []
    name = os.path.basename(cdir.rstrip('/'))
    for i, p in enumerate(fs):
        g, meta = read(p); f = fr[i] if i < len(fr) else {}; key = f.get('key', 'f%02d' % i)
        rest = (i in rest_l) if rest_l is not None else (bool(f['rest']) if 'rest' in f else bool('rest' in meta or re.search(r'idle|contact|stand|rest|neutral', key)))  # a96: explicit frames.json rest wins
        con = (i in con_l) if con_l is not None else bool(f.get('contact') or 'contact' in meta or 'contact' in key)
        air = bool(f.get('air') or 'air' in meta)
        sp = f.get('stamp') or a.get('stamp'); st = read(sp)[0] if sp and os.path.exists(sp) else None
        rects = [tuple(r) for r in f.get('deliberate', [])] + ([tuple(meta['shift'][:4])] if 'shift' in meta else [])
        ov = bool(f.get('overlap') or 'overlap' in meta)
        it = Item('%s_%s' % (name, os.path.basename(p)[:-4]), p, g, M); items.append(it); P = parts(g, pal)
        if P is None: it.fail('outline', 'EMPTY frame'); continue
        chk_palette(it, g, pal, M, st or head_window(M, PM)[0])
        cols = {c for r in M for c in r} | ({c for r in st for c in r} if st else set())
        chk_outline(it, g, pal, cols, P, M)
        Mx = ref_with_stamp(M, sp); PMx = PM if Mx is M else parts(Mx, pal); it.ref = Mx  # a96: expression-aware reference
        chk_eyes_single(it, g, pal, P, view, single=False)
        chk_frame_vs_ref(it, g, pal, P, Mx, PMx, st, rest, ov, rects, view)
        chk_layered(it, g, sp)   # h96
        G.append(g); fdn.append(f.get('feet_down')); keys.append(key); stamps.append(st or head_window(M, PM)[0]); Ps.append(P); rests.append(rest); cons.append(con); airs.append(air)
        it.metrics.update(view=view, key=key, rest=rest, contact=con, rows=P['rows'], head=P['head'],
                          bow_off=P['bow']['off'] if P['bow'] else None, eyes=[(e['x0'], e['y0'], e['catch']) for e in P['eyes']['list']])
    # continuity
    it = Item('%s_continuity' % name, cdir, G[0] if G else None, M); items.append(it)
    loop = not a.get('noloop') and fj.get('loop', True)
    if len(G) > 1:
        same = all(len(s) == len(stamps[0]) and len(s[0]) == len(stamps[0][0]) for s in stamps)
        txt, cd = CC.clip_report(G, pal, stamps if same else None, keys, loop, head_px=SPEC['head_px'] + 2, name=name)
        for f in cd['flags']:
            k = re.match(r'(\S+?)(?:->(\S+))? ', f); it.fail('continuity', 'FLICKER ' + f, [])
        soc = set(pal.ramps.get('socks', [])) - pal.univ
        prs = [(i, i + 1) for i in range(len(G) - 1)] + ([(len(G) - 1, 0)] if loop and len(G) > 2 else [])
        for i, j in prs:
            ha = Counter(c for r in G[i] for c in r if c in soc); hb = Counter(c for r in G[j] for c in r if c in soc)
            na, nb = sum(ha.values()), sum(hb.values())
            if na and nb and abs(na - nb) / max(na, nb) <= 0.25 and CC.l1(ha, hb) > 0.2:
                it.fail('continuity', 'FLICKER %s->%s socks colours change without a shape change: %s -> %s' % (keys[i], keys[j], dict(ha), dict(hb)))
    sole = fj['pivot'][1] if fj.get('pivot') else PM['sole']
    for i, P in enumerate(Ps):
        if not airs[i] and P['sole'] != sole:
            it.fail('continuity', 'FEET %s lowest row %d != sole/pivot row %d (feet must stand on the pivot row)' % (keys[i], P['sole'], sole),
                    [(x, P['sole']) for x in range(0, P['W'], 4)])
        if cons[i]:
            down = [C for C in P['boots'] if C['bbox'][3] >= PM['sole'] - 1]
            need = min(2, len([C for C in PM['boots'] if C['bbox'][3] >= PM['sole'] - 1])) if not a.get('contacts') else 2
            if fdn[i] is not None and not a.get('contacts'): need = min(need, fdn[i])  # a96: guide feet on the ground (walk contact = 1)
            if len(down) < need and len(P['boots']) >= 2:
                it.fail('continuity', 'FEET %s contact frame: only %d boot(s) on the ground row %d (need %d)' % (keys[i], len(down), PM['sole'], need))
        if rests[i] and P['obi_cx'] is not None and PM['obi_cx'] is not None and abs(P['obi_cx'] - PM['obi_cx']) > SPEC['pivot_drift']:
            it.fail('continuity', 'PIVOT %s body centre (obi) x %.1f vs master %.1f: drift %+.1fpx' % (keys[i], P['obi_cx'], PM['obi_cx'], P['obi_cx'] - PM['obi_cx']))
    data.setdefault('clips', {})[name] = dict(view=view, frames=len(G), rest=[keys[i] for i in range(len(G)) if rests[i]])
    return dict(view=view, name=name, P=[(keys[i], Ps[i]) for i in range(len(Ps)) if rests[i]] or [(keys[0], Ps[0])] if Ps else [], PM=PM)


def do_all(roots, a, pal, items, data, ms):
    dirs = []
    for r in roots:
        if clip_frames(r)[1]: dirs.append(r)
        else: dirs += sorted(d for d in glob.glob(r + '/*/') if clip_frames(d)[1])
    res = [x for x in (do_clip(d.rstrip('/'), a, pal, items, data, ms) for d in dirs) if x]
    it = Item('all_clips'); items.append(it); T = [['clip', 'view', 'head WxH', 'eye y', 'bow off', 'sole']]
    for r in res:
        for k, P in r['P'][:1]:
            T.append([r['name'], r['view'], '%dx%d' % (P['head']['w'], P['head']['h']), str(P['eye']), str(P['bow']['off'] if P['bow'] else '-'), str(P['sole'])])
            M = r['PM']
            if (P['head']['w'], P['head']['h']) != (M['head']['w'], M['head']['h']):
                it.fail('xview', 'CLIPS %s head %dx%d vs %s master %dx%d' % (r['name'], P['head']['w'], P['head']['h'], r['view'], M['head']['w'], M['head']['h']))
    byv = {}
    for r in res:
        for k, P in r['P']: byv.setdefault(r['view'], []).append((r['name'], k, P['eye'], P['crown']))
    for v, L in byv.items():
        ys = Counter((e - c) if e is not None else None for _, _, e, c in L)
        if len(ys) > 1: it.fail('xview', 'CLIPS view %s eye-to-crown distance differs across clips: %s' % (v, dict(ys)))
    w0 = [max(len(x[i]) for x in T) for i in range(len(T[0]))]
    it.table = '\n'.join('  '.join(c.ljust(w0[i]) for i, c in enumerate(x)) for x in T); data['clips_table'] = T


# ---------------------------------------------------------------- overlays
def render(g, pal, s):
    from PIL import Image
    H, W = len(g), len(g[0]); im = Image.new('RGB', (W, H), (110, 110, 110)); px = im.load()
    for y, r in enumerate(g):
        for x, c in enumerate(r):
            if c != '.': px[x, y] = pal.rgb.get(c, (255, 0, 255))
    return im.resize((W * s, H * s), Image.NEAREST)


def bbox_union(gs, pad=3):
    pts = [(x, y) for g in gs for y, r in enumerate(g) for x, c in enumerate(r) if c != '.']
    if not pts: return 0, 0, len(gs[0][0]) - 1, len(gs[0]) - 1
    return (max(0, min(p[0] for p in pts) - pad), max(0, min(p[1] for p in pts) - pad),
            max(p[0] for p in pts) + pad, max(p[1] for p in pts) + pad)


def overlay(it, check, iss, pal, path):
    from PIL import Image, ImageDraw
    if getattr(it, 'strip', None):  # xview: strip of views, flagged views boxed
        vs = [v for v in VIEWS if v in it.strip]; gs = [it.strip[v] for v in vs]; x0, y0, x1, y1 = bbox_union(gs)
        cw, ch = x1 - x0 + 1, y1 - y0 + 1; s = max(1, min(6, 800 // (cw * len(vs)), 800 // ch))
        im = Image.new('RGB', (cw * s * len(vs), ch * s + 12), (40, 40, 40)); d = ImageDraw.Draw(im)
        bad = {p[0]: p[1] for i in iss for p in i['pts'] if isinstance(p[0], str)}
        for k, v in enumerate(vs):
            im.paste(render([r[x0:x1 + 1] for r in it.strip[v][y0:y1 + 1]], pal, s), (k * cw * s, 12))
            d.text((k * cw * s + 2, 0), v, fill=(255, 255, 255))
            if v in bad:
                d.rectangle([k * cw * s, 12, (k + 1) * cw * s - 1, 12 + ch * s - 1], outline=(255, 40, 40), width=2)
                if bad[v]: yy = 12 + (bad[v] - y0) * s; d.line([k * cw * s, yy, (k + 1) * cw * s - 1, yy], fill=(0, 255, 255))
        im.save(path); return
    if it.grid is None: return
    gs = [it.grid] + ([it.ref] if it.ref else []); x0, y0, x1, y1 = bbox_union(gs)
    cw, ch = x1 - x0 + 1, y1 - y0 + 1; n = len(gs); s = max(1, min(6, 800 // (cw * n), 788 // ch))
    im = Image.new('RGB', (cw * s * n, ch * s + 12), (40, 40, 40)); d = ImageDraw.Draw(im)
    for k, g in enumerate(gs): im.paste(render([r[x0:x1 + 1] for r in g[y0:y1 + 1]], pal, s), (k * cw * s, 12))
    d.text((2, 0), '%s %s' % (it.name, check), fill=(255, 255, 255))
    if n > 1: d.text((cw * s + 2, 0), 'ref', fill=(255, 255, 255))
    for i in iss:
        for p in i['pts']:
            if isinstance(p[0], str): continue
            X, Y = (p[0] - x0) * s, (p[1] - y0) * s + 12
            if 0 <= X < cw * s and 12 <= Y < im.size[1]:
                for k in range(n): d.rectangle([X + k * cw * s, Y, X + k * cw * s + s - 1, Y + s - 1], outline=(255, 40, 40) if k == 0 else (0, 255, 255))
    im.save(path)


# ---------------------------------------------------------------- report
def report(items, data, out, pal, quiet=False, ov=True, mode=''):
    ok = all(i.ok for i in items); L = ['QC GATE %s: %s  (%d items, %d failing; palette %s)' % (mode, 'PASS' if ok else 'FAIL', len(items),
                                                                                              sum(not i.ok for i in items), os.path.relpath(pal.path, V2))]
    if eyehook() is None: L.append('  (eyes: built-in stub; m96/tools/eyecheck.py qc_hook not found)')
    J = dict(verdict='PASS' if ok else 'FAIL', mode=mode, items=[], **data)
    if out: os.makedirs(out, exist_ok=True)
    for it in items:
        f = [i for i in it.iss if i['sev'] == 'FAIL']; w = [i for i in it.iss if i['sev'] == 'WARN']
        cnt = Counter(i['check'] for i in f)
        L.append('%s %s%s' % ('PASS' if it.ok else 'FAIL', it.name, ('  [' + ' '.join('%s:%d' % kv for kv in sorted(cnt.items())) + ']') if cnt else ''))
        for i in f: L.append('   - [%s] %s' % (i['check'], i['msg'][:400]))
        if not quiet:
            for i in w: L.append('   ~ [%s] %s' % (i['check'], i['msg'][:200]))
        if getattr(it, 'table', None) and not quiet: L.append(it.table)
        ovs = []
        if out and ov and not it.ok:
            for ck in sorted(cnt):
                p = os.path.join(out, 'ov_%s_%s.png' % (re.sub(r'[^\w]+', '_', it.name), ck))
                try: overlay(it, ck, [i for i in f if i['check'] == ck], pal, p); ovs.append(os.path.basename(p))
                except Exception as e: L.append('   (overlay failed: %s)' % e)
        J['items'].append(dict(name=it.name, path=it.path, verdict='PASS' if it.ok else 'FAIL', overlays=ovs, metrics=it.metrics,
                               issues=[{k: v for k, v in i.items() if k != 'pts'} for i in it.iss]))
    txt = '\n'.join(L) + '\n'
    if out:
        open(out + '/report.txt', 'w').write(txt)
        json.dump(J, open(out + '/report.json', 'w'), indent=1, default=str)
    return ok, txt, J


def fix_lines(items, skip=()):
    return ['QC %s [%s] %s' % (it.name, i['check'], i['msg']) for it in items for i in it.iss if i['sev'] == 'FAIL' and i['check'] not in skip]


# ---------------------------------------------------------------- hooks
def frame_fixes(path, view, master=None, stamp=None, pal=None, rest=False, skip=(), mdir=None):
    pal = CC.load(pal or DEF_PAL); g, meta = read(path)
    M = read(master)[0] if master else master_grid(find_masters(mdir)[1], view)
    st = read(stamp)[0] if stamp and os.path.exists(stamp) else None
    M = ref_with_stamp(M, stamp)  # a96
    it = Item(os.path.basename(path)[:-4], path, g, M); P = parts(g, pal)
    if P is None: return ['QC EMPTY frame']
    PM = parts(M, pal) if M else None
    chk_palette(it, g, pal, M, (st or head_window(M, PM)[0]) if M else None); chk_outline(it, g, pal, ({c for r in M for c in r} | ({c for r in st for c in r} if st else set())) if M else None, P, M)
    chk_eyes_single(it, g, pal, P, view, single=M is None)
    if M:
        rects = [tuple(meta['shift'][:4])] if 'shift' in meta else []
        chk_frame_vs_ref(it, g, pal, P, M, PM, st, rest or 'rest' in meta, 'overlap' in meta, rects, view)
        chk_layered(it, g, stamp)   # h96
    return fix_lines([it], skip)


def validate_hook(path, fj, stamp, master=None):
    """ff_redraw.validate one-liner: fx += qc_gate.validate_hook(path, fj, stamp, master). Skips the palette/outline
    lines lint_style already reports; returns [] if the frame file is missing."""
    if not os.path.exists(path): return []
    m = re.search(r'f(\d+)\.txt$', path); i = int(m.group(1)) if m else -1
    fr = fj.get('frames', []); f = fr[i] if 0 <= i < len(fr) else {}
    rest = bool(f['rest']) if 'rest' in f else bool(re.search(r'idle|contact|stand|rest|neutral', f.get('key', '')))  # a96: explicit rest wins
    return frame_fixes(path, fj.get('dir') or fj.get('view'), master, f.get('stamp') or stamp, fj.get('palette'), rest, skip=('palette', 'outline'))


# ---------------------------------------------------------------- cli
def main(argv):
    a = {}; pos = []; it = iter(argv)
    flags = {'--json', '--quiet', '--no-overlay', '--noloop', '--rest-frame'}
    for x in it:
        if x in flags: a[x[2:].replace('-', '_')] = True
        elif x.startswith('--'): a[x[2:]] = next(it)
        else: pos.append(x)
    if not pos: print(__doc__); return 2
    mode = pos.pop(0); pal = CC.load(a.get('palette') or DEF_PAL); LS.set_palette(pal.path)
    items, data = [], {}; mdir = a.get('masters')
    if mode == 'frame':
        fx = frame_fixes(pos[0], a.get('view') or view_of(pos[0]), a.get('master'), a.get('stamp'), pal.path, bool(a.get('rest_frame')), mdir=mdir)
        print('PASS' if not fx else 'FAIL'); [print(' -', f) for f in fx]; return 1 if fx else 0
    name = os.path.basename((pos[0] if pos else (mdir or 'masters')).rstrip('/')) or mode
    if mode == 'masters': do_masters(pos[0] if pos else mdir, pal, items, data)
    elif mode == 'stamps': do_stamps(pos[0], mdir, pal, items, data)
    elif mode in ('clip', 'all'):
        _, ms = find_masters(mdir)
        if mode == 'clip': do_clip(pos[0].rstrip('/'), a, pal, items, data, ms)
        else: do_all([p.rstrip('/') for p in pos], a, pal, items, data, ms)
    else: print(__doc__); return 2
    out = a.get('out', V2 + '/qc/out/%s_%s' % (mode, name)); out = None if out == '-' else out
    ok, txt, J = report(items, data, out, pal, a.get('quiet'), not a.get('no_overlay'), mode)
    print(json.dumps(J, indent=1, default=str) if a.get('json') else txt, end='')
    if out and not a.get('json'): print('-> %s/report.txt, report.json, %d overlays' % (out, sum(len(i['overlays']) for i in J['items'])))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
