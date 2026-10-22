"""bust_base.pix builder, round 2 (after docs/review/r13_review1_bust.md).

Every pixel decision is typed here as explicit runs / per-row tables / literal blocks; the script only paints them.
Face construction follows candidate C (art/hand/S4/face_tests/C_dote.pix, pasted at +10,+5 in round 1), rebuilt as a
true 3/4 (facing screen-left): far side = screen-left, near side = screen-right.
"""
import os
from pipeline.tools.r13_bust.pixlib import read_grid, canvas, put, write

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
C = os.path.join(ROOT, "art/hand/S4/face_tests/C_dote.pix")
OUT = os.path.join(ROOT, "art/hand/S4/bust/bust_base.pix")
legend, _ = read_grid(C)
legend += ["g = #E2A434 gold_1", "y = #BA4A58 crn_2", "z = #A8C0E0 snow_1", "R = #DC3A40 red_1",
           "w = #DFEAF6 snow_2", "a = #20223E ink"]
g = canvas(96, 96)


def span(y, x0, x1, ch):
    for x in range(x0, x1 + 1):
        g[y][x] = ch


def paint(spec):
    for row in spec:
        for x0, x1, ch in row[1:]:
            span(row[0], x0, x1, ch)


def rows_tbl(pairs):
    """[((y0, y1), v), ...] -> {y: v}"""
    d = {}
    for (a, b), v in pairs:
        for y in range(a, b + 1):
            d[y] = v
    return d


# =====================================================================================================
# 1. HEAD SILHOUETTE: domed crown (runs 6-4-3-2-1), +2-3 px at the temples, skull bulging behind (right)
# =====================================================================================================
TOP = {9: [(47, 52)], 10: [(43, 46), (53, 56)], 11: [(40, 42), (57, 59)], 12: [(38, 39), (60, 61)]}
HL = rows_tbl([((13, 13), 37), ((14, 14), 36), ((15, 15), 35), ((16, 16), 34), ((17, 17), 33), ((18, 18), 32),
               ((19, 19), 31), ((20, 20), 30), ((21, 21), 29), ((22, 23), 28), ((24, 26), 27), ((27, 30), 26),
               ((31, 46), 25), ((47, 52), 24), ((53, 58), 23), ((59, 70), 22)])
HR = rows_tbl([((13, 13), 62), ((14, 14), 63), ((15, 15), 65), ((16, 16), 66), ((17, 17), 68), ((18, 18), 69),
               ((19, 19), 70), ((20, 20), 71), ((21, 21), 72), ((22, 22), 73), ((23, 23), 74), ((24, 25), 75),
               ((26, 29), 76), ((30, 44), 77), ((45, 70), 76)])
for y, runs in TOP.items():
    for a, b in runs:
        span(y, a, b, "K")
    if y > 9:
        span(y, runs[0][1] + 1, runs[1][0] - 1, "m")
for y in range(13, 71):
    span(y, HL[y] + 1, HR[y] - 1, "m")
    g[y][HL[y]] = "K"
    g[y][HR[y]] = "K"

# =====================================================================================================
# 2. FACE (true 3/4): far cheek bulge x33 y38-46 then steep taper; near jaw x62 -> chin, runs 1-1-2-2-3-3-4;
#    chin x43-45 y55-56. Lines: P against hair, L (line_skin) on the near jaw / chin.
# =====================================================================================================
FARL = rows_tbl([((30, 37), 34), ((38, 46), 33)])
FARRUN = {47: (34, 34), 48: (34, 34), 49: (34, 34), 50: (35, 35), 51: (36, 36), 52: (37, 38), 53: (39, 40),
          54: (41, 41), 55: (42, 42)}                # round lower cheek, then into the chin
for y, (a, b) in FARRUN.items():
    FARL[y] = b
NEAR = {y: [(62, 62)] for y in range(30, 49)}
NEAR.update({49: [(61, 61)], 50: [(60, 60)], 51: [(58, 59)], 52: [(56, 57)], 53: [(53, 55)], 54: [(50, 52)],
             55: [(46, 49)]})
