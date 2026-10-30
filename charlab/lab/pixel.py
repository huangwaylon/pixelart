"""charlab pixel chain: Blender passes -> locked-palette pixel walk at a target sprite height.
  python pixel.py RENDER_DIR MODEL.json OUT_DIR SIZES(32,48,64,96) [VIEWS]
Per size S (figure height in px; the hi-res render has the rest figure at FIG=768 px, so the supersample is f = 768/S):
  1 labels   : per 1x cell, the majority (material, line group) of its f x f hi-res block
  2 outline  : vector line on the hi-res silhouette (vecline.py), 1 px, closed, pixel-perfect, palette 'outline'
  3 shading  : one key light from the screen's upper left; N.L from the camera normals averaged in the cell and smoothed
               inside each material; 2 tones (base / shade) + 'hi' only where the palette has one (hair_hi); face skin is
               always flat; 1-px occlusion shadow under any nearer part (chin, fringe, hems); tiny band islands removed
  4 lines    : interior lines only where the line group changes (arm|body, leg|leg, hair|face, hat|face, pack|body ...)
               AND the depth steps; drawn on the far side (hair|face on the hair side); K on shadow, sel-out shade on lit
  5 face     : eyes + brows only, glyphs sized from the head's pixel height, placed at the 3D eye surface points
               (Blender anchors), hidden by depth/facing, ink clipped to face skin, an eye under 60 % visible is dropped
  6 export   : 1x frames (PNG + key grid), 1x strip, 4x GIF (S | SE | E, loop, 120 ms), 4x contact sheet, gates.json
Deterministic: no randomness, every tie broken by index order."""
import json, os, sys
import numpy as np
from scipy import ndimage as nd
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '../../docs/team_review/2026-10-30/line_art'))
from vecline import vec_line
import lamet

KEY = np.array([-0.55, 0.62, -0.56]); KEY = KEY / np.linalg.norm(KEY)
GI = {'bg': 0, 'head': 1, 'hair': 2, 'hat': 3, 'body': 4, 'armL': 5, 'armR': 6, 'legL': 7, 'legR': 8, 'pack': 9}
T_SH = 0.10          # N.L below this -> shade tone
T_HI = 0.80          # N.L above this -> hi tone (only materials with a hi key)
CAST_T = 0.035       # depth step (H) for an occlusion shadow
LINE_T = 0.012       # depth step (H) for an interior line between different parts (arm|body, leg|leg ...)
LINE_T_CHIN = 0.04   # head|body (chin over neck/collar), pack|body
LINE_T_HAIR = 0.015  # hair|face, hat|face
BG = (122, 128, 140)
MS = 120
POLISH = os.environ.get('CHARLAB_POLISH', '1') == '1'


def hex2rgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


class Palette:
    """locked per-character palette: index 0 = transparent; every other index is a named palette key."""
    def __init__(self, meta):
        P = dict(meta['palette'])
        face = meta.get('face', {})
        P.setdefault('eye_hi', '#fbf8f2')
        self.keys = ['', 'outline']
        self.hex = {k: v for k, v in P.items()}
        self.mats = []
        for base, shade, hi in meta['mats']:
            self.mats.append(tuple(self.add(k) if k else 0 for k in (base, shade, hi)))
        bc = face.get('brow_colour', 'hair_shade')
        self.brow = self.add(bc if bc in P else ('hair' if 'hair' in P else 'outline'))
        self.eye_hi = self.add('eye_hi')
        self.K = 1

    def add(self, k):
        if k not in self.keys: self.keys.append(k)
        return self.keys.index(k)

    def rgb(self, i):
        return hex2rgb(self.hex[self.keys[i]]) if i else None

    def lut(self):
        a = np.zeros((len(self.keys), 4), np.uint8)
        for i, k in enumerate(self.keys):
            if i: a[i, :3] = hex2rgb(self.hex[k]); a[i, 3] = 255
        return a


