"""Tiny helpers for hand-authoring .pix grids: every call writes pixels the artist specifies explicitly."""
import re

def read_grid(path):
    lines = open(path).read().splitlines()
    i = lines.index("grid:")
    legend = [l for l in lines[:i] if "=" in l and not l.startswith("#")]
    return legend, [list(r) for r in lines[i + 1:] if r.strip()]

def canvas(w, h, ch="."):
    return [[ch] * w for _ in range(h)]

def put(g, x, y, block, keep="_"):
    """Overlay a multi-line string block at (x, y); '_' keeps the pixel underneath."""
    rows = [r for r in block.strip("\n").split("\n")]
    rows = [r.strip() for r in rows]
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch != keep and 0 <= y + j < len(g) and 0 <= x + i < len(g[0]):
                g[y + j][x + i] = ch

def run(g, x, y, s):
    for i, ch in enumerate(s):
        g[y][x + i] = ch

def write(path, header, legend, g):
    with open(path, "w") as f:
        f.write(header.rstrip() + "\n")
        f.write(f"size: {len(g[0])} {len(g)}\nlegend:\n")
        f.write("\n".join(legend) + "\ngrid:\n")
        f.write("\n".join("".join(r) for r in g) + "\n")