for y in range(30, 56):
    x0 = FARL[y] + 1
    x1 = NEAR[y][0][0] - 1
    span(y, x0, x1, "s")
    g[y][FARL[y]] = "P"
    if y in FARRUN:
        span(y, FARRUN[y][0], FARRUN[y][1], "P")
    for a, b in NEAR[y]:
        span(y, a, b, "P" if y <= 48 else "L")
span(56, 43, 45, "L")                             # chin
# neck: front edge x44, back edge x58 (P), shaded under the jaw
for x in range(45, 58):
    jaw = max(y for y in range(30, 57) if g[y][x] in "LsP")
    g[jaw + 1][x] = "v"
    for y in range(jaw + 2, 62):
        g[y][x] = "u"
for y in range(57, 62):
    g[y][44] = "P"
for y in range(52, 62):
    g[y][58] = "P"
# hair behind the jaw / neck is in shadow
for y in range(47, 71):
    for x in range(HL[y] + 1, HR[y]):
        if g[y][x] == "m":
            g[y][x] = "d"

# =====================================================================================================
# 3. BANGS: 3 panels, centre lowest (y31-32), outer panels lifted; notches up to y27 at x42 / x55.
#    e[x] = row of the plum edge line; skin below, 1 px skin_1 cast shadow under it.
# =====================================================================================================
E = dict(zip(range(35, 63), [28, 29, 29, 29, 29, 28, 27, 25, 28, 29, 30, 31, 32, 32, 32, 32, 31, 30, 29, 28, 25, 27,
                             28, 29, 29, 29, 29, 28]))
for x, e in E.items():
    for y in range(e + 1, 34):
        g[y][x] = "s"
    g[e][x] = "P"
    g[e + 1][x] = "u"
for x in range(36, 62):                           # connect steps (notch walls) with plum
    for nb in (x - 1, x + 1):
        if nb in E and E[nb] < E[x] - 1:
            for y in range(E[nb] + 1, E[x]):
                g[y][x] = "P"
for x in (34,):
    for y in range(28, 30):
        g[y][x] = "m"
# clump lines (hair_1) curving from the whorl at x52,y12: A/B land on the notches, C/D split panels from locks
LINES = {
 "A": [(51, 13), (50, 14), (49, 15), (48, 16), (47, 17), (47, 18), (46, 19), (46, 20), (45, 21), (45, 22), (44, 23),
       (44, 24), (43, 25)],
 "B": [(52, 13), (53, 14), (53, 15), (53, 16), (54, 17), (54, 18), (54, 19), (54, 20), (55, 21), (55, 22), (55, 23),
       (55, 24), (55, 25)],
 "C": [(48, 12), (47, 12), (46, 13), (45, 13), (44, 14), (43, 14), (42, 15), (41, 16), (40, 17), (39, 18), (38, 19),
       (37, 20), (36, 21), (35, 22), (35, 23), (34, 24), (34, 25), (33, 26), (33, 27)],
 "D": [(54, 12), (55, 12), (56, 13), (57, 13), (58, 14), (59, 15), (60, 16), (60, 17), (61, 18), (61, 19), (62, 20),
       (62, 21), (63, 22), (63, 23), (63, 24), (64, 25), (64, 26), (64, 27)],
}
for pts in LINES.values():
    for x, y in pts:
        g[y][x] = "d"
# shadow side: right of D (toward the back of the skull) in hair_1
for y in range(13, 47):
    xd = max([x for x, yy in LINES["D"] if yy == y], default=64 if y > 27 else None)
    if xd is None:
        continue
    for x in range(xd + 1, HR[y]):
        if g[y][x] == "m":
            g[y][x] = "d"
# band highlight: one ring around the dome, broken per clump (upper dash over shorter dash)
for y, x0, x1, ch in [(16, 50, 52, "l"),
                      (17, 48, 53, "l"), (18, 49, 52, "l"),
                      (19, 40, 45, "l"), (20, 41, 44, "l"),
                      (19, 56, 59, "l"), (20, 57, 58, "l"),
                      (23, 28, 32, "l"), (24, 29, 31, "l"),
                      (21, 65, 68, "m"), (22, 66, 67, "m")]:
    for x in range(x0, x1 + 1):
        if g[y][x] in "md":
            g[y][x] = ch
# lower bang shading: panel tips darken toward the edge (hair_1 above the plum line, middle of each panel)
for x in list(range(37, 40)) + list(range(47, 51)) + list(range(58, 61)):
    if g[E[x] - 1][x] == "m":
        g[E[x] - 1][x] = "d"

