"""bust_base.pix builder. Starts from face test C (pasted, offset) then applies the artist's hand-typed blocks."""
import os
from pipeline.tools.r13_bust.pixlib import read_grid, canvas, put, write

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
C = os.path.join(ROOT, "art/hand/S4/face_tests/C_dote.pix")
OUT = os.path.join(ROOT, "art/hand/S4/bust/bust_base.pix")
DX, DY = 10, 5

legend, cg = read_grid(C)
g = canvas(96, 96)
for y in range(0, 62):
    for x in range(0, 63):
        ch = cg[y][x]
        if ch in "bce":
            ch = "."
        if ch != ".":
            g[y + DY][x + DX] = ch


# ---- pass 1: hime bang cut lifted 4 rows so the brows show (bible: cut 1px above brows) ----
# x34..x63; notches at x41 and x54 (2 notches = 3 panels, centre widest)
put(g, 34, 25, """
mmmmmmmdmmdmmmmmmdmmdmmmmmmmmm
mmmmmmmdmmmmmmmmmmmmdmmmmmmmmm
mmmmmmmdmmmmmmmmmmmmdmmmmmmmmm
mmmmmmdddmmmmmmmmmmdddmmmmmmmm
KmmmmmdPdmmmmmmmmmmdPdmmmmmmmK
KPPPPPPdPPPPPPPPPPPPdPPPPPPPPK
PsuuuuussssssssssssssuuuuuuuPK
PssssssssssssssssssssssssssuPK
PsssssssssssssssssssssssssssPK
""")
# neutral brows (hair_1, 1px): outer end 1px lower
put(g, 35, 32, "_dddddd")
put(g, 35, 33, "d")
put(g, 53, 32, "dddddd")
put(g, 59, 33, "d")

# ---- pass 2: crown + bang re-drawn as clumps (replaces C's stripes) ----
# outline: left edge Lx / right edge Rx per row (monotonic runs), top run x41-56 on row 12
L = {13: (37, 40), 14: (35, 36), 15: (33, 34), 16: (32, 32), 17: (31, 31), 18: (30, 30), 19: (29, 29), 20: (29, 29),
     21: (28, 28), 22: (28, 28), 23: (28, 28), 24: (27, 27), 25: (27, 27), 26: (27, 27), 27: (27, 27), 28: (27, 27)}
R = {13: (57, 60), 14: (61, 62), 15: (63, 64), 16: (65, 65), 17: (66, 66), 18: (67, 67), 19: (68, 68), 20: (69, 69),
     21: (69, 69), 22: (70, 70), 23: (70, 70), 24: (71, 71), 25: (71, 71), 26: (71, 71), 27: (71, 71), 28: (71, 71)}
for x in range(26, 73):
    for y in range(10, 29):
        g[y][x] = "."
for x in range(41, 57):
    g[12][x] = "K"
for y in range(13, 29):
    a0, a1 = L[y]; b0, b1 = R[y]
    for x in range(a0, b1 + 1):
        g[y][x] = "K" if (x <= a1 or x >= b0) else "m"
# clump split lines (hair_1), each fades in from the crown and lands on a notch / lock edge
lines = {
 "L1": {16: 38, 17: 38, 18: 37, 19: 37, 20: 36, 21: 36, 22: 36, 23: 35, 24: 35, 25: 35, 26: 35, 27: 34, 28: 34},
 "L2": {17: 45, 18: 45, 19: 44, 20: 44, 21: 44, 22: 43, 23: 43, 24: 42, 25: 42, 26: 42, 27: 41},
 "R2": {17: 51, 18: 51, 19: 52, 20: 52, 21: 52, 22: 53, 23: 53, 24: 53, 25: 54, 26: 54, 27: 54},
 "R1": {15: 57, 16: 58, 17: 58, 18: 59, 19: 59, 20: 60, 21: 60, 22: 61, 23: 61, 24: 62, 25: 62, 26: 62, 27: 63, 28: 63},
 "t1": {23: 31, 24: 31, 25: 31, 26: 31, 27: 31, 28: 31},
 "t2": {23: 48, 24: 48, 25: 48},
}
for ln in lines.values():
    for y, x in ln.items():
        g[y][x] = "d"
