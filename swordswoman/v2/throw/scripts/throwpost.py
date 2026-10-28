# throwpost.py [VIEWS] : (1) add ball/release data to v2/hy3d/frames_mocap/throw_<v>/s48/frames.json
#                        (2) preview GIF v2/throw/gifs/throw_<v>.gif: 1x flat matid (from the 4x guide, majority downsample) + orb/trail/sparkle/pop overlay, 96x64 game-camera strip, 6x NN on #6e6e6e
import sys, os, json, math
import numpy as np
from PIL import Image
FR = os.environ.get("FR_ROOT", "/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/hy3d/frames_mocap/"); FX = "/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/fx/"; OUT = os.environ.get("GIF_OUT", "/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/throw/gifs/")  # RIGCAL: env overrides (frames_G)
sys.path.insert(0, FX + "tools"); import fxlib as F
BG = (0x6e, 0x6e, 0x6e); Y0 = 16; CW, CH = 96, 80  # canvas = 96 cell rows 16..96 (64 cell + 16 rows below; full 96 width so the orb flight + pop stay visible)
FLIGHT_MS = int(os.environ.get("FLIGHT_MS", "220")); LAND_U = float(os.environ.get("LAND_U", "3.0")); ARC_PX = float(os.environ.get("ARC_PX", "16"))
CHEAT = {"S": 35, "N": 30, "NE": 0, "SE": 0, "E": 0}  # screen-space flight cheat (deg) toward the throwing-hand side for the depth views
def down1x(p):
    a = np.asarray(Image.open(p).convert("RGBA")); k = a.shape[0] // 96
    b = a.reshape(96, k, 96, k, 4).transpose(0, 2, 1, 3, 4).reshape(96, 96, k * k, 4); cov = (b[..., 3] > 127).mean(-1) > 0.5
    key = (b[..., 0].astype(np.int64) << 16) | (b[..., 1].astype(np.int64) << 8) | b[..., 2]; key = np.where(b[..., 3] > 127, key, -1)
    m = np.zeros((96, 96, 4), np.uint8)
    for y, x in zip(*np.nonzero(cov)):
        v, c = np.unique(key[y, x][key[y, x] >= 0], return_counts=True); kk = int(v[c.argmax()]); m[y, x] = ((kk >> 16) & 255, (kk >> 8) & 255, kk & 255, 255)
    return Image.fromarray(m)
def fx(n):
    a = json.load(open(FX + f"maps/{n}.anchors.json")); return [F.to_img(g) for g, _ in F.read(FX + f"maps/{n}.txt")], [ms for _, ms in F.read(FX + f"maps/{n}.txt")], a["pivot"]
ORB, PO, TR, SP = fx("throw_orb"), fx("throw_pop"), fx("throw_trail"), fx("throw_sparkle")
SHADOW = Image.new("RGBA", (5, 2), (0, 0, 0, 0)); [SHADOW.putpixel(q, (72, 66, 70, 255)) for q in [(1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1)]]  # flat 5x2 ground shadow of the flying orb
def paste(C, im, piv, at, flip=False):
    if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT); piv = [im.width - 1 - piv[0], piv[1]]
    C.alpha_composite(im, (int(round(at[0] - piv[0])), int(round(at[1] - Y0 - piv[1]))))
