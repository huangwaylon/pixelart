"""mgrid.py (M, round 3): labelled grid GIF of all timing/length variants of an action, every GIF frame >= 20 ms (20 ms ticks),
loops share the action's cycle (walk .84 s, run .56 s, idle 2.4 s) so the grid loops seamlessly; one-shots are padded with an end hold.
usage: python mgrid.py walk [px|pv_SE|pv_E] ; also gif_check(path) -> min frame ms"""
import sys, os, json, glob
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mrig import EXP
M = os.path.join(EXP, "motion")
FEEL = {"s": "snappy holds", "e": "even", "h": "holds"}


def label(name):
    p = name.split("_")
    if p[0] == "jump": return f"jump  antic {'short' if p[1] == 'as' else 'long'} / hang {'short' if p[2] == 'hs' else 'long'}"
    return f"{p[0]} {p[1][:-1]} fr, {FEEL[p[1][-1]]}"


def load(name, kind):
    m = json.load(open(os.path.join(M, "variants", f"{name}.json"))); n = len(m["frames"]); ims = []
    for k in range(n):
        if kind == "px": f = os.path.join(M, "prev", "var", name, f"{name}_SE_px", f"f{k:02d}.png")
        else: f = os.path.join(M, "prev", "var", name, "pv", f"{name}_{kind.split('_')[1]}_f{k:02d}_pv.png")
        ims.append(Image.open(f).convert("RGBA"))
    return m, ims


def grid(act, kind="px", cols=None, out=None):
    names = sorted({os.path.basename(p)[:-5] for p in glob.glob(os.path.join(M, "variants", f"{act}_*.json"))},
                   key=lambda s: (int("".join(c for c in s.split("_")[1] if c.isdigit()) or 0), s))
    data = [load(n, kind) for n in names]
    bb = None
    for m, ims in data:
        for im in ims:
            b = im.getchannel("A").getbbox()
            if b: bb = b if bb is None else (min(bb[0], b[0]), min(bb[1], b[1]), max(bb[2], b[2]), max(bb[3], b[3]))
    pad = 3; bb = (bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad)
    S = 3 if kind == "px" else 1
    cw, ch = (bb[2] - bb[0]) * S, (bb[3] - bb[1]) * S
    cols = cols or (2 if act != "jump" else 2); rows = (len(names) + cols - 1) // cols
    loops = [m.get("loop", True) for m, _ in data]
    L = max(sum(m["timing_ms"]) for m, _ in data) + (0 if all(loops) else 400)
    L = int(round(L / 20.0)) * 20
    def idx(m, t):
        tm = m["timing_ms"]; T = sum(tm)
        if m.get("loop", True): t %= T
        acc = 0
        for i, d in enumerate(tm):
            acc += d
            if t < acc: return i
        return len(tm) - 1
    cells = []
    for (m, ims) in data:
        cc = []
        for im in ims:
            bg = Image.new("RGBA", im.size, (128, 128, 128, 255)); bg.alpha_composite(im)
            c = bg.convert("RGB").crop(bb); cc.append(c.resize((cw, ch), Image.NEAREST))
        cells.append(cc)
    ev = []
    for t in range(0, L, 20):
        k = tuple(idx(m, t + 10) for m, _ in data)
        if ev and ev[-1][0] == k: ev[-1][1] += 20
        else: ev.append([k, 20])
    W = cols * (cw + 8) + 8; H = rows * (ch + 30) + 26
    frames = []
    for ks, d in ev:
        G = Image.new("RGB", (W, H), (50, 50, 50)); dr = ImageDraw.Draw(G)
        dr.text((8, 6), f"{act} timing/length variants ({'pixel chain 3x' if kind == 'px' else 'smooth preview ' + kind.split('_')[1]}); pick one", fill=(255, 255, 0))
        for j, (k, (m, _)) in enumerate(zip(ks, data)):
            x = 8 + (j % cols) * (cw + 8); y = 26 + (j // cols) * (ch + 30)
            G.paste(cells[j][k], (x, y + 26))
            ms = m["timing_ms"]
            dr.text((x, y + 2), f"{chr(65 + j)}  {label(names[j])}", fill=(255, 255, 255))
            dr.text((x, y + 13), f"f{k}/{len(ms)} {ms[k]}ms  {m['frames'][k].get('key', '')}", fill=(200, 200, 160))
        frames.append(G)
    out = out or os.path.join(M, "out", f"grid_{act}_{kind}.gif")
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=[d for _, d in ev], loop=0, disposal=1)
    print(out, len(frames), "frames, min ms", min(d for _, d in ev), "loop ms", sum(d for _, d in ev)); return out


def gif_check(p):
    from PIL import ImageSequence
    im = Image.open(p); d = [f.info.get("duration", 0) for f in ImageSequence.Iterator(im)]; return min(d), sum(d), len(d)


if __name__ == "__main__":
    grid(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "px")