# =====================================================================================================
# 4. PONYTAIL (behind, gathered under the knot at the back of the skull), S-taper to the shoulder
# =====================================================================================================
PR = rows_tbl([((30, 33), 81), ((34, 37), 82), ((38, 42), 83), ((43, 50), 84), ((51, 56), 83),
               ((57, 60), 82), ((61, 64), 81), ((65, 70), 80)])
for y, xr in PR.items():
    span(y, HR[y] + 1, xr - 1, "m")
    g[y][xr] = "K"
    span(y, max(HR[y] + 1, xr - 3), xr - 1, "d")
    g[y][xr - 1] = "P"
    if y <= 40:
        g[y][HR[y]] = "P"                          # head edge reads as an inner fold, not a wall
for x, y in [(77, 46), (77, 47), (78, 48), (78, 49), (78, 50), (78, 51), (78, 52), (77, 53), (77, 54)]:
    g[y][x] = "d"
span(45, 75, 76, "l"); span(46, 75, 75, "l")

# =====================================================================================================
# 5. BOW (binding): knot on the back of the skull x76-81 y22-29, partly behind the ponytail root;
#    pinched + creased loops, upper rises up-back, lower drops down-back; tip to tip ~41 px, >=3 px inside.
# =====================================================================================================
def loop(edges, top, bottom):
    ys = sorted(edges)
    for y, (l, r) in edges.items():
        span(y, l + 1, r - 1, "c")
        g[y][l] = "K"
        g[y][r] = "K"
    for a, b_ in zip(ys, ys[1:]):                 # close stair gaps so the outline is one connected line
        (la, ra), (lb, rb) = edges[a], edges[b_]
        if rb < ra - 1:
            span(b_, rb, ra - 1, "K")
        if rb > ra + 1:
            span(a, ra, rb - 1, "K")
        if lb > la + 1:
            span(b_, la + 1, lb, "K")
        if lb < la - 1:
            span(a, lb + 1, la, "K")
    span(top[0], top[1], top[2], "K")
    span(bottom[0], bottom[1], bottom[2], "K")
# tails first (they hang from under the knot, behind the loops) - they swing out to the back
T1 = rows_tbl([((30, 33), 76), ((34, 37), 77), ((38, 41), 78), ((42, 45), 79), ((46, 48), 80), ((49, 50), 81)])
T2 = rows_tbl([((30, 33), 82), ((34, 37), 83), ((38, 40), 84), ((41, 43), 85), ((44, 45), 86), ((46, 47), 87),
               ((48, 48), 88)])
for T, fill, end in ((T2, "KcbK", 49), (T1, "KecbK", 51)):
    for y, xl in T.items():
        for i, ch in enumerate(fill):
            g[y][xl + i] = ch
    xl = T[end - 1]
    put(g, xl, end, ("KcKK" if len(fill) == 4 else "KcKbK") + "\n" + ("K__K" if len(fill) == 4 else "K___K"))
# upper loop (rises up-back)
UP = {9: (84, 91), 10: (83, 92), 11: (82, 92), 12: (81, 93), 13: (81, 93), 14: (80, 93), 15: (80, 93),
      16: (80, 92), 17: (80, 91), 18: (80, 90), 19: (80, 88), 20: (80, 86), 21: (80, 84)}
loop(UP, (8, 86, 90), (22, 80, 82))
# lower loop (drops down-back)
LO = {24: (82, 88), 25: (81, 89), 26: (81, 90), 27: (81, 91), 28: (81, 91), 29: (81, 92), 30: (82, 92), 31: (82, 92),
      32: (83, 92), 33: (83, 92), 34: (83, 92), 35: (84, 92), 36: (84, 92), 37: (84, 92), 38: (84, 91), 39: (85, 91),
      40: (85, 91), 41: (86, 90), 42: (86, 90), 43: (87, 89)}
loop(LO, (23, 83, 87), (44, 87, 89))
# loop shading: lit top-left, one crease each from the pinch, shadowed underside / back rim
paint([(9, (85, 90, "e")), (10, (84, 89, "e")), (11, (83, 86, "e")), (12, (82, 84, "e")), (13, (82, 83, "e")), (14, (81, 81, "e")), (15, (81, 81, "e"))])
for x, y in [(81, 20), (82, 19), (83, 18), (84, 17), (85, 17), (86, 16), (87, 16)]:
    g[y][x] = "b"
