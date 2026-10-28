"""rl.py (I = integrator, round 4): release build of the swordswoman skinned-rig set.   Runs on the pixtools venv.

    rl.py plan                      -> prints "<build_id> <act>:<V> ..." (build id = date + short hash of every input file)
    rl.py clip  <build> <act> <V>   -> one clip end to end: R's render (--no-post) + P's part pass + F's face pass/preview (Blender,
                                       cached by input hash in release/work/cache/), P's pixel_chain.py, F's face_layer, preview + face
    rl.py assemble <build>          -> release/out/<build>/<act>/<V>.gif, <act>_8dir.gif, strips, sheets, preview GIFs
    rl.py gates <build>             -> GATES.md + gates.json (pxeval seq, P's limb audit, gifcheck + REVIEW/build.py gif_check)
    rl.py hub <build>               -> REVIEW/entries/2026-10-28_sw_current_build.json + REVIEW/build.py

Owners' code is only CALLED (R render/render_motion.py, P render/p_parts.py + pixel_chain.py + gifio.py + gifcheck.py, F face/f_render.py
+ face_layer.py); nothing in their folders is written.  Per-frame data goes to release/out/<build>/work/ and release/work/cache/ (gitignored).
"""
import os, sys, json, glob, hashlib, subprocess, time, shutil, re, datetime
import numpy as np
from PIL import Image, ImageDraw, ImageFont

EXP = '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned'
ROOT = '/Users/waylonhuang/Documents/other/pixelart'
REL = f'{EXP}/release'; OUTR = f'{REL}/out'; CACHE = f'{REL}/work/cache'
BL = '/Applications/Blender.app/Contents/MacOS/Blender'
PY = f'{ROOT}/.models/pixtools/venv/bin/python'
sys.path.insert(0, f'{EXP}/render'); sys.path.insert(0, f'{EXP}/face'); sys.path.insert(0, f'{ROOT}/REVIEW/exp/2026-10-28_sw_hires3d/scripts')
ORDER = ['S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW']
BG = (128, 128, 128)
GATE = {'boil': 0.02, 'shade_swap': 0.015, 'feet': 2, 'seam': 1.5}


# ------------------------------------------------------------------ config: actions x directions
def config():
    """release/actions.json: {"actions": {act: {"motion": rel path, "loop": bool|null}}, "dirs": [...] | "auto"}.
    Actions whose motion file is missing are skipped; dash/hurt are picked up automatically once motion/<act>.json exists.
    dirs "auto" = every view R has an alignment for in rig/align.json (R adds the 8 directions there)."""
    cfg = json.load(open(f'{REL}/actions.json'))
    acts = {}
    for a, c in cfg['actions'].items():
        m = f"{EXP}/{c['motion']}"
        if os.path.exists(m):
            loop = c.get('loop'); loop = json.load(open(m)).get('loop', True) if loop is None else loop
            acts[a] = {'motion': m, 'loop': bool(loop)}
    dirs = os.environ.get('DIRS', '').split() or cfg.get('dirs', 'auto')
    if dirs == 'auto':
        al = json.load(open(f'{EXP}/rig/align.json')); dirs = [v for v in ORDER if v in al]
    acts_env = os.environ.get('ACTS', '').split()
    if acts_env: acts = {a: v for a, v in acts.items() if a in acts_env}
    return acts, [v for v in ORDER if v in dirs]


# ------------------------------------------------------------------ hashing
_HC = {}


def fhash(p):
    if p not in _HC:
        h = hashlib.sha1()
        with open(p, 'rb') as f:
            for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
        _HC[p] = h.hexdigest()
    return _HC[p]


def hfiles(paths):
    h = hashlib.sha1()
    for p in sorted(set(paths)):
        if os.path.isfile(p): h.update(os.path.relpath(p, ROOT).encode()); h.update(fhash(p).encode())
    return h.hexdigest()[:10]


def g(pat): return sorted(glob.glob(f'{EXP}/{pat}'))


RIG_IN = lambda: [f'{EXP}/rig/rig.blend', f'{EXP}/rig/align.json', f'{EXP}/rig/face_anchors.json', *g('rig/tex/*.png'),
                  f'{EXP}/render/render_motion.py', f'{EXP}/render/p_parts.py']
