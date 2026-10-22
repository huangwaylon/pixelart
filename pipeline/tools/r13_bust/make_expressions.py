"""Writes the 10 dialogue-bust expressions as `extends: bust_base.pix` + `patch:` blocks.

Every feature below is a literal hand-typed block (eyes, mouths, cheeks, FX) or an explicit brow run list.
The script only composes them over the base face and writes the changed pixels as patches ('_' = keep base).
Face boxes (bust_base coords): brows rows 31-33 x35-61; far eye (screen-left) x35-43 rows 33-43;
near eye x50-61 rows 33-43; cheeks rows 45-47; mouth x43-50 rows 48-52.
"""
import copy
import os
from pipeline.tools.r13_bust.pixlib import read_grid

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BUST = os.path.join(ROOT, "art/hand/S4/bust")
_, BASE = read_grid(os.path.join(BUST, "bust_base.pix"))

def blk(s):
    return [r.strip() for r in s.strip("\n").split("\n")]

# ---------------- eyes (far x35, near x50; first row given = row 33 unless noted) ----------------
# '_' inside an eye block = skin (the box is cleared first). '.' never used here.
EYES = {}
EYES["open"] = (blk("""
_________
__KKKKK__
KKKKKKKK_
KKiiiiiK_
_KWWKKiw_
_KWWKKiw_
_KjjjKjw_
_Kjjjjjw_
_KkkkkWw_
_Kkkkkk__
__LL_____
"""), blk("""
____________
___KKKKKK___
_KKKKKKKKKK_
_KiiiiiiiKKK
_wiWWKKKiwK_
_wiWWKKKiwK_
_wjjjjKjjwK_
_wjjjjjjjwK_
_wkkkkkWkwK_
__kkkkkkkK__
_______LL___
"""))
EYES["smile"] = (blk("""
_________
__KKKKK__
KKKKKKKK_
KKiiiiiK_
_KWWKKiw_
_KWWKKiw_
_KjjjKjw_
_KjjjjjL_
_KjLLLjL_
__L___L__
_________
"""), blk("""
____________
___KKKKKK___
_KKKKKKKKKK_
_KiiiiiiiKKK
_wiWWKKKiwK_
_wiWWKKKiwK_
_wjjjjKjjwK_
_wjjjjjjjLK_
_LjLLLLLjLK_
__L_____L___
____________
"""))
EYES["laugh"] = (blk("""
_________
_________
_________
___KKK___
__KKKKK__
_KK___KK_
KK_____KK
K_______K
_________
_________
_________
"""), blk("""
____________
____________
____________
____KKKK____
___KKKKKK___
__KK____KK__
_KK______KK_
_K________KK
____________
____________
____________
"""))
EYES["surprised"] = (blk("""
__KKKKK__
KKKKKKKK_
KwwwwwwK_
_KWiiiWW_
_KWiKiWW_
_KWjKjWW_
_KWjjjWW_
_KWWWWWW_
_KWWWWW__
__LLLL___
_________
"""), blk("""
___KKKKKK___
_KKKKKKKKKK_
_KwwwwwwwwKK
_wWWiiiWWWK_
_wWWiKiWWWK_
_wWWjKjWWWK_
_wWWjjjWWWK_
_wWWWWWWWWK_
_wWWWWWWWWK_
__LLLLLLLK__
____________
"""))
EYES["sad"] = (blk("""
_________
_________
______KK_
___KKKKK_
KKKKKiiK_
_Kiiiiiw_
_KWWjjjw_
_KWWKKjw_
_KkkKKkw_
_Kkzzkk__
__LL_____
"""), blk("""
____________
____________
_KK_________
_KKKKK______
_KiiiKKKKKKK
_wiiiiiiiKK_
_wWWjjjjjwK_
_wWWjKKKjwK_
_wkkkKKKkwK_
__kkzzzkkK__
_______LL___
"""))
EYES["angry"] = (blk("""
_________
_________
KKK______
KKKKKK___
_KiiiKKK_
_KWWKKjw_
_KjjKKjw_
_Kjjjjjw_
_KkkkkWw_
_Kkkkkk__
__LL_____
"""), blk("""
____________
____________
_________KKK
_____KKKKKKK
_KKKKKiiiKK_
_wjWWKKKiwK_
_wjjjjKjjwK_
_wjjjjjjjwK_
_wkkkkkWkwK_
__kkkkkkkK__
_______LL___
"""))
EYES["determined"] = (blk("""
_________
_________
KKKKKKKK_
KKKKKKKK_
_KKWKKKw_
_KWWWKKw_
_KjWjKjw_
_Kjjjjjw_
_KkkkkWw_
_LLLLLL__
_________
"""), blk("""
____________
____________
_KKKKKKKKKKK
_KKKKKKKKKK_
_wiKWKKKiwK_
_wiWWWKKiwK_
_wjjWjKjjwK_
_wjjjjjjjwK_
_wkkkkWkkwK_
__LLLLLLLK__
____________
"""))
# worried: open lids, irises slide to screen-right (sideways glance)
EYES["worried"] = (blk("""
_________
__KKKKK__
KKKKKKKK_
KKwwiiiK_
_KwwWWKK_
_KwwWWKK_
_KwwjjKj_
_Kwwjjjj_
_KwwkkWk_
_Kwwkkk__
__LL_____
"""), blk("""
____________
___KKKKKK___
_KKKKKKKKKK_
_KwwwiiiiKKK
_wwwiWWKKiK_
_wwwiWWKKiK_
_wwwjjjjKjK_
_wwwjjjjjjK_
_wwwkkkkWkK_
__wwkkkkkK__
_______LL___
"""))
# embarrassed: irises slide to screen-left and down (averted), lower lids pushed up a little
EYES["embarrassed"] = (blk("""
_________
__KKKKK__
KKKKKKKK_
KKiiiiwK_
_KWKKiWw_
_KjKKjWw_
_KjKjjWw_
_KjjjjWw_
_KkkkkWL_
__LLLLL__
_________
"""), blk("""
____________
___KKKKKK___
_KKKKKKKKKK_
_KiiiiiiiKKK
_iWWKKKiWwK_
_iWWKKKiWwK_
_jjjjKjjWwK_
_jjjjjjjWwK_
_kkkkWkkWLK_
__LLLLLLL___
____________
"""))
EYES["content"] = (blk("""
_________
_________
_________
_________
_________
K________
KK_____KK
_KKKKKKK_
_________
_________
_________
"""), blk("""
____________
____________
____________
____________
____________
___________K
_KK______KKK
__KKKKKKKK__
____________
____________
____________
"""))

