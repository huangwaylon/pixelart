#!/usr/bin/env python3
"""Finisher: candidate frames -> locked, cleaned, FX'd animation frames.
fin.py PLAN.json   (plan: {"action","dir","frames":[{"src": path, "head": variant, "bow":[dx,dy], "fx":[...],
                   "motion":[dx,dy], "blade":1, "air":0|1, "ms": int, "smear": {...}}], "out": dir})
Per frame:  head stamp (master head variant) placed on the r6 head_offset trajectory (+ constant fit offset),
            Gemini blade erased, procedural katana from r6 blade angle at the detected/meta grip,
            feet pinned (y=120 on ground frames, guide lift on air frames), x locked to the head trajectory,
            spatial clean (orphans, outline repair), temporal de-crawl vs previous frame, FX."""
import json, math, os, sys
import numpy as np
from PIL import Image
ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
sys.path.insert(0, ROOT + '/v2/pixel/anim'); sys.path.insert(0, ROOT + '/v2/pixel/tools')
import fx2  # noqa
from fx2 import m, put, RGB, FOOT  # noqa
MASTER = ROOT + '/v2/pixel/master/SE_katana.png'
DARK = set('#rDh')


def load(p):
    return np.array(Image.open(p).convert('RGBA'))


def opaque(a):
    return a[..., 3] >= 128


def shift(a, dx, dy):
    o = np.zeros_like(a); H, W = a.shape[:2]
    ys, xs = np.nonzero(opaque(a)); ny, nx = ys + dy, xs + dx
    ok = (ny >= 0) & (ny < H) & (nx >= 0) & (nx < W)
    o[ny[ok], nx[ok]] = a[ys[ok], xs[ok]]; return o


def head_sprite_bow(H, bow):
    """shift the bow (red pixels in the top 38% of the head sprite) by bow=(dx,dy) for overlap/lag."""
    if not bow or bow == [0, 0]:
        return H
    h, w = H.shape[:2]; dx, dy = bow
    pad = 2; Hp = np.zeros((h + 2 * pad, w + 2 * pad, 4), np.uint8); Hp[pad:pad + h, pad:pad + w] = H
    top = int(h * 0.38) + pad
    red = m(Hp, 'rREe'); red[top:] = False
    # bow outline: '#' pixels touching bow red in the top band
    ol = m(Hp, '#'); ol[top:] = False
    rp = np.pad(red, 1); near = np.zeros_like(red)
    for yy in (-1, 0, 1):
        for xx in (-1, 0, 1):
            near |= rp[1 + yy:1 + yy + red.shape[0], 1 + xx:1 + xx + red.shape[1]]
    hairish = m(Hp, 'hHj')
    bowm = red | (ol & near & ~hairish)
    # only outline pixels that don't border hair (keep hair outline)
    B = np.zeros_like(Hp); B[bowm] = Hp[bowm]
    out = Hp.copy(); out[bowm] = 0
    # refill vacated pixels that lie inside the hair with hair base / outline
    Bs = shift(B, dx, dy)
    vac = bowm & ~opaque(Bs)
    hp = np.pad(hairish, 1); nh = np.zeros_like(hairish)
    for yy, xx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nh |= hp[1 + yy:1 + yy + red.shape[0], 1 + xx:1 + xx + red.shape[1]]
    out[vac & nh] = np.append(RGB['H'], 255)
    sel = opaque(Bs); out[sel] = Bs[sel]
    fx2.prune_outline(out)
    return out


def head_center(box):
    y0, y1, x0, x1 = box; return (x0 + x1) / 2, (y0 + y1) / 2


