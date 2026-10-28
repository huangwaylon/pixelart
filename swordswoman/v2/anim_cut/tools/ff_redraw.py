#!/usr/bin/env python3
"""ff_redraw.py: frame-by-frame redraw harness (Opus pixel artist per frame, guided by 3D renders).

  ff_redraw.py prep     ACT DIR --guides GDIR [--cell 64 64] [--pivot 32 61] [--gpivot 48 88] [--gscale 4] [--ms 100,100,..]
                        [--poses v2/pose/poses.json] [--stamps v2/masters/heads] [--root DIR]
     --pivot X Y = the master's sole row (Y) / feet centre, --cell W H = master cell size (new masters: v2/prop/).
     --poses fills per-frame expression/smear from poses[ACT].keys[KEY]; --stamps sets per-frame 'stamp' = <DIR>_<expr>.txt
     (fallback <DIR>_neutral.txt; W/SW/NW mirrored from E/SE/NE). GDIR/frames.json (guide JSON) adds expression/smear and
     the blade arc (blade_pommel/tip -> cell px) to the prompt; no blade data = unarmed, no arc lines.
  ff_redraw.py draw     ACT DIR --master M.txt --stamp S.txt [--frames 0,1] [--jobs N] [--accounts a,b,c] [--key0] [--retries 2]
  ff_redraw.py assemble ACT DIR [--stamp S.txt]
  ff_redraw.py all      ACT DIR --guides GDIR --master M.txt --stamp S.txt [...]      (prep + draw --key0 + assemble)
  ff_redraw.py stamp    MASTER.txt OUT.txt --rows Y0 Y1 [--pivot X Y]                  (cut a head stamp from a master)
  --palette P.json (any command; v2/final/palette.json = char -> hex -> material): LOCKED palette. prep stores it in
     frames.json (draw/assemble reuse it when --palette is not given); the prompt gets the legend with material names +
     per-material ramps + a colour-lock paragraph; validate rejects every off-palette pixel (PAL) and, with --master, adds
     the MAT ramp-swap lint vs the master (colorcheck.py); draw first checks every expression stamp's colours against the
     master face (stamp_check.txt); assemble [--master M] writes colors.txt/json (clip flicker report). No --palette and no
     palette in frames.json = old behaviour.

ANIMATE96 options (prep stores them in frames.json 'opts'; draw/assemble reuse them; none given = old behaviour):
  --expr-alias a=b,c=d   expression name aliases before the stamp lookup (e.g. smile=cheerful,squash=blink_closed,hurt=pain);
                         a missing stamp now prints a WARN instead of silently using neutral
  --head-lock [--head-ref snap|world] [--head-bob N] [--head-bias BX BY]  (bias default: ROOT/idle_<DIR>/frames.json head_bias
                         when prepping a non-idle clip, else the median head-silhouette fit of this clip)  (head-bob: y = stamp row + rig head height scaled to 0..N px)
                          LOCKED HEAD (world = head offset in rig space, not relative to the snapped feet): per-frame stamp anchor = stamp origin + guide head offset (guide head_centre joint,
                         bias from a head-silhouette fit vs --master); fNN.txt is pre-seeded with the stamp at the anchor,
                         the artist draws only the body, and the stamp is re-pasted after every artist pass (never redrawn)
  --qc gate,eye          extra validation: gate = v2/qc/qc_gate.validate_hook (head/bow/sections/eyes fix list, includes the
                         eyecheck hook), eye = v2/m96/tools/eyecheck.qc_hook directly. Retry prompts receive these fix lines.
  --lint-rel             lint relative to the master: O3 jaggies dropped (WARN in the gate), R1 interior-K tolerated up to
                         the master's own R1 count + 4
  --rules FILE           replace the STYLE_GUIDE 5/6/10 prompt rules with FILE (e.g. v2/animate96/RULES96.txt)
  --rest-keys k1,k2      frames whose key is listed get rest=true (all others rest=false) for the gate's row checks
  prep also writes per frame: feet_down (= separate opaque runs on the guide's pivot row; gate contact rule).

Work dir: v2/anim_cut/ff/<ACT>_<DIR>/
  guide:  gNN.txt (guide char-map at 1x in the target cell, pk palette by material), gNN_1x.png, gNN_4x.png, gNN_sil.png
  frames: fNN.txt (artist output, validated), pNN.txt (prompt), logNN.txt (artist replies), lintNN.txt
  out:    sheet.png (guide|frame pairs, <=1000px), <ACT>_<DIR>.gif (6x on #6e6e6e), lint.txt, frames.json (ms, key, air)
Guides: GDIR/fNN_matid.png (flat material IDs, gscale x, feet pivot gpivot at 1x; hy3d keys_parts or hy3d/frames).
A frame is airborne if its key name contains apex/rise/fall/air/launch (then '; air' meta skips the feet check).
Artist accounts run concurrently (tested OK up to 18 parallel claude-as calls; see NOTES.md).
"""
import json, os, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import lint_style as LS
ROOT = os.path.abspath(os.path.join(HERE, '..'))
V2 = os.path.abspath(os.path.join(ROOT, '..'))
GUIDE_MD = os.path.join(V2, 'style', 'STYLE_GUIDE.md')
RGB = {k: tuple(int(v[0][j:j + 2], 16) for j in (1, 3, 5)) for k, v in LS.PAL.items()}
BG = (0x6e, 0x6e, 0x6e)
IOU_MIN = 0.5  # min body-silhouette IoU between drawn frame and guide
AIR = ('apex', 'rise', 'fall', 'air', 'launch', 'hang')