for y in range(13, 22):
    for x in range(max(UP[y][0] + 1, UP[y][1] - 2), UP[y][1]):
        g[y][x] = "b"
paint([(25, (82, 86, "e")), (26, (82, 84, "e")), (27, (82, 83, "e"))])
for x, y in [(83, 28), (84, 29), (85, 30), (86, 31), (87, 32), (88, 33), (88, 34)]:
    g[y][x] = "b"
for y in range(30, 44):
    for x in range(max(LO[y][0] + 1, LO[y][1] - 2), LO[y][1]):
        g[y][x] = "b"
# loop openings: the inside of each loop shows as a dark oval near its outer end (reads as a loop, not a paddle)
# loop undersides (the fabric turning inward): two-tone below each crease
for y in range(17, 22):
    for x in range(UP[y][0] + 1, UP[y][1]):
        if g[y][x] == "c" and x >= 82 + (21 - y):
            g[y][x] = "b"
for y in range(38, 44):
    for x in range(LO[y][0] + 1, LO[y][1]):
        if g[y][x] == "c":
            g[y][x] = "b"
# knot (rounded, 6x8), its lower-left tucked behind the ponytail root
paint([(22, (77, 80, "K")),
       (23, (76, 76, "K"), (77, 78, "e"), (79, 80, "c"), (81, 81, "K")),
       (24, (76, 76, "K"), (77, 77, "e"), (78, 80, "c"), (81, 81, "b")),
       (25, (76, 76, "K"), (77, 78, "c"), (79, 79, "b"), (80, 80, "c"), (81, 81, "b")),
       (26, (76, 76, "K"), (77, 78, "c"), (79, 79, "b"), (80, 80, "c"), (81, 81, "b")),
       (27, (76, 76, "K"), (77, 80, "c"), (81, 81, "b")),
       (28, (76, 76, "K"), (77, 80, "b"), (81, 81, "K")),
       (29, (77, 80, "K"))])
# ponytail root over the knot's lower-left corner (hair gathered into the tie)
paint([(27, (75, 75, "d")), (28, (75, 76, "d")), (29, (75, 76, "d")), (30, (75, 75, "d"))])
g[26][75] = "P"

# =====================================================================================================
# 6. COAT: sloped shoulders, armhole seams, armpit wedges, bust crescents (light from upper-left)
# =====================================================================================================
LS = rows_tbl([((62, 62), (31, 32)), ((63, 63), (30, 30)), ((64, 64), (29, 29)), ((65, 65), (28, 28)),
               ((66, 66), (27, 27)), ((67, 67), (25, 26)), ((68, 68), (23, 24)), ((69, 69), (20, 22)),
               ((70, 70), (17, 19)), ((71, 71), (14, 16)), ((72, 72), (12, 13)), ((73, 73), (10, 11)),
               ((74, 74), (9, 9)), ((75, 75), (8, 8)), ((76, 76), (7, 7)), ((77, 78), (6, 6)), ((79, 81), (5, 5)),
               ((82, 85), (4, 4)), ((86, 90), (3, 3)), ((91, 95), (2, 2))])
RS = rows_tbl([((62, 62), (66, 67)), ((63, 63), (68, 68)), ((64, 64), (69, 69)), ((65, 65), (70, 70)),
               ((66, 66), (71, 71)), ((67, 67), (72, 73)), ((68, 68), (74, 75)), ((69, 69), (76, 77)),
               ((70, 70), (78, 79)), ((71, 71), (80, 81)), ((72, 72), (82, 83)), ((73, 73), (84, 84)),
               ((74, 74), (85, 85)), ((75, 76), (86, 86)), ((77, 79), (87, 87)), ((80, 83), (88, 88)),
               ((84, 88), (89, 89)), ((89, 95), (90, 90))])
for y in range(62, 96):
    a0, a1 = LS[y]
    b0, b1 = RS[y]
    span(y, a1 + 1, b0 - 1, "o")
    span(y, a0, a1, "q")
    span(y, b0, b1, "K")
