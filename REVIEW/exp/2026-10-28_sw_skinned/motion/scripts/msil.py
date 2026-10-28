"""msil.py (M, round 2): review sheets from pixel frames (P chain, motion/prev/<tag>/<act>/<act>_SE_px/fNN.png, RGBA 128 cell).
  sil  : key-pose silhouette sheet (solid fill) at 1x and 4x  -> motion/out/sil_<act>_SE.png
  strip: colour frame strip at 1x (actual size) and 4x, numbered with ms -> motion/out/strip_<act>_SE_<tag>.png
  ab   : A/B board, rows A = round 1, B = round 2, at 4x with a 1x row under each -> motion/crit/ab2_<act>.png
usage: python msil.py walk,run,idle,jump
"""
import sys, os, json
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mrig import EXP

M = os.path.join(EXP, "motion")


def frames(act, tag):
    d = os.path.join(M, "prev", tag, act, f"{act}_SE_px"); ims = []
    k = 0
    while os.path.exists(os.path.join(d, f"f{k:02d}.png")):
        ims.append(Image.open(os.path.join(d, f"f{k:02d}.png")).convert("RGBA")); k += 1
    return ims


def bbox(ims, pad=2):
    bb = None
    for im in ims:
        b = im.getchannel("A").getbbox()
        if b: bb = b if bb is None else (min(bb[0], b[0]), min(bb[1], b[1]), max(bb[2], b[2]), max(bb[3], b[3]))
    return (bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad)


def on_bg(im, bg=(128, 128, 128)):
    b = Image.new("RGBA", im.size, bg + (255,)); b.alpha_composite(im); return b.convert("RGB")


def sil(im):
    a = im.getchannel("A").point(lambda v: 255 if v > 0 else 0)
    out = Image.new("RGB", im.size, (255, 255, 255)); out.paste((30, 30, 40), mask=a); return out


def sheet(cells, labels, title, scale_rows):
    """cells: list of rows, each a list of cropped 1x images. scale_rows: scale per row."""
    W = max(sum(c.width * s + 6 for c in row) for row, s in zip(cells, scale_rows)) + 6
    H = sum(max(c.height for c in row) * s + 16 for row, s in zip(cells, scale_rows)) + 20
    B = Image.new("RGB", (W, H), (60, 60, 60)); d = ImageDraw.Draw(B); d.text((4, 3), title, fill=(255, 255, 0)); y = 20
    for row, s, lab in zip(cells, scale_rows, labels):
        x = 4
        for k, c in enumerate(row):
            B.paste(c.resize((c.width * s, c.height * s), Image.NEAREST), (x, y + 12)); d.text((x, y), lab[k] if s > 1 else (lab[k].split()[0] if lab[k] else ""), fill=(255, 255, 255)); x += c.width * s + 6
        y += max(c.height for c in row) * s + 16
    return B


def run(act):
    m = json.load(open(os.path.join(M, f"{act}.json")))
    lab = [f"f{k} {m['timing_ms'][k]}ms {fr.get('key', '')}" for k, fr in enumerate(m["frames"])]
    new = frames(act, "r2"); bb = bbox(new)
    crop = [im.crop(bb) for im in new]
    # silhouettes: 1x row + 4x row
    S = sheet([[sil(c) for c in crop], [sil(c) for c in crop]], [lab, lab], f"{act} SE key-pose silhouettes (solid fill): row 1 = 1x, row 2 = 4x", [1, 4])
    S.save(os.path.join(M, "out", f"sil_{act}_SE.png"))
    st = sheet([[on_bg(c) for c in crop], [on_bg(c) for c in crop]], [lab, lab], f"{act} SE round 2 pixel frames: row 1 = 1x (actual size), row 2 = 4x", [1, 4])
    st.save(os.path.join(M, "out", f"strip_{act}_SE_r2.png"))
    old = frames(act, "r1cmp")
    if old:
        m1 = json.load(open(os.path.join(M, "round1", f"{act}.json")))
        lab1 = [f"A f{k} {m1['timing_ms'][k]}ms {fr.get('key', '')}" for k, fr in enumerate(m1["frames"])]
        labB = ["B " + l for l in lab]
        bb2 = bbox(old + new); oc = [on_bg(im.crop(bb2)) for im in old]; nc = [on_bg(im.crop(bb2)) for im in new]
        ab = sheet([oc, oc, nc, nc], [lab1, lab1, labB, labB],
                   f"{act} SE  A = ROUND 1 (owner: 'gradual improvement, stiff, legs flicker, head/hair frozen')  B = ROUND 2.  Rows: A 4x, A 1x, B 4x, B 1x", [4, 1, 4, 1])
        ab.save(os.path.join(M, "crit", f"ab2_{act}.png"))
    print(act, "sheets done")


if __name__ == "__main__":
    for a in sys.argv[1].split(","): run(a)