FFROOT = os.environ.get('FF_ROOT') or os.path.join(ROOT, 'ff')
OPTS = {}  # ANIMATE96 options (expr_alias, head_lock, qc, lint_rel, rules, rest_keys); stored in frames.json 'opts'


def paste_stamp(g, stamp_path, at):
    """copy every non-'.' stamp char to (at+c, at+r) of grid g (list of str); returns (grid, n changed)."""
    st = LS.read(stamp_path)[0]; G = [list(r) for r in g]; n = 0
    for r, row in enumerate(st):
        for c, ch in enumerate(row):
            X, Y = at[0] + c, at[1] + r
            if ch != '.' and 0 <= Y < len(G) and 0 <= X < len(G[0]) and G[Y][X] != ch: G[Y][X] = ch; n += 1
    return [''.join(r) for r in G], n


def head_fit(g, master, y_chin):
    """(dx, dy) that best overlays the master head silhouette (rows < y_chin) on the guide's top rows (IoU)."""
    M = LS.read(master)[0]
    Mm = np.array([[c != '.' for c in r] for r in M]); Mm[y_chin:] = False
    a = np.array([[c != '.' for c in r] for r in g]); best = None
    for dy in range(-16, 17):
        for dx in range(-16, 17):
            sh = np.roll(np.roll(Mm, dy, 0), dx, 1); rows = sh.any(1).nonzero()[0]
            if not len(rows): continue
            ga = a.copy(); ga[rows.max() + 1:] = False; iou = (sh & ga).sum() / max(1, (sh | ga).sum())
            if best is None or iou > best[0]: best = (iou, dx, dy)
    return best


def wd(act, d):
    p = os.path.join(FFROOT, '%s_%s' % (act, d)); os.makedirs(p, exist_ok=True); return p


def opt(a, k, n=1, default=None, cast=str):
    if k not in a: return default
    i = a.index(k); v = [cast(x) for x in a[i + 1:i + 1 + n]]; del a[i:i + 1 + n]
    return v[0] if n == 1 else v


def write_cm(path, g, meta=()):
    open(path, 'w').write(''.join('; %s\n' % m for m in meta) + '\n'.join(g) + '\n')


def render(g, s=1, bg=None):
    h, w = len(g), len(g[0]); im = Image.new('RGBA', (w, h), (bg + (255,)) if bg else (0, 0, 0, 0)); px = im.load()
    for y, r in enumerate(g):
        for x, c in enumerate(r):
            if c in RGB: px[x, y] = RGB[c] + (255,)
    return im.resize((w * s, h * s), Image.NEAREST)


# ---------------- prep ----------------
PALOBJ = None  # colorcheck.Palette when --palette is used (or frames.json has 'palette')


def use_palette(path):
    global PALOBJ, RGB
    PALOBJ = LS.set_palette(path); RGB = dict(PALOBJ.rgb); return PALOBJ


def nearest_char(rgb, chars='KWsSLHhEeRrdIink'):
    if PALOBJ is not None:
        cs = ''.join(c for c in chars if c in RGB); chars = cs if len(cs) >= 8 else ''.join(RGB)
    best = min(chars, key=lambda c: sum((a - b) ** 2 for a, b in zip(rgb, RGB[c])))
    return best


def guide_from_matid(path, cell, pivot, gpivot, gs, snap_feet=True, ret_off=False):
    im = np.array(Image.open(path).convert('RGBA')); H, W = im.shape[0] // gs, im.shape[1] // gs
    g = [['.'] * cell[0] for _ in range(cell[1])]; cache = {}
    ox, oy = gpivot[0] - pivot[0], gpivot[1] - pivot[1]
    if snap_feet:  # standing frame: put the lowest opaque 1x row exactly on the pivot row
        rows = np.where((im[..., 3] > 128).reshape(H, gs, W, gs).sum(axis=(1, 3)).max(axis=1) * 2 >= gs * gs)[0]
        if len(rows): oy = int(rows.max()) - pivot[1]
    for y in range(cell[1]):
        for x in range(cell[0]):
            X, Y = x + ox, y + oy
            if not (0 <= X < W and 0 <= Y < H): continue
            blk = im[Y * gs:(Y + 1) * gs, X * gs:(X + 1) * gs].reshape(-1, 4)
            blk = blk[blk[:, 3] > 128]
            if len(blk) * 2 < gs * gs: continue
            cols, cnt = np.unique(blk[:, :3], axis=0, return_counts=True)
            c = tuple(int(v) for v in cols[cnt.argmax()])
            if c not in cache: cache[c] = nearest_char(c)
            g[y][x] = cache[c]
    g = [''.join(r) for r in g]
    return (g, (ox, oy)) if ret_off else g


IMPACT = ('impact', 'hit', 'strike')
CONTACT = ('contact', 'land', 'plant', 'touch')
MIRROR = {'W': 'E', 'SW': 'SE', 'NW': 'NE'}