# far-side lock in shadow (right of R1)
for y in range(19, 29):
    for x in range(lines["R1"][y] + 1, R[y][0]):
        g[y][x] = "d"
# band highlight: one ring, broken per clump (upper dash 4-5 px over a 2-3 px dash), lower toward the sides
for y, x0, s_ in [(21, 30, "llll"), (22, 31, "ll"),
                  (19, 38, "lllll"), (20, 39, "lll"),
                  (18, 46, "lllll"), (19, 47, "lll"),
                  (19, 54, "llll"), (20, 55, "ll"),
                  (21, 63, "mmmm"), (22, 64, "mm")]:
    for i, ch in enumerate(s_):
        g[y][x0 + i] = ch
# notch tips (rows 28-29 kept from pass 1)
put(g, 40, 28, "ddd")
put(g, 53, 28, "ddd")

# ---- pass 3: BIG winged bow at the back of the crown (teal_0 b / teal_1 c / teal_2 e) ----
# Wings rise from a low knot (butterfly V), pinched to 4 rows at the knot, 18 rows tall at the outer end.
for y in range(0, 70):
    for x in range(72, 96):
        g[y][x] = "."
for y in range(0, 12):
    for x in range(40, 72):
        g[y][x] = "."
def span(y, x0, x1, ch):
    for x in range(x0, x1 + 1):
        g[y][x] = ch
def paint(spec):
    for row in spec:
        y = row[0]
        for x0, x1, ch in row[1:]:
            span(y, x0, x1, ch)
# right wing (far): outline + fill rows
paint([
 (1, (84, 88, "K")),
 (2, (82, 83, "K"), (84, 88, "e"), (89, 90, "K")),
 (3, (80, 81, "K"), (82, 83, "c"), (84, 89, "e"), (90, 90, "c"), (91, 91, "K")),
 (4, (78, 79, "K"), (80, 81, "c"), (82, 86, "e"), (87, 91, "c"), (92, 92, "K")),
 (5, (77, 77, "K"), (78, 92, "c"), (93, 93, "K")),
 (6, (76, 76, "K"), (77, 92, "c"), (93, 93, "K")),
 (7, (75, 75, "K"), (76, 92, "c"), (93, 93, "b"), (94, 94, "K")),
 (8, (74, 74, "K"), (75, 92, "c"), (93, 93, "b"), (94, 94, "K")),
 (9, (72, 73, "K"), (74, 85, "c"), (86, 89, "b"), (90, 92, "c"), (93, 93, "b"), (94, 94, "K")),
 (10, (73, 80, "c"), (81, 85, "b"), (86, 92, "c"), (93, 93, "b"), (94, 94, "K")),
 (11, (73, 76, "c"), (77, 80, "b"), (81, 92, "c"), (93, 93, "b"), (94, 94, "K")),
 (12, (73, 76, "b"), (77, 92, "c"), (93, 93, "b"), (94, 94, "K")),
 (13, (73, 79, "b"), (80, 91, "c"), (92, 92, "b"), (93, 93, "K")),
 (14, (73, 75, "K"), (76, 82, "b"), (83, 90, "c"), (91, 92, "b"), (93, 93, "K")),
 (15, (76, 78, "K"), (79, 91, "b"), (92, 92, "K")),
 (16, (79, 81, "K"), (82, 90, "b"), (91, 91, "K")),
 (17, (82, 84, "K"), (85, 88, "b"), (89, 90, "K")),
 (18, (85, 88, "K")),
])
# left wing (near, lit): bottom edge hidden behind the crown
paint([
 (1, (49, 53, "K")),
 (2, (47, 48, "K"), (49, 53, "e"), (54, 55, "K")),
 (3, (46, 46, "K"), (47, 47, "c"), (48, 54, "e"), (55, 55, "c"), (56, 57, "K")),
 (4, (45, 45, "K"), (46, 48, "c"), (49, 53, "e"), (54, 57, "c"), (58, 59, "K")),
 (5, (44, 44, "K"), (45, 59, "c"), (60, 60, "K")),
 (6, (44, 44, "K"), (45, 60, "c"), (61, 61, "K")),
 (7, (43, 43, "K"), (44, 61, "c"), (62, 62, "K")),
 (8, (43, 43, "K"), (44, 62, "c"), (63, 63, "K")),
 (9, (43, 43, "K"), (44, 52, "c"), (53, 56, "b"), (57, 63, "c"), (64, 65, "K")),
 (10, (43, 43, "K"), (44, 56, "c"), (57, 60, "b"), (61, 64, "c")),
 (11, (43, 43, "K"), (44, 45, "b"), (46, 60, "c"), (61, 64, "b")),
 (12, (57, 60, "b"), (61, 64, "b")),
 (13, (61, 64, "b")),
 (14, (63, 64, "b")),
])
# knot x65-72, rows 8-15 (round: corners cut)
paint([
 (8, (66, 71, "K")),
 (9, (66, 67, "e"), (68, 70, "c"), (71, 71, "b")),
 (10, (65, 65, "b"), (66, 66, "e"), (67, 70, "c"), (71, 71, "b"), (72, 72, "b")),
 (11, (65, 65, "b"), (66, 67, "c"), (68, 68, "b"), (69, 70, "c"), (71, 71, "b"), (72, 72, "b")),
 (12, (65, 65, "b"), (66, 67, "c"), (68, 68, "b"), (69, 70, "c"), (71, 71, "b"), (72, 72, "b")),
 (13, (65, 65, "b"), (66, 70, "c"), (71, 71, "b"), (72, 72, "b")),
 (14, (65, 65, "K"), (66, 71, "b"), (72, 72, "K")),
 (15, (66, 71, "K")),
])

