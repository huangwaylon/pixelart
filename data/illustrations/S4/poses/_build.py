"""Build the 8 S4 full-body cut-scene poses from the canonical model sheet (3/4 panel).

The model-sheet shapes are copied verbatim and re-posed by a small 2-bone skin warp (shoulder/elbow,
hip/knee, neck, hip-pivot torso lean) plus secondary motion (hair / ponytail / bow tails / scarf tail
hang + swing, hem flare, shrug). Extra per-pose shapes (pulled-up scarf, fx) are authored here in
design units. Output: data/illustrations/S4/poses/<pose>.json (plain illustrate.py sources).

    .venv/bin/python data/illustrations/S4/poses/_build.py
"""
import copy
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, ROOT)
from pipeline.illustrate import parse_path  # noqa: E402

SHEET = json.load(open(os.path.join(HERE, "..", "model_sheet.json")))
REST = SHEET["panels"][1]  # three_quarter

# ---- rest-pose joints (design units, 8x) ----
HIP_PIVOT = (390, 620)
NECK = (388, 340)
ARM = {"near": {"S": (468, 428), "E": (490, 540), "W": (503, 648)},
       "far": {"S": (312, 425), "E": (292, 540), "W": (288, 645)}}
LEG = {"far": {"H": (356, 790), "K": (356, 885)}, "near": {"H": (414, 790), "K": (414, 885)}}

HEAD = {"bow_far", "bow_far_shade", "face", "face_shade", "bangs", "bangs_shade", "bangs_hi", "sidelock_far",
        "sidelock", "sidelock_shade", "bow", "bow_shade", "bow_hi", "bow_knot", "neck"}
HAIR = {"hair_back", "hair_back_line"}
PONY = {"ponytail", "ponytail_shade", "ponytail_hi", "ponytail_line"}
BOWTAIL = {"bow_tail"}
TORSO = {"coat", "coat_shade", "button", "hem", "belt", "buckle", "scarf", "scarf_shade", "scarf_hi", "knot", "knot_hi"}
SCARFTAIL = {"scarf_tail", "scarf_tail_shade"}
ARM_NEAR = {"arm", "arm_shade", "cuff", "hand", "hand_shade"}
ARM_FAR = {"arm_far", "cuff_far", "hand_far"}
LEGS = {"tights", "tights_shade", "boot_far", "boot", "boot_shade", "boot_hi", "boot_far_shade", "boot_cuff",
        "boot_cuff_far"}