def pose_key(poses, act, key):
    """poses.json key entry for act/key ('contact2' falls back to 'contact')."""
    ks = (poses or {}).get(act, {}).get('keys', {})
    return ks.get(key) or ks.get(re.sub(r'\d+$', '', key)) or {}


def resolve_stamp(sdir, view, expr, out, cw):
    """<sdir>/<view>_<expr>.txt, else <view>_neutral.txt; W/SW/NW = x-mirror of E/SE/NE (written to out/)."""
    src = MIRROR.get(view, view)
    for e in (expr, 'neutral'):
        p = os.path.join(sdir, '%s_%s.txt' % (src, e))
        if os.path.exists(p): break
    else:
        return None
    p = os.path.abspath(p)
    if src == view: return p
    g, meta = LS.read(p); w = max(map(len, g)); g = [r.ljust(w, '.')[::-1] for r in g]
    m = ['view %s (mirror of %s)' % (view, os.path.basename(p))]
    if 'origin' in meta: m.insert(0, 'origin %d %d' % (cw - meta['origin'][0] - w, meta['origin'][1]))
    q = os.path.join(out, 'stamp_%s_%s.txt' % (view, e)); write_cm(q, g, m); return q


def prep(act, d, gdir, cell=(64, 64), pivot=(32, 61), gpivot=(48, 88), gs=4, ms=None, poses=None, stamps=None):
    out = wd(act, d); keys = []
    kj = os.path.join(gdir, 'keys.json')
    kjd = json.load(open(kj)) if os.path.exists(kj) else {}
    keys = kjd.get('keys', []); ms = ms or kjd.get('ms')
    gj = os.path.join(gdir, 'frames.json')  # optional guide JSON (render meta: expression, smear, blade_pommel/tip)
    gjf = json.load(open(gj)).get('frames', []) if os.path.exists(gj) else []
    pz = json.load(open(poses)) if poses else None
    files = sorted(f for f in os.listdir(gdir) if re.match(r'f\d+_matid\.png$', f))
    frames = []; prev_expr = 'neutral'; hdr_bias = None
    for i, f in enumerate(files):
        key = keys[i] if i < len(keys) else 'f%02d' % i
        air = any(a in key for a in AIR)
        if i < len(gjf) and 'air' in gjf[i]: air = bool(gjf[i]['air'])  # guide JSON knows (idle 'rise' is not airborne)
        g, (ox, oy) = guide_from_matid(os.path.join(gdir, f), cell, pivot, gpivot, gs, not air, ret_off=True)
        write_cm(os.path.join(out, 'g%02d.txt' % i), g, ['pivot %d %d' % tuple(pivot)] + (['air'] if air else []))
        render(g, 1).save(os.path.join(out, 'g%02d_1x.png' % i))
        render(g, 4, BG).save(os.path.join(out, 'g%02d_4x.png' % i))
        sil = [''.join('K' if c != '.' else '.' for c in r) for r in g]
        render(sil, 4, (255, 255, 255)).save(os.path.join(out, 'g%02d_sil.png' % i))
        fr = {'i': i, 'key': key, 'ms': (ms[i] if ms and i < len(ms) else 100), 'air': air, 'src': os.path.abspath(os.path.join(gdir, f))}
        gf = gjf[i] if i < len(gjf) else {}; pk = pose_key(pz, act, key)
        if pz or gf:  # key intent (only when a poses file or guide JSON is available)
            ex = pk.get('expression') or gf.get('expression') or 'neutral'
            ex = prev_expr if ex == 'hold' else ex; prev_expr = ex
            ex = OPTS.get('expr_alias', {}).get(ex, ex)
            fr.update(expression=ex, smear=bool(pk.get('smear', gf.get('smear', False))),
                      impact=any(t in key for t in IMPACT), contact=any(t in key for t in CONTACT) and not air)
            if gf.get('blade_pommel') and gf.get('blade_tip') and gf.get('katana', True):  # guide 1x px -> cell px
                fr['blade'] = {k: [round(gf['blade_' + k][0] - ox, 1), round(gf['blade_' + k][1] - oy, 1)] for k in ('pommel', 'tip')}
            elif gf: fr['unarmed'] = True
            if stamps:
                st = resolve_stamp(stamps, d, ex, out, cell[0])
                if st and OPTS and d != 'N' and not os.path.basename(st).endswith('_%s.txt' % ex): print('WARN no stamp %s_%s in %s -> using %s' % (d, ex, stamps, os.path.basename(st)))
                if st: fr['stamp'] = st
                else: print('WARN no stamp %s_%s / %s_neutral in %s' % (d, ex, d, stamps))
        if OPTS:
            runs = re.findall(r'[^.]+', g[pivot[1]]) if 0 <= pivot[1] < len(g) else []
            fr['feet_down'] = min(2, len(runs)) if not air else 0
            if OPTS.get('rest_keys') is not None: fr['rest'] = key in OPTS['rest_keys']
            if OPTS.get('head_lock') and i < len(gjf) and gjf[i].get('head_centre'):
                hy0 = (gpivot[1] - pivot[1]) if OPTS['head_lock'] == 'world' else oy  # world: no feet snap (rig feet slide in idle)
                fr['_hc'] = [gjf[i]['head_centre'][0] - ox, gjf[i]['head_centre'][1] - hy0]
                fr['_hw'] = gjf[i]['head_centre'][1]  # rig-space head height (for --head-bob)
        frames.append(fr)
    if OPTS.get('head_lock') and OPTS.get('master'):  # LOCKED HEAD anchors: stamp origin + joint offset + fitted bias
        M = LS.read(OPTS['master'])[0]; bias = []
        for fr in frames:
            if '_hc' not in fr or 'stamp' not in fr: continue
            so = LS.read(fr['stamp'])[1].get('origin'); g = LS.read(os.path.join(out, 'g%02d.txt' % fr['i']))[0]
            iou, dx, dy = head_fit(g, OPTS['master'], so[1] + len(LS.read(fr['stamp'])[0]) - 1)
            fr['_fit'] = [dx, dy, round(float(iou), 3)]; bias.append((dx - fr['_hc'][0], dy - fr['_hc'][1]))
        ij = os.path.join(FFROOT, 'idle_%s' % d, 'frames.json')  # per-view constant (same camera/rig): reuse the idle fit
        hb0 = OPTS.get('head_bias') or (json.load(open(ij)).get('head_bias') if act != 'idle' and os.path.exists(ij) else None)
        if hb0: bias = [tuple(hb0)]
        if bias:
            bx, by = float(np.median([b[0] for b in bias])), float(np.median([b[1] for b in bias]))
            hdr_bias = [round(bx, 2), round(by, 2)]
            hw = [fr['_hw'] for fr in frames if '_hw' in fr]; hb = OPTS.get('head_bob')
            for fr in frames:
                if '_hc' not in fr or 'stamp' not in fr: continue
                so = LS.read(fr['stamp'])[1]['origin']
                fr['head_at'] = [so[0] + int(round(fr['_hc'][0] + bx)), so[1] + int(round(fr['_hc'][1] + by))]
                if hb is not None:  # y = master head row + rig head height normalised to 0..hb px (highest = master)
                    fr['head_at'][1] = so[1] + int(round((fr['_hw'] - min(hw)) / max(1e-6, max(hw) - min(hw)) * hb))
                fr['head_fit'] = fr.pop('_fit', None); fr.pop('_hc')
                h, _ = paste_stamp(['.' * cell[0]] * cell[1], fr['stamp'], fr['head_at'])
                write_cm(os.path.join(out, 'h%02d.txt' % fr['i']), h, ['pivot %d %d' % tuple(pivot)] + (['air'] if fr['air'] else []))
            print('head-lock bias %.2f %.2f; anchors %s' % (bx, by, [f.get('head_at') for f in frames]))
    for fr in frames: fr.pop('_hc', None); fr.pop('_hw', None)
    hdr = {'act': act, 'dir': d, 'cell': list(cell), 'pivot': list(pivot)}
    if hdr_bias: hdr['head_bias'] = hdr_bias
    if PALOBJ is not None: hdr['palette'] = PALOBJ.path
    if OPTS: hdr['opts'] = {k: v for k, v in OPTS.items() if k != 'master'}
    if os.path.exists(gj) and 'loop' in json.load(open(gj)): hdr['loop'] = bool(json.load(open(gj))['loop'])
    json.dump(dict(hdr, frames=frames),
              open(os.path.join(out, 'frames.json'), 'w'), indent=1)
    print('prep %s_%s: %d guide frames -> %s' % (act, d, len(frames), out))