FACE_IN = lambda: [*g('face/*.py'), f'{EXP}/face/parts.json', f'{EXP}/face/calib.json', *g('face/tex/*')]
CODE_IN = lambda: [*g('render/pixel_chain.py'), *g('render/r_tex_head.py'), *g('render/gifio.py'), *g('render/gifcheck.py'),
                   *g('face/face_layer.py'), *g('face/face_lib.py'), f'{ROOT}/REVIEW/exp/2026-10-28_sw_hires3d/scripts/hx.py',
                   *g('release/*.py'), *g('release/*.sh'), f'{REL}/actions.json']


def pass_hash(act, V, acts):
    return hfiles(RIG_IN() + [acts[act]['motion']]) + f'_{act}_{V}'


def face_hash(act, V, acts):
    return hfiles(RIG_IN() + FACE_IN() + [acts[act]['motion']]) + f'_{act}_{V}'


def plan():
    acts, dirs = config()
    allin = RIG_IN() + FACE_IN() + CODE_IN() + [a['motion'] for a in acts.values()]
    h = hashlib.sha1((hfiles(allin) + ' '.join(acts) + ' ' + ' '.join(dirs)).encode()).hexdigest()[:7]
    bid = datetime.date.today().strftime('%Y%m%d') + '_' + h
    return bid, acts, dirs


# ------------------------------------------------------------------ one clip
def run(cmd, log, env=None):
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, **(env or {})})
    with open(log, 'a') as f:
        f.write(f"$ {' '.join(cmd)}\n[{time.time() - t0:.1f}s rc={r.returncode}]\n{r.stdout[-6000:]}\n{r.stderr[-3000:]}\n")
    return r


def blender(script, mot, V, out, log, extra=()):
    os.makedirs(out, exist_ok=True)
    return run([BL, '-b', f'{EXP}/rig/rig.blend', '-P', script, '--', mot, V, out, *extra], log)


def clip(bid, act, V):
    acts, _ = config(); mot = acts[act]['motion']; loop = acts[act]['loop']
    W = f'{OUTR}/{bid}/work/{act}/{V}'; os.makedirs(W, exist_ok=True); log = f'{W}/clip.log'; open(log, 'w').close()
    st = {'act': act, 'view': V, 'loop': loop, 'motion': os.path.relpath(mot, EXP), 'errors': [], 't0': time.time()}
    stem = f'{act}_{V}'
    # 1. R's passes + P's part pass (cached by rig/motion/renderer hash)
    C = f'{CACHE}/p_{pass_hash(act, V, acts)}'
    if not os.path.exists(f'{C}/DONE'):
        shutil.rmtree(C, ignore_errors=True)
        blender(f'{EXP}/render/render_motion.py', mot, V, C, log, ['--no-post'])
        blender(f'{EXP}/render/p_parts.py', mot, V, f'{C}/parts', log)
        if os.path.exists(f'{C}/{stem}.json') and glob.glob(f'{C}/parts/*_part.png'): open(f'{C}/DONE', 'w').close()
        else: st['errors'].append('R render / P parts failed (see clip.log)'); return done(W, st)
    st['passes'] = os.path.relpath(C, REL)
    # 2. F's faceless head pass + anchors, full and preview (cached)
    F = f'{CACHE}/f_{face_hash(act, V, acts)}'
    if not os.path.exists(f'{F}/DONE'):
        shutil.rmtree(F, ignore_errors=True)
        blender(f'{EXP}/face/f_render.py', mot, V, F, log)
        blender(f'{EXP}/face/f_render.py', mot, V, f'{F}/pv', log, ['--preview'])
        if os.path.exists(f'{F}/{stem}_face.json') and glob.glob(f'{F}/pv/*_pv.png'): open(f'{F}/DONE', 'w').close()
        else: st['errors'].append('F face render failed (see clip.log); frames ship without the face layer')
    st['face'] = os.path.relpath(F, REL)
    # 3. P's pixel chain on symlinked passes (outputs land in the build work dir).  Since P's round-3 chain applies F's face layer itself
    #    (pixel_chain.apply_face reads <clip dir>/face/, as P's p3_run.sh), the face cache is linked there; FACE=0 if it is missing.
    for p in glob.glob(f'{C}/*'):
        d = f'{W}/{os.path.basename(p)}'
        if os.path.basename(p) == 'DONE' or os.path.lexists(d): continue
        os.symlink(p, d)
    face_ok = os.path.exists(f'{F}/DONE')
    if face_ok and not os.path.lexists(f'{W}/face'): os.symlink(F, f'{W}/face')
    p_face = 'def apply_face' in open(f'{EXP}/render/pixel_chain.py').read()
    r = run([PY, f'{EXP}/render/pixel_chain.py', f'{W}/{stem}.json'], log, env=None if face_ok else {'FACE': '0'})
    if not glob.glob(f'{W}/{stem}_px/f*.txt'):
        st['errors'].append('P pixel_chain failed (see clip.log): ' + (r.stderr.strip().splitlines() or ['?'])[-1][:200]); return done(W, st)
    m = re.search(r'LIMB_AUDIT \S+ (.*)', r.stdout); st['limb_line'] = m.group(1)[:300] if m else None
    # 4. face: inside P's chain (current) or F's face_layer called here (fallback for a chain without it)
    fw = [l for l in r.stdout.splitlines() if 'WARN' in l and 'face' in l.lower()]
    if p_face and face_ok:
        copy_px(W, act, V); st['face_layer'] = 'ok (in P chain)' if not fw else 'P chain WARN: ' + ' | '.join(fw)[:300]
        if fw: face_ok = False
    elif face_ok:
        try:
            st['face_layer'] = apply_face(W, F, act, V, loop)
        except Exception as e:  # noqa: BLE001
            st['errors'].append(f'F face_layer failed: {e!r}'[:300]); st['face_layer'] = 'failed'; face_ok = False; copy_px(W, act, V)
    else:
        copy_px(W, act, V); st['face_layer'] = 'skipped (no face pass)'
    try:
        st['preview'] = preview(W, F, act, V, loop, os.path.exists(f'{F}/DONE'))
    except Exception as e:  # noqa: BLE001
        st['errors'].append(f'preview failed: {e!r}'[:300])
    return done(W, st)