# ---------------- brows: hair_1 'd' runs (y, x0, x1); left = far brow, right = near brow ----------------
BROWS = {
 "neutral":     [(32, 36, 41), (33, 35, 35), (32, 53, 58), (33, 59, 59)],
 "smile":       [(31, 36, 41), (32, 35, 35), (31, 53, 58), (32, 59, 59)],
 "laugh":       [(32, 35, 35), (31, 36, 40), (32, 41, 41), (32, 53, 53), (31, 54, 58), (32, 59, 59)],
 "surprised":   [(32, 35, 35), (31, 36, 40), (32, 53, 53), (31, 54, 58), (32, 59, 59)],
 "sad":         [(33, 35, 37), (32, 38, 39), (31, 40, 41), (31, 53, 54), (32, 55, 56), (33, 57, 59)],
 "angry":       [(31, 35, 36), (32, 36, 39), (33, 39, 42), (33, 52, 55), (32, 55, 58), (31, 58, 60)],
 "embarrassed": [(33, 35, 35), (32, 36, 37), (33, 38, 38), (32, 39, 39), (31, 40, 41),
                 (31, 53, 54), (32, 55, 55), (33, 56, 56), (32, 57, 58), (33, 59, 59)],
 "determined":  [(32, 35, 38), (33, 38, 42), (33, 52, 56), (32, 55, 59)],
 "worried":     [(33, 35, 36), (32, 37, 38), (31, 39, 40), (32, 41, 42), (32, 52, 53), (31, 54, 55), (32, 56, 57), (33, 58, 59)],
 "content":     [(33, 35, 36), (32, 37, 40), (33, 41, 41), (33, 53, 53), (32, 54, 57), (33, 58, 59)],
}

# ---------------- mouths (block, x, y) ----------------
MOUTH = {
 "neutral":     (blk("LLL"), 45, 50),
 "smile":       (blk("L___L\n_LLL_"), 44, 49),
 "laugh":       (blk("LLLLLL\nrrrrrr\nLryyrL\n_LLLL_"), 43, 48),
 "surprised":   (blk("_LL_\nLrrL\nLyyL\n_LL_"), 45, 48),
 "sad":         (blk("_LLL_\nL___L"), 44, 49),
 "angry":       (blk("__L__\n_L_L_\nL___L"), 44, 48),
 "embarrassed": (blk("_LL__L\nL__LL_"), 43, 49),
 "determined":  (blk("_____L\nLLLLL_"), 43, 49),
 "worried":     (blk("LL_\n__L"), 45, 50),
 "content":     (blk("L_____L\n_LLLLL_"), 43, 49),
}