# ---------------- prompt ----------------
def guide_rules():
    if OPTS.get('rules'): return open(OPTS['rules']).read().strip()
    t = open(GUIDE_MD).read()
    secs = []
    for h in ('## 5.', '## 6.', '## 10.'):
        i = t.find(h)
        if i >= 0:
            j = t.find('\n## ', i + 4); secs.append(t[i:j if j > 0 else None].strip())
    return '\n\n'.join(secs)


def legend():
    if PALOBJ is not None: return PALOBJ.legend()
    return '\n'.join('%s %s %s' % (k, v[0], v[1]) for k, v in LS.PAL.items())


def colour_lock(master):
    if PALOBJ is None: return ''
    return ('COLOUR LOCK (validated pixel by pixel; any char not in the legend is rejected): use ONLY the palette legend chars. '
            'Every material uses only its own ramp from MATERIAL RAMPS (outline char excepted); never borrow another material\'s '
            'colours (e.g. no bow/sleeve drawn with skin or boot colours, no dress shadow with the hair shadow, no hair sheen on the '
            'obi). Copy which ramp chars each material uses, and where, from the master %s; the face uses only the stamp\'s colours.\n' % master)


def lint_cmd(fpath, stamp, px, py, air, master):
    c = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/.venv/bin/python %s/lint_style.py %s --stamp %s --pivot %s %s%s' % (HERE, fpath, stamp, px, py, ' --air' if air else '')
    if PALOBJ is not None: c += ' --palette %s' % PALOBJ.path + (' --master %s' % master if master else '')
    return c


