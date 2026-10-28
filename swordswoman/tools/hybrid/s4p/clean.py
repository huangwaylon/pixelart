"""Conservative body cleanup after the polish: orphans in cloth/hair/leather -> same-ramp majority,
1px spurs off the silhouette removed.  Protected: head stamp px, sword/pink/eye/FX tones, hand edits."""
import numpy as np
import pl

N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
N4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
RAMP = {c: g for g, cs in {"red": "vrRC", "hair": "hHJ", "leather": "lL", "skin": "msS", "dark": "d"}.items() for c in cs}


def clean(a, protect, ground=107):
    ch = np.array([[pl.name_at(a, x, y) for x in range(128)] for y in range(128)])
    st = dict(orphans=0, spurs=0)
    for y in range(1, 127):
        for x in range(1, 127):
            c = ch[y, x]
            if c == "." or protect[y, x] or c not in RAMP or c == "m":
                continue
            nb = [ch[y + dy, x + dx] for dy, dx in N8]
            if c in nb:
                continue
            same = [n for n in nb if RAMP.get(n) == RAMP[c]]
            if not same:
                continue          # isolated accent of its own ramp (e.g. a buckle) -> leave
            v, k = np.unique(same, return_counts=True)
            ch[y, x] = v[k.argmax()]
            a[y, x] = pl.T(ch[y, x])
            st["orphans"] += 1
    op = a[..., 3] > 0
    for y in range(1, ground - 1):
        for x in range(1, 127):
            if not op[y, x] or protect[y, x] or ch[y, x] in ("w", "t", "T", "p", "P"):
                continue
            tr4 = sum(not op[y + dy, x + dx] for dy, dx in N4)
            n8 = sum(op[y + dy, x + dx] for dy, dx in N8)
            if tr4 >= 3 and n8 <= 1:
                a[y, x] = pl.T(".")
                st["spurs"] += 1
    return a, st
