"""Per-sprite hand edits (Claude pixel artist).  pre_<stem>(g, log) runs before the global passes,
post_<stem>(g, log) after them.  plib.put() rows: '_' keeps, '.' clears."""
import numpy as np
import plib
from plib import put
HAIR_YMAX = {}
CORSET = {}
BLADE = {}
FINAL = []
import passes as P


def post_slash_SE_k1(g, log):
    # 1. clear the pixelized crescent (stair-stepped inner edge) and the broken blade
    plib.erase_where(g, (66, 50, 104, 93), 'pPwtT', log, 'k1: clear stair-stepped Gemini crescent + broken blade',
                     keep=lambda x, y: x <= 79 and y >= 85)
    # 2. clean katana, guard at the fist, tip on the end of the smear
    P.blade_redraw(g, log, (79, 90), (96, 92))
    # 3. blade-arc smear: tip path from behind the bun (tail, -95 deg) to the tip (lead, 25 deg);
    #    outer edge = tip path (steel_2, unbroken), band thickens tail -> lead, pink inside.
    P.crescent(g, log, 68, 80, 30, 28, -92, 31, 7, reason='k1 SMEAR: smooth crescent along the tip path, thick at the blade')
import math


def behind(g, op_list, log, reason):
    """run draw ops on a copy, keep only pixels that land on transparency (paint behind the body)"""
    t = g.copy()
    plib.ops(t, op_list, None, reason)
    m = (g == '.') & (t != '.')
    g[m] = t[m]
    log.append({'op': 'behind', 'ops': op_list, 'px': int(m.sum()), 'reason': reason})


def setp(g, log, pts, c, reason):
    plib.setpx(g, pts, c, log, reason)


def fierce_SE(g, log, lid_row, lx, rx):
    """fierce SE face: inner top corner of each iris -> outline (lids slant down to the nose)"""
    setp(g, log, [(lx, lid_row + 1), (rx, lid_row + 1)], 'K', 'fierce face: inner lid corners pulled down (slash effort)')


def effort_eye_E(g, log, gx, gy):
    """E profile: replace the open eye (glint at gx,gy) by a squeezed '>' effort eye"""
    x0, y0 = gx - 3, gy - 1          # eye block (lid row = gy-1)
    for y in range(y0, y0 + 4):
        for x in range(x0, x0 + 6):
            if g[y, x] in 'eEwK':
                g[y, x] = 's'
    rows = ['KK____', '__KKK_', 'KK____']
    put(g, x0, y0, rows, log, 'effort face: squeezed ">" eye (jump crouch / landing strain, as Gemini drew)')


def shift_mask(g, log, mask, dx, dy, reason):
    src = g.copy(); ys, xs = np.nonzero(mask)
    g[mask] = '.'
    for y, x in zip(ys, xs):
        g[y + dy, x + dx] = src[y, x]
    log.append({'op': 'shift_mask', 'n': int(mask.sum()), 'dxy': [dx, dy], 'reason': reason})


def head_mask(g, box, body_cut=None):
    """head = hair/bow/face pixels (and their outline) inside box; body_cut(x,y) excludes body px"""
    x0, y0, x1, y1 = box
    m = np.zeros(g.shape, bool)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if g[y, x] != '.' and not (body_cut and body_cut(x, y)):
                m[y, x] = True
    return m


# ---------------------------------------------------------------- slash
def post_slash_SE_k0(g, log):
    plib.erase_where(g, (52, 42, 55, 45), 'mEK', log, 'k0: stray specks beside the raised blade')
    # hilt from the raised fist up to the guard (it was missing: the fist floated 7 px from the blade)
    setp(g, log, [(37, 56), (38, 54), (40, 52)], 'K', 'k0: wrapped hilt (outline wraps)')
    setp(g, log, [(38, 55), (39, 53)], 'R', 'k0: hilt red diamond wrap')
    fierce_SE(g, log, 73, 56, 62)


def post_slash_SE_k2(g, log):
    setp(g, log, [(74, 97), (74, 98), (74, 99), (77, 99), (77, 100), (82, 103), (87, 97)], '.',
         'k2: leftover specks of the pixelized spark')
    # impact spark at the tip (hit-stop): 4-point star, hot core, pink sparks on the diagonals
    plib.ops(g, ['stamp 86,96 ___w___/___w___/_P_w_P_/wwwSwww/_P_w_P_/___w___/___w___'], log,
             'k2 IMPACT: hit spark star at the blade tip (hit-stop frame)')
    fierce_SE(g, log, 74, 56, 62)
    setp(g, log, [(59, 79)], 'K', 'k2: open shouting mouth (kiai)')
    setp(g, log, [(59, 80)], 'v', 'k2: open shouting mouth (kiai)')