def prompt(act, d, fj, i, master, stamp, fixes=None):
    out = wd(act, d); fr = fj['frames'][i]; n = len(fj['frames']); cw, ch = fj['cell']; px, py = fj['pivot']
    fpath = os.path.join(out, 'f%02d.txt' % i)
    if fixes:
        pl = ('' if PALOBJ is None else '\n%sPALETTE (only these chars, \'.\' transparent):\n%s\nRe-check with: %s\n' % (
            colour_lock(master), legend(), lint_cmd(fpath, stamp, px, py, fr['air'], master)))
        return ('You are the Pokemon-style pixel artist. Your frame %s failed the automatic style lint. Edit that file in place '
                '(Read it first) and fix EVERY item, changing as little else as possible; keep the head stamp face exact%s.\n'
                'FIX LIST:\n- %s\n%s\nRules recap:\n%s\nReply <=30 words.' % (fpath, ' (the head is locked: never edit head pixels, they are re-pasted; fix the body around it)' if fr.get('head_at') else '', '\n- '.join(fixes), pl, guide_rules()[:2500]))
    def nb(j):
        j %= n; f = os.path.join(out, 'f%02d.txt' % j)
        return ('drawn frame %s' % f) if os.path.exists(f) else ('guide %s (not drawn yet)' % os.path.join(out, 'g%02d.txt' % j))
    g = open(os.path.join(out, 'g%02d.txt' % i)).read()
    src = fr['src']  # new frames.json: absolute; old ones: relative to the prep cwd (usually v2/anim_cut)
    if not os.path.isabs(src):
        src = next((q for q in (os.path.abspath(src), os.path.join(ROOT, src), os.path.join(V2, src)) if os.path.exists(q)), os.path.abspath(src))
    intent = ''
    if 'expression' in fr:
        t = []
        t.append("expression '%s' (the head stamp below is that expression; keep it exact)" % fr['expression'])
        if fr.get('smear'): t.append('SMEAR frame: stretch the moving limbs/blade into one long smear shape along the motion, no in-between detail')
        if fr.get('impact'): t.append('IMPACT frame: the hit pose at full extension, snappy and readable (hit-stop is added later)')
        if fr.get('contact'): t.append('CONTACT frame: the planted foot is on the pivot row, weight lands on it')
        b0, b1 = fr.get('blade'), fj['frames'][(i + 1) % n].get('blade')
        if b0:
            t.append('BLADE ARC (cell px): this frame pommel (%g,%g) tip (%g,%g)' % tuple(b0['pommel'] + b0['tip'])
                     + ('; next frame pommel (%g,%g) tip (%g,%g) - the swing travels this way' % tuple(b1['pommel'] + b1['tip']) if b1 and (i + 1 < n or fj.get('loop', True)) else '; this is the end of the swing'))
        intent = 'KEY INTENT: ' + '; '.join(t) + '.\n'
    unarmed = fr.get('unarmed')
    if fr.get('head_at'):
        headtxt = (f"- LOCKED HEAD (already placed): {fpath} is pre-seeded with the locked head stamp {stamp} (expression '{fr.get('expression', 'neutral')}') at its anchor "
                   f"(stamp origin {fr['head_at'][0]},{fr['head_at'][1]}). Read it first. NEVER move, redraw or recolour any head pixel (face, eyes, brows, hair mass, bow); "
                   "it is re-pasted automatically after you finish, so anything you draw over it is lost. You draw ONLY the body: neck/collar, torso, sleeves and arms, "
                   "obi, skirt, legs, socks, boots, and the long hair ends that hang below the stamp, joining the stamp edges cleanly (outline continuous).")
    else:
        headtxt = f"- LOCKED HEAD + FACE STAMP: {stamp}. Paste it pixel-identical (eyes, lash, mouth, hair mass); you may shift it as a whole, squash it by 1px on landings, and change hair-end/bang tips only by 1-2px for overlap."
    return f"""You are a senior Pokemon-style pixel artist (PMD / BW battle-trainer look) redrawing ONE animation frame by hand as a char-map. Work autonomously; nobody answers questions.
ACTION {act}, direction {d}, frame {i} of {n} (key '{fr['key']}', {fr['ms']} ms{', AIRBORNE' if fr['air'] else ''}). Cell {cw}x{ch}; feet pivot ({px},{py}) = the lowest row of the standing feet{' (airborne: feet above it)' if fr['air'] else ''}.
{intent}INPUTS (Read the PNGs; all are <=1000px):
- 3D pose guide for this frame (proportions, pose, foreshortening; colours = material IDs only, NOT the style): char-map below, and {out}/g{i:02d}_4x.png (4x), {out}/g{i:02d}_sil.png (silhouette), original render {src} (4x).
- STYLE MASTER (the look to copy exactly: outline, shading clusters, hair sheen, red ramp, proportions): {master} (char-map; Read it; render at 1x in your head).
{headtxt}
- Continuity: previous = {nb(i - 1)}; next = {nb(i + 1)}. Same character, same palette, same volumes; motion must read between them.
GUIDE CHAR-MAP (1x, {cw}x{ch}, material colours mapped to the nearest palette char):
{g}
PALETTE (only these chars, '.' transparent):
{legend()}
{colour_lock(master)}STYLE RULES (binding):
{guide_rules()}
TASK: draw the whole figure for this frame (torso, sleeves, skirt, legs, {'hair ends below the locked head' if fr.get('head_at') else 'hair silhouette'}{' (unarmed: no sword)' if unarmed else ' and katana'} redrawn for the pose; head from the stamp) following the guide's pose but cheating limbs{'' if unarmed else '/blade'} across the screen where the 3D depth axis foreshortens them. Pure black K outline on every silhouette edge, no K inside except lash/pupils, no 1-3-1 jaggies, no orphan pixels, feet on the pivot row.
Write the result with the Write tool to {fpath}{' (keep the pre-seeded head)' if fr.get('head_at') else ''}: exactly {ch} rows of {cw} chars{', first line "; air"' if fr['air'] else ''}. Then self-check by running: {lint_cmd(fpath, stamp, px, py, fr['air'], master)} and fix until OK (max 3 passes). Do not modify any other file. Reply <=30 words."""


