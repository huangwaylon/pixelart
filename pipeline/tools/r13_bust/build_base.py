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
PR = rows_tbl([((22, 29), 86), ((30, 31), 83), ((32, 33), 82), ((34, 37), 82), ((38, 42), 83), ((43, 52), 84), ((53, 58), 83),
               ((59, 63), 82), ((64, 66), 81), ((67, 70), 80)])
for y, xr in PR.items():
    span(y, HR[y] + 1, xr - 1, "m")
    g[y][xr] = "K"
    span(y, max(HR[y] + 1, xr - 3), xr - 1, "d")
    g[y][xr - 1] = "P"
    if y <= 40:
        g[y][HR[y]] = "P"                          # head edge reads as an inner fold, not a wall
    else:
        g[y][HR[y]] = "d"                          # (gemini triage) no K seam inside the hair
for x, y in [(77, 46), (77, 47), (78, 48), (78, 49), (78, 50), (78, 51), (78, 52), (77, 53), (77, 54)]:
    g[y][x] = "d"
span(45, 75, 76, "l"); span(46, 75, 75, "l")

# =====================================================================================================
# 5. BOW (binding): knot on the back of the skull x76-81 y22-29, partly behind the ponytail root;
#    pinched + creased loops, upper rises up-back, lower drops down-back; tip to tip ~41 px, >=3 px inside.
# =====================================================================================================
# (round 4, review 3: a ribbon bow - far-loop tip behind the crown, pinched knot, near loop, two short splayed tails)
# half-up gather: the upper hair is pulled back from the crown into the knot
paint([(9, (71, 76, "K")), (10, (67, 70, "K"), (71, 76, "m"), (77, 77, "K")),
       (11, (64, 66, "K"), (67, 77, "m"), (78, 78, "K")), (12, (62, 63, "K"), (64, 77, "m"))])
for y in range(13, 30):
    for x in range(HR[y] + 1, 78):
        g[y][x] = "m" if y < 22 else "d"
    g[y][HR[y]] = "m" if y < 20 else g[y][HR[y]]
for t in range(8):                                # one 2 px hair_1 split converging on the knot
    g[14 + t][65 + t] = "d"
    g[14 + t][66 + t] = "d"
span(12, 67, 71, "l"); span(13, 69, 72, "l")
# near loop x79-93, y6-24: outer end widest, inner end pinched to the knot height (y13-20)
LOOP = {7: (85, 92), 8: (84, 93), 9: (83, 93), 10: (82, 93), 11: (81, 93), 12: (80, 93), 13: (79, 93), 14: (79, 93),
        15: (79, 93), 16: (79, 93), 17: (79, 93), 18: (79, 93), 19: (79, 93), 20: (79, 93), 21: (80, 93), 22: (82, 93),
        23: (84, 92)}
span(6, 86, 91, "K")
for y, (l, r) in LOOP.items():
    span(y, l + 1, r - 1, "c")
    g[y][r] = "K"
    g[y][l] = "c" if 13 <= y <= 20 else "K"
for a, b_ in zip(sorted(LOOP), sorted(LOOP)[1:]):
    (la, ra), (lb, rb) = LOOP[a], LOOP[b_]
    if lb > la + 1:
        span(b_, la + 1, lb, "K")
span(24, 85, 91, "K")
g[7][93] = "."
paint([(7, (86, 90, "e")), (8, (84, 90, "e")), (9, (84, 89, "e"))])
for y in (22, 23):
    for x in range(LOOP[y][0] + 1, LOOP[y][1]):
        g[y][x] = "b"
for y in range(15, 20):
    span(y, 80, 83, "b")
g[15][83] = g[19][83] = "c"          # pocket rounds off toward the outer end
for y in range(10, 22):
    g[y][92] = "b"
# near tail: 4 px, from y21 drifting +1 px every 3 rows, V-cut tip at y33
for y in range(21, 34):
    x0 = 78 + (y - 21) // 3
    w = 4 if y < 33 else 3
    for k, ch in enumerate("eccb"[:w] if w == 4 else "ccb"):
        g[y][x0 + k] = ch
    g[y][x0 - 1] = "K"
    g[y][x0 + w] = "K"
g[33][83] = "d"; g[34][82] = "K"; g[34][84] = "K"; g[34][83] = "d"
# far tail: 3 px, drifting -1 px every 3 rows to x71-73 by y30, V-cut at (72,30)
for y in range(21, 31):
    x0 = 74 - (y - 21) // 3
    for k, ch in enumerate("cbb"):
        g[y][x0 + k] = ch
    g[y][x0 - 1] = "K"
    if g[y][x0 + 3] not in "ceb":
        g[y][x0 + 3] = "K"
g[30][72] = "d"
# pinched knot x75-78, y13-20 (outline notches at the inner corners)
for y in range(13, 21):
    span(y, 75, 78, "c")
    g[y][74] = "K"