def post_slash_SE_k3(g, log):
    plib.ops(g, ['replace 69,89 74,89 C R', 'replace 63,92 71,92 p r', 'replace 63,92 71,92 P r'], log,
             'k3: flat coral bar and pink line pasted across the dress -> dress red')
    # trailing smear: thin fading pink arc behind the body, from the back sweep down to the blade
    P.crescent(g, log, 52, 84, 38, 18, 20, 150, 2.2, tones=('P', 'p', 'p'), core=1.0, tmin=1.0,
               reason='k3 follow-through: thin decaying smear trail behind the body')


# ---------------------------------------------------------------- jump
def pre_jump_E_crouch(g, log):
    effort_eye_E(g, log, 91, 78)
    setp(g, log, [(68, 75)], 'r', 'crouch: stray eye-blue pixel in the sleeve')
    # head sat forward of the body and read detached: sink it 3 px back and 2 px down into the
    # shoulders (squash: head drops into the collar)
    m = head_mask(g, (71, 46, 98, 87), body_cut=lambda x, y: y >= 75 and x <= 76)
    shift_mask(g, log, m, -3, 2, 'crouch: head sunk into the shoulders (squash, reattached)')


def pre_jump_E_land(g, log):
    effort_eye_E(g, log, 81, 79)
    m = head_mask(g, (61, 50, 90, 88), body_cut=lambda x, y: (y >= 77 and x <= 65) or y >= 87 and x <= 72)
    shift_mask(g, log, m, 0, 1, 'land: head drops 1 row into the squash (impact weight)')


# ---------------------------------------------------------------- walk
WALK_ANG = {0: 26, 1: 32, 2: 40, 3: 33}      # blade angle below horizontal: dips 1 frame after the body (lag)
# scarf tail: anchor at the nape, wave = (mid y offset, tip y offset); the wave travels one frame
# behind the body bob (body down on k1, up on k3 -> tail low on k2, high on k0)
WALK_RIB = {0: (-3, -1), 1: (-1, 2), 2: (1, 4), 3: (-2, 1)}


def _walk(k):
    def f(g, log):
        gd, tp = P.blade_find(g)
        L = 23.0
        a = math.radians(WALK_ANG[k])
        tip = (gd[0] + L * math.cos(a), gd[1] + L * math.sin(a))
        plib.erase_where(g, (int(gd[0]) + 2, int(gd[1]) - 3, 127, 115), 'tw', log,
                         'walk: old blade cleared (re-angled for the swing)')
        P.blade_redraw(g, log, gd, tip)
        wm, wt = WALK_RIB[k]
        ax, ay = 52, 79
        mx, my = 45, ay + wm
        ex, ey = 39, ay + wt
        behind(g, [f'curve {ax},{ay} {ax - 3},{ay + wm - 2} {mx},{my} P',
                   f'curve {mx},{my} {mx - 3},{my + 2 + wt - wm} {ex},{ey} P',
                   f'curve {ax},{ay + 1} {ax - 3},{ay + wm - 1} {mx},{my + 1} p',
                   f'curve {mx},{my + 1} {mx - 3},{my + 3 + wt - wm} {ex + 1},{ey + 1} p',
                   f'line {ex},{ey + 1} {ex - 1},{ey + 2} p'], log,
               'walk: pink scarf tails trail behind and wave one frame behind the body bob (overlap)')
    return f


for _k in range(4):
    globals()[f'post_walk_SE_k{_k}'] = _walk(_k)


def post_jump_E_land(g, log):
    behind(g, ['stamp 54,101 __JJ_/_JJLJ/JJJJ_', 'stamp 71,102 _JJ__/JJLJJ/_JJJ_'], log,
           'land: dust puffs kicked out on both sides of the feet (impact)')


# ---------------------------------------------------------------- turn set
def post_turn_SW(g, log):
    plib.ops(g, ['replace 63,78 65,80 S s'], log, 'SW: white cross on the bare shoulder -> skin_1')
    plib.erase_where(g, (76, 99, 86, 107), 'Sm', log, 'SW: ghost of the old pixelized blade')


def post_turn_NE(g, log):
    put(g, 65, 100, ['KsKsK', 'KmKmK', 'KlKlK', '_K_K_'], log,
        'NE: heels peeking under the long back hem (canon back view shows the strappy heels)')


def post_turn_NW(g, log):
    put(g, 63, 102, ['KsKsK', 'KlKlK', '_K_K_'], log,
        'NW: heels peeking under the long back hem (canon back view shows the strappy heels)')
