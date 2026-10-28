"""Per-frame animation recipes for the S4 STANDARD TEST SET (secondary lag, expressions, smears, FX).

Each recipe: head_dy (head sinks into the collar on squash), bow (dx, dy) = bow-cel lag/overshoot vs
the head, face ('focus'), katana override, pre_head(fr, img) FX painted before the head stamp,
post(fr, img, head_mask) FX after it (never over the face)."""
import numpy as np

import celrender as CR
import fx as FX

# slash cut-plane ellipse (SE): centre on the impact hands, ry = 0.5 rx (30 deg camera)
SL_C = (75.0, 86.0)
SL_R = (31.0, 15.0)
A0, A1 = -168.0, -373.0          # coil side (left) -> impact (right), sweeping across her front


def _ground(img):
    a = img[..., 3] > 0
    ys, xs = np.nonzero(a[:110])
    y = ys.max()
    row = np.nonzero(a[y])[0]
    return y, row.min(), row.max()


def k0_katana(fr):
    # anticipation: blade drawn back over her RIGHT shoulder (screen left in SE), behind the body
    h = np.array(fr.joints["hand_L"][:2])
    u = np.array([-0.80, -0.60])
    return {"pommel": h - u * 3.5, "guard": h + u * 2.5, "tip": h + u * 30, "vis": False}


def k1_pre(fr, img):
    cx, cy = SL_C
    rx, ry = SL_R
    # full-motion blade-arc smear (k1 = active frame): coil -> just behind the blade (lead blunt)
    L = FX.arc_layer(cx, cy, rx, ry, A0, -328, 7, "w,P,p", taper="lead", grow="in")
    FX.composite(img, L, "over")
    # stretched-limb smear: sleeve cuff + forearm streak trailing toward the coil side
    h = fr.joints["hand_L"][:2]
    FX.composite(img, FX.streak_layer(h[0] - 12, h[1] - 3, h[0] - 2, h[1], 4, "R,r,v", taper="lead"), "over")
    # one hand echo 4-5 px back along the arc (behind)
    L2 = FX.Layer()
    ex, ey = int(round(h[0] - 6)), int(round(h[1] + 2))
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        L2.put(ex + dx, ey + dy, CR.tone("pink_1"))
    FX.composite(img, L2, "behind")


def k2_pre(fr, img):
    cx, cy = SL_C
    rx, ry = SL_R
    a0 = A0 + 0.65 * (A1 - A0)
    L = FX.arc_layer(cx, cy, rx, ry, a0, A1 + 4, 3, "P,p", taper="lead", grow="in")
    FX.composite(img, L, "over")


def k2_post(fr, img, head):
    t = CR.katana_pts(fr)[2]
    FX.spark(img, t[0] + 2, t[1] - 1, 3)


def k3_pre(fr, img):
    cx, cy = SL_C
    rx, ry = SL_R
    # follow-through wisps: 2 short pink_0 slivers trailing the recovering tip (it moved back left)
    t = CR.katana_pts(fr)[2]
    L = FX.Layer()
    for dx, dy in ((3, -1), (4, -1), (5, -1), (6, -2), (3, 1), (4, 1)):
        L.put(round(t[0] + dx), round(t[1] + dy), CR.tone("pink_0"))
    FX.composite(img, L, "behind")


def land_post(fr, img, head):
    y, x0, x1 = _ground(img)
    FX.dust(img, x0 - 1, y, -1)
    FX.dust(img, x1 + 1, y, +1)


RECIPES = {
    "walk_SE_k0": {"hem_dy": -2, "bow": (0, 0)},
    "walk_SE_k1": {"hem_dy": -2, "bow": (0, -1)},
    "walk_SE_k2": {"hem_dy": -2, "bow": (0, 1)},
    "walk_SE_k3": {"hem_dy": -2, "bow": (0, 1)},
    "slash_SE_k0": {"face": "focus", "bow": (1, -1), "katana": k0_katana},
    "slash_SE_k1": {"face": "focus", "bow": (-1, 0), "pre_head": k1_pre},
    "slash_SE_k2": {"face": "focus", "bow": (-1, 0), "pre_head": k2_pre, "post": k2_post},
    "slash_SE_k3": {"face": "focus", "bow": (1, 1), "pre_head": k3_pre},
    "jump_E_crouch": {"head_dy": 1, "hem_hips": 2, "bow": (0, -1), "scale": (1.08, 0.90)},
    "jump_E_apex": {"hem_hips": 2, "bow": (0, 1), "scale": (0.92, 1.22), "ground": False},
    "jump_E_land": {"head_dy": 1, "hem_hips": 2, "bow": (0, 1), "post": land_post, "scale": (1.12, 0.86)},
}


