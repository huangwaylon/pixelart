"""mboard.py (M): critique boards per action: grid of numbered SE frames, grid of E frames, onion skin (E) of all frames."""
import sys, os, json
from PIL import Image, ImageDraw, ImageChops
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mprev
from mrig import EXP

CW, CH = 250, 330


RIG = "--rig" in sys.argv
BL = "/Applications/Blender.app/Contents/MacOS/Blender"


def rig_render(act, v):
    import subprocess
    out = os.path.join(EXP, "motion", "prev", "rig", act); os.makedirs(out, exist_ok=True)
    subprocess.run([BL, "-b", os.path.join(EXP, "rig", "rig.blend"), "-P", os.path.join(EXP, "render", "render_motion.py"), "--",
                    os.path.join(EXP, "motion", f"{act}.json"), v, out, "--preview"], capture_output=True)
    return out


_BB = {}


def rig_frame(act, v, k):
    im = Image.open(os.path.join(EXP, "motion", "prev", "rig", act, f"{act}_{v}_f{k:02d}_pv.png")).convert("RGBA")
    bg = Image.new("RGBA", im.size, (128, 128, 128, 255)); bg.alpha_composite(im); return bg.convert("RGB"), im.getchannel("A")


def rig_cell(act, v, k):
    key = (act, v)
    if key not in _BB:  # union bbox over all frames of this clip
        bb = None; n = 0
        while os.path.exists(os.path.join(EXP, "motion", "prev", "rig", act, f"{act}_{v}_f{n:02d}_pv.png")):
            b = rig_frame(act, v, n)[1].getbbox(); n += 1
            bb = b if bb is None else (min(bb[0], b[0]), min(bb[1], b[1]), max(bb[2], b[2]), max(bb[3], b[3]))
        _BB[key] = bb
    x0, y0, x1, y1 = _BB[key]; im = rig_frame(act, v, k)[0]
    pad = 8; box = (x0 - pad, y0 - pad, x1 + pad, y1 + pad); cr = im.crop(box)
    sc = min((CW - 4) / cr.width, (CH - 20) / cr.height); cr = cr.resize((int(cr.width * sc), int(cr.height * sc)), Image.LANCZOS)
    c = Image.new("RGB", (CW, CH), (128, 128, 128)); c.paste(cr, ((CW - cr.width) // 2, 18)); return c


def cells(act, v, m):
    out = []
    for k in range(len(m["frames"])):
        if RIG:
            im = rig_cell(act, v, k)
            c = im
        else:
            im = Image.open(os.path.join(EXP, "motion", "prev", act, f"{act}_{v}_f{k:02d}.png")).convert("RGB")
            c = im.crop((85, 50, 85 + CW, 50 + CH))
        d = ImageDraw.Draw(c)
        d.rectangle((0, 0, CW, 16), fill=(30, 30, 30)); d.text((3, 2), f"f{k} {m['timing_ms'][k]}ms {m['frames'][k].get('key', '')}", fill=(255, 255, 255))
        out.append(c)
    return out


def board(act, tag="r1", views=("SE", "E")):
    path = os.path.join(EXP, "motion", f"{act}.json"); m = json.load(open(path)); n = len(m["frames"])
    for v in views:
        mprev.preview(path, v)
        if RIG: rig_render(act, v)
    outs = []
    cols = n if n <= 8 else (n + 1) // 2
    for v in views:
        cs = cells(act, v, m); rows = (n + cols - 1) // cols
        B = Image.new("RGB", (cols * CW, rows * CH + 22), (40, 40, 40)); dr = ImageDraw.Draw(B)
        dr.text((6, 5), f"{act} [{tag}] view {v} (game camera 30deg ortho), {n} frames, cycle {sum(m['timing_ms'])} ms; read left->right, top->bottom", fill=(255, 255, 0))
        for k, c in enumerate(cs): B.paste(c, ((k % cols) * CW, 22 + (k // cols) * CH))
        o = os.path.join(EXP, "motion", "crit", f"board_{act}_{v}_{tag}.png"); B.save(o); outs.append(o)
    on = None
    for k in range(n):
        im = rig_cell(act, "E", k) if RIG else Image.open(os.path.join(EXP, "motion", "prev", act, f"{act}_E_f{k:02d}.png")).convert("RGB")
        on = im if on is None else ImageChops.darker(on, im)
    o = os.path.join(EXP, "motion", "crit", f"onion_{act}_E_{tag}.png"); (on if RIG else on.crop((40, 20, 380, 420))).save(o); outs.append(o)
    print("\n".join(outs)); return outs


if __name__ == "__main__":
    tag = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "r1"
    for a in sys.argv[1].split(","): board(a, tag)
