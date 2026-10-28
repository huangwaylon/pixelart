#!/usr/bin/env python3
"""Pixel cutout composer (integer placement only, no resampling).

  compose.py actions/<action>.json [--out NAME] [--mirror] [--s 6]

Action JSON:
{
  "name": "idle_SE", "partdir": "parts/se", "cell": [64, 64], "ground": [32, 60],
  "rig": {                      # default instances: part, attach point, z, offset
     "legs":  {"part": "legs_stand", "at": "root", "z": 1},
     "skirt": {"part": "skirt_rest", "at": "legs.hip", "z": 3}, ...
  },
  "frames": [
     {"ms": 200, "root": [0, 0],
      "set": {"head": {"part": "head_squash", "off": [0, 1]}, "bow": {"off": [0, -1]}},
      "hide": ["sword"], "fx": [{"part": "dust1", "at": "ground", "off": [-8, 0], "z": 9}]}
  ]
}
Attach points: "root" (ground + frame root), "ground" (fixed ground pivot), "<inst>.<anchor>".
A child's pivot is placed at the attach point + off. flip: true mirrors a part around its pivot.
"""
import json, os, sys, copy
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cm

ROOT = os.path.abspath(os.path.join(HERE, '..'))
_cache = {}


def load_part(partdir, name):
    key = (partdir, name)
    if key not in _cache:
        p = os.path.join(ROOT, partdir, name + '.txt')
        if not os.path.exists(p):
            p = os.path.join(ROOT, 'parts', 'common', name + '.txt')
        g, meta = cm.read_cm(p)
        _cache[key] = (g, meta)
    return _cache[key]


def flipped(g, meta):
    W = g.shape[1]
    g2 = g[:, ::-1]
    m2 = {'pivot': (W - 1 - meta['pivot'][0], meta['pivot'][1]),
          'anchors': {k: (W - 1 - v[0], v[1]) for k, v in meta['anchors'].items()}}
    return g2, m2


def render_frame(act, fr):
    W, H = act['cell']
    gx, gy = act['ground']
    partdir = act.get('partdir', 'parts/se')
    inst = copy.deepcopy(act['rig'])
    for k, v in fr.get('set', {}).items():
        inst.setdefault(k, {}).update(v)
    for k in fr.get('hide', []):
        inst.pop(k, None)
    for i, f in enumerate(fr.get('fx', [])):
        inst['_fx%d' % i] = dict(f)
    rx, ry = fr.get('root', [0, 0])
    placed = {}  # inst -> (gridx0, gridy0, meta-with-abs-anchors)

    def resolve(name, depth=0):
        if name in placed:
            return placed[name]
        if depth > 20:
            raise SystemExit('attach loop at ' + name)
        spec = inst[name]
        g, meta = load_part(partdir, spec['part'])
        if spec.get('flip'):
            g, meta = flipped(g, meta)
        at = spec.get('at', 'root')
        if at == 'root':
            ax, ay = gx + rx, gy + ry
        elif at == 'ground':
            ax, ay = gx, gy
        else:
            pn, an = at.split('.')
            if pn not in inst:
                ax, ay = gx + rx, gy + ry
            else:
                pp = resolve(pn, depth + 1)
                ax, ay = pp['anch'][an]
        ox, oy = spec.get('off', [0, 0])
        px, py = meta['pivot']
        x0, y0 = ax + ox - px, ay + oy - py
        anch = {k: (x0 + v[0], y0 + v[1]) for k, v in meta['anchors'].items()}
        placed[name] = {'g': g, 'x0': x0, 'y0': y0, 'anch': anch, 'z': spec.get('z', 5)}
        return placed[name]

    for n in list(inst):
        resolve(n)
    canvas = np.full((H, W), '.', dtype='<U1')
    for n in sorted(placed, key=lambda n: (placed[n]['z'])):
        p = placed[n]
        g = p['g']
        h, w = g.shape
        for y in range(h):
            yy = p['y0'] + y
            if not (0 <= yy < H):
                continue
            for x in range(w):
                c = g[y, x]
                if c == '.':
                    continue
                xx = p['x0'] + x
                if 0 <= xx < W:
                    canvas[yy, xx] = c
    # optional per-frame pixel edits [[x,y,char],...] relative to ground
    for x, y, c in fr.get('px', []):
        canvas[gy + y, gx + x] = c
    return canvas