def post(v):
    d0 = FR + f"throw_{v}/s48/"; J = json.load(open(d0 + "frames.json")); fr = J["frames"]
    ri = [f["name"] for f in fr].index("release"); si = ri - 1; ppu = J["px_per_unit_1x"]; up = 0.25 * ppu * math.cos(math.radians(30))
    P = [f["pts"] for f in fr]; rel = P[ri]["hand_tip.R"]
    ah = np.subtract(P[ri]["throw_ahead"], P[ri]["throw_hips"]); vel = ah / np.linalg.norm(ah)
    sg = 1 if rel[0] >= P[ri]["chest"][0] else -1; ca = math.radians(CHEAT[v]) * sg
    def rot(q):
        if abs(q[1]) <= abs(q[0]) or not ca: return np.array(q, float)
        cands = [np.array([q[0] * math.cos(a) - q[1] * math.sin(a), q[0] * math.sin(a) + q[1] * math.cos(a)]) for a in (ca, -ca)]
        return max(cands, key=lambda c: c[0] * sg)
    ah = rot(ah); vel = ah / np.linalg.norm(ah)
    gdir = ah + np.array([0, up]); land = np.array(J["pivot_1x"], float) + LAND_U * gdir  # ground point LAND_U units ahead of the feet pivot
    dv = land - np.array(J["pivot_1x"], float); n_ = np.linalg.norm(dv); land = np.array(J["pivot_1x"], float) + dv * max(1.0, 18.0 / max(n_, 1e-6))  # >= 18 px from the feet
    land[0] = min(max(land[0], 10), CW - 10); land[1] = min(max(land[1], Y0 + 8), Y0 + CH - 3)
    hv = np.subtract(rel, P[si]["hand_tip.R"]) / (fr[si]["ms"] / 1000.0)
    flip = rel[0] < P[si]["hand_tip.R"][0]  # trail art is drawn left->right (E); flip when the arc runs right->left on screen
    for i, f in enumerate(fr):
        st = "held" if i < ri else "release" if i == ri else "flying"
        f["ball"] = {"state": st, "pos_px": [round(x, 2) for x in P[i]["hand_tip.R"]] if i <= ri else None}
    J["ball"] = {"release_frame": ri, "spawn_px": [round(x, 2) for x in rel], "vel_dir_px": [round(float(x), 3) for x in vel], "hand_vel_px_s": [round(float(x), 1) for x in hv],
                 "ground_dir_px_per_unit": [round(float(x), 2) for x in gdir], "preview_land_px": [round(float(x), 1) for x in land], "trail_flip_x": bool(flip), "orb_px": 7, "flight_cheat_deg": CHEAT[v] * sg,
                 "note": "1x 96-cell px (x right, y down; pivot 48,76; 64 cell = crop x16..80 y16..80). Orb (fx throw_orb) sits in hand.R (pos_px = hand_tip.R) while held; spawned at spawn_px on the release key, flies along vel_dir_px (her forward + 0.25 up projected; hand_vel_px_s = measured hand speed stride->release). Release key: throw_trail (flip x if trail_flip_x) + throw_sparkle at spawn_px. Landing / throw_pop = game code (preview lands LAND_U=1.5 units ahead on the ground)."}
    json.dump(J, open(d0 + "frames.json", "w"), indent=1)
    # ---- preview timeline (10 ms grid)
    bodies = [down1x(d0 + f"f{f['i']:02d}_matid.png").crop((0, Y0, CW, Y0 + CH)) for f in fr]
    starts = np.cumsum([0] + [f["ms"] for f in fr]); t_rel = starts[ri]; pop_ms = sum(PO[1]); total = max(starts[-1], t_rel + fr[ri]["ms"] + FLIGHT_MS + pop_ms + 60) + 300
    states = []
    for t in range(0, int(total), 10):
        pi = int(np.searchsorted(starts, t, side="right") - 1); pi = min(pi, len(fr) - 1); items = []
        if t < t_rel: items.append(("orb", 0, tuple(np.round(P[pi]["hand_tip.R"], 0))))
        elif t < t_rel + fr[ri]["ms"]:
            k = 0 if t - t_rel < TR[1][0] else 1; items += [("trail", k, tuple(rel)), ("orb", 0, tuple(np.round(rel, 0)))]
            items.append(("spark", 0, tuple(rel)))
        else:
            tf = t - (t_rel + fr[ri]["ms"]); ts = t - t_rel
            if ts < sum(SP[1]): items.append(("spark", int(np.searchsorted(np.cumsum(SP[1]), ts, side="right")), tuple(rel)))
            if tf < FLIGHT_MS:
                s = (tf + fr[ri]["ms"]) / (FLIGHT_MS + fr[ri]["ms"]); s = 1 - (1 - s) ** 1.6; p = np.array(rel) + s * (land - np.array(rel)); p[1] -= ARC_PX * 4 * s * (1 - s)
                g0 = np.array(J["pivot_1x"], float) + 0.35 * (land - np.array(J["pivot_1x"], float)); gp = g0 + s * (land - g0)
                items.append(("shadow", 0, tuple(np.round(gp, 0)))); items.append(("orb", (tf // 60) % 4, tuple(np.round(p - [0, 3], 0))))  # orb centre 3 px above the ground point at landing
            elif tf < FLIGHT_MS + pop_ms:
                items.append(("pop", int(np.searchsorted(np.cumsum(PO[1]), tf - FLIGHT_MS, side="right")), tuple(land)))
        states.append((pi, tuple(items)))
    frames, ms = [], []
    for st in states:
        if frames and st == frames[-1]: ms[-1] += 10
        else: frames.append(st); ms.append(10)
    ims = []
    for pi, items in frames:
        C = Image.new("RGBA", (CW, CH), BG + (255,)); C.alpha_composite(bodies[pi])
        for kind, k, at in items:
            if kind == "shadow": paste(C, SHADOW, [2, 0], at)
            elif kind == "orb": paste(C, ORB[0][k], ORB[2], at)
            elif kind == "trail": paste(C, TR[0][min(k, len(TR[0]) - 1)], TR[2], at, flip)
            elif kind == "spark": paste(C, SP[0][min(k, len(SP[0]) - 1)], SP[2], at)
            elif kind == "pop": paste(C, PO[0][min(k, len(PO[0]) - 1)], PO[2], at)
        ims.append(C.convert("RGB").resize((CW * 6, CH * 6), Image.NEAREST))
    os.makedirs(OUT, exist_ok=True); ims[0].save(OUT + f"throw_{v}.gif", save_all=True, append_images=ims[1:], duration=ms, loop=0, disposal=1)
    # contact strip for critics: 8 frames sampled at fixed times (2x)
    tc = np.cumsum([0] + ms); want = [starts[i] + 5 for i in range(len(fr))] + [t_rel + fr[ri]["ms"] + FLIGHT_MS // 2, t_rel + fr[ri]["ms"] + FLIGHT_MS + 50]
    want = sorted(want)[:10]; sel = [ims[int(np.searchsorted(tc, t, side="right") - 1)] for t in want]
    sm = [im.resize((CW * 2, CH * 2), Image.NEAREST) for im in sel]; cols = 4; S = Image.new("RGB", (CW * 2 * cols, CH * 2 * ((len(sm) + cols - 1) // cols)), BG)
    for j, im in enumerate(sm): S.paste(im, ((j % cols) * CW * 2, (j // cols) * CH * 2))
    S.save(OUT + f"throw_{v}_strip.png"); keyims = sel
    print(v, "gif frames", len(ims), "ms", sum(ms), "release", rel, "vel", J["ball"]["vel_dir_px"], "land", J["ball"]["preview_land_px"], "flip", flip)
    return keyims
if __name__ == "__main__":
    for v in (sys.argv[1].split(",") if len(sys.argv) > 1 else ["S", "SE", "E", "NE", "N"]): post(v)