def call_artist(acc, ptxt, log):
    for k in range(3):
        r = subprocess.run(['zsh', '-ic', 'claude-as %s --dangerously-skip-permissions --model claude-opus-5-5 -p "$(cat %s)"' % (acc, ptxt)],
                           stdin=subprocess.DEVNULL, capture_output=True, text=True)
        o = r.stdout + r.stderr; open(log, 'a').write('\n=== %s try %d\n%s' % (acc, k, o))
        if not re.search(r'API Error|Proxy startup failed|ECONNREFUSED|no available port', o): return o
        time.sleep(30)
    return o


def validate(path, fj, stamp, master=None):
    cw, ch = fj['cell']
    if not os.path.exists(path): return ['MISSING the artist did not write %s' % path]
    g, meta = LS.read(path)
    fx = []
    if len(g) != ch or any(len(r) != cw for r in g):
        fx.append('SIZE grid is %dx%d, must be exactly %dx%d (pad with ".")' % (max(map(len, g)) if g else 0, len(g), cw, ch))
        g = [r[:cw].ljust(cw, '.') for r in g[:ch]] + ['.' * cw] * max(0, ch - len(g))
    mg = LS.read(master)[0] if (master and PALOBJ is not None) else None
    fx += LS.lint(g, meta, LS.read(stamp)[0] if stamp else None, tuple(fj['pivot']), palette=PALOBJ, master=mg)
    gp = os.path.join(os.path.dirname(path), 'g' + os.path.basename(path)[1:])  # POSE: silhouette IoU with the 3D guide (katana excluded)
    if os.path.exists(gp):
        gg = LS.read(gp)[0]
        A = {(x, y) for y, r in enumerate(g) for x, c in enumerate(r) if c not in '.nk'}
        B = {(x, y) for y, r in enumerate(gg) for x, c in enumerate(r) if c not in '.nk'}
        iou = len(A & B) / max(1, len(A | B))
        if iou < IOU_MIN:
            fx.append('POSE body silhouette overlaps the 3D guide only %d%% (need >=%d%%): follow the guide pose, position and limb placement more closely' % (iou * 100, IOU_MIN * 100))
    if OPTS.get('lint_rel'): fx = lint_rel(fx, master, stamp, fj)
    fx += qc_hooks(path, fj, stamp, master)
    return fx


_MR1 = {}
def lint_rel(fx, master, stamp, fj):
    """--lint-rel: drop O3 (gate WARN); R1 interior K tolerated up to the master's own count + 4."""
    out = []
    for f in fx:
        if f.startswith('O3 '): continue
        if f.startswith('R1 ') and master:
            if master not in _MR1:
                mg, mm = LS.read(master)
                _MR1[master] = next((int(x.split()[1]) for x in LS.lint(mg, mm, None, tuple(fj['pivot'])) if x.startswith('R1 ')), 0)
            if int(f.split()[1]) <= _MR1[master] + 4: continue
        out.append(f)
    return out


def qc_hooks(path, fj, stamp, master):
    """--qc gate,eye: consistency gate + eyecheck fix lines for the artist retry."""
    q = OPTS.get('qc') or []; fx = []
    if not q or not os.path.exists(path): return fx
    if 'gate' in q:
        sys.path.insert(0, os.path.join(V2, 'qc')); import qc_gate
        try: fx += qc_gate.validate_hook(path, fj, stamp, master)
        except Exception as e: fx.append('QC gate hook error (ignore): %s' % e)
    if 'eye' in q and not any('eyecheck:' in f for f in fx):
        import importlib.util
        sp = importlib.util.spec_from_file_location('eyecheck', os.path.join(V2, 'm96/tools/eyecheck.py')); EC = importlib.util.module_from_spec(sp)
        sys.path.insert(0, os.path.join(V2, 'm96/tools')); sp.loader.exec_module(EC)
        g = LS.read(path)[0]; ref = LS.read(master)[0] if master else None
        try:
            _, efx = EC.qc_hook(g, fj.get('dir'), ref, fj.get('palette') or os.path.join(V2, 'pixelize/palette.json'))
            fx += ['EYE ' + f for f in efx]
        except Exception as e: fx.append('EYE hook error (ignore): %s' % e)
    return fx


def enforce_head(fpath, fr):
    """--head-lock: re-paste the locked stamp at its anchor after an artist pass; returns px restored."""
    if not fr.get('head_at') or not os.path.exists(fpath): return 0
    g, meta = LS.read(fpath); cw = len(g[0]) if g else 0
    raw = open(fpath).read().splitlines(); mt = [l for l in raw if l.startswith(';')]
    g2, n = paste_stamp(g, fr['stamp'], fr['head_at'])
    if n: open(fpath, 'w').write(''.join(l + '\n' for l in mt) + '\n'.join(g2) + '\n')
    return n