# ---- pass 4: ponytail behind the head (right) + swallowtail bow tails ----
PR = {}
for y, x in [(16, 73), (17, 74), (18, 75), (19, 76), (20, 77), (21, 78)]:
    PR[y] = x
for ys, x in [((22, 23), 79), ((24, 25), 80), ((26, 28), 81), ((29, 32), 82), ((33, 40), 83), ((41, 44), 82),
              ((45, 48), 81), ((49, 52), 80), ((53, 57), 79), ((58, 62), 78), ((63, 70), 77)]:
    for y in range(ys[0], ys[1] + 1):
        PR[y] = x
for y, xr in PR.items():
    x0 = 66
    while g[y][x0] != "." and x0 < xr:   # start right of the head silhouette
        x0 += 1
    for x in range(x0, xr):
        g[y][x] = "m"
    g[y][xr] = "K"
    # shadow side (right) 3px hair_1, plum rim
    for x in range(max(x0, xr - 4), xr):
        g[y][x] = "d"
    if xr - 1 >= x0:
        g[y][xr - 1] = "P" if y > 30 else "d"
# clump split + highlight on the ponytail (lit dash near the gather)
for y, x in [(24, 75), (25, 75), (26, 76), (27, 76), (28, 76), (29, 76), (30, 77), (31, 77), (32, 77), (33, 77)]:
    g[y][x] = "d"
for y, x0, n in [(20, 72, 3), (21, 72, 4), (22, 73, 2)]:
    for x in range(x0, x0 + n):
        g[y][x] = "l"

# bow tails (swallowtail), drawn only right of the head silhouette (they hang behind the head)
def head_px(y, x):
    return x <= 71 and y >= 16 and g[y][x] in "mdlPK" and x <= {16: 65, 17: 66, 18: 67, 19: 68, 20: 69, 21: 69,
                                                             22: 70, 23: 70}.get(y, 71)
def tail(rows, fill, end_y, end_rows):
    for y, xl in rows:
        for i, ch in enumerate(fill):
            x = xl + i
            if not head_px(y, x):
                g[y][x] = ch
    for j, r in enumerate(end_rows):
        y = end_y + j
        xl = rows[-1][1]
        for i, ch in enumerate(r):
            if ch != "_" and not head_px(y, xl + i):
                g[y][xl + i] = ch
T2 = []
for ys, x in [((16, 16), 73), ((17, 17), 74), ((18, 18), 75), ((19, 19), 76), ((20, 21), 77), ((22, 23), 78),
              ((24, 25), 79), ((26, 27), 79), ((28, 31), 80), ((32, 34), 81)]:
    T2 += [(y, x) for y in range(ys[0], ys[1] + 1)]
