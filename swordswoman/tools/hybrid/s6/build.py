"""S6 sprite builder: underlay paint + lock stamps + hand-drawn sword/ribbons/smears + per-frame hand ops."""
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import *
import paint

OUT = os.path.join(ROOT, "hybrid", "S6_claude_pixel", "r1")


def line_pts(x0, y0, x1, y1):
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    e = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * e
        if e2 >= dy:
            e += dy
            x0 += sx
        if e2 <= dx:
            e += dx
            y0 += sy
    return pts


class Canvas:
    def __init__(self, grid):
        self.g = grid

    def put(self, x, y, c, behind=False):
        if 0 <= x < 128 and 0 <= y < 128:
            if behind and self.g[y, x] != ".":
                return
            self.g[y, x] = c

    def get(self, x, y):
        return self.g[y, x] if (0 <= x < 128 and 0 <= y < 128) else "."

    def line(self, a, b, c, behind=False):
        for x, y in line_pts(*a, *b):
            self.put(x, y, c, behind)

    def pix(self, x0, y0, rows, behind=False):
        """rows of legend chars; '_' / ' ' = skip, '.' = erase."""
        for dy, r in enumerate(rows):
            for dx, ch in enumerate(r):
                if ch in "_ ":
                    continue
                if behind and self.get(x0 + dx, y0 + dy) != "." and ch != ".":
                    continue
                if 0 <= x0 + dx < 128 and 0 <= y0 + dy < 128:
                    self.g[y0 + dy, x0 + dx] = ch

    def stamp(self, st, x0, y0, behind=False, keep_dot=True):
        h, w = st.shape[:2]
        rows = rgba_to_chars(st)
        for dy in range(h):
            for dx in range(w):
                ch = rows[dy][dx]
                if ch == ".":
                    continue
                self.put(x0 + dx, y0 + dy, ch, behind)


def katana(cv, hilt_end, guard, tip, hook_side=1, behind=False, fist=None, blade_only=False):
    """hilt_end -> guard: diamond-wrapped handle (R/d alternating, K edges); guard bar + crescent kagi;
    2 px blade steel_2 lit edge + steel_0 back edge to the tip."""
    (hx, hy), (gx, gy), (tx, ty) = hilt_end, guard, tip
    vx, vy = tx - gx, ty - gy
    L = math.hypot(vx, vy)
    ux, uy = vx / L, vy / L
    # perpendicular on screen (towards lower-right is the shadow side)
    px, py = -uy, ux
    if px + py < 0:
        px, py = -px, -py
    sx, sy = int(round(px)), int(round(py))
    if sx == 0 and sy == 0:
        sy = 1
    # blade: lit line + shadow line offset by the perpendicular
    b0 = (int(round(gx + ux * 2)), int(round(gy + uy * 2)))
    for i, (x, y) in enumerate(line_pts(*b0, tx, ty)):
        cv.put(x, y, "w", behind)
    for i, (x, y) in enumerate(line_pts(b0[0] + sx, b0[1] + sy, tx, ty)):
        if cv.get(x, y) != "w":
            cv.put(x, y, "t", behind)
    if blade_only:
        return
    # habaki (1 px steel_1) right after the guard
    cv.put(int(round(gx + ux)), int(round(gy + uy)), "T", behind)
    # handle
    hp = line_pts(hx, hy, int(round(gx - ux)), int(round(gy - uy)))
    for i, (x, y) in enumerate(hp):
        cv.put(x, y, "R" if i % 2 == 0 else "d", behind)
        cv.put(x + sx, y + sy, "d" if i % 2 == 0 else "R", behind)
    cv.put(hx - int(round(ux)), hy - int(round(uy)), "T", behind)  # kashira
    # guard bar: 3 px perpendicular
    gxi, gyi = int(round(gx)), int(round(gy))
    for k in (-1, 0, 1, 2):
        cv.put(int(round(gx + px * k)), int(round(gy + py * k)), "t" if k == 2 else "T", behind)
    # crescent kagi: hook on one side of the bar, curling toward the blade
    s = hook_side
    hx0, hy0 = gx - px * 2 * s, gy - py * 2 * s
    cv.put(int(round(hx0)), int(round(hy0)), "T", behind)
    cv.put(int(round(hx0 + ux)), int(round(hy0 + uy)), "T", behind)
    cv.put(int(round(hx0 + ux * 2 + px * s)), int(round(hy0 + uy * 2 + py * s)), "t", behind)
    if fist:
        fx, fy = fist
        cv.pix(fx - 1, fy - 1, ["Kss", "smm", "Km_"][:3])


def finish(cv, ol=True):
    g = cv.g
    if ol:
        g = paint.outline(g)
        g = paint.selout_inner(g)
    cv.g = g
    return cv


def save(name, cv, hires=None):
    a = to_rgba(cv.g)
    save_rgba(a, os.path.join(OUT, "sprite", name + ".png"))
    return a


def to_rgba(g):
    return chars_to_rgba(["".join(r) for r in g])


def preview(names, path, z=6, crop=(24, 34, 104, 110), bg=(36, 32, 44)):
    from PIL import Image, ImageDraw
    x0, y0, x1, y1 = crop
    tiles = []
    for n in names:
        a = load_rgba(os.path.join(OUT, "sprite", n + ".png"))[y0:y1, x0:x1]
        im = Image.fromarray(zoom(a, z, bg, grid=True))
        ImageDraw.Draw(im).text((3, 3), n, fill=(255, 255, 255))
        tiles.append(im)
        one = Image.fromarray(zoom(a, 1, bg))
        tiles[-1].paste(one, (tiles[-1].width - one.width - 2, 2))
    W = (x1 - x0) * z
    H = (y1 - y0) * z
    sheet = Image.new("RGB", (W * len(tiles), H), (10, 10, 10))
    for i, t in enumerate(tiles):
        sheet.paste(t, (i * W, 0))
    sheet.save(path)


def grid_preview(names, path, z=5, cols=4, crop=(28, 36, 108, 120), bg=(36, 32, 44)):
    from PIL import Image, ImageDraw
    x0, y0, x1, y1 = crop
    W, H = (x1 - x0) * z, (y1 - y0) * z
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new("RGB", (W * cols, H * rows), (10, 10, 10))
    for i, n in enumerate(names):
        a = load_rgba(os.path.join(OUT, "sprite", n + ".png"))[y0:y1, x0:x1]
        im = Image.fromarray(zoom(a, z, bg, grid=False))
        one = Image.fromarray(zoom(a, 1, bg))
        im.paste(one, (W - one.width - 2, 2))
        ImageDraw.Draw(im).text((3, 3), n, fill=(255, 255, 255))
        sheet.paste(im, ((i % cols) * W, (i // cols) * H))
    sheet.save(path)
