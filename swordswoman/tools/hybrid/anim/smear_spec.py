"""Smear geometry per direction from the guide's blade-tip track (ANIM_DIRECTION.md section 4.4).

  .venv/bin/python tools/hybrid/anim/smear_spec.py   -> hybrid/anim/smears.json (+ smears_overlay.png)

Reads hybrid/anim/preview/<pose>_<DIR>.json (blade guard/b45/b70/tip + hands in 128-cell px, written
by pose_preview.py for all 8 directions).  For every smear frame it fits an axis-aligned ellipse
(draw.py `smear` geometry) through the tip track tail -> lead, centred near the hands, and writes a
ready draw.py command.  Horizontal cuts prefer ry = 0.5 rx (flat circle under the 30 deg camera).
"""
import json, math, os
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
PRE = os.path.join(ROOT, "hybrid", "anim", "preview")
DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]

SAMPLES = os.path.join(PRE, "samples")
SL = [f"samples/slashS_{i:02d}" for i in range(10)]          # f1 -> f2 (5) -> f3 (4) + f3
OHS = [f"samples/ohS_{i:02d}" for i in range(9)] + ["overhead_f4"]   # f2 -> f3 (5) -> f4 (4) + f4
# smear frame -> tip-track slice (tail..lead) of the swing samples, band width, tones, over-body dirs
SMEARS = {
    "slash_f2": dict(track=SL, use=(0, 9), W=5, tones="w,P,p", over=("S", "SE", "SW"),
                     what="blade-arc smear k1: FULL motion coil(f1) -> just short of impact(f3)"),
    "slash_f3": dict(track=SL, use=(6, 10), W=2, tones="P,p", over=("S", "SE", "SW"),
                     what="impact sliver k2: leading ~35 % of the arc, ends at the blade"),
    "overhead_f3": dict(track=OHS, use=(0, 8), W=6, tones="w,P,p", over=("S", "SE", "SW"),
                        what="smear 1: vertical crescent apex(f2) -> past the top-front, steel core"),
    "overhead_f4": dict(track=OHS, use=(5, 10), W=3, tones="P,w,p", over=("S", "SE", "SW"),
                        what="smear 2 / impact: lower 40 % of the arc into the ground, pink core (complementary flash)"),
}