def draw_one(act, d, fj, i, master, stamp, acc, retries):
    out = wd(act, d); log = os.path.join(out, 'log%02d.txt' % i); fpath = os.path.join(out, 'f%02d.txt' % i)
    stamp = fj['frames'][i].get('stamp') or stamp
    fr = fj['frames'][i]; hp = os.path.join(out, 'h%02d.txt' % i)
    if fr.get('head_at') and os.path.exists(hp): open(fpath, 'w').write(open(hp).read())  # pre-seed the locked head
    p = os.path.join(out, 'p%02d.txt' % i); open(p, 'w').write(prompt(act, d, fj, i, master, stamp))
    t0 = time.time(); call_artist(acc, p, log); hr = [enforce_head(fpath, fr)]; fixes = validate(fpath, fj, stamp, master); k = 0
    while fixes and k < retries and not fixes[0].startswith('MISSING'):
        k += 1; pf = os.path.join(out, 'p%02d_fix%d.txt' % (i, k)); open(pf, 'w').write(prompt(act, d, fj, i, master, stamp, fixes))
        call_artist(acc, pf, log); hr.append(enforce_head(fpath, fr)); fixes = validate(fpath, fj, stamp, master)
    if fr.get('head_at'): open(log, 'a').write('\n=== head re-paste px per pass: %s\n' % hr)
    open(os.path.join(out, 'lint%02d.txt' % i), 'w').write('\n'.join(fixes) or 'OK')
    print('f%02d %s (%s, %d fix rounds, %ds)%s' % (i, 'OK' if not fixes else 'LINT %d' % len(fixes), acc, k, time.time() - t0,
                                                   '' if not fixes else ': ' + '; '.join(f[:60] for f in fixes)), flush=True)
    return fixes


def draw(act, d, master, stamp, frames=None, jobs=3, accounts=('bni_requests', 'nsystem4', 'be_system'), key0=False, retries=2):
    fj = json.load(open(os.path.join(wd(act, d), 'frames.json')))
    if PALOBJ is None and fj.get('palette'): use_palette(fj['palette'])
    load_opts(fj)
    if PALOBJ is not None and master: check_stamps(act, d, fj, master, stamp)
    idx = frames if frames is not None else list(range(len(fj['frames'])))
    if key0 and 0 in idx:
        draw_one(act, d, fj, 0, master, stamp, accounts[0], retries); idx = [i for i in idx if i != 0]
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        list(ex.map(lambda t: draw_one(act, d, fj, t[1], master, stamp, accounts[(t[0] + int(key0)) % len(accounts)], retries), enumerate(idx)))


def load_opts(fj):
    """frames.json 'opts' (written by prep) fill the options not given on this command line."""
    for k, v in (fj.get('opts') or {}).items(): OPTS.setdefault(k, v)


def check_stamps(act, d, fj, master, stamp=None):
    """palette mode: every expression stamp used by the clip may only use the master's face colours."""
    import colorcheck as CC
    mg = LS.read(master)[0]; sts = sorted({f.get('stamp') or stamp for f in fj['frames']} - {None}); rep = []
    for st in sts:
        iss = CC.stamp_check(st, mg, PALOBJ); rep.append(('OK   ' if not iss else 'WARN ') + st + ''.join('\n    ' + x for x in iss))
    open(os.path.join(wd(act, d), 'stamp_check.txt'), 'w').write('\n'.join(rep) + '\n')
    for r in rep:
        if r.startswith('WARN'): print('STAMP', r)
    return rep