def blocks(a, k):
    h, w = a.shape[:2]
    return a.reshape(h // k, k, w // k, k, *a.shape[2:])


def masked_smooth(v, m, sig):
    if sig <= 0: return v
    num = nd.gaussian_filter(np.where(m, v, 0.0), sig, mode='constant')
    den = nd.gaussian_filter(m.astype(float), sig, mode='constant')
    return np.where(m, num / np.maximum(den, 1e-6), v)


def size_params(S):
    return dict(sig={32: 0.6, 48: 0.75, 64: 0.85, 96: 0.9}.get(S, 0.85), eps={32: 0.6, 48: 0.7, 64: 0.8, 96: 0.8}.get(S, 0.8),
                minb={32: 2, 48: 3, 64: 4, 96: 6}.get(S, 4), minline={32: 3, 48: 3, 64: 4, 96: 4}.get(S, 4),
                nsig={32: 0.5, 48: 0.6, 64: 0.7, 96: 0.9}.get(S, 0.7), cast=1 if S <= 64 else 2,
                shrink={32: 0.0, 48: 0.25, 64: 0.5, 96: 0.5}.get(S, 0.5), thin={32: 1.1, 48: 1.1, 64: 1.1, 96: 1.0}.get(S, 1.1))


def silhouette(al, f, sp):
    """hi-res silhouette for the vector line.  Parts narrower than 2*thin px are widened (limbs stay >= 2 px of fill at
    every size); only the thick parts are eroded by shrink px so the 1-px line sits on their edge."""
    dist = nd.distance_transform_edt(al)
    r = sp['thin'] * f
    core = dist > r
    thick = nd.distance_transform_edt(~core) <= r + 1
    thin = al & ~thick
    s = int(round(sp['shrink'] * f))
    out = (dist > s) if s > 0 else al.copy()
    if thin.any():
        out |= nd.distance_transform_edt(~thin) <= r * 0.8
    return out


def remove_islands(mask, region, minsz):
    """flip connected components of mask (4-conn) smaller than minsz cells, within region."""
    lab, n = nd.label(mask & region)
    if not n: return mask
    sz = nd.sum(np.ones_like(lab), lab, range(1, n + 1))
    small = np.isin(lab, [i + 1 for i, s in enumerate(sz) if s < minsz])
    return mask & ~small


class Chain:
    def __init__(self, rdir, meta_path):
        self.rdir = rdir
        self.meta = json.load(open(meta_path)); self.info = json.load(open(os.path.join(rdir, 'frames.json')))
        self.pal = Palette(self.meta)
        self.skin = self.meta['skin_mat']; self.hair = self.meta['hair_mat']
        self.HI, self.FIG = self.info['hi'], self.info['fig']
        self._eyevis = {}

    # ------------------------------------------------------------------------------------------------ one frame
    def frame(self, view, i, S):
        HI = self.HI; f = self.FIG // S; N = HI // f; k4 = f // 4; sp = size_params(S)
        z = np.load(os.path.join(self.rdir, f'{view}_f{i:02d}.npz'))
        mat, grp = z['mat'].astype(np.int32), z['grp'].astype(np.int32)
        al = grp > 0
        code = mat * 16 + grp
        best = np.zeros((N, N)); lab = np.full((N, N), -1)
        for c in np.unique(code[al]):
            cnt = blocks(code == c, f).sum((1, 3))
            up = cnt > best; best[up] = cnt[up]; lab[up] = c
        nx4, ny4, dep4 = z['nx'].astype(float), z['ny'].astype(float), z['dep'].astype(float)
        v4 = dep4 > 0
        cnt4 = blocks(v4, k4).sum((1, 3))
        nx = blocks(nx4 * v4, k4).sum((1, 3)) / np.maximum(cnt4, 1)
        ny = blocks(ny4 * v4, k4).sum((1, 3)) / np.maximum(cnt4, 1)
        dep = np.where(cnt4 > 0, blocks(np.where(v4, dep4, 1e9), k4).min((1, 3)), 1e9)
        # ---- outline + inside
        al_e = silhouette(al, f, sp)
        line, inside = vec_line(al_e, N, f, sp['sig'], sp['eps'], 100.0)
        fill = inside & ~line
        # labels for every filled cell (nearest real label where the smoothed silhouette grew)
        have = lab >= 0
        if (fill & ~have).any() and have.any():
            idx = nd.distance_transform_edt(~have, return_distances=False, return_indices=True)
            lab = np.where(have, lab, lab[idx[0], idx[1]])
            dfill = dep[idx[0], idx[1]]; dep = np.where(cnt4 > 0, dep, dfill)
            nx = np.where(cnt4 > 0, nx, nx[idx[0], idx[1]]); ny = np.where(cnt4 > 0, ny, ny[idx[0], idx[1]])
        M = np.where(fill, lab // 16, -1); G = np.where(fill, lab % 16, 0)
        # ---- shading
        nz = -np.sqrt(np.clip(1 - nx ** 2 - ny ** 2, 0, 1))
        ndl = nx * KEY[0] + ny * KEY[1] + nz * KEY[2]
        tone = np.zeros((N, N), np.int32)
        for m in np.unique(M[M >= 0]):
            mm = M == m
            s = masked_smooth(ndl, mm, sp['nsig'])
            base, shade, hi = self.pal.mats[m]
            if shade: tone[mm & (s < T_SH)] = 1
            if hi: tone[mm & (s > T_HI)] = 2
        face = (M == self.skin) & (G == GI['head'])
        tone[face] = 0
        # occlusion shadow: a nearer, different part right above
        cast = np.zeros((N, N), bool)
        for dy in range(1, sp['cast'] + 1):
            up_d = np.full((N, N), 1e9); up_d[dy:] = dep[:-dy]
            up_f = np.zeros((N, N), bool); up_f[dy:] = fill[:-dy]
            up_l = np.full((N, N), -1); up_l[dy:] = lab[:-dy]
            c = fill & up_f & (up_l != lab) & (up_d < dep - CAST_T)
            if dy > 1: c &= np.roll(cast, 1, 0)
            cast |= c
        for m in np.unique(M[M >= 0]):
            if self.pal.mats[m][1]: tone[(M == m) & cast] = 1
        # clean tiny band islands (both directions), per material
        for m in np.unique(M[M >= 0]):
            mm = M == m
            for t in (1, 2):
                sh = (tone == t) & mm
                keep = remove_islands(sh, mm, sp['minb'] if t == 1 else 2)
                tone[sh & ~keep] = 0
            lit = (tone == 0) & mm
            keep = remove_islands(lit, mm, sp['minb'])
            tone[lit & ~keep & ~face] = 1 if self.pal.mats[m][1] else 0
        # ---- interior lines
        il = self.interior(G, dep, fill, line, N, sp)
        # ---- compose
        out = np.zeros((N, N), np.int32)
        for m in np.unique(M[M >= 0]):
            b, s, h = self.pal.mats[m]
            mm = M == m
            out[mm] = b
            if s: out[mm & (tone == 1)] = s
            if h: out[mm & (tone == 2)] = h
        for m in np.unique(M[M >= 0]):
            b, s, h = self.pal.mats[m]
            mm = (M == m) & il
            # sel-out: interior lines take the material's shade (always at <= 48 px, on lit cells above); K on shadow / flat
            col = np.full(tone.shape, self.pal.K if s == 0 else s) if S <= 48 else np.where((tone == 1) | (s == 0), self.pal.K, s)
            out[mm] = col[mm]
        out[line] = self.pal.K
        if POLISH: out = polish(out, self.pal.K)
        pre_face = out.copy()
        eyes = self.face(view, i, S, f, out, M, G, dep)
        return dict(grid=out, pre_face=pre_face, line=line, il=il, N=N, eyes=eyes)

    def interior(self, G, dep, fill, line, N, sp):
        il = np.zeros((N, N), bool)
        hair_side = np.zeros((N, N), bool)
        for dy, dx in ((0, 1), (1, 0)):
            a = (slice(0, N - dy), slice(0, N - dx)); b = (slice(dy, N), slice(dx, N))
            ok = fill[a] & fill[b] & (G[a] != G[b])
            ga, gb = G[a], G[b]; da, db = dep[a], dep[b]
            soft = ((ga == GI['hair']) & (gb == GI['head'])) | ((gb == GI['hair']) & (ga == GI['head'])) | \
                   ((ga == GI['hat']) & (gb == GI['head'])) | ((gb == GI['hat']) & (ga == GI['head'])) | \
                   ((ga == GI['hat']) & (gb == GI['hair'])) | ((gb == GI['hat']) & (ga == GI['hair']))
            chin = ((ga == GI['head']) & (gb == GI['body'])) | ((gb == GI['head']) & (ga == GI['body'])) | (ga == GI['pack']) | (gb == GI['pack'])
            thr = np.where(soft, LINE_T_HAIR, np.where(chin, LINE_T_CHIN, LINE_T))
            far_b = ok & (db - da > thr); far_a = ok & (da - db > thr)
            # hair|face: always on the hair side so the face keeps its width
            hf_a = ok & (ga == GI['hair']) & (gb == GI['head']) & (np.abs(da - db) > LINE_T_HAIR)
            hf_b = ok & (gb == GI['hair']) & (ga == GI['head']) & (np.abs(da - db) > LINE_T_HAIR)
            far_a = (far_a & ~hf_b) | hf_a; far_b = (far_b & ~hf_a) | hf_b
            il[a] |= far_a; il[b] |= far_b
        il &= fill
        # never thin a part below 2 px: drop line cells whose own part would be 1 px across there
        for _ in range(1):
            p = np.pad(G, 1, constant_values=0)
            same_lr = (p[1:-1, :-2] == G) | (p[1:-1, 2:] == G)
            same_ud = (p[:-2, 1:-1] == G) | (p[2:, 1:-1] == G)
            il &= same_lr & same_ud | ~fill
        # pixel-perfect + no 2x2 with the outline + minimum length
        K = il | line
        c = K[:-1, :-1] & K[1:, :-1] & K[:-1, 1:] & K[1:, 1:]
        for y, x in zip(*np.nonzero(c)):
            for yy, xx in ((y, x), (y, x + 1), (y + 1, x), (y + 1, x + 1)):
                if il[yy, xx]: il[yy, xx] = False; break
        labn, n = nd.label(il, np.ones((3, 3)))
        if n:
            sz = nd.sum(il, labn, range(1, n + 1))
            il &= np.isin(labn, [j + 1 for j, s_ in enumerate(sz) if s_ >= sp['minline']])
        return il

    # ------------------------------------------------------------------------------------------------ face
    def eye_vis(self, view, s):
        """per view and eye, decided once for the whole cycle (majority over the frames): facing the camera and not covered
        (anchor depth vs the hi-res depth pass at the anchor).  The head barely turns in a walk, so this kills eye flicker."""
        key = (view, s)
        if key not in self._eyevis:
            votes = 0; nf = self.info['nf']
            for i in range(nf):
                a = self.info['frames'][i]['views'][view]['anchors'].get('eye.' + s)
                if not a or a['facing'] < 0.12: continue
                d4 = np.load(os.path.join(self.rdir, f'{view}_f{i:02d}.npz'))['dep'].astype(float)
                yy, xx = int(a['y'] / 4), int(a['x'] / 4)
                win = d4[max(0, yy - 1):yy + 2, max(0, xx - 1):xx + 2]; win = win[win > 0]
                if len(win) and a['depth'] <= win.max() + 0.03: votes += 1
            self._eyevis[key] = votes * 2 >= nf
        return self._eyevis[key]

    def glyphs(self, S, f):
        fs = self.meta.get('face', {})
        hpx = self.info['ppu'] / f                       # head height in px at this size
        eh = max(1, int(round(fs.get('eye_size', 0.12) * hpx * 1.15)))
        ew = max(1, int(round(eh * 0.7)))
        hl = bool(fs.get('highlight', False)) and S >= 48 and ew >= 2 and eh >= 3

        def eye(far):
            w = ew - 1 if (far and ew >= 2) else ew
            g = np.full((eh, w), 'K', dtype='<U1')
            if w >= 3 and eh >= 4:
                g[0, 0] = g[0, -1] = g[-1, 0] = g[-1, -1] = ' '
            if hl:
                r = 1 if (w >= 3 and eh >= 4) else 0
                g[r, 0 if w < 3 else 1 if eh >= 5 else 0] = 'W'
            return g
        brow = None
        if hpx >= 12:
            bw = ew + (1 if ew >= 2 else 0)
            brow = dict(w=bw, gap=max(1, int(round(eh * 0.35))), arch=fs.get('brows', 'short_flat') == 'soft_arch' and bw >= 3)
        return eye, brow, hpx

    def face(self, view, i, S, f, out, M, G, dep):
        an = self.info['frames'][i]['views'][view]['anchors']
        if 'eye.L' not in an: return []
        eye, brow, hpx = self.glyphs(S, f)
        skin = (M == self.skin) & (G == GI['head'])
        N = out.shape[0]
        cands = []
        for s in ('L', 'R'):
            a = an['eye.' + s]
            if not self.eye_vis(view, s): continue
            x, y = a['x'] / f, a['y'] / f
            yi, xi = int(y), int(x)
            if not (0 <= yi < N and 0 <= xi < N): continue
            cands.append((s, x, y, a['facing']))
        if not cands: return []
        # near eye = more facing; the far eye is narrower in 3/4 views
        far_s = None
        if len(cands) == 2 and abs(cands[0][3] - cands[1][3]) > 0.15:
            far_s = min(cands, key=lambda c: c[3])[0]
        placed = []
        for s, x, y, fc in sorted(cands, key=lambda c: c[1]):
            g = eye(s == far_s)
            h, w = g.shape
            bx = int(np.floor(x - w / 2 + 0.5)); y0 = int(np.floor(y - h / 2 + 0.5))
            ink = [(r, c) for r in range(h) for c in range(w) if g[r, c] != ' ']
            best = None
            for dx in (0, -1, 1, -2, 2):        # nudge off the face edge (1-2 px) onto skin; prefer no shift
                x0 = bx + dx
                if placed and x0 <= placed[-1][0] + placed[-1][2]: continue   # keep >= 1 px between the eyes
                vis = sum(1 for r, c in ink if 0 <= y0 + r < N and 0 <= x0 + c < N and skin[y0 + r, x0 + c]) / len(ink)
                if best is None or vis > best[0] + 1e-9: best = (vis, x0)
                if vis >= 0.999: break
            if best is None: continue
            placed.append((best[1], y0, w, h, g, s))
        res = []
        for x0, y0, w, h, g, s in placed:
            ink = [(y0 + r, x0 + c, g[r, c]) for r in range(h) for c in range(w) if g[r, c] != " "]
            vis = [(yy, xx, ch) for yy, xx, ch in ink if 0 <= yy < N and 0 <= xx < N and skin[yy, xx]]
            if not vis: continue
            for yy, xx, ch in vis:
                out[yy, xx] = self.pal.K if ch == 'K' else self.pal.eye_hi
            if brow:
                by = y0 - brow['gap'] - 1
                bx0 = x0 - (brow['w'] - w) // 2 if s == 'R' else x0 - (brow['w'] - w + 1) // 2
                pts = [(by, bx0 + c) for c in range(brow['w'])]
                if brow['arch']:
                    outer = 0 if x0 < (placed[0][0] + placed[-1][0]) / 2 or len(placed) == 1 else brow['w'] - 1
                    pts[outer] = (by + 1, pts[outer][1])
                for yy, xx in pts:
                    if 0 <= yy < N and 0 <= xx < N and skin[yy, xx] and out[yy, xx] != self.pal.K:
                        out[yy, xx] = self.pal.brow
            res.append(dict(side=s, x=x0, y=y0, w=w, h=h))
        return res


def defect_score(grid, K):
    op = grid > 0
    zig, irr, kink, npx, bad = lamet.run_defects(op)
    g = np.where(grid == K, 'K', np.where(op, 'a', '.'))
    dm = lamet.doubles(g); dbl = int(dm.sum())
    N_, S_, W_, E_ = lamet.n4(~op)
    gap = int((op & (N_ | S_ | W_ | E_) & (grid != K)).sum())
    c = (grid == K); cl = int((c[:-1, :-1] & c[1:, :-1] & c[:-1, 1:] & c[1:, 1:]).sum())
    return zig * 4 + dbl + cl + 50 * gap, [p_ for k, p_ in bad if k == 'zig'] + [tuple(q) for q in np.argwhere(dm)]


def polish(grid, K, max_iter=40):
    """local 1-px outline edits around lamet zigzags (the lock pipeline's dezig/polish idea): add a K pixel on the background
    next to the line, or remove a K pixel that touches no fill; keep an edit only if the defect score drops (gap-free)."""
    best, zz = defect_score(grid, K)
    H, W = grid.shape
    for _ in range(max_iter):
        if not zz: break
        improved = False
        for (y, x) in zz:
            cands = []
            for yy in range(y - 2, y + 3):
                for xx in range(x - 2, x + 3):
                    if not (0 < yy < H - 1 and 0 < xx < W - 1): continue
                    v = grid[yy, xx]; nb = [grid[yy - 1, xx], grid[yy + 1, xx], grid[yy, xx - 1], grid[yy, xx + 1]]
                    if v == 0 and any(n == K for n in nb): cands.append((yy, xx, K))
                    elif v == K and not any(n not in (0, K) for n in nb): cands.append((yy, xx, 0))
            for yy, xx, nv in cands:
                old = grid[yy, xx]; grid[yy, xx] = nv
                s, z2 = defect_score(grid, K)
                if s < best:
                    best, zz = s, z2; improved = True; break
                grid[yy, xx] = old
            if improved: break
        if not improved: break
    return grid


# ---------------------------------------------------------------------------------------------------- exports + gates
def chars(grid, pal, mask_eyes=None):
    g = np.full(grid.shape, '.', dtype='<U1')
    for i in range(1, len(pal.keys)):
        g[grid == i] = 'K' if i == pal.K else chr(ord('a') + (i % 26))
    return g


def gif_ok(path):
    b = open(path, 'rb').read(); loop = b'NETSCAPE2.0' in b
    delays, i = [], b.find(b'\x21\xf9\x04')
    while i != -1:
        delays.append(10 * int.from_bytes(b[i + 4:i + 6], 'little')); i = b.find(b'\x21\xf9\x04', i + 8)
    return dict(loop=loop, frames=len(delays), min_ms=min(delays) if delays else 0, ok=loop and len(delays) > 1 and min(delays) >= 20)


def save_gif(frames_rgba, path, scale, ms=MS, bg=BG):
    ims = []
    for a in frames_rgba:
        h, w = a.shape[:2]
        im = Image.new('RGB', (w, h), bg); im.paste(Image.fromarray(a, 'RGBA'), (0, 0), Image.fromarray(a, 'RGBA'))
        ims.append(im.resize((w * scale, h * scale), Image.NEAREST).quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=ms, loop=0, disposal=1, optimize=False)


def run(rdir, meta_path, odir, sizes, views=None):
    ch = Chain(rdir, meta_path); pal = ch.pal; lut = pal.lut()
    views = views or ch.info['views']; nf = ch.info['nf']
    order = [v for v in ('S', 'SE', 'E') if v in views] + [v for v in views if v not in ('S', 'SE', 'E')]
    summary = {}
    for S in sizes:
        od = os.path.join(odir, str(S)); os.makedirs(od, exist_ok=True)
        F = {v: [ch.frame(v, i, S) for i in range(nf)] for v in order}
        N = F[order[0]][0]['N']
        # crop box shared by all frames/views at this size (pad 1)
        occ = np.zeros((N, N), bool)
        for v in order:
            for r in F[v]: occ |= r['grid'] > 0
        ys, xs = np.nonzero(occ)
        y0, y1 = max(0, ys.min() - 1), min(N, ys.max() + 2); x0, x1 = max(0, xs.min() - 1), min(N, xs.max() + 2)
        gates = dict(size=S, cell=[int(N), int(N)], crop=[int(x0), int(y0), int(x1), int(y1)], views={}, palette=pal.keys[1:])
        rgba = {v: [] for v in order}
        for v in order:
            ms = []
            for i, r in enumerate(F[v]):
                g = r['grid']
                img = lut[g]
                rgba[v].append(img)
                Image.fromarray(img, 'RGBA').save(os.path.join(od, f'{v}_f{i:02d}.png'))
                cg = chars(r['pre_face'], pal)
                m = lamet.metrics(cg)
                cols = sorted(set(np.unique(g).tolist()) - {0})
                ms.append(dict(zig=m['zig'], dbl=m['dbl'], gap=m['gap'], clump=m['clump'], mono=round(m['mono'], 3), intK=m['intK'],
                               orphK=m['orphK'], colours=len(cols), eyes=len(r['eyes']), il=int(r['il'].sum())))
                open(os.path.join(od, f'{v}_f{i:02d}.txt'), 'w').write('\n'.join(''.join(row) for row in chars(g, pal)[y0:y1, x0:x1]) + '\n')
            gates['views'][v] = ms
        # line boil (silhouette / interior) per view, lamet definition
        for v in order:
            fr = [chars(r['pre_face'], pal)[y0:y1, x0:x1] for r in F[v]]
            s_, i_ = lamet.flicker(fr)
            gates['views'][v + '_boil'] = dict(sil=round(s_, 3), int=round(i_, 3))
        # strips + gif + sheet
        crop = lambda a: a[y0:y1, x0:x1]
        strip = np.concatenate([np.concatenate([crop(a) for a in rgba[v]], 1) for v in order], 0)
        Image.fromarray(strip, 'RGBA').save(os.path.join(od, 'walk_strip1x.png'))
        gap = np.zeros((y1 - y0, 2, 4), np.uint8)
        gframes = []
        for i in range(nf):
            parts = []
            for j, v in enumerate(order):
                parts.append(crop(rgba[v][i]))
                if j < len(order) - 1: parts.append(gap)
            gframes.append(np.concatenate(parts, 1))
        save_gif(gframes, os.path.join(od, 'walk_4x.gif'), 4)
        sheet = Image.new('RGB', (strip.shape[1] * 4, strip.shape[0] * 4), BG)
        sheet.paste(Image.fromarray(strip, 'RGBA').resize((strip.shape[1] * 4, strip.shape[0] * 4), Image.NEAREST), (0, 0),
                    Image.fromarray(strip, 'RGBA').resize((strip.shape[1] * 4, strip.shape[0] * 4), Image.NEAREST))
        sheet.save(os.path.join(od, 'sheet_4x.png'))
        gates['gif'] = gif_ok(os.path.join(od, 'walk_4x.gif'))
        allm = [m for v in order for m in gates['views'][v]]
        pal_n = len(pal.keys) - 1
        gates['summary'] = dict(
            zig_max=max(m['zig'] for m in allm), zig_mean=round(float(np.mean([m['zig'] for m in allm])), 2),
            dbl_max=max(m['dbl'] for m in allm), gap_max=max(m['gap'] for m in allm), clump_max=max(m['clump'] for m in allm),
            mono_mean=round(float(np.mean([m['mono'] for m in allm])), 3), colours_max=max(m['colours'] for m in allm), palette=pal_n,
            off_palette=0, eyes_min=min(m['eyes'] for m in gates['views'].get('SE', allm)) if 'SE' in gates['views'] else None,
            boil_sil=round(float(np.mean([gates['views'][v + '_boil']['sil'] for v in order])), 3))
        sm = gates['summary']
        gates['pass'] = dict(zig=sm['zig_max'] <= 1, dbl=sm['dbl_max'] <= 3, gap=sm['gap_max'] == 0, colours=sm['colours_max'] <= pal_n,
                             gif=gates['gif']['ok'])
        gates['PASS'] = all(gates['pass'].values())
        json.dump(gates, open(os.path.join(od, 'gates.json'), 'w'), indent=1)
        summary[S] = dict(PASS=gates['PASS'], **sm)
        print(f'  {os.path.basename(odir)} {S}px: ' + ' '.join(f'{k}={v}' for k, v in sm.items()) + f'  PASS={gates["PASS"]}', flush=True)
    json.dump(summary, open(os.path.join(odir, 'summary.json'), 'w'), indent=1)
    return summary


if __name__ == '__main__':
    rdir, meta, odir = sys.argv[1:4]
    sizes = [int(s) for s in (sys.argv[4] if len(sys.argv) > 4 else '32,48,64,96').split(',')]
    views = sys.argv[5].split(',') if len(sys.argv) > 5 else None
    run(rdir, meta, odir, sizes, views)