def done(W, st):
    st['secs'] = round(time.time() - st.pop('t0'), 1); json.dump(st, open(f'{W}/clip.json', 'w'), indent=1)
    print('CLIP', st['act'], st['view'], 'OK' if not st['errors'] else 'ERR ' + '; '.join(st['errors']), f"{st['secs']}s", flush=True)
    return st


def copy_px(W, act, V):
    import hx
    os.makedirs(f'{W}/final', exist_ok=True)
    for t in sorted(glob.glob(f'{W}/{act}_{V}_px/f*.txt')):
        gg = hx.read_grid(t); save_final(gg, f"{W}/final/{os.path.basename(t)[:-4]}", V)


def save_final(gg, stem, V):
    import hx
    hx.save(gg, stem, V)
    a = np.zeros(gg.shape + (4,), np.uint8)
    for i, k in enumerate(hx.KEYS): a[gg == k] = (*hx.RGB[i], 255)
    Image.fromarray(a).save(stem + '_rgba.png')


def apply_face(W, F, act, V, loop):
    import face_layer as FLY
    import hx
    info = json.load(open(f'{W}/{act}_{V}.json')); os.makedirs(f'{W}/final', exist_ok=True)
    n = 0
    for k, fr in enumerate(info['frames']):
        i = fr['i']; gg = hx.read_grid(f'{W}/{act}_{V}_px/f{i:02d}.txt')
        fi = {'action': act, 'view': V, 'i': i, 'face_dir': F, 'loop': loop, 'rface': fr.get('face') or None}
        g2 = FLY.face_layer(fi, gg, {'rface': fr.get('face') or None})
        n += int((np.asarray(g2) != gg).sum()); save_final(np.asarray(g2), f'{W}/final/f{i:02d}', V)
    return f'ok ({n} px changed)'


