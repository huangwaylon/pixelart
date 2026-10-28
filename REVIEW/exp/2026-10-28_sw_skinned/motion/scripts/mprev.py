"""mprev.py (M): quick capsule-figure preview of a motion JSON from the game camera (30 deg elevation, ortho).
Reads ONLY the motion file + skeleton (round trip of the local quaternions), so it checks the file R will play.
usage: python mprev.py motion/walk.json [SE|E|S] [outdir]
Outputs: <out>/<act>_<view>_fNN.png, <act>_<view>.gif (timing_ms), <act>_<view>_strip.png (numbered), plus a sprite-scale strip.
"""
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mrig import Skel, EXP, UP, FWD, nrm

PX_M = 190.0      # preview px per metre
W, Hh = 420, 420
GROUND_Y = 360
COL = dict(hair=(70, 52, 58), hair2=(96, 72, 78), skin=(246, 214, 192), red=(200, 48, 58), red2=(160, 30, 44), red3=(150, 32, 46),
           obi=(74, 62, 84), sock=(36, 42, 78), boot=(42, 34, 44), bow=(236, 96, 82), eye=(30, 24, 40), band=(190, 40, 52), shadow=(150, 150, 150))
FONT = None


def cam(view, sk):
    hd = {"S": FWD, "E": sk.RIGHT, "SE": nrm(FWD + sk.RIGHT), "SW": nrm(FWD + sk.LEFT), "W": sk.LEFT, "N": -FWD}[view]
    e = math.radians(30)
    pos = math.cos(e) * hd + math.sin(e) * UP; f = -pos
    rs = nrm(np.cross(f, UP)); us = np.cross(rs, f)
    return f, rs, us


class Proj:
    def __init__(self, view, sk):
        self.f, self.rs, self.us = cam(view, sk)
    def __call__(self, p):
        p = np.asarray(p, float)
        return (W / 2 + PX_M * np.dot(p, self.rs), GROUND_Y - PX_M * np.dot(p, self.us), float(np.dot(p, self.f)))


def shade(c, k): return tuple(int(max(0, min(255, v * k))) for v in c)


def capsule_poly(a, b, ra, rb, n=10):
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay; L = math.hypot(dx, dy) + 1e-9; ang = math.atan2(dy, dx)
    pts = []
    for i in range(n + 1):
        t = ang + math.pi / 2 + math.pi * i / n; pts.append((bx + rb * math.cos(t - math.pi), by + rb * math.sin(t - math.pi)))
    for i in range(n + 1):
        t = ang + math.pi / 2 + math.pi * i / n; pts.append((ax + ra * math.cos(t), ay + ra * math.sin(t)))
    return pts


def fk_from_file(sk, fr):
    r = {n: sk.rel_from_local(n, b["rot"]) for n, b in fr["bones"].items() if sk.has(n)}
    sc = {b: v for b, v in fr.get("scale", {}).items()}
    return sk.fk(r, fr["root"]["loc"], sc)


