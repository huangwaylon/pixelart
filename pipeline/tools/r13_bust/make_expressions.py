"""Writes the 10 dialogue-bust expressions as `extends: bust_base.pix` + `patch:` blocks (round 2 face).

Every feature below is a literal hand-typed block (eyes, mouths, cheeks, FX) or an explicit brow run list.
The script clears the base face boxes, lays the blocks, and writes only the changed pixels ('_' = keep base).
Boxes (bust_base coords): brows rows 30-32; far eye (screen-left) x35-44 rows 32-43; near eye x50-61 rows 32-43;
cheeks rows 45-47; mouth x40-49 rows 48-52.
"""
import copy
import os
from pipeline.tools.r13_bust.pixlib import read_grid

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BUST = os.path.join(ROOT, "art/hand/S4/bust")
_, BASE = read_grid(os.path.join(BUST, "bust_base.pix"))
# bang edge rows (same table as build_base.py): skin below, skin_1 cast shadow on the first skin row
E = dict(zip(range(35, 63), [28, 29, 29, 29, 29, 28, 27, 25, 28, 29, 30, 31, 32, 32, 32, 32, 31, 30, 29, 28, 25, 27,
                             28, 29, 29, 29, 29, 28]))


def blk(s):
    return [r.strip() for r in s.strip("\n").split("\n")]


# ---------- eyes: (far block, near block, first row). '_' = skin. far block 10 wide @x35, near 12 wide @x50 ----------
EYES = {}
EYES["open"] = (blk("""
___KKKKK__
_KKKKKKKKK
KKiiiiiiw_
__iWWKKiw_
__iWWKKiw_
__ijjKjiw_
__ijjjjiw_
__ikkkkiw_
__ikkkWi__
_LLiiii___
"""), blk("""
___KKKKK____
_KKKKKKKKK__
_wiiiiiiiKKK
_wiWWKKKiw__
_wiWWKKKiw__
_wijjjKjiw__
_wijjjjjiw__
_wikkkkkiw__
__ikkkkWi___
___iiiiiLL__
"""), 33)
EYES["smile"] = (blk("""
___KKKKK__
_KKKKKKKKK
KKiiiiiiw_
__iWWKKiw_
__iWWKKiw_
__ijjKjiw_
__ijjjjiw_
__ikkkkiw_
__iLLLLi__
"""), blk("""
___KKKKK____
_KKKKKKKKK__
_wiiiiiiiKKK
_wiWWKKKiw__
_wiWWKKKiw__
_wijjjKjiw__
_wijjjjjiw__
_wikkkkkiw__
__iLLLLLi___
"""), 33)
EYES["laugh"] = (blk("""
____KK____
__KKKKKK__
_KK____KK_
KK______KK
K_________
"""), blk("""
_____KK_____
___KKKKKK___
__KK____KK__
_KK______KK_
_K________KK
"""), 35)
EYES["surprised"] = (blk("""
___KKKKK__
_KKKKKKKKK
K_wwwwwww_
__WiiiiiW_
__WiWKiiW_
__WijKjiW_
__WijjjiW_
__WikkkiW_
__WWiiiWW_
__LLL_____
"""), blk("""
___KKKKK____
_KKKKKKKKKK_
_wwwwwwwwKKK
_WiiiiiiW___
_WiWWKiiW___
_WiWWKiiW___
_WijjjjiW___
_WikkkkiW___
_WWiiiiWW___
________LL__
"""), 32)
EYES["sad"] = (blk("""
_____KKK__
__KKKKKKKK
KKKKiiiiw_
__iiiiiiw_
__iWWjjiw_
__iWWKKiw_
__ijjKKiw_
__ikkkkiw_
__izzzzi__
_LLiiii___
"""), blk("""
__KKKK______
_KKKKKKKKK__
_wiiiiiKKKKK
_wiiiiiiiw__
_wiWWjjjiw__
_wiWWKKKiw__
_wijjKKKiw__
_wikkkkkiw__
__izzzzzi___
___iiiiiLL__
"""), 33)
EYES["angry"] = (blk("""
_KKKK_____
KKKKKKKKKK
__iiiiKKKK
__iWWKKiw_
__iWWKKiw_
__ijjjKiw_
__LLLLLLL_
"""), blk("""
_____KKKK___
_KKKKKKKKKKK
_KKKKiiiiKK_
_wiWWKKKiw__
_wiWWKKKiw__
_wijjjjKiw__
_LLLLLLLLL__
"""), 33)
EYES["embarrassed"] = (blk("""
___KKKKK__
_KKKKKKKKK
KKiiiiiiw_
__WKKjjiw_
__iKKjjiw_
__ijKjjiw_
__ijjjjiw_
__iLLLLLL_
"""), blk("""
___KKKKK____
_KKKKKKKKK__
_wiiiiiiiKKK
_wWKKKjjiw__
_wiKKKjjiw__
_wijKjjjiw__
_wijjjjjiw__
_wiLLLLLLL__
"""), 33)
EYES["determined"] = (blk("""
__________
KKKKKKKKKK
_KKKKKKKKK
__iWWKKiw_
__iWWKKiw_
__ijjKjiw_
__ijjjjiw_
__ikkkkiw_
__ikkkWi__
_LLiiii___
"""), blk("""
____________
_KKKKKKKKKKK
_KKKKKKKKKK_
_wiWWKKKiw__
_wiWWKKKiw__
_wijjjKjiw__
_wijjjjjiw__
_wikkkkkiw__
__ikkkkWi___
___iiiiiLL__
"""), 33)
# worried: open lids, irises slide 1 px to screen-right (sideways glance); far eye keeps most of its iris
EYES["worried"] = (blk("""
___KKKKK__
_KKKKKKKKK
KKwiiiiiiK
__wiWWKKi_
__wiWWKKi_
__wijjjKj_
__wijjjji_
__wikkkki_
__wikkkWi_
_LL_iiii__
"""), blk("""
___KKKKK____
_KKKKKKKKK__
_wwiiiiiiKKK
_wwiWWKKKi__
_wwiWWKKKi__
_wwijjjKji__
_wwijjjjji__
_wwikkkkki__
__wikkkkWi__
____iiiiiLL_
"""), 33)
EYES["content"] = (blk("""
K_________
KK_____KK_
__KKKKK___
"""), blk("""
___________K
_KK______KKK
___KKKKKK___
"""), 37)