# ---------------- cheeks ----------------
LIGHT = [(blk("ttxttx\ntxttxt"), 36, 45), (blk("ttxttx\ntxttxt"), 53, 45)]
HEAVY = [(blk("ttxttxt\ntxttxtt\nxttxttt"), 36, 45), (blk("ttttt\ntt_tt\nttttt"), 43, 45),
         (blk("ttxttxttx\ntxttxttxt\nxttxttxtt"), 52, 45)]
CHEEKS = {"smile": LIGHT, "laugh": LIGHT, "content": LIGHT, "embarrassed": HEAVY}

# ---------------- FX (block, x, y) ; '_' = keep ----------------
FX = {
 "surprised": [(blk("K_\n_K"), 24, 22), (blk("KK"), 20, 27), (blk("_K\nK_"), 22, 32)],
 "sad":       [(blk("_z_\nzWz\nzWz\n_z_"), 60, 43)],
 "angry":     [(blk("_R_R_\nRR_RR\n_____\nRR_RR\n_R_R_"), 56, 20),
               (blk("s\ns\ns\ns\ns"), 62, 45), (blk("P\nP\nP\nP\nP"), 63, 45)],
 "embarrassed": [(blk("_zz_\nzWWz\nzWWz\n_zz_"), 26, 8), (blk("_zz\nzWz\n_z_"), 21, 3), (blk("zz\nzz"), 31, 2)],
 "determined": [],
 "worried":   [(blk("__K__\n_KzK_\n_KzK_\nKWzzK\nKWzzK\nKzzzK\n_KKK_"), 63, 30)],
}

NAMES = ["neutral", "smile", "laugh", "surprised", "sad", "angry", "embarrassed", "determined", "worried", "content"]
EYEKEY = {"neutral": "open"}

def compose(name):
    g = copy.deepcopy(BASE)
    # clear brows (back to the bare forehead: cast shadow row 31 under the bang)
    for x in range(35, 62):
        g[31][x] = "u" if (36 <= x <= 40 or x >= 55) else "s"
        g[32][x] = "u" if x == 61 else "s"
        g[33][x] = "s"
    for x0, x1 in ((35, 43), (50, 61)):
        for y in range(34, 44):
            for x in range(x0, x1 + 1):
                g[y][x] = "s"
    for y in range(45, 48):
        for x in list(range(36, 43)) + list(range(43, 61)):
            if not (x == 45 and y == 46):
                g[y][x] = "s"
    for y in range(48, 53):
        for x in range(42, 52):
            if BASE[y][x] in "sL" and 42 <= x <= 51 and y <= 51:
                g[y][x] = "s"
    far, near = EYES[EYEKEY.get(name, name)]
    for (b, x0) in ((far, 35), (near, 50)):
        for j, r in enumerate(b):
            for i, ch in enumerate(r):
                g[33 + j][x0 + i] = "s" if ch == "_" else ch
    for y, x0, x1 in BROWS[name]:
        for x in range(x0, x1 + 1):
            g[y][x] = "d"
    g[31][35] = "u" if g[31][36] == "u" else "s"     # shadow run under the bang stays one cluster
    b, mx, my = MOUTH[name]
    for j, r in enumerate(b):
        for i, ch in enumerate(r):
            if ch != "_":
                g[my + j][mx + i] = ch
    for b, cx, cy in CHEEKS.get(name, []):
        for j, r in enumerate(b):
            for i, ch in enumerate(r):
                if ch != "_" and not (cx + i == 45 and cy + j == 46):
                    g[cy + j][cx + i] = ch
    for b, fx, fy in FX.get(name, []):
        for j, r in enumerate(b):
            for i, ch in enumerate(r):
                if ch != "_":
                    g[fy + j][fx + i] = ch
    return g

def patches(g):
    diff = [(x, y) for y in range(96) for x in range(96) if g[y][x] != BASE[y][x]]
    if not diff:
        return []
    # one patch per connected-ish region: face box + each FX outside it
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
 "neutral": "open eyes / flat brows / 3px line / none",
 "smile": "lower lids pushed up (crescent) / brows raised 1px / small u / light blush",
 "laugh": "closed ^^ / high arch / open D with crn_2 tongue / light blush",
 "surprised": "wide, lash up 1px, 3px pinpoint irises / floating arcs / small o / shock ticks",
 "sad": "half-lid, gaze down / inner ends up / downturned / outer tear (snow_1)",
 "angry": "lid cut flat on a slant / inner ends sharply down / ^ pout + puffed near cheek / red_1 vein mark",
 "embarrassed": "averted down-left, lower lids up / wavy / ~ / 3-row blush across the nose / steam puffs",
 "determined": "flattened top lid / straight down-in / firm, pulled up on one side / star catchlight",
 "worried": "open, glancing sideways / inner up / small flat / one sweat drop",
 "content": "closed u arcs / relaxed low / closed smile / light blush",
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