def _sw(act, sh):  # per-frame 'shadow': int = shadow half-width (e.g. smaller in the air), bool = on/off
    return sh if isinstance(sh, int) and not isinstance(sh, bool) and sh > 0 else act.get('shadow_w', 8)


def shadow_bg(W, H, gx, gy, s, bg=(0x6e, 0x6e, 0x6e), shadow=True, w=9):
    im = Image.new('RGB', (W * s, H * s), bg)
    if shadow:
        d = ImageDraw.Draw(im)
        col = tuple(int(c * 0.8) for c in bg)
        for dx in range(-w, w + 1):
            r = 1 if abs(dx) > w - 3 else 2
            d.rectangle([(gx + dx) * s, (gy - r + 1) * s, (gx + dx + 1) * s - 1, (gy + 1) * s - 1], fill=col) if False else None
        # simple ellipse of pixels
        for yy in range(-1, 2):
            half = w if yy == 0 else w - 3
            d.rectangle([(gx - half) * s, (gy + yy - 0) * s, (gx + half + 1) * s - 1, (gy + yy + 1) * s - 1], fill=col) if yy != 0 else None
        d.rectangle([(gx - w) * s, gy * s, (gx + w + 1) * s - 1, (gy + 1) * s - 1], fill=col)
        d.rectangle([(gx - w + 3) * s, (gy - 1) * s, (gx + w - 2) * s - 1, gy * s - 1], fill=col)
        d.rectangle([(gx - w + 3) * s, (gy + 1) * s, (gx + w - 2) * s - 1, (gy + 2) * s - 1], fill=col)
    return im