# ---------- brows: hair_1 'd' runs (y, x0, x1) ----------
BROWS = {
 "neutral":     [(31, 36, 41), (32, 35, 35), (31, 54, 59), (32, 60, 60)],
 "smile":       [(30, 36, 41), (31, 35, 35), (30, 54, 59), (31, 60, 60)],
 "laugh":       [(31, 35, 35), (30, 36, 40), (31, 41, 41), (31, 54, 54), (30, 55, 59), (31, 60, 60)],
 "surprised":   [(30, 36, 40), (30, 55, 58), (31, 59, 59)],
 "sad":         [(32, 35, 37), (31, 38, 39), (30, 40, 41), (30, 54, 55), (31, 56, 57), (32, 58, 60)],
 "angry":       [(30, 36, 37), (31, 37, 39), (32, 39, 42), (32, 52, 55), (31, 55, 58), (30, 58, 60)],
 "embarrassed": [(32, 35, 35), (31, 36, 37), (32, 38, 38), (31, 39, 39), (30, 40, 41),
                 (30, 54, 55), (31, 56, 56), (32, 57, 57), (31, 58, 59), (32, 60, 60)],
 "determined":  [(30, 36, 37), (31, 37, 39), (32, 39, 42), (32, 52, 55), (31, 55, 57), (30, 57, 60)],
 "worried":     [(32, 35, 37), (31, 38, 39), (30, 40, 41), (31, 42, 42), (31, 53, 53), (30, 54, 55), (31, 56, 57),
                 (32, 58, 60)],
 "content":     [(32, 36, 41), (32, 54, 59)],
}

# ---------- mouths (block, x, y); no lip outlines on open mouths ----------
MOUTH = {
 "neutral":     (blk("L__L\n_LL_"), 42, 50),
 "smile":       (blk("r____r\n_rrrr_\n__yy__"), 40, 49),
 "laugh":       (blk("LLLLLL\nrrrrrr\nrrrrrr\nryyyyr\n_ryyr_"), 40, 48),
 "surprised":   (blk("_rr_\nrrrr\nryyr\n_rr_"), 42, 48),
 "sad":         (blk("_LLL_\nL___L"), 41, 50),
 "angry":       (blk("__L__\n_L_L_\nL___L"), 41, 49),
 "embarrassed": (blk("_LL___\nL__L__\n____LL"), 41, 49),
 "determined":  (blk("LLLLL"), 41, 51),
 "worried":     (blk("_L_L\nL_L_"), 42, 50),
 "content":     (blk("L____L\n_LLLL_"), 40, 49),
}

# ---------- cheeks (block, x, y): hatches (red_2) on a skin_mid patch; never a solid band ----------
LIGHT = [(blk("ttxttx\ntxttxt"), 35, 45), (blk("ttxttxt\ntxttxtt"), 52, 45)]
HEAVY = [(blk("ttxttxt\ntxttxtt\nxttxttt"), 35, 45), (blk("_x_x\nx_x_"), 46, 45),
         (blk("ttxttxttx\ntxttxttxt\nxttxttxtt"), 51, 45)]
CHEEKS = {"neutral": LIGHT, "smile": LIGHT, "laugh": LIGHT, "content": LIGHT, "embarrassed": HEAVY}