def draw_frame(sk, fr, view, t_s=0.0, travel=0.0, label=None):
    pr = Proj(view, sk); D, H, T = fk_from_file(sk, fr)
    S = (sk.tail0["head"][2]) / 1.75  # radii were tuned on the 1.75 m stand-in
    prim = []  # (depth, kind, data)
    def cap(a, b, ra, rb, col, bias=0.0):
        A, B = pr(a), pr(b); prim.append(((A[2] + B[2]) / 2 + bias, "poly", capsule_poly(A[:2], B[:2], ra * S * PX_M, rb * S * PX_M), col))
    def ball(p, rad, col, bias=0.0):
        r_ = rad * S * PX_M; P = pr(p); prim.append((P[2] + bias, "ell", (P[0] - r_, P[1] - r_, P[0] + r_, P[1] + r_), col))
    def quad(ps, col, bias=0.0):
        Q = [pr(p) for p in ps]; prim.append((sum(q[2] for q in Q) / len(Q) + bias, "poly", [q[:2] for q in Q], col))
    # legs
    for s in "LR":
        th, sh, ft, toe = f"thigh.{s}", f"shin.{s}", f"foot.{s}", f"toe.{s}"
        cap(H[th], T[th] if np.linalg.norm(T[th] - H[sh]) < 0.02 else H[sh], 0.075, 0.06, COL["sock"])
        cap(H[sh], T[sh], 0.058, 0.045, COL["sock"])
        cap(H[ft], T[ft], 0.05, 0.045, COL["boot"], -0.01)
        if sk.has(toe): cap(H[toe], T[toe], 0.042, 0.035, COL["boot"], -0.01)
        # sock top band
        k = H[th] + 0.35 * (H[sh] - H[th]); cap(k, k + 0.04 * nrm(H[sh] - H[th]), 0.078, 0.078, COL["band"], -0.005)
    # torso
    cap(H["pelvis"], T["pelvis"], 0.11, 0.115, COL["red"])
    cap(H["spine"], T["spine"], 0.125, 0.125, COL["obi"], -0.01)
    cap(H["chest"], T["chest"], 0.12, 0.11, COL["red"])
    cap(H["neck"], H["neck"] + 0.4 * (T["neck"] - H["neck"]), 0.045, 0.045, COL["skin"])
    # head: skull sphere + face disc + eyes (direction cue)
    hc = H["head"] + 0.45 * (T["head"] - H["head"])
    hs = np.diag(np.linalg.norm(np.array([T["head"] - H["head"]]), axis=1))[0, 0] / max(1e-6, np.linalg.norm(sk.tail0["head"] - sk.head0["head"]))
    Dh = D["head"]
    ball(hc, 0.255, COL["hair"])
    ball(hc + S * (Dh @ (FWD * 0.10 + UP * -0.04)), 0.19, COL["skin"], -0.001)
    for sg in (-1, 1):
        ball(hc + S * (Dh @ (FWD * 0.255 + sk.RIGHT * 0.085 * sg + UP * -0.03)), 0.033, COL["eye"], -0.002)
    cap(hc + S * (Dh @ (FWD * 0.17 + UP * 0.12 + sk.RIGHT * 0.15)), hc + S * (Dh @ (FWD * 0.17 + UP * 0.12 - sk.RIGHT * 0.15)), 0.07, 0.07, COL["hair"], -0.003)
    # arms
    for s in "LR":
        ua, fa, hd = f"upper_arm.{s}", f"forearm.{s}", f"hand.{s}"
        cap(H[ua], T[ua], 0.05, 0.045, COL["red"])
        cap(H[fa], T[fa], 0.035, 0.03, COL["skin"])
        ball(T[fa] + 0.5 * (T[hd] - H[hd]), 0.04, COL["skin"])
    # secondary chains
    for n in sk.order:
        if n.startswith("hair_front"): cap(H[n], T[n], 0.035, 0.025, COL["hair2"], -0.005)
        elif n.startswith("hair_side"): cap(H[n], T[n], 0.05, 0.04, COL["hair2"])
        elif n.startswith("hair_back"): cap(H[n], T[n], 0.07, 0.06, COL["hair2"], 0.02)
        elif n == "bun": ball(H[n] + 0.6 * (T[n] - H[n]), 0.085, COL["hair2"])
        elif n == "bow_knot": ball(H[n], 0.04, COL["bow"], -0.01)
        elif n.startswith("bow."): cap(H[n], T[n], 0.04, 0.06 if n.endswith(".2") else 0.045, COL["bow"], -0.01)
        elif n.startswith("sleeve.") and n.endswith(".1"):
            n2 = n[:-1] + "2"
            cap(H[n], T[n], 0.07, 0.10, COL["red3"], 0.01)
            if sk.has(n2): cap(H[n2], T[n2], 0.10, 0.12, COL["red3"], 0.01)
    order = ["F", "FL", "L", "BL", "B", "BR", "R", "FR"]
    ks = [k for k in order if sk.has(f"skirt.{k}.1")]
    for i, k in enumerate(ks):
        k2 = ks[(i + 1) % len(ks)]
        a1, b1 = f"skirt.{k}.1", f"skirt.{k2}.1"; a2, b2 = f"skirt.{k}.2", f"skirt.{k2}.2"
        nmid = nrm(np.cross(T[b1] - T[a1], H[a1] - T[a1]))
        lit = 0.75 + 0.35 * max(0, np.dot(nmid, nrm(-pr.f + UP)))
        quad([H[a1], H[b1], T[b1], T[a1]], shade(COL["red2"], lit))
        quad([T[a1], T[b1], T[b2], T[a2]], shade(COL["red2"], lit), -0.002)
    img = Image.new("RGB", (W, Hh), (128, 128, 128)); dr = ImageDraw.Draw(img)
    # ground ticks scroll back at the travel speed: planted feet should hold still against them
    for k in range(-12, 13):
        y = k * 0.25 - (travel * t_s) % 0.25
        for x in (-0.5, 0.5):
            p0 = pr(np.array([x * 0.6, y, 0.0])); dr.ellipse((p0[0] - 2, p0[1] - 1, p0[0] + 2, p0[1] + 1), fill=(110, 110, 110))
    gc = pr(np.array([H["pelvis"][0], H["pelvis"][1], 0.0]))
    dr.ellipse((gc[0] - 55, gc[1] - 18, gc[0] + 55, gc[1] + 18), fill=(112, 112, 112))
    for d, kind, data, col in sorted(prim, key=lambda x: -x[0]):
        if kind == "poly": dr.polygon(data, fill=col, outline=shade(col, 0.55))
        else: dr.ellipse(data, fill=col, outline=shade(col, 0.55))
    if label: dr.text((6, 6), label, fill=(255, 255, 160), font=FONT)
    return img


def preview(path, view="SE", outdir=None):
    m = json.load(open(path)); sk = Skel(); act = m["action"]
    outdir = outdir or os.path.join(EXP, "motion", "prev", act); os.makedirs(outdir, exist_ok=True)
    trav = m.get("travel_m_per_s", 0.0); t = 0.0; ims = []
    for k, fr in enumerate(m["frames"]):
        im = draw_frame(sk, fr, view, t, trav, f"{act} {view} f{k:02d} {m['timing_ms'][k]}ms  {fr.get('key', '')}")
        im.save(os.path.join(outdir, f"{act}_{view}_f{k:02d}.png")); ims.append(im); t += m["timing_ms"][k] / 1000
    ims[0].save(os.path.join(outdir, f"{act}_{view}.gif"), save_all=True, append_images=ims[1:], duration=m["timing_ms"], loop=0)
    # numbered strip (crop to the figure area)
    cw = 260; x0 = (W - cw) // 2; crop = [im.crop((x0, 30, x0 + cw, Hh)) for im in ims]
    strip = Image.new("RGB", (cw * len(crop), crop[0].height + 22), (60, 60, 60)); dr = ImageDraw.Draw(strip)
    for k, c in enumerate(crop):
        strip.paste(c, (k * cw, 22)); dr.text((k * cw + 4, 4), f"f{k} {m['timing_ms'][k]}ms {m['frames'][k].get('key', '')}", fill=(255, 255, 255))
    strip.save(os.path.join(outdir, f"{act}_{view}_strip.png"))
    print("preview", outdir, len(ims), "frames")
    return outdir


if __name__ == "__main__":
    p = sys.argv[1]; v = sys.argv[2] if len(sys.argv) > 2 else "SE"
    preview(p, v, sys.argv[3] if len(sys.argv) > 3 else None)
