"""Sheet / strip / GIF / contact-sheet writers. All upscaling is nearest-neighbour, integer only."""
import os

import numpy as np
from PIL import Image, ImageDraw

DIR_GRID = {"NW": (0, 0), "N": (1, 0), "NE": (2, 0), "W": (0, 1), "E": (2, 1), "SW": (0, 2), "S": (1, 2), "SE": (2, 2)}


def save_png(rgba, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(path, optimize=False)


def sheet(frames_by_dir, dirs, size):
    """rows = directions, cols = frames."""
    W, H = size
    n = len(next(iter(frames_by_dir.values())))
    out = np.full((H * len(dirs), W * n), -1, int)
    for r, d in enumerate(dirs):
        for c, f in enumerate(frames_by_dir[d]):
            out[r * H:(r + 1) * H, c * W:(c + 1) * W] = f
    return out


def strip(frames, size):
    W, H = size
    out = np.full((H, W * len(frames)), -1, int)
    for c, f in enumerate(frames):
        out[:, c * W:(c + 1) * W] = f
    return out


def layer(dst, src):
    m = src >= 0
    dst[m] = src[m]
    return dst


def snow_ground(palette, size, pivot):
    """Preview background: snow with a faint 2:1 iso tile grid so the ground plane reads."""
    W, H = size
    bg = np.full((H, W), palette.index["snow_3"], int)
    ys, xs = np.mgrid[0:H, 0:W]
    u = (xs - pivot[0]) + 2 * (ys - pivot[1])
    v = (xs - pivot[0]) - 2 * (ys - pivot[1])
    grid = (np.mod(u, 32) == 0) | (np.mod(v, 32) == 0)
    bg[grid] = palette.index["snow_2"]
    return bg


def baked_frame(char_idx, shadow_idx, fx_back, fx_front, z_px, palette, size, pivot, canvas_h, background=True):
    """Composite one preview frame with the engine-style vertical offset applied."""
    W, H = size
    top = canvas_h - H                        # extra headroom above the cell
    piv = (pivot[0], pivot[1] + top)
    out = snow_ground(palette, (W, canvas_h), piv) if background else np.full((canvas_h, W), -1, int)
    for lay, dy in ((shadow_idx, 0), (fx_back, 0), (char_idx, -z_px), (fx_front, 0)):
        tmp = np.full((canvas_h, W), -1, int)
        y0 = top + dy
        tmp[max(y0, 0):y0 + H] = lay[max(-y0, 0):canvas_h - y0][:H]
        layer(out, tmp)
    return out


def gif(frames_idx, durations_ms, palette, path, scale=4, extra_colors=()):
    """Exact-palette GIF (no dithering, no colour drift)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    colors = list(palette.rgb) + list(extra_colors)
    flat = [c for rgb in colors for c in rgb] + [0, 0, 0] * (256 - len(colors))
    ims = []
    for f in frames_idx:
        a = np.where(f >= 0, f, palette.index["snow_3"]).astype(np.uint8)
        im = Image.fromarray(a, "P")
        im.putpalette(flat)
        ims.append(im.resize((im.width * scale, im.height * scale), Image.NEAREST))
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=list(durations_ms), loop=0,
                disposal=1, optimize=False)


def compass_frame(frames_by_dir, k, size, palette, label=None):
    """3x3 compass layout of all 8 directions for frame k (centre cell left blank / label)."""
    W, H = size
    out = np.full((H * 3, W * 3), palette.index["snow_3"], int)
    for d, (cx, cy) in DIR_GRID.items():
        if d in frames_by_dir:
            out[cy * H:(cy + 1) * H, cx * W:(cx + 1) * W] = frames_by_dir[d][k]
    return out


def contact_sheet(frames_by_dir, dirs, infos, palette, size, path, scale=4):
    """Labelled review sheet: directions x frames, upscaled, with frame names/durations."""
    W, H = size
    n = len(infos)
    pad_l, pad_t = 40, 34
    img = Image.new("RGB", (pad_l + n * W * scale, pad_t + len(dirs) * H * scale), (36, 22, 40))
    draw = ImageDraw.Draw(img)
    for c, inf in enumerate(infos):
        draw.text((pad_l + c * W * scale + 4, 4), f'{inf["index"] + 1} {inf["name"]}', fill=(244, 234, 210))
        draw.text((pad_l + c * W * scale + 4, 18), f'{inf["duration_ms"]}ms z{inf["z_px"]}', fill=(168, 192, 224))
    for r, d in enumerate(dirs):
        draw.text((6, pad_t + r * H * scale + H * scale // 2 - 6), d, fill=(244, 234, 210))
        for c in range(n):
            f = frames_by_dir[d][c]
            bg = snow_ground(palette, size, (W // 2, H - H // 8))
            rgba = palette.to_rgba(layer(bg, f))
            im = Image.fromarray(rgba).convert("RGB").resize((W * scale, H * scale), Image.NEAREST)
            img.paste(im, (pad_l + c * W * scale, pad_t + r * H * scale))
    for c in range(n + 1):
        x = pad_l + c * W * scale
        draw.line([(x, pad_t), (x, img.height)], fill=(36, 22, 40), width=2)
    for r in range(len(dirs) + 1):
        y = pad_t + r * H * scale
        draw.line([(pad_l, y), (img.width, y)], fill=(36, 22, 40), width=2)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def greyscale_check(frames_by_dir, dirs, palette, size, path, frames=(0, 5, 11), scale=3):
    """Luminance-only view on the snow ground: the silhouette must read without colour (GD criterion 6)."""
    W, H = size
    img = Image.new("L", (len(frames) * W * scale, len(dirs) * H * scale))
    for r, d in enumerate(dirs):
        for c, f in enumerate(frames):
            bg = snow_ground(palette, size, (W // 2, H - 8))
            im = Image.fromarray(palette.to_rgba(layer(bg, frames_by_dir[d][f]))).convert("L")
            img.paste(im.resize((W * scale, H * scale), Image.NEAREST), (c * W * scale, r * H * scale))
    img.save(path)


def distance_test(frames_by_dir, dirs, palette, size, path, frames=(0, -1)):
    """Readability-at-distance sheet: per direction, the ready frame at 1x and 2x on snow and on a dark tile,
    a black silhouette, and a blurred 'squint' version (should read as 3-4 value masses)."""
    from PIL import ImageFilter
    W, H = size
    cols = []
    for d in dirs:
        f = frames_by_dir[d][frames[-1]]
        rgba = Image.fromarray(palette.to_rgba(f))
        cells = []
        for bgc in ((223, 234, 246), (62, 74, 110)):
            for sc in (1, 2):
                c = Image.new("RGB", (W * 2, H * 2), bgc)
                im = rgba.resize((W * sc, H * sc), Image.NEAREST)
                c.paste(im, ((W * 2 - W * sc) // 2, (H * 2 - H * sc) // 2), im)
                cells.append(c)
        sil = Image.new("RGB", (W * 2, H * 2), (223, 234, 246))
        a = np.array(rgba)[..., 3] > 0
        blk = Image.fromarray(np.where(a, 0, 255).astype(np.uint8)).resize((W * 2, H * 2), Image.NEAREST)
        sil.paste((20, 20, 20), (0, 0), Image.fromarray((~np.array(blk).astype(bool)).astype(np.uint8) * 255))
        cells.append(sil)
        sq = Image.new("RGB", (W * 2, H * 2), (223, 234, 246))
        im2 = rgba.resize((W * 2, H * 2), Image.NEAREST)
        sq.paste(im2, (0, 0), im2)
        cells.append(sq.filter(ImageFilter.GaussianBlur(3)))
        col = Image.new("RGB", (W * 2, H * 2 * len(cells)), (36, 22, 40))
        for k, c in enumerate(cells):
            col.paste(c, (0, k * H * 2))
        cols.append(col)
    out = Image.new("RGB", (W * 2 * len(cols), H * 2 * 6), (36, 22, 40))
    for k, c in enumerate(cols):
        out.paste(c, (k * W * 2, 0))
    out.save(path)