def stamp_at(fr, Hv, oy, ox):
    """erase generated head (hair/skin/iris/blush; bow red+outline in the top third) then paste Hv at (oy, ox)."""
    fy0, fy1, fx0, fx1 = fx2.head_box(fr)
    out = fr.copy()
    er = np.zeros(fr.shape[:2], bool); er[max(0, fy0 - 1):fy1 + 2, max(0, fx0 - 1):fx1 + 2] = True
    top3 = np.zeros_like(er); top3[:fy0 + (fy1 - fy0) // 3] = True
    kill = er & ~m(fr, 'mn') & (m(fr, 'hHj123iIp') | (top3 & m(fr, 'rREe#')))
    out[kill] = 0
    hh, hw = Hv.shape[:2]
    hm = np.zeros(fr.shape[:2], bool)
    for y in range(hh):
        for x in range(hw):
            if Hv[y, x, 3] >= 128 and 0 <= oy + y < 128 and 0 <= ox + x < 128:
                out[oy + y, ox + x] = Hv[y, x]; hm[oy + y, ox + x] = True
    # fill holes between chin and collar: transparent px in the erase box with head above and body below (<=5px)
    for x in range(max(0, fx0 - 1), min(128, fx1 + 2)):
        col = opaque(out)[:, x]
        for y in range(max(0, fy0), min(127, fy1 + 3)):
            if not col[y] and hm[:y, x].any() and col[y + 1:y + 6].any():
                hy = np.nonzero(hm[:y, x])[0].max()
                if y - hy <= 5:
                    out[y, x] = np.append(RGB['1'], 255)
    fx2.prune_outline(out)
    return out, hm


def blade_draw(a, grip, ang, L=34, hl=7, protect=None):
    """katana: handle (hl px, d/D) behind the grip, guard, 3px blade (w/n/#) of length L ahead."""
    gx, gy = grip; c, s = math.cos(ang), math.sin(ang)
    steep = abs(s) > abs(c)
    def P(y, x, col):
        if protect is not None and 0 <= y < 128 and 0 <= x < 128 and protect[y, x]:
            return
        put(a, y, x, col)
    # handle
    for (x, y) in fx2.line(int(round(gx - c * hl)), int(round(gy - s * hl)), int(round(gx)), int(round(gy))):
        P(y, x, 'd')
        if steep: P(y, x + 1, 'D')
        else: P(y + 1, x, 'D')
    # blade
    pts = fx2.line(int(round(gx + c * 2)), int(round(gy + s * 2)), int(round(gx + c * L)), int(round(gy + s * L)))
    for (x, y) in pts:
        if steep:
            P(y, x - 1, 'w'); P(y, x, 'n'); P(y, x + 1, '#')
        else:
            P(y - 1, x, 'w'); P(y, x, 'n'); P(y + 1, x, '#')
    x, y = pts[-1]; P(y, x, 'w')
    nx_, ny_ = -s, c
    for t in (-2, -1, 0, 1, 2):
        P(int(round(gy + s * 1 + ny_ * t)), int(round(gx + c * 1 + nx_ * t)), 'D')
    return pts


def outline_repair(a):
    """every opaque silhouette pixel 4-adjacent to transparency must be dark; if it's a light colour and its
    outward neighbour is transparent, add a '#' pixel outside (only where that keeps a 1px line)."""
    op = opaque(a); H, W = op.shape
    dark = m(a, '#rDhRdm') | m(a, 'uU')
    add = []
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if op[y, x] and not dark[y, x]:
                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    if not op[y + dy, x + dx]:
                        add.append((y + dy, x + dx))
    for y, x in add:
        put(a, y, x, '#')
    return len(add)


def orphans(a, protect='wiIp'):
    """1px specks: colour with no same-colour 8-neighbour -> majority neighbour (transparent counts)."""
    H, W = a.shape[:2]
    key = np.where(opaque(a), a[..., 0].astype(int) * 65536 + a[..., 1].astype(int) * 256 + a[..., 2], -1)
    prot = m(a, protect); n = 0
    for y in range(H):
        for x in range(W):
            k = key[y, x]
            if k < 0 or prot[y, x]:
                continue
            nb = [key[y + dy, x + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                  if (dy or dx) and 0 <= y + dy < H and 0 <= x + dx < W]
            if k in nb:
                continue
            vals, cnt = np.unique(nb, return_counts=True); v = vals[cnt.argmax()]
            if v < 0: a[y, x] = 0
            else: a[y, x, :3] = [(v >> 16) & 255, (v >> 8) & 255, v & 255]; a[y, x, 3] = 255
            n += 1
    return n


def decrawl(cur, prev, lock=None, r=2):
    """Kill pixel crawl: pixels that differ from prev while their (2r+1)^2 neighbourhood is otherwise identical
    to prev (static region, isolated change <=3px) are reverted to prev. lock: mask where prev wins entirely."""
    if prev is None:
        return cur, 0
    out = cur.copy()
    diff = (cur != prev).any(-1)
    H, W = diff.shape; n = 0
    if lock is not None:
        out[lock] = prev[lock]; n += int((diff & lock).sum())
    dp = np.pad(diff, r)
    cnt = sum(dp[r + dy:r + dy + H, r + dx:r + dx + W].astype(int) for dy in range(-r, r + 1) for dx in range(-r, r + 1))
    iso = diff & (cnt <= 3)
    out[iso] = prev[iso]; n += int(iso.sum())
    return out, n


def comps_label(mask):
    from scipy import ndimage
    return ndimage.label(mask, structure=np.ones((3, 3)))


def keep_main(a, min_px=30):
    """drop opaque components smaller than min_px that are not the main body (floating debris)."""
    lab, n = comps_label(opaque(a))
    if n <= 1:
        return a
    sizes = np.bincount(lab.ravel()); sizes[0] = 0; big = sizes.argmax()
    out = a.copy()
    for k in range(1, n + 1):
        if k != big and sizes[k] < min_px:
            out[lab == k] = 0
    return out


def head_debris(a, hm, chin):
    """remove leftover generated hair/bow pixels outside the stamped head (above the chin)."""
    out = a.copy()
    from scipy import ndimage
    near = ndimage.binary_dilation(hm, iterations=4)
    zone = np.zeros_like(hm); zone[:max(0, chin - 6)] = True
    hair = m(a, 'hHj') & ~hm & zone
    bowish = m(a, 'rREe#') & ~hm & near & zone
    out[hair | bowish] = 0
    fx2.prune_outline(out)
    return out


def obi_cx(a):
    ot = fx2.obi_top(a)
    ob = m(a, 'Dd'); ob[:ot] = False; ob[ot + 4:] = False
    xs = np.nonzero(ob)[1]
    return xs.mean() if len(xs) else np.nonzero(opaque(a))[1].mean()


def guide_lift(gd, i, scale):
    g = load(f'{gd}/f{i:02d}.png'); ys = np.nonzero(g[..., 3].any(1))[0]
    piv = json.load(open(gd + '/frames.json'))['pivot']
    return max(0.0, (piv[1] - ys.max()) * scale)


def main():
    plan = json.load(open(sys.argv[1]))
    act, d = plan['action'], plan.get('dir', 'SE')
    gd = f"{ROOT}/v2/anim/guides/{plan.get('guide', act + '_' + d)}"
    meta = json.load(open(gd + '/frames.json')); mf = meta['frames']
    out = plan['out']; os.makedirs(out, exist_ok=True)
    master = load(plan.get('master', MASTER))
    H0, mbox = fx2.head_sprite(master)
    mcx, mcy = head_center(mbox)
    fit = plan.get('head_fit', [0, 0])
    hx_ref = plan.get('hx_ref', float(np.mean([f['head_offset'][0] for f in mf])) if act in ('run', 'walk', 'idle') else 0.0)
    prev = None; cleans = []; log = []
    for i, fr in enumerate(plan['frames']):
        src = fr['src'] if os.path.isabs(fr['src']) else os.path.join(os.path.dirname(sys.argv[1]), fr['src'])
        a = load(src)
        mi = fr.get('meta', i); md = mf[mi]
        # ---- erase Gemini blade first (it confuses head box/pin); remember its grip
        be = fx2.blade_ends(a)
        if be and fr.get('blade', 1):
            fx2.erase_blade(a)
        a = keep_main(a)
        Hv = fx2.variant(H0, fr.get('head', 'neutral'))
        Hv = head_sprite_bow(Hv, fr.get('bow', [0, 0]))
        body = opaque(a) & ~m(a, 'mnw'); ys = np.nonzero(body.any(1))[0]
        air = fr.get('air', None)
        lift = guide_lift(gd, mi, meta['art_scale']) if air is None else fr.get('lift', 0)
        lift *= plan.get('lift_scale', 1.0)
        dy = int(round(FOOT - lift - ys.max())) + fr.get('dy', 0)
        if plan.get('xpin', 'head') == 'head':      # pin the head centre to master head x + r6 head_offset trajectory
            hcx0, _ = head_center(fx2.head_box(a))
            dx = int(round(plan.get('hx0', mcx) + plan.get('hx_scale', 1.0) * (md['head_offset'][0] - hx_ref) - hcx0)) + fr.get('dx', 0)
        else:
            ocx = obi_cx(a)
            dx = int(round(plan.get('x0', 64) - ocx)) + fr.get('dx', 0)
        a = shift(a, dx, dy)
        hb = fx2.head_box(a); gcx, gcy = head_center(hb)
        hh, hw = Hv.shape[:2]
        oy = hb[1] + 1 - hh + fr.get('head_dy', 0)
        ox = int(round(gcx - hw / 2)) + fr.get('head_dx', 0)
        a, hm = stamp_at(a, Hv, oy, ox)
        if fr.get('debris', 1):
            a = head_debris(a, hm, oy + hh)
        a = keep_main(a)
        # ---- procedural blade: r6 meta angle; grip = Gemini's hand (detected grip) or meta hilt rel. to obi
        if fr.get('blade', 1) and 'blade' in md:
            b = md['blade']
            hx, hy = b['hilt']; tx_, ty_ = b['tip']
            ang = math.atan2(ty_ - hy, tx_ - hx) + math.radians(fr.get('blade_rot', 0))
            if be is not None and not fr.get('grip_meta'):
                grip = (be[0][0] + dx, be[0][1] + dy)
            else:
                grip = (plan.get('x0', 64) + hx, FOOT - lift + hy)
            g2 = fr.get('grip', [0, 0]); grip = (grip[0] + g2[0], grip[1] + g2[1])
            if fr.get('grip_abs'):
                grip = tuple(fr['grip_abs'])
            prot = hm.copy()
            if fr.get('blade_behind', 0):
                prot |= opaque(a)
            blade_draw(a, grip, ang, L=plan.get('blade_len', 34), protect=prot)
            fr['_grip'] = grip; fr['_ang'] = math.degrees(ang)
        gcx = gcx; tx = gcx; oy_gen = oy; oy_tgt = oy
        # ---- spatial clean
        n_or = orphans(a)
        n_ol = outline_repair(a) if plan.get('outline_repair', 1) else 0
        n_or += orphans(a)
        # ---- temporal de-crawl vs previous clean frame (only if declared static-ish)
        n_dc = 0
        if fr.get('decrawl', plan.get('decrawl', 1)) and prev is not None:
            a, n_dc = decrawl(a, prev)
        clean = a.copy(); cleans.append(clean)
        Image.fromarray(clean).save(f'{out}/c{i:02d}.png')
        prev = clean
        log.append(dict(f=i, dx=dx, dy=dy, head_gen_vs_tgt=[round(gcx - tx, 1), round(oy_gen - oy_tgt, 1)],
                        orph=n_or, ol=n_ol, decrawl=n_dc))
        print(log[-1], flush=True)
    json.dump(log, open(f'{out}/log.json', 'w'), indent=0, default=float)


if __name__ == '__main__':
    main()