# back hair ends square behind the shoulder (no tangent): straight drop, then the shoulder line cuts across it
for y in range(63, 70):
    if g[y][22] == "K" and y >= 69:
        g[y][22] = "q"
# armhole seams: from the shoulder point curving to the armpit, then the sleeve/torso split
for x, y in [(13, 73), (14, 74), (14, 75), (15, 76), (15, 77), (16, 78), (16, 79), (16, 80), (17, 81), (17, 82),
             (17, 83), (16, 84), (16, 85), (16, 86), (16, 87), (15, 88), (15, 89), (15, 90), (15, 91), (15, 92),
             (14, 93), (14, 94), (14, 95)]:
    g[y][x] = "q"
for x, y in [(82, 73), (81, 74), (81, 75), (80, 76), (80, 77), (79, 78), (79, 79), (79, 80), (78, 81), (78, 82),
             (78, 83), (79, 84), (79, 85), (79, 86), (79, 87), (80, 88), (80, 89), (80, 90), (80, 91), (80, 92),
             (81, 93), (81, 94), (81, 95)]:
    g[y][x] = "q"
# far-side (right) sleeve in shadow: a band hugging the back edge, widening down the arm
for y in range(74, 96):
    w = 2 + (y - 74) // 4
    for x in range(RS[y][0] - w, RS[y][0]):
        if g[y][x] == "o":
            g[y][x] = "O"
# torso side shadow along the right seam (crescent, not a box)
for y, x0, x1 in [(84, 76, 77), (85, 75, 77), (86, 74, 77), (87, 74, 77), (88, 74, 78), (89, 75, 79), (90, 75, 79),
                  (91, 76, 79), (92, 76, 79), (93, 77, 79), (94, 77, 79), (95, 78, 79)]:
    span(y, x0, x1, "O")
# armpit wedges (2-4 px, pointing in to the bust)
paint([(83, (18, 19, "O")), (84, (17, 21, "O")), (85, (17, 23, "O")), (86, (17, 21, "O")), (87, (17, 18, "O")),
       (84, (76, 77, "O")), (85, (73, 77, "O")), (86, (72, 73, "O"))])
# bust crescents (1 px bust step: the curve shades the coat under it)
paint([(88, (26, 27, "O")), (89, (27, 30, "O")), (90, (28, 40, "O")), (91, (30, 40, "O")), (92, (33, 38, "O")),
       (88, (70, 71, "O")), (89, (67, 71, "O")), (90, (64, 70, "O")), (91, (65, 69, "O")), (90, (53, 55, "O")),
       (91, (51, 55, "O")), (92, (52, 54, "O"))])
# left sleeve: soft lit fold from the shoulder point
paint([(78, (8, 9, "O")), (79, (8, 10, "O")), (80, (9, 10, "O"))])

# =====================================================================================================
# 7. SCARF: 11-12 rows, top dips at the throat, tilted 3/4 (near side lower), overlaps the shoulders,
#    2 teal_2 ridges per roll, tail 8 px on HER LEFT (viewer's right)
# =====================================================================================================
def rng(pairs):
    d = {}
    for (a, b), v in pairs:
        for x in range(a, b + 1):
            d[x] = v
    return d
UTOP = rng([((37, 37), 62), ((38, 38), 61), ((39, 44), 60), ((45, 51), 61), ((52, 60), 60), ((61, 61), 61),
            ((62, 63), 62)])
SPLIT = rng([((33, 33), 68), ((34, 34), 67), ((35, 40), 66), ((41, 65), 67), ((66, 66), 68), ((67, 67), 69)])
LBOT = rng([((33, 33), 70), ((34, 35), 71), ((36, 65), 72), ((66, 66), 71), ((67, 67), 70)])
# chunky knit: each roll = a lit top edge, body, shadowed underside, and 3 raised ridges (teal_2 crest + teal_0 groove)
UGROOVE = (44, 52, 59)
LGROOVE = (39, 48, 57, 64)
for x in range(33, 68):
    sp, bot = SPLIT[x], LBOT[x]
    if x in UTOP:
        t = UTOP[x]
        g[t][x] = "K"
        for y in range(t + 1, sp):
            g[y][x] = "c"
        if x < 60:
            g[t + 1][x] = "e"
        g[sp - 1][x] = "b" if x >= 40 else "c"
        g[sp][x] = "b"
    else:
        g[sp][x] = "K"
    for y in range(sp + 1, bot):
        g[y][x] = "c"
    if x < 64:
        g[sp + 1][x] = "e"
    g[bot - 1][x] = "b"
    g[bot][x] = "K"
