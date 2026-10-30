"""Eyes+brows-only face system (2026-10-30). Templates are for the SCREEN-LEFT eye (outer corner = col 0, inner = col 4),
8 rows: rows 0-2 = brow band (B0..B2), row 3 = dome (r0), row 4 = lash (r1), rows 5-7 = iris (r2-r4).
Chars: K lash/pupil/closed line, g iris mid, @ catchlight (W, always on the iris's SCREEN-LEFT column), h brow (hair shadow),
'.' = skin (cleared), ' ' = keep base.  Screen-right eye = mirror, then '@' is moved back to the iris's left column.
Far eye (SE) / profile eye (E) = drop column 2 (the pupil column; keeps outer corner, catchlight and inner end) -> 4 wide."""
import numpy as np
T = {
 'open': ['.....', '.hhh.', '.....', '.KKK.', 'KKKKK', 'K@KK.', '.@Kg.', '.ggg.'],
 'half': ['.....', '.hhh.', '.....', '.....', '.....', 'KKKKK', '.@Kg.', '.ggg.'],
 'closed': ['.....', '.hhh.', '.....', '.....', '.....', 'K....', '.KKKK', '.....'],
 'happy': ['.hhh.', 'h...h', '.....', '.....', '.KKK.', 'K...K', '.....', '.....'],
 'determined': ['hh...', '..hhh', '.....', '.....', 'KKKKK', 'K@KK.', '.@Kg.', '.ggg.'],
 'surprised': ['.hhh.', '.....', '.....', '.KKK.', 'KWWWK', 'KWKWK', '.KKK.', '.....'],
 'hurt': ['...hh', '.hh..', '.....', '.....', 'KK...', '..KKK', 'KK...', '.....'],
}
COL = {'K': (22, 12, 13), 'g': (94, 74, 69), '@': (246, 238, 234), 'W': (246, 238, 234), 'h': (52, 33, 38)}
EXPR = list(T)

def mirror(rows):
    out = []
    for r in rows:
        m = r[::-1]
        if '@' in m:  # catchlight stays on the iris's screen-left column
            j = m.index('@'); cols = [k for k, c in enumerate(m) if c in 'KgW@']
            i0 = min(k for k in cols if k > 0) if cols else j
            l = list(m); l[j], l[i0] = l[i0], '@'; m = ''.join(l)
        out.append(m)
    return out

def narrow(rows, drop=2):
    return [r[:drop] + r[drop + 1:] for r in rows]

def eye(expr, side='left', kind='front'):
    """side: screen-left/right; kind: front | far | profile."""
    rows = list(T[expr])
    if kind in ('far', 'profile'): rows = narrow(rows)
    if side == 'right': rows = mirror(rows)
    return rows

# per-view layout in master 128-cell coords: (x of template col 0, y of template row 0), side, kind
# derived from v2/m96 masters (eye/brow rows of EC0_<V>_96 + anchor.json); row 0 = 2 rows above the master brow row... see report
LAYOUT = {
 'S': [((56, 46), 'left', 'front'), ((67, 46), 'right', 'front')],
 'SE': [((61, 47), 'left', 'front'), ((72, 47), 'right', 'far')],
 'E': [((73, 46), 'left', 'profile')],
}
NE_LASH = {'open': [(76, 56), (76, 55)], 'half': [(76, 56)], 'surprised': [(76, 56), (76, 55)], 'determined': [(76, 56), (76, 55)]}

def stamp(img, ox, oy, rows, skin=(234, 169, 145)):
    a = img
    for r, line in enumerate(rows):
        for c, ch in enumerate(line):
            if ch == ' ': continue
            y, x = oy + r, ox + c
            if not (0 <= y < a.shape[0] and 0 <= x < a.shape[1]) or a[y, x, 3] == 0: continue
            if ch == '.':
                continue
            a[y, x, :3] = COL[ch]; a[y, x, 3] = 255
    return a