def load(pose, d):
    p = os.path.join(PRE, f"{pose}_{d}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def fit_ellipse(pts):
    """least squares x^2 + A y^2 + B x + C y + D = 0 -> (cx, cy, rx, ry) or None."""
    M = np.array([[y * y, x, y, 1.0] for x, y in pts])
    b = -np.array([x * x for x, y in pts])
    (A, B, C, D), *_ = np.linalg.lstsq(M, b, rcond=None)
    if A <= 0.05:
        return None
    cx, cy = -B / 2, -C / (2 * A)
    r2 = cx * cx + A * cy * cy - D
    if r2 <= 4:
        return None
    rx = math.sqrt(r2)
    return float(cx), float(cy), rx, rx / math.sqrt(A)


def ang(e, p):
    cx, cy, rx, ry = e
    return math.degrees(math.atan2((p[1] - cy) / ry, (p[0] - cx) / rx))


def unwrap(a):
    out = [a[0]]
    for v in a[1:]:
        while v - out[-1] > 180:
            v -= 360
        while v - out[-1] < -180:
            v += 360
        out.append(v)
    return out


res = {}
for name, S in SMEARS.items():
    res[name] = {"what": S["what"], "dirs": {}}
    for d in DIRS:
        J = [load(t, d) for t in S["track"]]
        if any(j is None for j in J):
            continue
        full = [j["tip"] for j in J]
        a_, b_ = S["use"]
        pts = full[a_:b_]
        e = fit_ellipse(full)
        info = {"tip_track": pts, "full_track": full}
        if e is not None:
            resid = float(np.mean([abs(math.hypot((x - e[0]) / e[2], (y - e[1]) / e[3]) - 1) * e[2] for x, y in full]))
        if e is None or resid > 2.5 or max(e[2], e[3]) > 90:
            p0, p1 = pts[0], pts[-1]
            info.update(kind="polyline", draw=f"streak {p0[0]:.0f},{p0[1]:.0f} {p1[0]:.0f},{p1[1]:.0f} {S['W']} tones={S['tones']} taper=lead"
                        + (" over" if d in S["over"] else ""), note="arc ~ edge-on here: follow tip_track as a polyline band")
        else:
            A = unwrap([ang(e, p) for p in full])[a_:b_]
            a0, a1 = A[0], A[-1]
            info.update(kind="arc", ellipse=[round(v, 1) for v in e], fit_resid_px=round(resid, 2), a0=round(a0, 1), a1=round(a1, 1),
                        span_deg=round(abs(a1 - a0), 1),
                        draw=f"smear {e[0]:.0f},{e[1]:.0f} {e[2]:.0f},{e[3]:.0f} {a0:.0f} {a1:.0f} {S['W']} tones={S['tones']} taper=lead grow=in"
                        + (" over" if d in S["over"] else ""))
        info["over_body"] = d in S["over"]
        res[name]["dirs"][d] = info

# ---- flat slash: drawn on the CUT PLANE (horizontal circle at impact height round the hands), not on
# the raised coil track -- the coil lifts the blade for readability, the arc shows the hitbox sweep.
# A horizontal circle projects to ry = 0.5 rx; character azimuth az (deg from +X toward +Y) in
# direction yaw psi lands at draw.py angle a = -(az + psi) (screen y down).
SLASH_AZ = (123.0, 330.0)      # coil blade azimuth -> impact blade azimuth (increasing: right -> front -> left)


def split_front(a0, a1):
    """sub-ranges of [a0,a1] (deg, draw.py convention) nearer the camera (ey > 0 -> sin a > 0) vs behind."""
    import numpy as _np
    xs = _np.linspace(a0, a1, 181)
    segs, cur, st = [], None, None
    for x in xs:
        f = math.sin(math.radians(x)) > 0
        if cur is None:
            cur, st = f, x
        elif f != cur:
            segs.append((cur, st, x)); cur, st = f, x
    segs.append((cur, st, xs[-1]))
    return segs


for name, (f0, f1, W, tones) in {"slash_f2": (0.0, 0.9, 5, "w,P,p"), "slash_f3": (0.65, 1.0, 2, "P,p")}.items():
    for d in DIRS:
        J = load("slash_f3", d)
        if J is None:
            continue
        psi = DIRS.index(d) * 45.0
        hx = (J["hand.L"][0] + J["hand.R"][0]) / 2
        hy = (J["hand.L"][1] + J["hand.R"][1]) / 2
        dx, dy = J["tip"][0] - hx, J["tip"][1] - hy
        rx = math.hypot(dx, dy / 0.5)
        az0 = SLASH_AZ[0] + (SLASH_AZ[1] - SLASH_AZ[0]) * f0
        az1 = SLASH_AZ[0] + (SLASH_AZ[1] - SLASH_AZ[0]) * f1
        a0, a1 = -(az0 + psi), -(az1 + psi)          # decreasing; draw.py wants a0 tail, a1 lead
        base_cmd = f"smear {hx:.0f},{hy:.0f} {rx:.0f},{rx * 0.5:.0f} {a0:.0f} {a1:.0f} {W} tones={tones} taper=lead grow=in"
        front = [[round(s0), round(s1)] for f_, s0, s1 in split_front(a0, a1) if f_ and abs(s1 - s0) > 3]
        # one continuous taper: pass 1 behind everywhere, pass 2 'over' (same geometry, so the same taper) --
        # then erase pass 2 where the arc runs BEHIND the body (angles outside front_ranges)
        cmds = [base_cmd] + ([base_cmd + " over"] if front else [])
        info = res[name]["dirs"].get(d, {})
        info.update(kind="cut_plane_arc", ellipse=[round(hx, 1), round(hy, 1), round(rx, 1), round(rx * 0.5, 1)],
                    a0=round(a0, 1), a1=round(a1, 1), span_deg=round(abs(a1 - a0), 1),
                    draw=cmds[0], draw_over=cmds[1] if len(cmds) > 1 else None, front_ranges=front,
                    note="horizontal cut plane round the impact hands; parts with 'over' pass in front of the body "
                         "(cut 1 px clear of the face): run `draw` (behind), then for the front_ranges either run `draw_over` and erase "
                         "its part outside front_ranges, or hand-paint the front part over the body. "
                         "rig_tip_track = the guide blade tip (raised coil), for reference only.")
        info["rig_tip_track"] = info.pop("full_track", None)
        info.pop("tip_track", None)
        info.pop("fit_resid_px", None)
        res[name]["dirs"][d] = info

json.dump(res, open(os.path.join(ROOT, "hybrid", "anim", "smears.json"), "w"), indent=1)
# overlay check: draw the arcs over the guide renders that exist (256 px = 2x cell)
try:
    from PIL import Image, ImageDraw
    tiles = []
    for name in SMEARS:
        for d in DIRS:
            png = os.path.join(PRE, f"{name}_{d}.png")
            info = res[name]["dirs"].get(d)
            if not os.path.exists(png) or not info:
                continue
            im = Image.open(png).convert("RGBA")
            dr = ImageDraw.Draw(im)
            for p in (info.get("full_track") or info.get("rig_tip_track") or []):
                dr.ellipse([p[0] * 2 - 3, p[1] * 2 - 3, p[0] * 2 + 3, p[1] * 2 + 3], outline=(255, 255, 0, 255))
            if "ellipse" in info:
                cx, cy, rx, ry = info["ellipse"]
                a0, a1 = info["a0"], info["a1"]
                pts = [((cx + rx * math.cos(math.radians(a))) * 2, (cy + ry * math.sin(math.radians(a))) * 2)
                       for a in np.linspace(a0, a1, 40)]
                dr.line(pts, fill=(248, 181, 200, 255), width=3)
            elif info.get("tip_track"):
                dr.line([(p[0] * 2, p[1] * 2) for p in info["tip_track"]], fill=(248, 181, 200, 255), width=3)
            dr.text((4, 4), f"{name} {d}", fill=(255, 255, 255, 255))
            tiles.append(im)
    if tiles:
        cols = 6
        W, H = tiles[0].size
        S_ = Image.new("RGBA", (cols * W, ((len(tiles) + cols - 1) // cols) * H), (92, 88, 100, 255))
        for i, t in enumerate(tiles):
            S_.alpha_composite(t, ((i % cols) * W, (i // cols) * H))
        S_.save(os.path.join(ROOT, "hybrid", "anim", "review", "smears_overlay.png"))
except Exception as ex:
    print("overlay skipped:", ex)
for n, v in res.items():
    print(n, {d: (x["kind"][:4], x.get("span_deg")) for d, x in v["dirs"].items()})