# ---------- FX (block, x, y); '_' = keep ----------
FX = {
 "surprised": [(blk("K_\n_K"), 24, 16), (blk("KK"), 20, 21), (blk("_K\nK_"), 21, 26)],
 "sad":       [(blk("_z_\n_z_\n_z_\n_z_\nzWz\nzWz\n_z_"), 57, 43)],
 "angry":     [(blk("_R_R_\nRR_RR\n_____\nRR_RR\n_R_R_"), 56, 18),
               (blk("s\ns\ns\ns\ns"), 62, 44), (blk("P\nP\nP\nP\nP"), 63, 44)],
 "embarrassed": [(blk("__zzz__\n_zWWWz_\nzWWWWWz\nzWWWWzz\n_zzzz__"), 26, 2), (blk("_zz_\nzWWz\nzWzz\n_zz_"), 19, 0),
                 (blk("_zz_\nzWWz\n_zz_"), 35, 0)],
 "worried":   [(blk("__K__\n_KzK_\n_KzK_\nKWzzK\nKWzzK\nKzzzK\n_KKK_"), 27, 29)],
}

NAMES = ["neutral", "smile", "laugh", "surprised", "sad", "angry", "embarrassed", "determined", "worried", "content"]
EYEKEY = {"neutral": "open"}


def bg(x, y):
    """bare forehead under the bang (no brows / lashes)"""
    if x in E and y <= E[x]:
        return BASE[y][x]
    if x in E and y == E[x] + 1 and (x, y) != (35, 29):
        return "u"
    return "s"


def compose(name):
    g = copy.deepcopy(BASE)
    for y in range(29, 34):
        for x in range(35, 62):
            if x in E and y > E[x]:
                g[y][x] = bg(x, y)
    for x0, x1 in ((35, 44), (50, 61)):
        for y in range(34, 44):
            for x in range(x0, x1 + 1):
                g[y][x] = "s"
    for y in range(45, 48):
        for x in list(range(35, 42)) + list(range(45, 61)):
            g[y][x] = "s"
    for y in range(48, 53):
        for x in range(40, 50):
            g[y][x] = "s"
    far, near, y0 = EYES[EYEKEY.get(name, name)]
    for b, x0 in ((far, 35), (near, 50)):
        for j, r in enumerate(b):
            for i, ch in enumerate(r):
                if ch != "_":
                    g[y0 + j][x0 + i] = ch
    for y, x0, x1 in BROWS[name]:
        for x in range(x0, x1 + 1):
            g[y][x] = "d"
    for layer in ([MOUTH[name]], CHEEKS.get(name, []), FX.get(name, [])):
        for b, bx, by in layer:
            for j, r in enumerate(b):
                for i, ch in enumerate(r):
                    if ch != "_":
                        g[by + j][bx + i] = ch
    return g


def patches(g):
    diff = [(x, y) for y in range(96) for x in range(96) if g[y][x] != BASE[y][x]]
    groups = []
    for x, y in diff:
        for gr in groups:
            if gr[0] - 3 <= x <= gr[2] + 3 and gr[1] - 3 <= y <= gr[3] + 3:
                gr[0], gr[1], gr[2], gr[3] = min(gr[0], x), min(gr[1], y), max(gr[2], x), max(gr[3], y)
                break
        else:
            groups.append([x, y, x, y])
    out = []
    for x0, y0, x1, y1 in groups:
        rows = ["".join(g[y][x] if g[y][x] != BASE[y][x] else "_" for x in range(x0, x1 + 1)) for y in range(y0, y1 + 1)]
        out.append((x0, y0, rows))
    return out


DESC = {
 "neutral": "open eyes / flat brows / 1-2-1 mouth / signature blush (base face)",
 "smile": "lower lids pushed up / brows raised 1px / 1-3-1 smile / blush",
 "laugh": "closed ^^ / high arch / open D (no lip outline) with crn_2 tongue / blush",
 "surprised": "wide, lash up 1px, 5px irises with pinpoint pupils / floating arcs / small o / shock ticks",
 "sad": "drooping lids, gaze down, tear welling / inner ends up / downturned / outer tear",
 "angry": "lids cut on a slant + lower lid up (glare) / V brows / ^ pout + puffed cheek / red_1 vein",
 "embarrassed": "averted, lower lids up / wavy / ~ / hatched blush over both cheeks + nose / steam",
 "determined": "flattened top lid / straight, down-in / firm, pulled to one side",
 "worried": "open, glancing sideways / inner up, wavy / small uneasy line / sweat drop",
 "content": "closed u arcs / relaxed low / closed smile / blush",
}

if __name__ == "__main__":
    for n in NAMES:
        g = compose(n)
        lines = [f"# r13 dialogue bust: {n}. {DESC[n]}", "# Hand-authored face patches over bust_base.pix (lead pixel artist).",
                 "extends: bust_base.pix"]
        for x0, y0, rows in patches(g):
            lines.append(f"patch: {x0} {y0}")
            lines += rows
        open(os.path.join(BUST, f"{NAMES.index(n) + 1:02d}_{n}.pix"), "w").write("\n".join(lines) + "\n")
    print("ok")
