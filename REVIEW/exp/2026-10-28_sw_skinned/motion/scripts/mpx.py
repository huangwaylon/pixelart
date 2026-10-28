"""mpx.py (M): pixel-aware amplitude check of a motion file at 1x in the game view (R camera: 30 deg ortho, 67.88 px/m,
SE with R's default -15 deg rig yaw). Reports, per frame and as ranges (px at 1x):
  pelvis / head-top screen bob, head tilt (deg, screen roll) and nod, per-chain TIP deviation from the rigidly attached rest
  (the visible secondary bounce), hand outside sleeve (px the hand sits beyond the sleeve hem), leg separation (screen distance
  between the L and R shin/ankle centrelines), planted-foot slip under the game travel speed.
usage: python mpx.py walk [SE|E|S] [--json out.json]
"""
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mrig import Skel, EXP, UP, FWD, nrm, axang
from mprev import fk_from_file

PPM = 52.608 / 0.775   # px per metre at 1x (R camera)
try:
    YAW = {k: v["yaw"] for k, v in json.load(open(os.path.join(EXP, "rig", "align.json"))).items() if isinstance(v, dict) and "yaw" in v}
except Exception:
    YAW = {"SE": -10.0}


def cam(view, sk):
    hd = {"S": FWD, "E": sk.RIGHT, "SE": nrm(FWD + sk.RIGHT)}[view]
    e = math.radians(30); pos = math.cos(e) * hd + math.sin(e) * UP; f = -pos
    rs = nrm(np.cross(f, UP)); us = np.cross(rs, f); return rs, us


def flips(vs):
    """share of frame steps where the tip offset reverses direction along its main axis (2 per bounce is normal; ~1.0 = jitter)"""
    v = np.array(vs); v = v - v.mean(0); ax = int(np.argmax(v.std(0))); d = np.diff(np.r_[v[:, ax], v[:1, ax]])
    return float(np.mean(np.sign(d) != np.sign(np.roll(d, 1))))


def measure(act, view="SE"):
    sk = Skel(); m = json.load(open(os.path.join(os.environ.get("MPX_DIR", os.path.join(EXP, "motion")), f"{act}.json")))
    rs, us = cam(view, sk); Ry = axang(UP, YAW.get(view, 0.0))
    P = lambda p: np.array([np.dot(Ry @ p, rs), -np.dot(Ry @ p, us)]) * PPM   # screen px (y down)
    chains = {}
    for n in sk.order:
        for key in ("hair_front", "hair_side", "hair_back", "bun", "bow.", "sleeve", "skirt"):
            if n.startswith(key): chains.setdefault(key.rstrip("."), []).append(n)
    tips = {g: [b for b in bs if not any(sk.parent[c] == b for c in bs)] for g, bs in chains.items()}
    secondary = set(b for bs in chains.values() for b in bs)
    rows = []; trav = m.get("travel_m_per_s", 0.0); t = 0.0
    for k, fr in enumerate(m["frames"]):
        D, H, T = fk_from_file(sk, fr)
        fr2 = dict(fr); fr2["bones"] = {n: v for n, v in fr["bones"].items() if n not in secondary}
        D0, H0, T0 = fk_from_file(sk, fr2)   # same body, secondary rigid
        r = {"pelvis": P(H["pelvis"]), "headtop": P(T["head"])}
        hv = P(T["head"]) - P(H["head"]); r["head_roll"] = math.degrees(math.atan2(hv[0], -hv[1]))
        fwd = D["head"] @ FWD; r["head_nod"] = math.degrees(math.asin(max(-1, min(1, -fwd[2]))))
        r["head_yaw"] = math.degrees(math.atan2(np.dot(fwd, sk.LEFT), np.dot(fwd, FWD)))
        for g, ts in tips.items():
            r["tip_" + g] = max(float(np.linalg.norm(P(T[b]) - P(T0[b]))) for b in ts)
            r["tipv_" + g] = {b: P(T[b]) - P(T0[b]) for b in ts}
        for s in "LR":
            hand = P(T[f"hand.{s}"]); hem = P(T[f"sleeve.{s}.2"]) if sk.has(f"sleeve.{s}.2") else hand
            r[f"hand_out_{s}"] = float(np.linalg.norm(hand - hem))
        legs = []
        for part in ("shin", "foot"):
            a = (P(H[f"{part}.L"]) + P(T[f"{part}.L"])) / 2; b = (P(H[f"{part}.R"]) + P(T[f"{part}.R"])) / 2
            legs.append(abs(a[0] - b[0]))
        r["leg_sep_x"] = min(legs)
        # planted foot: world toe-ball position + travel (should stay still while planted)
        r["ball"] = {s: H[f"toe.{s}"] + FWD * trav * t for s in "LR"}; r["flat"] = {s: H[f"foot.{s}"][2] < sk.head0[f"foot.{s}"][2] + 0.006 and H[f"toe.{s}"][2] < sk.head0[f"toe.{s}"][2] + 0.006 for s in "LR"}
        rows.append(r); t += m["timing_ms"][k] / 1000
    def rng(key, ax=None):
        v = np.array([r[key] if ax is None else r[key][ax] for r in rows]); return float(v.max() - v.min())
    out = {"action": act, "view": view, "frames": len(rows),
           "pelvis_bob_px": round(rng("pelvis", 1), 2), "headtop_bob_px": round(rng("headtop", 1), 2), "headtop_x_px": round(rng("headtop", 0), 2),
           "head_roll_deg": round(rng("head_roll"), 1), "head_nod_deg": round(rng("head_nod"), 1), "head_yaw_deg": round(rng("head_yaw"), 1),
           "tip_px_max": {g: round(max(r["tip_" + g] for r in rows), 2) for g in tips},
           "tip_px_range": {g: round(max(max(float(np.ptp([r["tipv_" + g][b][ax] for r in rows])) for ax in (0, 1)) for b in tips[g]), 2) for g in tips},
           "tip_flip": {g: round(max(flips([r["tipv_" + g][b] for r in rows]) for b in tips[g]), 2) for g in tips},
           "hand_out_px_max": {s: round(max(r[f"hand_out_{s}"] for r in rows), 1) for s in "LR"},
           "leg_sep_min_px": round(min(r["leg_sep_x"] for r in rows), 1),
           "per_frame": [{"f": k, "pelvis_y": round(float(r["pelvis"][1]), 1), "head_y": round(float(r["headtop"][1]), 1), "roll": round(r["head_roll"], 1),
                          "leg_sep": round(r["leg_sep_x"], 1), **{g: round(r["tip_" + g], 1) for g in tips}} for k, r in enumerate(rows)]}
    # planted-foot slip: largest world motion of a ball point between consecutive frames while it is on the ground (z < 1 cm)
    slip = 0.0
    for k in range(len(rows) - 1):
        for s in "LR":
            a, b = rows[k]["ball"][s], rows[k + 1]["ball"][s]
            if rows[k]["flat"][s] and rows[k + 1]["flat"][s]: slip = max(slip, float(np.linalg.norm((a - b)[:2])) * PPM)
    out["planted_slip_px"] = round(slip, 2)
    return out


if __name__ == "__main__":
    act = sys.argv[1]; view = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else "SE"
    o = measure(act, view)
    if "--json" in sys.argv: json.dump(o, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)
    pf = o.pop("per_frame")
    print(json.dumps(o))
    if "-v" in sys.argv:
        for r in pf: print(r)