for gx in UGROOVE:                                # groove leans with the roll's curve; crest lit on its left
    for y in range(UTOP[gx] + 2, SPLIT[gx] - 1):
        g[y][gx] = "b"
    g[UTOP[gx] + 1][gx] = "c"
    for y in range(UTOP[gx] + 2, SPLIT[gx] - 2):
        g[y][gx - 1] = "e"
for gx in LGROOVE:
    for y in range(SPLIT[gx] + 2, LBOT[gx] - 1):
        g[y][gx] = "b"
    g[SPLIT[gx] + 1][gx] = "c"
    for y in range(SPLIT[gx] + 2, LBOT[gx] - 2):
        g[y][gx - 1] = "e"
# rounded ends (outline) + shadowed near ends
for y in range(62, 66):
    g[y][36] = "K"
g[61][37] = "K"
for y in range(63, 67):
    g[y][64] = "K"
g[67][32] = "K"; g[68][32] = "K"; g[69][32] = "K"; g[70][33] = "K"
g[69][68] = "K"; g[70][68] = "K"; g[71][67] = "K"; g[68][67] = "K"
for y in range(61, 72):
    for x in range(58, 68):
        if g[y][x] in "ec" and x >= (61 if y < 67 else 64):
            g[y][x] = "b"
# hair (behind) fills the pockets between the locks and the scarf, so no coat slivers show there
for y in range(60, 70):
    for x in list(range(23, 37)) + list(range(63, 77)):
        if g[y][x] in "oqK." and g[y - 1][x] in "dmPlK" and not (g[y][x] == "K" and y >= 66):
            if x < 37 and y < SPLIT.get(x, 67) or x >= 63 and y < SPLIT.get(x, 69):
                g[y][x] = "d"
# tail (8 px incl. line), drifts 1 px outward every 12 rows
for y in range(73, 96):
    x0 = 56 + (y - 73) // 12
    row = "KeccccbK"
    for i, ch in enumerate(row):
        g[y][x0 + i] = ch
for y in (77, 82, 87, 92):                        # knit ridges across the tail
    x0 = 56 + (y - 73) // 12
    span(y, x0 + 1, x0 + 5, "e")
    g[y][x0 + 6] = "b"
span(73, 57, 62, "b"); span(72, 56, 63, "K")

# =====================================================================================================
# 8. PETER PAN COLLAR: two round lobes under the scarf, meeting at the centre front x46; placket + buttons
# =====================================================================================================
LOBE_L = [(73, 35, 45), (74, 35, 45), (75, 36, 45), (76, 37, 44), (77, 39, 43)]
for y, a, b in LOBE_L:
    span(y, a, b, "o")
    g[y][a - 1] = "q"
    g[y][b + 1] = "q"
span(78, 39, 43, "q"); g[77][38] = "q"; g[76][36] = "q"; g[77][44] = "q"; g[76][45] = "q"
LOBE_R = [(73, 47, 55), (74, 47, 55), (75, 48, 55), (76, 49, 55)]
for y, a, b in LOBE_R:
    span(y, a, b, "o")
    g[y][a - 1] = "q"
span(77, 49, 55, "q"); g[76][48] = "q"; g[75][47] = "q"
span(73, 46, 46, "O")
paint([(79, (39, 43, "O")), (78, (49, 55, "O")), (78, (44, 48, "O")), (79, (45, 47, "O")), (80, (40, 42, "O")),
       (79, (50, 54, "O"))])
for y in range(79, 96):
    g[y][46] = "q"
for y in (82, 83, 90, 91):
    g[y][44] = g[y][45] = "g"

# =====================================================================================================
# 9. SIDE LOCKS: tapering C-curves, 2 px clumps; far (left) narrower. Tips near y64, over the scarf.
#    (row, left edge, right edge) of the fill; plum line on both sides and under the tip.
# =====================================================================================================
FAR_LOCK = rows_tbl([((26, 30), (27, 32)), ((31, 37), (27, 33)), ((38, 46), (27, 32)), ((47, 54), (27, 31)),
                     ((55, 58), (28, 31)), ((59, 61), (29, 31)), ((62, 63), (30, 31))])