def run(path, out=None, mirror=False, s=6, outdir=None):
    act = json.load(open(path))
    name = out or act['name']
    W, H = act['cell']
    gx, gy = act['ground']
    frames = [render_frame(act, f) for f in act['frames']]
    # afterimage ghosts: {"src": frame index|"self", "outline": char (silhouette mode), "off": [dx,dy], "ch": char, "dither": 0|1|2, "shake": ...}
    # drawn BEHIND the body silhouette of the current frame; dither 1 = checker, 2 = sparse 1/4
    import numpy as _np
    base = [f.copy() for f in frames]
    for i, f in enumerate(act['frames']):
        for gh in f.get('ghosts', []):
            src = base[i if gh['src'] == 'self' else gh['src']]; dx, dy = gh['off']; ch = gh.get('ch', 'R'); dt = gh.get('dither', 0)
            oc = gh.get('outline')  # silhouette mode: outline pixels -> oc, interior -> ch
            cur = frames[i].copy()
            for y, x in zip(*_np.where(src != '.')):
                yy, xx = y + dy, x + dx
                if not (0 <= yy < H and 0 <= xx < W) or cur[yy, xx] != '.':
                    continue
                if oc and src[y, x] == '#':
                    cur[yy, xx] = oc; continue
                if dt == 1 and (xx + yy) % 2: continue
                if dt == 2 and (xx % 2 or yy % 2): continue
                if dt == 3 and yy % 2: continue
                if dt == 4 and yy % 3: continue
                cur[yy, xx] = ch
            frames[i] = cur
        if 'shake' in f:
            dx, dy = f['shake']; frames[i] = _np.roll(_np.roll(frames[i], dy, 0), dx, 1)
    if mirror:
        frames = [f[:, ::-1] for f in frames]
        gx = W - 1 - gx
    outdir = outdir or ROOT
    fdir = os.path.join(outdir, 'frames', name)
    os.makedirs(fdir, exist_ok=True)
    rgbas = []
    for i, f in enumerate(frames):
        a = cm.to_rgba(f)
        rgbas.append(a)
        Image.fromarray(a, 'RGBA').save(os.path.join(fdir, 'f%02d.png' % i))
        cm.write_cm(os.path.join(fdir, 'f%02d.txt' % i), f)
    # 1x sprite sheet
    sheet = np.zeros((H, W * len(frames), 4), np.uint8)
    for i, a in enumerate(rgbas):
        sheet[:, i * W:(i + 1) * W] = a
    os.makedirs(os.path.join(outdir, 'sheets'), exist_ok=True)
    Image.fromarray(sheet, 'RGBA').save(os.path.join(outdir, 'sheets', name + '_1x.png'))
    # GIF
    ms = [f.get('ms', 100) for f in act['frames']]
    shadow = act.get('shadow', True)
    ims = []
    for i, a in enumerate(rgbas):
        sh = act['frames'][i].get('shadow', shadow)
        b = shadow_bg(W, H, gx, gy, s, shadow=sh, w=_sw(act, sh)).convert('RGBA')
        b.alpha_composite(Image.fromarray(a, 'RGBA').resize((W * s, H * s), Image.NEAREST))
        ims.append(b.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=64))
    os.makedirs(os.path.join(outdir, 'gifs'), exist_ok=True)
    ims[0].save(os.path.join(outdir, 'gifs', name + '.gif'), save_all=True, append_images=ims[1:],
                duration=ms, loop=0, disposal=1, optimize=False)
    # contact sheet (labels): crop to union bbox, keep width <= 1000px
    m = np.zeros((H, W), bool)
    for f in frames:
        m |= (f != '.')
    ys, xs = np.where(m)
    cy0, cy1 = max(ys.min() - 2, 0), min(ys.max() + 3, H)
    cx0, cx1 = max(min(xs.min(), gx - 9) - 2, 0), min(max(xs.max(), gx + 9) + 3, W)
    cw, ch = cx1 - cx0, cy1 - cy0
    best = None  # pick the column count giving the largest scale within 1000x1000
    for cols in range(1, len(frames) + 1):
        rows = (len(frames) + cols - 1) // cols
        cs = min(4, (1000 - 4 * (cols + 1)) // (cols * cw), (1000 - 4 * (rows + 1) - 14 * rows) // (rows * ch))
        if cs >= 1 and (best is None or cs > best[0] or (cs == best[0] and rows < best[2])):
            best = (cs, cols, rows)
    cs, cols, rows = best if best else (1, len(frames), 1)
    lab = 14
    CS = Image.new('RGB', (cols * cw * cs + (cols + 1) * 4, rows * (ch * cs + lab) + (rows + 1) * 4), (40, 40, 40))
    d = ImageDraw.Draw(CS)
    for i, a in enumerate(rgbas):
        c, r = i % cols, i // cols
        x0, y0 = 4 + c * (cw * cs + 4), 4 + r * (ch * cs + lab + 4)
        _sh = act['frames'][i].get('shadow', shadow)
        b = shadow_bg(W, H, gx, gy, 1, shadow=_sh, w=_sw(act, _sh)).convert('RGBA')
        b.alpha_composite(Image.fromarray(a, 'RGBA'))
        b = b.crop((cx0, cy0, cx1, cy1)).resize((cw * cs, ch * cs), Image.NEAREST)
        CS.paste(b.convert('RGB'), (x0, y0 + lab))
        d.text((x0 + 2, y0 + 1), '%d %dms %s' % (i, ms[i], act['frames'][i].get('label', ''))[:cw * cs // 6], fill=(230, 230, 230))
    CS.save(os.path.join(outdir, 'sheets', name + '_sheet.png'))
    return frames


if __name__ == '__main__':
    a = sys.argv[1:]
    out = a[a.index('--out') + 1] if '--out' in a else None
    s = int(a[a.index('--s') + 1]) if '--s' in a else 6
    run(a[0], out, '--mirror' in a, s)
    print('ok', out or json.load(open(a[0]))['name'])