def preview(W, F, act, V, loop, face_ok):
    """port of F's face/f_preview.py with release paths: F's faceless EEVEE preview + the face parts as 2x2 blocks at the
    projected anchors (half-pixel face offset), so the face follows the head in the smooth preview too."""
    import face_layer as FLY
    hx = FLY.hx
    RGB = {k: tuple(int(c) for c in hx.RGB[i]) for i, k in enumerate(hx.KEYS)}
    pd = f'{F}/pv'; info = json.load(open(f'{pd}/{act}_{V}.json')); SC = info['scale']
    od = f'{W}/pv_final'; os.makedirs(od, exist_ok=True)
    if face_ok:
        fj = f'{F}/{act}_{V}_face.json'; d = json.load(open(fj)); DX, DY = d['align']['dx'], d['align']['dy']
        Cp = FLY.plan_clip(fj, act, loop)
    for k, fr in enumerate(info['frames']):
        i = fr['i']; im = Image.open(f'{pd}/{act}_{V}_f{i:02d}_pv.png').convert('RGBA'); a = np.array(im)
        if face_ok:
            pl = Cp['plan'][k]
            T, gn = FLY.tex_cells(FLY.load_ftex(f'{F}/{act}_{V}_f{i:02d}_tex.png', DX, DY))
            g1 = FLY.draw(gn, gn, T, V, Cp['parts'], pl)
            G0 = (pl['G'][0] - d['tex_off'][0], pl['G'][1] - d['tex_off'][1])
            sx = int(round((pl['g_cont'][0] - G0[0]) * SC)); sy = int(round((pl['g_cont'][1] - G0[1]) * SC))
            ys, xs = np.nonzero((g1 != gn) & (g1 != 's'))
            for y, x in zip(ys, xs):
                X = (x + 32 - DX) * SC + sx; Y = (y + 32 - DY) * SC + sy
                blk = a[Y:Y + SC, X:X + SC]
                if blk.size and (blk[..., 3] > 0).all(): blk[..., :3] = RGB[g1[y, x]]
        Image.fromarray(a).save(f'{od}/f{i:02d}.png')
    json.dump({'ms': [int(f['ms']) for f in info['frames']], 'scale': SC, 'face': face_ok}, open(f'{od}/meta.json', 'w'))
    return 'ok' + ('' if face_ok else ' (no face)')


# ------------------------------------------------------------------ assemble the review set
def font(sz):
    for p in ('/System/Library/Fonts/Supplemental/Arial Bold.ttf', '/System/Library/Fonts/Helvetica.ttc'):
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def bbox_union(ims, pad):
    bb = None
    for im in ims:
        b = im.getchannel('A').getbbox()
        if b: bb = b if bb is None else (min(bb[0], b[0]), min(bb[1], b[1]), max(bb[2], b[2]), max(bb[3], b[3]))
    W, H = ims[0].size
    return (max(0, bb[0] - pad), max(0, bb[1] - pad), min(W, bb[2] + pad), min(H, bb[3] + pad))


def on_bg(im, bg=BG):
    b = Image.new('RGBA', im.size, bg + (255,)); b.alpha_composite(im); return b.convert('RGB')


