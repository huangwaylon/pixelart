"""gifio.py (P, round 3): the experiment's GIF writer.  Use it for every review GIF (any venv with Pillow; no other deps).

    from gifio import write_gif
    write_gif(path, frames, durations_ms, bg=(128, 128, 128), scale=1)

Guarantees (checked by render/gifcheck.py):
  * loop=0 (infinite), written explicitly.
  * delays are quantised to the GIF's 10 ms unit with error diffusion (total cycle time kept; Pillow would otherwise truncate 105 -> 100).
  * every frame >= MIN_MS (20 ms; browsers clamp shorter frames to 100 ms).  Frames shorter than that are MERGED into the previous
    frame's display time if they are identical to it, otherwise their time is borrowed from the longest neighbour (total cycle time kept).
  * every frame is a full, opaque canvas (RGBA is composited on `bg`), written with disposal=2 and optimize=False, so no partial tiles
    or transparent pixels can leave ghosts of the previous frame.
  * one global palette for all frames (no per-frame re-quantisation flicker); exact for <= 256 colours (pixel art).
  * consecutive identical frames are merged (durations summed) so Pillow can't silently drop them and shorten the loop.
  * seam: nothing is appended or duplicated at the end; the loop seam is last -> first as rendered (gifcheck reports the seam ratio).
"""
import numpy as np
from PIL import Image

MIN_MS = 20


def _rgb(im, bg):
    im = im if isinstance(im, Image.Image) else Image.fromarray(np.asarray(im))
    if im.mode in ('RGBA', 'LA', 'P', 'PA'):
        im = im.convert('RGBA'); b = Image.new('RGBA', im.size, tuple(bg) + (255,)); b.alpha_composite(im); im = b
    return im.convert('RGB')


def normalise_timing(arrs, durs, min_ms=MIN_MS):
    """merge identical consecutive frames (sum ms); then raise frames < min_ms by borrowing from the longest neighbour"""
    A, D = [], []
    for a, d in zip(arrs, durs):
        d = int(round(d))
        if A and np.array_equal(A[-1], a): D[-1] += d; continue
        A.append(a); D.append(d)
    if len(A) > 1 and np.array_equal(A[0], A[-1]):  # loop seam would show a double-length hold: fold the last into the first
        D[0] += D[-1]; A.pop(); D.pop()
    for i in range(len(D)):
        if D[i] < min_ms:
            need = min_ms - D[i]; nb = [j for j in ((i - 1) % len(D), (i + 1) % len(D)) if j != i]
            j = max(nb, key=lambda k: D[k]) if nb else i
            if j != i and D[j] - need >= min_ms: D[j] -= need
            D[i] = min_ms
    # GIF delays are centiseconds: quantise to 10 ms with error diffusion so the cycle length is kept (105,105,.. -> 110,100,110,..)
    Q, err = [], 0.0
    for d in D:
        q = max(min_ms, int(round((d + err) / 10.0)) * 10); err += d - q; Q.append(q)
    return A, Q


def write_gif(path, frames, durations, bg=(128, 128, 128), scale=1, min_ms=MIN_MS):
    if np.isscalar(durations): durations = [durations] * len(frames)
    ims = [_rgb(f, bg) for f in frames]
    if scale > 1: ims = [im.resize((im.width * scale, im.height * scale), Image.NEAREST) for im in ims]
    arrs, durs = normalise_timing([np.asarray(im) for im in ims], durations, min_ms)
    allpx = np.concatenate([a.reshape(-1, 3) for a in arrs])
    cols = np.unique(allpx, axis=0)
    if len(cols) <= 256:
        pal = cols
    else:  # not pixel art: one shared median-cut palette over a mosaic of all frames
        mos = Image.fromarray(np.concatenate(arrs, 0)).quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        pal = np.array(mos.getpalette()[:768]).reshape(-1, 3)[:256]
    pim = Image.new('P', (1, 1)); flat = list(pal.astype(int).ravel()) + [0] * (768 - 3 * len(pal)); pim.putpalette(flat)
    out = []
    for a in arrs:
        im = Image.fromarray(a)
        if len(cols) <= 256:  # exact index map
            key = (a[..., 0].astype(np.int64) << 16) | (a[..., 1].astype(np.int64) << 8) | a[..., 2]
            pk = (pal[:, 0].astype(np.int64) << 16) | (pal[:, 1].astype(np.int64) << 8) | pal[:, 2]
            idx = np.searchsorted(pk, key); q = Image.fromarray(idx.astype(np.uint8), 'P'); q.putpalette(flat)
        else:
            q = im.quantize(palette=pim, dither=Image.Dither.NONE)
        out.append(q)
    out[0].save(path, save_all=True, append_images=out[1:], duration=durs, loop=0, disposal=2, optimize=False)
    return durs