span(20, 75, 78, "b")
g[15][76] = "e"
span(12, 75, 78, "K"); span(21, 75, 78, "K")
g[13][75] = "K"; g[20][75] = "K"; g[12][79] = "K"
# far loop (review 4): a 5x6 wedge behind the knot, opening into the knot's K at x75; hair K covers its left edge
put(g, 70, 10, """
__Kcc
_Kcbb
Kbbbb
Kbbbb
_Kbbb
__Kbb
""")
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
# (gemini triage) far side in 6 px (x8 by y85), near side in 3 px (x87): steeper arms, smooth runs
LS.update(rows_tbl([((74, 74), (9, 9)), ((75, 75), (8, 8)), ((76, 84), (7, 7)), ((85, 95), (8, 8))]))
RS.update(rows_tbl([((74, 74), (85, 85)), ((75, 76), (86, 86)), ((77, 95), (87, 87))]))
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
# (round 3: C's chunky roll re-pasted at +10,+5: one 11-row roll, a teal_0 rib every 4 px, teal_2 on the top
#  2 rows, teal_0 (not K) underneath, rounded corners, near side 1 px higher; 9 px cable tail)
_, CG = read_grid(C)
SC = {}
for cy in range(55, 68):
    for cx in range(22, 59):
        ch = CG[cy][cx]
        if ch in "bce" or (ch == "K" and any(CG[cy + dy][cx + dx] in "bce" for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                                             if 0 <= cy + dy < 80 and 0 <= cx + dx < 80)):
            SC[(cx + 10, cy + 5)] = ch
for (x, y), ch in list(SC.items()):
    if y >= 71 and ch == "K":
        SC[(x, y)] = "b"                          # no black row underneath
for (x, y), ch in sorted(SC.items(), key=lambda t: t[0][1]):
    yy = y - 1 if x >= 64 else y                  # near side 1 px higher
    g[yy][x] = ch
for x in range(64, 70):                           # what the lift uncovers is coat
    ys = [y for (xx, y) in SC if xx == x]
    if ys and g[max(ys)][x] in "bceK":
        g[max(ys)][x] = "o" if max(ys) > 66 else g[max(ys)][x]
# hair (behind) fills the pockets between the locks and the scarf, so no coat slivers show there
for x in list(range(23, 37)) + list(range(63, 77)):
    for y in range(58, 68):
        if g[y][x] in "bceK":
            break
        if g[y][x] in "oq." and g[y - 1][x] in "dmPlK":
            g[y][x] = "d"
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
    g[y][44] = "q"
for y in (82, 83, 90, 91):
    g[y][42] = g[y][43] = "g"

# scarf tail (C's 9 px cable, x55-63), repeated down past the crop
for y in range(71, 96):
    cy = 66 + (y - 71) if y <= 84 else 67 + ((y - 85) % 3)
    for i in range(9):
        ch = CG[cy][45 + i]
        g[y][55 + i] = ch if ch in "bce" else "b"

# =====================================================================================================
# 9. SIDE LOCKS: tapering C-curves, 2 px clumps; far (left) narrower. Tips near y64, over the scarf.
#    (row, left edge, right edge) of the fill; plum line on both sides and under the tip.
# =====================================================================================================
FAR_LOCK = rows_tbl([((26, 30), (27, 32)), ((31, 37), (27, 33)), ((38, 39), (27, 32)), ((40, 46), (26, 32)),
                     ((47, 50), (26, 31)), ((51, 54), (27, 31)),
                     ((55, 58), (28, 31)), ((59, 61), (29, 31)), ((62, 63), (30, 31))])
NEAR_LOCK = rows_tbl([((26, 30), (65, 70)), ((31, 39), (63, 68)), ((40, 50), (63, 69)), ((51, 54), (63, 68)), ((55, 58), (64, 68)),
                      ((59, 61), (64, 67)), ((62, 63), (64, 66))])
for lock, clump in ((FAR_LOCK, 2), (NEAR_LOCK, 3)):
    for y, (a, b) in lock.items():
        span(y, a, b, "m")
        g[y][a - 1] = "P"
        if g[y][b + 1] not in "sPL" or y > 46:
            g[y][b + 1] = "P" if not (lock is NEAR_LOCK and y > 44) else "d"
    ys = sorted(lock)
    last = lock[ys[-1]]
    span(ys[-1] + 1, last[0], last[1], "P")
# 2 px clumps: the shadow-side clump of each lock in hair_1 (no 1 px stripes)
for y in range(31, 72):
    for lock in (FAR_LOCK, NEAR_LOCK):
        if y in lock:
            a, b_ = lock[y]
            if lock is FAR_LOCK and y > 48:
                continue                           # far shadow clump ends at y48 (tapered)
            for x in range(b_ - 1 + (1 if lock is FAR_LOCK and y >= 47 else 0), b_ + 1):
                if x > a:
                    g[y][x] = "d"
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
g[45][44] = "v"; g[46][44] = "v"; g[46][45] = "u"
# mouth (neutral, 1-2-1) and the signature blush (hatches on a skin_mid patch)
span(51, 42, 43, "L"); g[51][44] = "v"          # neutral: flat mouth (review 2)
span(45, 35, 40, "t"); span(45, 52, 58, "t")    # blush softened to one pale skin_mid row

# (gemini triage) cast shadow right of the scarf tail and under the roll
for y in range(73, 96):
    if g[y][64] in "oq":
        g[y][64] = "O"
for x in range(36, 55):
    if g[73][x] in "oq":
        g[73][x] = "O"
# ---- cleanup of stray singles (each checked at x12) ----
g[26][42] = g[26][55] = "s"; g[29][35] = "s"
g[61][44] = "e"; g[69][65] = "b"; g[73][46] = "o"; g[45][76] = "m"; g[61][59] = "c"
g[93][80] = "O"; g[13][64] = "m"; g[19][73] = "m"; g[21][72] = "d"; g[40][77] = "d"
# ==== END ====
write(OUT, "# r13 dialogue bust base, round 2 (lead pixel artist). Built from face test C. Hand-authored.", legend, g)
