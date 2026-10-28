"""shared helpers for the S5 r3 specs: piecewise-offset torso (stepped lean that keeps the lock cels pixel-identical:
the chest/shoulder rows and the corset rows are moved by INTEGER offsets, never sheared)."""
import sys, importlib.util
ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
def cel(name):
    p = f'{ROOT}/tools/hybrid/h4/cels/{name}.py'
    s = importlib.util.spec_from_file_location('cel_' + name, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m
def rows(text):
    out = []
    for ln in text.strip('\n').splitlines():
        y, x, s = ln.split(None, 2); out.append((int(y), int(x), s))
    return out
def fmt(rs, dx, dy, keep=lambda y: True):
    return '\n'.join(f'{y + dy} {x + dx} {s}' for y, x, s in rs if keep(y))
def torso_split(base, upper, lower, split=78, drop_near=0):
    """upper rows (< split: neck, chest, shoulders, bust) at offset `upper`, corset rows (>= split) at `lower`.
    drop_near: the near-shoulder skin run (x < 57 on SE) is pushed down by n rows (shoulder drop)."""
    c = cel(base); rs = rows(c.TORSO)
    up = fmt(rs, upper[0], upper[1], lambda y: y < split)
    lo = fmt(rs, lower[0], lower[1], lambda y: y >= split)
    return up + '\n' + lo

def torso_bands(base, bands):
    """bands = [(y_end_exclusive, (dx, dy)), ...] ascending; rows go to the first band whose y_end > row.
    A stepped (integer) lean: every band is the lock cel's own rows, moved, never resampled."""
    c = cel(base); rs = rows(c.TORSO); out = []
    for y, x, s in rs:
        for ye, (dx, dy) in bands:
            if y < ye: out.append(f'{y + dy} {x + dx} {s}'); break
    return '\n'.join(out)