tail(T2, "KccbbK", 35, ["KcKKbK", "KK__KK"])
T1 = []
for ys, x in [((16, 16), 71), ((17, 19), 72), ((20, 23), 73), ((24, 27), 74), ((28, 31), 75), ((32, 35), 76),
              ((36, 39), 77), ((40, 44), 78)]:
    T1 += [(y, x) for y in range(ys[0], ys[1] + 1)]
tail(T1, "KeccbK", 45, ["KcKKbK", "KK__KK"])

# ---- pass 5: body. order: back hair -> coat -> scarf -> collar -> front side locks ----
import copy
locks = copy.deepcopy(g)
for y in range(56, 96):
    for x in range(0, 96):
        if y >= 61 or x < 27 or (x > 61 and x < 72):
            if not (x >= 72 and y < 66):          # keep ponytail above the shoulder
                g[y][x] = "."
# (a) back hair on the left: straight fall behind the shoulder (hair_1, plum clump lines)
BH = {56: 22, 57: 22, 58: 22, 59: 22, 60: 22, 61: 21, 62: 21, 63: 21, 64: 21, 65: 20, 66: 20, 67: 20, 68: 20, 69: 20}
for y, xo in BH.items():
    g[y][xo] = "K"
    span(y, xo + 1, 27, "d")
for y in range(57, 70):
    g[y][24] = "P"
for y in range(62, 70):
    g[y][25] = "m" if y < 66 else "d"
# (b) coat. shoulder outline: left (lit) oat_0 q, right (shadow) K
LS = {62: (31, 32), 63: (30, 30), 64: (29, 29), 65: (28, 28), 66: (27, 27), 67: (25, 26), 68: (23, 24), 69: (20, 22),
      70: (17, 19), 71: (14, 16), 72: (12, 13), 73: (10, 11), 74: (9, 9), 75: (8, 8), 76: (7, 7), 77: (6, 6), 78: (6, 6)}
for y in range(79, 82): LS[y] = (5, 5)
for y in range(82, 86): LS[y] = (4, 4)
for y in range(86, 91): LS[y] = (3, 3)
for y in range(91, 96): LS[y] = (2, 2)
RS = {62: (66, 67), 63: (68, 68), 64: (69, 69), 65: (70, 70), 66: (71, 71), 67: (72, 73), 68: (74, 75), 69: (76, 77),
      70: (78, 79), 71: (80, 81), 72: (82, 83), 73: (84, 84), 74: (85, 85), 75: (86, 86), 76: (87, 87), 77: (87, 87)}
for y in range(78, 81): RS[y] = (88, 88)
for y in range(81, 85): RS[y] = (89, 89)
for y in range(85, 90): RS[y] = (90, 90)
for y in range(90, 96): RS[y] = (91, 91)
for y in range(62, 96):
    a0, a1 = LS[y]; b0, b1 = RS[y]
    for x in range(a1 + 1, b0):
        g[y][x] = "o"
    span(y, a0, a1, "q"); span(y, b0, b1, "K")
# sleeve/torso split lines from the armpit down
for y, x in [(81, 16), (82, 16), (83, 16), (84, 15), (85, 15), (86, 15), (87, 15), (88, 15), (89, 14), (90, 14),
             (91, 14), (92, 14), (93, 14), (94, 14), (95, 14)]:
    g[y][x] = "q"
for y, x in [(81, 79), (82, 79), (83, 79), (84, 80), (85, 80), (86, 80), (87, 80), (88, 80), (89, 81), (90, 81),
             (91, 81), (92, 81), (93, 81), (94, 81), (95, 81)]:
    g[y][x] = "q"
# shadow: far sleeve (right of its split) + a band down the far side of the torso
for y in range(74, 96):
    for x in range(1, 96):
        if g[y][x] == "o" and x > RS[y][0] - 4:
            g[y][x] = "O"