NEAR_LOCK = rows_tbl([((26, 30), (65, 70)), ((31, 48), (63, 68)), ((49, 54), (63, 68)), ((55, 58), (64, 68)),
                      ((59, 61), (64, 67)), ((62, 63), (64, 66))])
for lock, clump in ((FAR_LOCK, 2), (NEAR_LOCK, 3)):
    for y, (a, b) in lock.items():
        span(y, a, b, "m")
        g[y][a - 1] = "P"
        if g[y][b + 1] not in "sPL" or y > 46:
            g[y][b + 1] = "P"
    ys = sorted(lock)
    last = lock[ys[-1]]
    span(ys[-1] + 1, last[0], last[1], "P")
# clump split lines (start at the root, fade before the tip) + lit dashes
for x, y in [(29, 32), (29, 33), (29, 34), (29, 35), (29, 36), (29, 37), (29, 38), (29, 39), (29, 40), (29, 41),
             (29, 42), (30, 43), (30, 44)]:
    g[y][x] = "d"
for x, y in [(65, 31), (65, 32), (65, 33), (65, 34), (65, 35), (65, 36), (65, 37), (65, 38), (65, 39), (65, 40),
             (65, 41), (66, 42), (66, 43), (66, 44)]:
    g[y][x] = "d"
for y in range(31, 72):                          # shadow edge on the right side of each lock
    for lock in (FAR_LOCK, NEAR_LOCK):
        if y in lock:
            g[y][lock[y][1]] = "d"
for y, x0, x1 in [(34, 30, 31), (35, 30, 31), (36, 30, 30), (34, 27, 28), (35, 27, 28),
                  (35, 63, 64), (36, 63, 64), (37, 63, 63), (35, 66, 67), (36, 66, 67), (37, 67, 67)]:
    span(y, x0, x1, "l")
# far back hair beside the lock (x26) stays shadowed; near hair behind the lock (x70-73) shadowed
for y in range(26, 71):
    for x in range(HL[y] + 1, 27):
        if g[y][x] in "ml":
            g[y][x] = "d"
    for x in range(71, HR[y]):
        if g[y][x] in "ml":
            g[y][x] = "d"

# near-side back hair: shadow mass with one lit dash where the hair turns toward the light
for y, x0, x1 in [(30, 71, 73), (31, 71, 73), (32, 72, 73), (33, 72, 72)]:
    for x in range(x0, x1 + 1):
        if g[y][x] == "d":
            g[y][x] = "m"
# =====================================================================================================
# 10. EYES (C construction, no K walls on the sides): top lash 5-9 + 2 px outer wing, iris_0 rim below
#     the corners, iris ramp i/j/k, pupil, 2x2 + 1 px catchlights, sclera, lower lash on the outer third.
# =====================================================================================================
FAR_EYE = """
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
"""
NEAR_EYE = """
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
"""
put(g, 35, 33, FAR_EYE)
put(g, 50, 33, NEAR_EYE)
# brows (1 px hair_1), outer end 1 px lower
span(31, 36, 41, "d"); g[32][35] = "d"
span(31, 54, 59, "d"); g[32][60] = "d"
# nose: 2 px skin_0 on the shadow side, shifted toward the facing side
g[45][44] = "v"; g[46][44] = "v"
# mouth (neutral, 1-2-1) and the signature blush (hatches on a skin_mid patch)
g[50][42] = "L"; span(51, 43, 44, "L"); g[50][45] = "L"
put(g, 35, 45, "ttxttx\ntxttxt")
put(g, 52, 45, "ttxttxt\ntxttxtt")

# ---- cleanup of stray singles (each checked at x12) ----
g[26][42] = g[26][55] = "s"; g[29][35] = "s"
g[61][44] = "e"; g[69][65] = "b"; g[73][46] = "o"; g[26][75] = "d"; g[43][86] = "b"; g[45][76] = "m"; g[61][59] = "c"; g[90][56] = "o"
# ==== END ====
write(OUT, "# r13 dialogue bust base, round 2 (lead pixel artist). Built from face test C. Hand-authored.", legend, g)