# ---------------- assemble ----------------
def assemble(act, d, stamp=None, s=6, master=None):
    out = wd(act, d); fj = json.load(open(os.path.join(out, 'frames.json'))); cw, ch = fj['cell']
    if PALOBJ is None and fj.get('palette'): use_palette(fj['palette'])
    mg = LS.read(master)[0] if (master and PALOBJ is not None) else None; G, STs = [], []
    ims, pairs, rep = [], [], []
    for f in fj['frames']:
        i = f['i']; fp = os.path.join(out, 'f%02d.txt' % i)
        gg = LS.read(os.path.join(out, 'g%02d.txt' % i))[0]
        if os.path.exists(fp):
            g, meta = LS.read(fp); g = [r[:cw].ljust(cw, '.') for r in g[:ch]] + ['.' * cw] * max(0, ch - len(g))
            st = f.get('stamp') or stamp
            fx = LS.lint(g, meta, LS.read(st)[0] if st else None, tuple(fj['pivot']), palette=PALOBJ, master=mg)
            G.append(g); STs.append(LS.read(st)[0] if st else None)
        else:
            g, fx = ['.' * cw] * ch, ['MISSING']
        rep.append('f%02d %s %s\n%s' % (i, f['key'], 'OK' if not fx else 'FAIL', ''.join('    %s\n' % x for x in fx)))
        ims.append(render(g, s, BG).convert('RGB')); pairs.append((render(gg, 1, BG), render(g, 1, BG), f))
    # gif
    ims[0].save(os.path.join(out, '%s_%s.gif' % (act, d)), save_all=True, append_images=ims[1:], loop=0,
                duration=[f['ms'] for f in fj['frames']], disposal=2)
    # sheet: per frame a column [guide | frame], scale to fit 1000px
    n = len(pairs); cols = min(n, 4); rows = (n + cols - 1) // cols
    sc = max(1, min(4, (1000 - 8 * (cols + 1)) // (cols * 2 * cw), (1000 - rows * 22) // (rows * ch)))
    W, H = cols * (2 * cw * sc + 8) + 8, rows * (ch * sc + 22) + 8
    sh = Image.new('RGB', (W, H), (40, 40, 40)); dr = ImageDraw.Draw(sh)
    for k, (gi, fi, f) in enumerate(pairs):
        c, r = k % cols, k // cols; x0, y0 = 8 + c * (2 * cw * sc + 8), 8 + r * (ch * sc + 22)
        dr.text((x0, y0), 'f%02d %s %dms (guide | frame)' % (f['i'], f['key'], f['ms']), fill=(230, 230, 230))
        sh.paste(gi.resize((cw * sc, ch * sc), Image.NEAREST).convert('RGB'), (x0, y0 + 14))
        sh.paste(fi.resize((cw * sc, ch * sc), Image.NEAREST).convert('RGB'), (x0 + cw * sc, y0 + 14))
    sh.save(os.path.join(out, 'sheet.png'))
    open(os.path.join(out, 'lint.txt'), 'w').write(''.join(rep))
    if PALOBJ is not None and len(G) == len(fj['frames']) and G:  # clip colour/flicker report
        import colorcheck as CC
        txt, data = CC.clip_report(G, PALOBJ, STs if all(STs) else None, [f['key'] for f in fj['frames']], fj.get('loop', True), name='%s_%s' % (act, d))
        open(os.path.join(out, 'colors.txt'), 'w').write(txt); json.dump(data, open(os.path.join(out, 'colors.json'), 'w'), indent=1, default=str)
        print(txt)
    print('assemble -> %s/{%s_%s.gif, sheet.png %dx%d, lint.txt}' % (out, act, d, W, H)); print(''.join(rep))


def cut_stamp(master, outp, y0, y1, pivot=None):
    g, _ = LS.read(master); rows = g[y0:y1 + 1]
    xs = [x for r in rows for x, c in enumerate(r) if c != '.']; x0, x1 = min(xs), max(xs)
    meta = ['source %s rows %d %d cols %d %d' % (os.path.basename(master), y0, y1, x0, x1)]
    if pivot: meta.append('pivot %d %d' % (pivot[0] - x0, pivot[1] - y0))
    write_cm(outp, [r[x0:x1 + 1] for r in rows], meta); print('stamp', outp, x1 - x0 + 1, 'x', len(rows))


if __name__ == '__main__':
    a = sys.argv[1:]; cmd = a.pop(0)
    if cmd == 'stamp':
        rows = opt(a, '--rows', 2, cast=int); pv = opt(a, '--pivot', 2, cast=int); cut_stamp(a[0], a[1], rows[0], rows[1], pv); sys.exit()
    cell = opt(a, '--cell', 2, [64, 64], int); piv = opt(a, '--pivot', 2, [32, 61], int); gp = opt(a, '--gpivot', 2, [48, 88], int)
    gs = opt(a, '--gscale', 1, 4, int); ms = opt(a, '--ms'); ms = [int(x) for x in ms.split(',')] if ms else None
    pal0 = opt(a, '--palette')
    if pal0: use_palette(pal0)
    rt0 = opt(a, '--root')
    if rt0: FFROOT = os.path.abspath(rt0)
    gdir = opt(a, '--guides'); master = opt(a, '--master'); stamp = opt(a, '--stamp'); fr = opt(a, '--frames')
    fr = [int(x) for x in fr.split(',')] if fr else None; jobs = opt(a, '--jobs', 1, 3, int)
    accs = tuple(opt(a, '--accounts', 1, 'bni_requests,nsystem4,be_system').split(',')); rt = opt(a, '--retries', 1, 2, int)
    poses = opt(a, '--poses'); stamps = opt(a, '--stamps')
    v = opt(a, '--expr-alias')
    if v: OPTS['expr_alias'] = dict(x.split('=') for x in v.split(','))
    if '--head-lock' in a: a.remove('--head-lock'); OPTS['head_lock'] = True
    v = opt(a, '--head-bias', 2, cast=float)
    if v: OPTS['head_bias'] = v
    v = opt(a, '--head-bob', cast=int)
    if v is not None: OPTS['head_bob'] = v
    v = opt(a, '--head-ref')
    if v and OPTS.get('head_lock'): OPTS['head_lock'] = v  # snap (default) | world
    v = opt(a, '--qc')
    if v: OPTS['qc'] = v.split(',')
    if '--lint-rel' in a: a.remove('--lint-rel'); OPTS['lint_rel'] = True
    v = opt(a, '--rules')
    if v: OPTS['rules'] = os.path.abspath(v)
    v = opt(a, '--rest-keys')
    if v is not None: OPTS['rest_keys'] = [x for x in v.split(',') if x]
    if OPTS.get('head_lock') and master: OPTS['master'] = os.path.abspath(master)
    key0 = '--key0' in a; a = [x for x in a if x != '--key0']; act, d = a[0], a[1]
    if cmd in ('prep', 'all'): prep(act, d, gdir, cell, piv, gp, gs, ms, poses, stamps)
    if cmd in ('draw', 'all'): draw(act, d, master, stamp, fr, jobs, accs, key0 or cmd == 'all', rt)
    if cmd in ('assemble', 'all'): assemble(act, d, stamp, master=master)