for y in range(81, 96):
    for x in range(72 + (y - 81) // 4, 80 + (y - 81) // 4):
        if g[y][x] == "o":
            g[y][x] = "O"
# armpit fold wedges (2-4 px oat_1), pointing in toward the bust
paint([(82, (17, 18, "O")), (83, (17, 20, "O")), (84, (18, 21, "O")), (85, (20, 22, "O")),
       (83, (77, 78, "O")), (84, (75, 78, "O")), (85, (74, 77, "O")), (86, (73, 75, "O"))])
# left sleeve: one fold from the shoulder point
paint([(77, (9, 10, "O")), (78, (9, 11, "O")), (79, (10, 12, "O")), (80, (11, 12, "O"))])
# bust: 1px under-curve each side
paint([(90, (27, 30, "O")), (91, (30, 35, "O")), (92, (35, 41, "O")), (91, (66, 69, "O")), (92, (62, 66, "O"))])
# (c) chunky double-wrap scarf: upper roll hugs the neck, lower roll rests on the shoulders
paint([
 (60, (39, 63, "K")),
 (61, (38, 38, "K"), (39, 63, "c"), (64, 64, "K")),
 (62, (37, 37, "K"), (38, 64, "c"), (65, 65, "K")),
 (63, (36, 36, "K"), (37, 64, "c"), (65, 65, "K")),
 (64, (36, 36, "K"), (37, 64, "c"), (65, 65, "K")),
 (65, (36, 36, "K"), (37, 64, "c"), (65, 65, "K")),
 (66, (36, 36, "K"), (37, 64, "b"), (65, 65, "K")),
 (67, (28, 35, "K"), (36, 65, "b"), (66, 72, "K")),
 (68, (26, 27, "K"), (28, 72, "c"), (73, 74, "K")),
 (69, (25, 25, "K"), (26, 73, "c"), (74, 74, "K")),
 (70, (24, 24, "K"), (25, 74, "c"), (75, 75, "K")),
 (71, (24, 24, "K"), (25, 74, "c"), (75, 75, "K")),
 (72, (24, 24, "K"), (25, 74, "c"), (75, 75, "K")),
 (73, (24, 24, "K"), (25, 74, "c"), (75, 75, "K")),
 (74, (24, 24, "K"), (25, 74, "b"), (75, 75, "K")),
 (75, (25, 25, "K"), (26, 73, "b"), (74, 74, "K")),
 (76, (26, 28, "K"), (29, 71, "b"), (72, 73, "K")),
 (77, (29, 71, "K")),
])
# knit: one lit teal_2 ridge along the top of each roll (broken), vertical rib grooves, shadowed underside
paint([
 (61, (39, 45, "e"), (48, 53, "e"), (56, 58, "e")),
 (62, (38, 39, "e")),
 (68, (28, 36, "e"), (39, 46, "e"), (49, 54, "e"), (57, 59, "e")),
 (69, (26, 28, "e")),
])
for x in range(40, 64, 3):
    for y in (63, 64, 65):
        g[y][x] = "b"
for x in range(29, 74, 3):
    for y in (70, 71, 72, 73):
        g[y][x] = "b"
for y in range(61, 66):
    g[y][63] = g[y][64] = "b"
for y in range(68, 74):
    g[y][73] = g[y][74] = "b"
# scarf tail (one, on HER LEFT): x55-66, rows 77-95, slight outward drift, vertical knit ribs
for y in range(76, 96):
    d = (y - 76) // 10
    x0 = 55 + d
    g[y][x0] = "K"; g[y][x0 + 11] = "K"
    for i, ch in enumerate("ecccbccbccb"[:10]):
        g[y][x0 + 1 + i] = ch
span(76, 56, 65, "b"); span(77, 56, 65, "b")
g[78][56] = g[79][56] = "c"
# (d) collar: rounded (Peter Pan) flaps peeking under the lower roll, centre placket, gold buttons
flapL = [(78, [(30, 30, "q"), (31, 47, "o")]), (79, [(31, 31, "q"), (32, 46, "o"), (47, 47, "q")]),
         (80, [(32, 33, "q"), (34, 45, "o"), (46, 46, "q")]), (81, [(34, 36, "q"), (37, 44, "o"), (45, 45, "q")]),
         (82, [(37, 44, "q")])]
for y, runs in flapL:
    for x0, x1, ch in runs:
        span(y, x0, x1, ch)
        span(y, 97 - x1, 97 - x0, ch)     # mirror about x48.5 (the tail covers most of it)
# shadows that separate the flaps from the coat: gap at centre front + 2px cast shadow under each curve
paint([(78, (48, 49, "O")), (79, (48, 49, "O")), (80, (47, 50, "O")), (81, (46, 51, "O")), (82, (45, 52, "O")),
       (83, (36, 61, "O")), (84, (38, 43, "O")), (84, (54, 59, "O")),
       (79, (29, 30, "O")), (80, (30, 31, "O")), (81, (31, 33, "O")), (82, (33, 36, "O"))])
g[78][67] = "o"
for y in range(84, 96):
    g[y][48] = "q"
for y in (87, 88, 93, 94):
    g[y][46] = g[y][47] = "g"
# re-lay the tail over the right flap
for y in range(76, 96):
    d = (y - 76) // 10
    x0 = 55 + d
    g[y][x0] = "K"; g[y][x0 + 11] = "K"
    for i, ch in enumerate("ecccbccbccb"[:10]):
        g[y][x0 + 1 + i] = ch
span(76, 56, 65, "b"); span(77, 56, 65, "b")
for y in (84, 91):
    span(y, 56 + (y - 76) // 10, 65 + (y - 76) // 10, "b")
# (e) front side locks, blunt cut at the collarbone, over the scarf
for y in range(46, 77):
    g[y][27] = "K"; g[y][34] = "K" if y >= 56 else g[y][34]
    if y >= 56:
        for i, ch in enumerate("mlmdmd" if 62 <= y <= 64 else "mmmdmd"):
            g[y][28 + i] = ch
span(76, 27, 34, "K"); span(75, 28, 33, "d")
for y in range(56, 75):
    g[y][71] = "K"; g[y][64] = "K"
    for i, ch in enumerate("dmdmmd" if not 60 <= y <= 62 else "dlmmmd"):
        g[y][65 + i] = ch
span(74, 64, 71, "K"); span(73, 65, 70, "d")
# neck-side back hair between lock and neck (shadow) above the scarf
for y in range(56, 60):
    for x in range(35, 40):
        if locks[y][x] != ".":
            g[y][x] = locks[y][x]
    for x in range(62, 64):
        g[y][x] = "d"

# ---- pass 7: eyes rebuilt to the style guide (pupil + 2x2 / 1px catchlights, sclera, tare-me outer droop) ----
# near eye = screen-right (she is turned slightly to screen-left), far eye = screen-left (narrower)
for y in range(34, 44):
    for x in list(range(35, 44)) + list(range(50, 62)):
        g[y][x] = "s"
put(g, 35, 34, """
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
""")
put(g, 50, 34, """
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
""")

# ---- pass 8: joins / cleanup ----
paint([(61, (35, 37, "K")), (62, (35, 36, "c"), (37, 37, "c")), (63, (35, 36, "c"), (37, 37, "c")),
       (64, (35, 36, "c"), (37, 37, "c")), (65, (35, 36, "b"), (37, 37, "c")), (66, (35, 37, "b"))])
g[62][37] = "e"
g[69][26] = "c"
span(15, 72, 75, "c"); g[15][72] = "e"; g[15][75] = "b"; g[15][65] = "K"
# ponytail continues down behind the right shoulder
for y, x0, x1 in [(66, 72, 77), (67, 74, 77), (68, 76, 77)]:
    for x in range(x0, x1 + 1):
        if g[y][x] == ".":
            g[y][x] = "d" if x < 76 else ("P" if x == 76 else "K")

g[35][62] = "s"
# ---- pass 9: base = NEUTRAL face (bible: open / flat / short line / no extras) ----
for y in (46, 47):                       # C's blush off (neutral has none)
    for x in range(35, 60):
        if g[y][x] in "xv":
            g[y][x] = "s"
g[46][35] = g[47][35] = "P"              # re-close the face outline where C's blush sat on it
for y in (49, 50):                       # C's ":3" mouth off
    for x in range(44, 50):
        if g[y][x] in "Lr":
            g[y][x] = "s"
span(50, 45, 47, "L")
g[34][47] = g[34][48] = "s"          # C forehead speck off

# ==== END ====
legend += ["g = #E2A434 gold_1", "y = #BA4A58 crn_2", "z = #A8C0E0 snow_1", "R = #DC3A40 red_1", "w = #DFEAF6 snow_2", "a = #20223E ink"]
write(OUT, "# r13 dialogue bust base (lead pixel artist). Derived from face test C. Hand-authored.", legend, g)