def jump_legs(fr, img, ci):
    """hand-drawn bent legs under the shortened front panel (deep squash keys): thigh hip->knee,
    shin knee->ankle, strappy heel on the ground.  Painted behind the dress (empty px only)."""
    J = fr.joints
    hx, hy = J["hips"][:2]
    occ = img[..., 3] > 0
    for s in ("R", "L"):  # far leg first
        kx, ky = J["knee_" + s][:2]
        ax, ay = J["ankle_" + s][:2]
        FX.limb(img, [(hx + 1, hy + 1), (kx + 1, ky), (ax, ay - 1)], 2, behind_mask=occ)
        FX.heel(img, ax - 1, ay + 1, facing=1)
        occ = img[..., 3] > 0


# (r1 pass I: skirt_cut + jump_legs tried on crouch/land; the guide crouch leaves only ~7 px of leg
#  room under the sleeves, so the drawn legs read as noise -> not used.  See self-critique.)


def _kat(dirv, back=3.0, length=30, vis=False):
    def f(fr):
        h = np.array(fr.joints["hand_L"][:2])
        u = np.array(dirv, float)
        u = u / np.hypot(*u)
        return {"pommel": h - u * back, "guard": h + u * 2.5, "tip": h + u * length, "vis": vis}
    return f


# jump: the katana trails behind her (against the motion) in all three keys, held low in the left hand
RECIPES["jump_E_crouch"]["katana"] = _kat((-1.0, 0.5))      # coiled low behind, tip near the ground
RECIPES["jump_E_apex"]["katana"] = _kat((-0.5, 1.0), vis="all")       # trailing down-back on the rise
RECIPES["jump_E_land"]["katana"] = _kat((-1.0, -0.33))      # still swinging up-back (lag) as she lands


def ribbon_tails(fr, img, head):
    """front-ish views: if the guide ribbons are hidden by the dress, show the two pink scarf tails
    fluttering out beside the collar (iso_v5), drawn behind the body."""
    J = fr.joints
    pink = np.array([CR.tone("pink_0")[:3], CR.tone("pink_1")[:3]])
    a = img[..., :3]
    has = ((a[..., None, :] == pink[None, None]).all(-1).any(-1)) & (img[..., 3] > 0)
    cx, cy = J["chin"][:2]
    cy = int(round(cy)) + 3
    for s in (-1, 1):
        side = has[:, :int(cx)] if s < 0 else has[:, int(cx):]
        if side[cy - 4:cy + 14].sum() >= 4:
            continue
        # find the body edge at this row
        row = np.nonzero(img[cy, :, 3])[0]
        if not len(row):
            continue
        x0 = row.min() if s < 0 else row.max()
        pts = [(x0 - s * 0, cy), (x0 + s * 2, cy + 2), (x0 + s * 3, cy + 5), (x0 + s * 2, cy + 8), (x0 + s * 3, cy + 10)]
        L = FX.Layer()
        path = []
        for p0, p1 in zip(pts[:-1], pts[1:]):
            seg = CR.line_pts(p0[0], p0[1], p1[0], p1[1])
            path += seg if not path else seg[1:]
        for k, (x, y) in enumerate(path):
            L.put(x, y, CR.tone("pink_1" if k < len(path) * 0.6 else "pink_0"))
            if k < 3:
                L.put(x, y + 1, CR.tone("pink_0"))
        FX.composite(img, L, "behind")


for n in ("turn_S", "turn_SE", "turn_SW", "turn_E", "turn_W"):
    RECIPES.setdefault(n, {})["post"] = ribbon_tails