def smooth(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def rot(p, c, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * ca - y * sa, c[1] + x * sa + y * ca)


def lerp(a, b, w):
    return (a[0] + (b[0] - a[0]) * w, a[1] + (b[1] - a[1]) * w)


class Rig:
    def __init__(self, P):
        self.P = P
        self.root = tuple(P.get("root", (0, 0)))
        self.torso_a = P.get("torso", 0)

    # rigid chains
    def T_root(self, p):
        return (p[0] + self.root[0], p[1] + self.root[1])

    def T_torso(self, p):
        return self.T_root(rot(p, HIP_PIVOT, self.torso_a))

    def T_head(self, p):
        h = self.P.get("head", {})
        q = rot(p, NECK, h.get("a", 0))
        q = (q[0] + h.get("dx", 0), q[1] + h.get("dy", 0))
        return self.T_torso(q)

    def shrug(self, p):
        s = self.P.get("shrug", 0)
        if not s:
            return p
        return (p[0], p[1] - s * (1 - smooth(410, 560, p[1])))

    def T_arm(self, side, p):
        j = ARM[side]
        a1, a2 = self.P.get("arm_" + side, (0, 0))[:2]
        S, E, W = j["S"], j["E"], j["W"]
        ax, ay = W[0] - S[0], W[1] - S[1]
        L = math.hypot(ax, ay)
        t = ((p[0] - S[0]) * ax + (p[1] - S[1]) * ay) / L
        e = ((E[0] - S[0]) * ax + (E[1] - S[1]) * ay) / L
        w = smooth(e - 18, e + 18, t)
        k = self.P.get("pinch_" + side, 0)
        if k:  # elbow taper: pull the sleeve edges toward the arm axis around the elbow
            f = k * math.exp(-((t - e) / 34.0) ** 2)
            fx, fy = S[0] + ax / L * t, S[1] + ay / L * t
            p = (fx + (p[0] - fx) * (1 - f), fy + (p[1] - fy) * (1 - f))
        p = self.shrug(p)
        Ss, Es = self.shrug(S), self.shrug(E)
        up = rot(p, Ss, a1)
        lo = rot(rot(p, Es, a2), Ss, a1)
        return self.T_torso(lerp(up, lo, w))

    def T_leg(self, side, p):
        j = LEG[side]
        a1, a2 = self.P.get("leg_" + side, (0, 0))[:2]
        H, K = j["H"], j["K"]
        kb = self.P.get("knee_soft", {}).get(side, 25)
        w = smooth(K[1] - kb, K[1] + kb, p[1])
        wh = smooth(H[1] - 10, H[1] + 40, p[1])  # tights top stays tucked under the hem
        up = lerp(p, rot(p, H, a1), wh)
        lo = rot(rot(p, K, a2), H, a1)
        return self.T_root(lerp(up, lo, w))

    def T_hang(self, p, y0, y1, vec, base="head", end="torso"):
        w = smooth(y0, y1, p[1])
        A = self.T_head(p) if base == "head" else self.T_torso(p)
        B = {"torso": self.T_torso, "root": self.T_root, "head": self.T_head}[end](p)
        q = lerp(A, B, w)
        return (q[0] + vec[0] * w * w, q[1] + vec[1] * w * w)

    def coat_pre(self, p):
        f = self.P.get("flare", 0)
        if f and p[1] > 640:
            k = smooth(640, 800, p[1])
            p = (390 + (p[0] - 390) * (1 + f * k), p[1] - abs(f) * 30 * k)
        return self.shrug(p) if p[1] < 470 else p

    def point_fn(self, name, side=None):
        P = self.P
        if name in HEAD:
            return self.T_head
        if name in HAIR:
            return lambda p: self.T_hang(p, 220, 660, P.get("hang_hair", (0, 0)))
        if name in PONY:
            return lambda p: self.T_hang(p, 170, 680, P.get("hang_pony", (0, 0)))
        if name in BOWTAIL:
            return lambda p: self.T_hang(p, 150, 280, P.get("hang_bowtail", (0, 0)), end="head")
        if name in TORSO:
            return lambda p: self.T_torso(self.coat_pre(p))
        if name in SCARFTAIL:
            return lambda p: self.T_hang(self.shrug(p), 440, 560, P.get("hang_scarf", (0, 0)), base="torso",
                                         end="root")
        if name in ARM_NEAR:
            return lambda p: self.T_arm("near", p)
        if name in ARM_FAR:
            return lambda p: self.T_arm("far", p)
        if name in LEGS:
            return lambda p: self.T_leg(side, p)
        return self.T_torso


def fmt(polys):
    out = []
    for poly in polys:
        closed = len(poly) > 2 and abs(poly[0][0] - poly[-1][0]) < 1e-6 and abs(poly[0][1] - poly[-1][1]) < 1e-6
        pts = poly[:-1] if closed else poly
        s = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        out.append(s + (" Z" if closed else ""))
    return " ".join(out)


def warp_d(d, fn, translate=(0, 0)):
    polys = parse_path(d, steps=16)
    return fmt([[fn((x + translate[0], y + translate[1])) for x, y in poly] for poly in polys])


def centroid_x(d, translate):
    pts = [pt for poly in parse_path(d) for pt in poly]
    xs = [p[0] for p in pts]
    if max(xs) - min(xs) > 100:
        return None  # spans both legs
    return sum(xs) / len(xs) + translate[0]


def rest_layers():
    """model-sheet 3/4 layers with explicit z, leg layers split per leg (side tag)."""
    out, z = [], 0
    for l in REST["layers"]:
        l = copy.deepcopy(l)
        z = l.get("z", z)
        l["z"] = z
        if l["name"] in LEGS:
            tr = l.pop("translate", (0, 0))
            ds = l.pop("paths", None) or [l.pop("d")]
            per = {"far": [], "near": []}
            for d in ds:
                cx = centroid_x(d, tr)
                if cx is None:
                    per["far"].append(d); per["near"].append(d)  # hip band: both
                    continue
                per["far" if cx < 385 else "near"].append(d)
            for side in ("far", "near"):
                if per[side]:
                    ll = dict(l, paths=per[side], side=side, translate=tr)
                    if l["name"] == "tights":
                        ll["part"] = "tights"
                    out.append(ll)
        else:
            out.append(l)
    return out


def group_of(name):
    for g, s in (("head", HEAD), ("hair", HAIR), ("pony", PONY), ("bowtail", BOWTAIL), ("torso", TORSO),
                 ("scarftail", SCARFTAIL), ("arm_near", ARM_NEAR), ("arm_far", ARM_FAR)):
        if name in s:
            return g
    if name in LEGS:
        return "leg"
    return "other"


def load_cel(ref):
    """embed cel grids inline (poses/face/ first, then the shared S4/face/)."""
    flip = ref.endswith(":flip")
    ref = ref[:-5] if flip else ref
    for d in (os.path.join(HERE, "face"), os.path.join(HERE, "..", "face")):
        f = os.path.join(d, ref + ".json")
        if os.path.exists(f):
            c = json.load(open(f))
            c["ref"] = ref
            if flip:
                w = max(len(r) for r in c["grid"])
                c["grid"] = [r.ljust(w, ".")[::-1] for r in c["grid"]]
                c["anchor"] = [w - 1 - c["anchor"][0], c["anchor"][1]]
            return c
    raise FileNotFoundError(ref)


def build(pname, P):
    rig = Rig(P)
    layers = []
    zo = P.get("z", {})
    for l in rest_layers():
        side = l.pop("side", None)
        fn = rig.point_fn(l["name"], side)
        tr = l.pop("translate", (0, 0))
        nl = {k: v for k, v in l.items() if k not in ("d", "paths")}
        if "d" in l:
            nl["d"] = warp_d(l["d"], fn, tr)
        if "paths" in l:
            nl["paths"] = [warp_d(d, fn, tr) for d in l["paths"]]
        g = group_of(l["name"])
        key = f"leg_{side}" if g == "leg" else g
        if key in zo:
            nl["z"] = zo[key] + (0.001 * len(layers))
        if l["name"] in P.get("hide", []):
            continue
        layers.append(nl)
    for extra in P.get("add", []):
        e = copy.deepcopy(extra)
        fn = {"head": rig.T_head, "torso": rig.T_torso, "root": rig.T_root, "none": lambda p: p,
              "arm_near": lambda p: rig.T_arm("near", p), "arm_far": lambda p: rig.T_arm("far", p),
              "leg_near": lambda p: rig.T_leg("near", p), "leg_far": lambda p: rig.T_leg("far", p)}[e.pop("bone", "none")]
        if "d" in e:
            e["d"] = warp_d(e["d"], fn)
        if "paths" in e:
            e["paths"] = [warp_d(d, fn) for d in e["paths"]]
        layers.append(e)
    anchors = {}
    for k, (x, y) in REST["anchors"].items():
        q = rig.T_head((x * 8 + 4, y * 8 + 4))
        anchors[k] = [int(math.floor(q[0] / 8)), int(math.floor(q[1] / 8))]
    for k, (x, y) in P.get("anchors_add", {}).items():
        anchors[k] = [x, y]
    for k, (dx, dy) in P.get("anchor_nudge", {}).items():
        anchors[k] = [anchors[k][0] + dx, anchors[k][1] + dy]
    cels = dict(REST["cels"])
    cels.update(P.get("cels", {}))
    cels = {k: load_cel(v) for k, v in cels.items() if v}
    src = {
        "name": f"S4 pose: {pname}",
        "note": P.get("note", "") + " | generated by poses/_build.py from model_sheet.json three_quarter panel",
        "canvas": SHEET["canvas"], "design_scale": 8, "size": SHEET["size"], "palette": SHEET["palette"],
        "outline": dict(SHEET["outline"], line_colors=dict(SHEET["outline"]["line_colors"], scarf_up="teal_0")), "layers": layers, "anchors": anchors, "cels": cels,
    }
    path = os.path.join(HERE, f"{pname}.json")
    json.dump(src, open(path, "w"), indent=0)
    if P.get("cleanup", True):
        cleanup(path, src)
    return src


def _orphans(idx):
    import numpy as np
    H, W = idx.shape
    pad = np.full((H + 2, W + 2), -9, int)
    pad[1:-1, 1:-1] = idx
    same = np.zeros((H, W), bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                same |= pad[1 + dy:H + 1 + dy, 1 + dx:W + 1 + dx] == idx
    return (idx >= 0) & ~same


def cleanup(path, src, rounds=3):
    """Pixel-pass step 5 for warped shapes: recolour each isolated 1 px speck (not part of a face/fx cel)
    to its dominant 4-neighbour colour. Stored as 1x1 'fix_*' cels so the source stays one JSON."""
    import numpy as np
    from collections import Counter
    from pipeline.illustrate import render_illustration
    H, W = src["size"][1], src["size"][0]
    prot = np.zeros((H, W), bool)
    for slot, cel in src["cels"].items():
        X, Y = src["anchors"].get(slot, (None, None))
        if X is None:
            continue
        ax, ay = cel.get("anchor", (0, 0))
        for r, row in enumerate(cel["grid"]):
            for c, ch in enumerate(row):
                y, x = Y - ay + r, X - ax + c
                if ch not in ". " and 0 <= y < H and 0 <= x < W:
                    prot[y, x] = True
    n = 0
    for _ in range(rounds):
        pal, idx, _, _ = render_illustration(path)
        orph = _orphans(idx) & ~prot
        if not orph.any():
            break
        for y, x in zip(*np.nonzero(orph)):
            nb = [idx[y + dy, x + dx] for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))
                  if 0 <= y + dy < H and 0 <= x + dx < W and idx[y + dy, x + dx] >= 0]
            if not nb:
                continue
            col = pal.names[Counter(nb).most_common(1)[0][0]]
            slot = f"fix_{n}"
            n += 1
            src["anchors"][slot] = [int(x), int(y)]
            src["cels"][slot] = {"anchor": [0, 0], "legend": {"c": col}, "grid": ["c"]}
        json.dump(src, open(path, "w"), indent=0)
    src["cleanup_px"] = n
    json.dump(src, open(path, "w"), indent=0)


if __name__ == "__main__":
    from poses_def import POSES  # noqa: E402
    only = sys.argv[1:]
    for name, P in POSES.items():
        if not only or name in only:
            build(name, P)
            print("built", name)