def label_row(tiles, labels, sz, bg=BG, gap=0, title=None):
    lh = sz + 8; th = (sz + 10) if title else 0
    W = sum(t.width for t in tiles) + gap * (len(tiles) - 1); H = tiles[0].height + lh + th
    c = Image.new('RGB', (W, H), bg); d = ImageDraw.Draw(c); f = font(sz); x = 0
    if title: d.text((6, 3), title, fill=(255, 255, 220), font=font(sz))
    for t, l in zip(tiles, labels):
        c.paste(t, (x, th + lh)); d.text((x + t.width // 2 - d.textlength(l, font=f) // 2, th + 3), l, fill=(255, 255, 210), font=f); x += t.width + gap
    return c


def assemble(bid):
    from gifio import write_gif
    acts, dirs = config(); B = f'{OUTR}/{bid}'; made = {}
    for act in acts:
        A = f'{B}/{act}'; os.makedirs(A, exist_ok=True)
        fr, pv, ms = {}, {}, None
        for V in dirs:
            W = f'{B}/work/{act}/{V}'
            fs = sorted(glob.glob(f'{W}/final/f??_rgba.png'))
            if not fs: continue
            fr[V] = [Image.open(p).convert('RGBA') for p in fs]
            info = json.load(open(f'{W}/{act}_{V}.json')); ms = [int(f['ms']) for f in info['frames']]
            pf = sorted(glob.glob(f'{W}/pv_final/f??.png'))
            if pf: pv[V] = [Image.open(p).convert('RGBA') for p in pf]
        if not fr: continue
        Vs = [V for V in dirs if V in fr]; n = min(len(fr[V]) for V in Vs)
        bb = bbox_union([im for V in Vs for im in fr[V]], 3)
        crop = {V: [im.crop(bb) for im in fr[V][:n]] for V in Vs}
        out = {'dirs': Vs, 'frames': n, 'ms': ms[:n], 'gifs': {}, 'pv': {}}
        for V in Vs:  # per-direction 4x GIF + 1x strip
            write_gif(f'{A}/{V}.gif', [on_bg(im) for im in crop[V]], ms[:n], bg=BG, scale=4); out['gifs'][V] = f'{act}/{V}.gif'
            s = Image.new('RGBA', (crop[V][0].width * n, crop[V][0].height), (0, 0, 0, 0))
            for k, im in enumerate(crop[V]): s.paste(im, (k * im.width, 0))
            s.save(f'{A}/{V}_strip1x.png')
        # all directions in one labelled row (4x)
        rows = []
        for k in range(n):
            tiles = [on_bg(crop[V][k]).resize((crop[V][k].width * 4, crop[V][k].height * 4), Image.NEAREST) for V in Vs]
            rows.append(label_row(tiles, Vs, 28, gap=8))
        write_gif(f'{A}/{act}_8dir.gif', rows, ms[:n], bg=BG); out['8dir'] = f'{act}/{act}_8dir.gif'
        # 1x strip: rows = directions (true size, on grey) and contact sheet (3x, labelled frame/ms)
        cw, chh = crop[Vs[0]][0].size
        st1 = Image.new('RGB', (cw * n, chh * len(Vs)), BG)
        for r, V in enumerate(Vs):
            for k in range(n): st1.paste(on_bg(crop[V][k]), (k * cw, r * chh))
        st1.save(f'{A}/{act}_strip1x.png'); out['strip1x'] = f'{act}/{act}_strip1x.png'
        S, L, T = 3, 70, 46
        sh = Image.new('RGB', (L + n * (cw * S + 4), T + len(Vs) * (chh * S + 4) + 30), (60, 60, 64)); d = ImageDraw.Draw(sh); f = font(16)
        d.text((4, 4), f'{act}  ({bid})  3x', fill=(255, 255, 210), font=f)
        for k in range(n): d.text((L + k * (cw * S + 4) + 4, T - 18), f'f{k:02d} {ms[k]}ms', fill=(220, 220, 220), font=font(13))
        for r, V in enumerate(Vs):
            y = T + r * (chh * S + 4); d.text((8, y + chh * S // 2 - 10), V, fill=(255, 255, 210), font=font(22))
            for k in range(n): sh.paste(on_bg(crop[V][k]).resize((cw * S, chh * S), Image.NEAREST), (L + k * (cw * S + 4), y))
        sh.save(f'{A}/{act}_sheet.png'); out['sheet'] = f'{act}/{act}_sheet.png'
        # smooth previews (face composited), cropped to the union bbox
        if pv:
            PVs = [V for V in Vs if V in pv]; m = min(len(pv[V]) for V in PVs)
            pb = bbox_union([im for V in PVs for im in pv[V]], 6)
            pc = {V: [on_bg(im.crop(pb)) for im in pv[V][:m]] for V in PVs}
            for V in PVs:
                write_gif(f'{A}/{V}_preview.gif', pc[V], ms[:m], bg=BG); out['pv'][V] = f'{act}/{V}_preview.gif'
            rows = [label_row([pc[V][k] for V in PVs], PVs, 22, gap=6) for k in range(m)]
            write_gif(f'{A}/{act}_8dir_preview.gif', rows, ms[:m], bg=BG); out['8dir_pv'] = f'{act}/{act}_8dir_preview.gif'
            pw, ph = pc[PVs[0]][0].size
            ps = Image.new('RGB', (L + m * (pw + 4), T + len(PVs) * (ph + 4)), (60, 60, 64)); d = ImageDraw.Draw(ps)
            d.text((4, 4), f'{act} smooth preview + face ({bid})', fill=(255, 255, 210), font=f)
            for r, V in enumerate(PVs):
                y = T + r * (ph + 4); d.text((8, y + ph // 2 - 10), V, fill=(255, 255, 210), font=font(22))
                for k in range(m): ps.paste(pc[V][k], (L + k * (pw + 4), y))
            ps.save(f'{A}/{act}_preview_sheet.png'); out['pv_sheet'] = f'{act}/{act}_preview_sheet.png'
        made[act] = out
        print('ASSEMBLED', act, Vs, n, flush=True)
    json.dump({'build': bid, 'dirs': dirs, 'actions': made, 'time': time.strftime('%Y-%m-%d %H:%M')}, open(f'{B}/manifest.json', 'w'), indent=1)
    masters_board(B)
    return made


def masters_board(B):
    M = f'{ROOT}/swordswoman/v2/m96/masters'; tiles, labs = [], []
    for V in ORDER:
        src, mir = (V, False) if os.path.exists(f'{M}/EC0_{V}_96.png') else ({'NW': 'NE', 'W': 'E', 'SW': 'SE'}.get(V), True)
        if not src or not os.path.exists(f'{M}/EC0_{src}_96.png'): continue
        im = Image.open(f'{M}/EC0_{src}_96.png').convert('RGBA')
        if mir: im = im.transpose(Image.FLIP_LEFT_RIGHT)
        tiles.append(on_bg(im).resize((im.width * 3, im.height * 3), Image.NEAREST)); labs.append(V + (' (mirr.)' if mir else ''))
    label_row(tiles, labs, 20, gap=6, title='m96 masters (on-model reference), 3x').save(f'{B}/masters_ref.png')


# ------------------------------------------------------------------ gates
def gates(bid):
    import gifcheck
    sys.path.insert(0, f'{ROOT}/REVIEW'); import build as hub  # noqa: E402
    acts, dirs = config(); B = f'{OUTR}/{bid}'; man = json.load(open(f'{B}/manifest.json'))
    os.makedirs(f'{B}/work/gates', exist_ok=True); rows = []
    for act, a in man['actions'].items():
        loop = acts[act]['loop'] if act in acts else True
        for V in a['dirs']:
            W = f'{B}/work/{act}/{V}'; st = json.load(open(f'{W}/clip.json'))
            js = f'{B}/work/gates/pxeval_{act}_{V}.json'
            cmd = [PY, '-I', f'{ROOT}/pipeline/tools/pxeval.py', 'seq', f'{W}/final/f*_rgba.png', '--ms', *map(str, a['ms']),
                   '--loop', 'yes' if loop else 'no', '--json', js, '--compact']
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
            try: px = json.loads(r.stdout)
            except Exception: px = {'error': r.stderr[-300:]}
            lj = f'{W}/{act}_{V}_limbs.json'; la = json.load(open(lj))['summary'] if os.path.exists(lj) else None
            gc = gifcheck.check(f'{B}/{act}/{V}.gif', oneshot=tuple(x for x in acts if not acts[x]['loop']) or ('jump',))
            hubp = hub.gif_check(f'{B}/{act}/{V}.gif')
            rows.append({'act': act, 'view': V, 'loop': loop, 'px': {k: px.get(k) for k in ('boil', 'shade_swap', 'flicker', 'feet_range', 'seam_ratio',
                         'articulation_per_s', 'motion_px', 'flags', 'n_frames', 'cycle_ms')}, 'limbs': la, 'gif': gc, 'hub_gif': hubp,
                         'errors': st.get('errors', []), 'face_layer': st.get('face_layer'), 'preview': st.get('preview')})
    for act in acts:  # clips that were planned but did not produce frames
        for V in dirs:
            cj = f'{B}/work/{act}/{V}/clip.json'
            if os.path.exists(cj) and not any(r['act'] == act and r['view'] == V for r in rows):
                st = json.load(open(cj))
                rows.append({'act': act, 'view': V, 'loop': acts[act]['loop'], 'px': {}, 'limbs': None, 'gif': {'flags': ['NOT_BUILT']}, 'hub_gif': [],
                             'errors': st.get('errors', []), 'face_layer': st.get('face_layer'), 'preview': st.get('preview')})
    # every GIF of the build (8-dir rows, previews) through both checkers
    allg = []
    for p in sorted(glob.glob(f'{B}/**/*.gif', recursive=True)):
        if '/work/' in p: continue
        c = gifcheck.check(p, oneshot=tuple(x for x in acts if not acts[x]['loop']) or ('jump',))
        allg.append({'path': os.path.relpath(p, B), 'flags': c['flags'], 'hub': hub.gif_check(p), 'min_ms': c['min_ms'], 'frames': c['frames'],
                     'seam': c['seam_ratio'], 'disposal': c['disposal'], 'loop': c['loop']})
    json.dump({'clips': rows, 'gifs': allg}, open(f'{B}/gates.json', 'w'), indent=1)
    write_gates_md(bid, rows, allg)
    return rows, allg


def _f(v, k=3): return '-' if v is None else (f'{v:.{k}f}' if isinstance(v, float) else str(v))


def clip_verdict(r):
    p = r['px']; out = {}
    out['boil'] = None if p.get('boil') is None else p['boil'] <= GATE['boil']
    out['shade'] = None if p.get('shade_swap') is None else p['shade_swap'] <= GATE['shade_swap']
    out['feet'] = None if (not r['loop'] or p.get('feet_range') is None) else p['feet_range'] <= GATE['feet']
    out['seam'] = None if (not r['loop'] or p.get('seam_ratio') is None) else p['seam_ratio'] <= GATE['seam']
    out['limbs'] = None if r['limbs'] is None else r['limbs']['pass']
    out['gif'] = not r['gif']['flags'] and not r['hub_gif']
    return out


def write_gates_md(bid, rows, allg):
    def pf(v): return 'n/a' if v is None else ('PASS' if v else '**FAIL**')
    L = [f'# GATES — build {bid}', '',
         f"Gates (reported, not blocking): pxeval seq on the final 1x frames (P chain + F face) — boil ≤ {GATE['boil']}, shade_swap ≤ {GATE['shade_swap']}, "
         f"feet_range ≤ {GATE['feet']} px (loops only; in SE/E/NE and the other off-axis views a real stride projects ~5–7 px lower at 30° elevation, so "
         f"FEET there is partly perspective, P notes), seam_ratio ≤ {GATE['seam']} (loops); P's limb audit (VANISHED/SPLIT/THIN/DETACHED, failed frames / frames); "
         'GIF = render/gifcheck.py (loop=0, ≥20 ms, disposal/ghosting, seam, dup frames) + REVIEW/build.py gif_check on the per-direction 4x GIF.', '',
         '| clip | boil | shade_swap | feet px | seam | limb audit | GIF | other pxeval flags | notes |', '|---|---|---|---|---|---|---|---|---|']
    tot = {k: [0, 0] for k in ('boil', 'shade', 'feet', 'seam', 'limbs', 'gif')}
    for r in rows:
        v = clip_verdict(r); p = r['px']
        for k, x in v.items():
            if x is not None: tot[k][0] += int(bool(x)); tot[k][1] += 1
        la = r['limbs']; lt = 'n/a' if la is None else ('PASS' if la['pass'] else f"**FAIL** {la['failed_frames']}/{la['frames']}")
        if la and not la['pass']:
            kinds = sorted({fl for fr in la['fails'].values() for fls in fr.values() for fl in fls}); lt += ' ' + '/'.join(kinds)
        persp = r['view'] not in ('S', 'N')
        ft = 'n/a' if v['feet'] is None else (f"{_f(p['feet_range'], 0)} " + ('PASS' if v['feet'] else ('FAIL (persp.)' if persp else '**FAIL**')))
        other = ' '.join(x for x in (p.get('flags') or []) if x not in ('BOILING', 'SHADE_SWAP', 'FEET_JITTER', 'SEAM'))
        gt = 'PASS' if v['gif'] else '**FAIL** ' + ' '.join(r['gif']['flags'] + r['hub_gif'])
        notes = '; '.join(r['errors']) or ('' if str(r.get('face_layer', '')).startswith('ok') else f"face: {r.get('face_layer')}")
        L.append(f"| {r['act']} {r['view']} | {_f(p.get('boil'))} {pf(v['boil'])} | {_f(p.get('shade_swap'))} {pf(v['shade'])} | {ft} | "
                 f"{_f(p.get('seam_ratio'), 2)} {pf(v['seam'])} | {lt} | {gt} | {other} | {notes} |")
    L += ['', '**Totals (pass / gated clips):** ' + ', '.join(f'{k} {a}/{b}' for k, (a, b) in tot.items()), '']
    bad = [g for g in allg if g['flags'] or g['hub']]
    L += [f'## All GIFs in the build: {len(allg)} checked, {len(bad)} flagged', '']
    L += [f"- {g['path']}: {' '.join(g['flags'] + g['hub'])}" for g in bad] or ['- none flagged (loop=0, min frame ≥ 20 ms, disposal 2 full frames, seam ok).']
    open(f'{OUTR}/{bid}/GATES.md', 'w').write('\n'.join(L) + '\n')
    s = ', '.join(f'{k} {a}/{b}' for k, (a, b) in tot.items())
    open(f'{OUTR}/{bid}/work/gates/summary.txt', 'w').write(s)
    print('GATES', s, flush=True)


# ------------------------------------------------------------------ hub entry
def hub(bid):
    B = f'{OUTR}/{bid}'; man = json.load(open(f'{B}/manifest.json')); rel = os.path.relpath(B, f'{ROOT}/REVIEW')
    G = json.load(open(f'{B}/gates.json')); summ = open(f'{B}/work/gates/summary.txt').read()
    media = []
    for act, a in man['actions'].items():
        media.append({'src': f"{rel}/{a['8dir']}", 'caption': f"{act}: all {len(a['dirs'])} directions ({' '.join(a['dirs'])}), 4x pixel + face", 'wide': True})
    for act, a in man['actions'].items():
        if a.get('8dir_pv'): media.append({'src': f"{rel}/{a['8dir_pv']}", 'caption': f'{act}: smooth preview with face', 'wide': True})
    for act, a in man['actions'].items():
        media.append({'src': f"{rel}/{a['sheet']}", 'caption': f'{act}: contact sheet (3x) — rows = directions', 'wide': True})
    worst = []
    for r in G['clips']:
        v = clip_verdict(r); fails = [k for k, x in v.items() if x is False]
        if fails: worst.append(f"{r['act']} {r['view']}: {'/'.join(fails)}")
    pm = f'{B}/PANEL.md'; verdict = 'Critic panel pending.'
    if os.path.exists(pm):
        t = open(pm).read(); m = re.search(r'## Summary\n(.*?)\n## ', t, re.S); verdict = (m.group(1).strip() if m else t[:900]).replace('\n', ' ')
    sc = json.load(open(f'{B}/panel_scores.json')) if os.path.exists(f'{B}/panel_scores.json') else {}
    e = {'id': '2026-10-28_sw_current_build', 'date': datetime.date.today().isoformat(), 'project': 'swordswoman', 'kind': 'release',
         'status': 'needs-review', 'pinned': True, 'title': f'Swordswoman current build ({bid})',
         'question': 'The latest gated review set: every action x direction on the current rig (R), motion (M), pixel chain (P) and face layer (F).',
         'method': f"release/make_all.sh (I): R render_motion.py --no-post + P p_parts.py -> P pixel_chain.py -> F face_layer; F faceless preview + face composite. "
                   f"Actions {', '.join(man['actions'])}; directions {' '.join(man['dirs'])}. Gates: pxeval seq, P limb audit, gifcheck. Build {bid} ({man['time']}).",
         'result': f"Gates pass/total: {summ}. Failing clips: " + ('; '.join(worst) if worst else 'none') + f'. Full table: exp/.../release/out/{bid}/GATES.md',
         'verdict': verdict, 'scores': sc, 'media': media,
         'links': [{'href': f'{rel}/GATES.md', 'label': 'GATES.md'}, {'href': f'{rel}/PANEL.md', 'label': 'PANEL.md'},
                   {'href': f'{os.path.relpath(EXP, ROOT + "/REVIEW")}/CONTRACT.md', 'label': 'CONTRACT.md'}],
         'next': 'ROUND 5 proposals in CONTRACT.md (ranked fix list from PANEL.md).'}
    p = f'{ROOT}/REVIEW/entries/2026-10-28_sw_current_build.json'; json.dump(e, open(p, 'w'), indent=1, ensure_ascii=False)
    r = subprocess.run(['python3', f'{ROOT}/REVIEW/build.py'], capture_output=True, text=True, cwd=ROOT)
    print(r.stdout[-3000:], r.stderr[-2000:])


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'plan':
        bid, acts, dirs = plan(); print(bid, ' '.join(f'{x}:{V}' for x in acts for V in dirs))
    elif a[0] == 'clip': clip(a[1], a[2], a[3])
    elif a[0] == 'assemble': assemble(a[1])
    elif a[0] == 'gates': sys.exit(0 if gates(a[1])[0] else 2)
    elif a[0] == 'hub': hub(a[1])
