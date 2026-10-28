"""msim.py (M): dynamic layers baked into the motion.
 - HeadLag: damped angular spring on the head/neck driven by the neck-base acceleration (bob -> nod lag, sway -> tilt lag).
 - Chains: damped-spring particle chains for every secondary chain (hair, bun, bow lobes, sleeves, skirt panels),
   driven by the parent bone's world motion; inertia + air drag (travel wind) + gravity toward the world-rest hang;
   capsule collision (skirt vs thighs, hair vs head, sleeves vs torso); skirt panels coupled to their neighbours.
"""
import math, re, numpy as np
from mrig import nrm, min_rot, axang, UP, FWD
from scipy.spatial.transform import Rotation as Rot

# group: freq Hz, damping ratio, gravity-hang blend, air drag 1/s, follow (chain curl), gain (output exaggeration), max deg
GROUPS = {
    "hair_front": dict(f=4.2, z=0.30, gw=0.15, cd=0.6, follow=0.7, gain=1.6, mx=14),
    "hair_side":  dict(f=2.3, z=0.32, gw=0.45, cd=1.2, follow=0.5, gain=2.4, mx=22),
    "hair_back":  dict(f=2.1, z=0.32, gw=0.40, cd=1.4, follow=0.5, gain=2.5, mx=28),
    "bun":        dict(f=2.6, z=0.2, gw=0.00, cd=0.2, follow=0.0, gain=3.4, mx=16),
    "bow":        dict(f=2.3, z=0.22, gw=0.08, cd=0.8, follow=0.6, gain=3.0, mx=24),
    "sleeve":     dict(f=2.3, z=0.34, gw=0.45, cd=1.6, follow=0.7, gain=1.0, mx=25),
    "skirt":      dict(f=3.0, z=0.3, gw=0.12, cd=1.4, follow=0.6, gain=2.6, mx=34),
    "obi_tail":   dict(f=2.0, z=0.22, gw=0.50, cd=1.5, follow=0.8, gain=1.5, mx=40),
}
COLL = {  # radii in metres for the R rig (~1.55 m); clamped to 0.97 x rest distance per particle
  # group -> [(capsule from bone head, to bone tail-or-next-head, radius)]
    "hair_front": [("head@", 0.17)], "hair_side": [("head@", 0.17), ("neck", 0.06)], "hair_back": [("head@", 0.17), ("neck", 0.06)],
    "sleeve": [("chest", 0.11), ("spine", 0.10)],
    "skirt": [("thigh.L", 0.075), ("thigh.R", 0.075), ("pelvis", 0.10)],
}


def chains_of(sk):
    """list of (group, [bone names in order], anchor bone)"""
    out = []; seen = set()
    for n in sk.order:
        if n in seen: continue
        g = None
        for key in GROUPS:
            if n == key or n.startswith(key + ".") or (key == "bow" and re.match(r"bow\.[LR]\.\d", n)):
                g = key; break
        if g is None or n == "bow_knot": continue
        par = sk.parent[n]
        if par in seen or (par and any(par in ch[1] for ch in out)): continue
        ch = [n]; cur = n
        while True:
            kids = [k for k in sk.children[cur] if k not in seen and k.rsplit(".", 1)[0] == cur.rsplit(".", 1)[0]]
            if not kids: break
            cur = kids[0]; ch.append(cur)
        for b in ch: seen.add(b)
        out.append((g, ch, par))
    return out


HEAD_C = 0.45  # 'bone@' = sphere at head + 0.45 (tail - head)


def coll_geom(cb, H, T):
    if cb.endswith("@"):
        b = cb[:-1]; c = H[b] + HEAD_C * (T[b] - H[b]); return c, c
    return H[cb], T[cb]


def seg_dist(p, a, b):
    ab = b - a; t = np.clip(np.dot(p - a, ab) / (np.dot(ab, ab) + 1e-12), 0, 1); q = a + ab * t; return np.linalg.norm(p - q), q


class HeadLag:
    def __init__(self, f=2.6, z=0.32, k_up=2.2, k_fwd=1.4, k_side=1.6):
        self.w = 2 * math.pi * f; self.z = z; self.k = (k_up, k_fwd, k_side)
        self.th = np.zeros(2); self.om = np.zeros(2)

    def step(self, acc_char, dt):
        """acc_char = (right, fwd, up) acceleration of the neck base (m/s^2). returns (pitch, roll) offsets in degrees"""
        drive = np.array([self.k[0] * acc_char[2] - self.k[1] * acc_char[1], -self.k[2] * acc_char[0]])
        a = drive - self.w ** 2 * self.th - 2 * self.z * self.w * self.om
        self.om += a * dt; self.th += self.om * dt
        return self.th.copy()


class ChainSim:
    def __init__(self, sk, chains=None):
        self.sk = sk; self.chains = chains if chains is not None else chains_of(sk)
        self.state = {}
        for g, ch, anc in self.chains:
            pts = [sk.head0[ch[0]]] + [sk.tail0[b] for b in ch]
            self.state[ch[0]] = dict(x=np.array(pts, float), v=np.zeros((len(pts), 3)), T=None)
        self.rest_seg = {b: sk.tail0[b] - sk.head0[b] for g, ch, a in self.chains for b in ch}
        self.lens = {b: np.linalg.norm(v) for b, v in self.rest_seg.items()}
        # rest distances to collision capsules
        self.rd = {}
        for g, ch, a in self.chains:
            for cb, rad in COLL.get(g, []):
                if not sk.has(cb.rstrip("@")): continue
                A, B = coll_geom(cb, sk.head0, sk.tail0)
                for i, b in enumerate(ch):
                    self.rd[(b, cb)] = seg_dist(sk.tail0[b], A, B)[0]
        skirts = [ch for g, ch, a in self.chains if g == "skirt"]
        order = ["F", "FL", "L", "BL", "B", "BR", "R", "FR"]
        self.ring = []
        byk = {ch[0].split(".")[1]: ch for ch in skirts}
        ks = [k for k in order if k in byk]
        for i, k in enumerate(ks):
            a, b = byk[k], byk[ks[(i + 1) % len(ks)]]
            for j in range(min(len(a), len(b))):
                self.ring.append((a[0], b[0], j + 1, np.linalg.norm(sk.tail0[a[j]] - sk.tail0[b[j]])))

    def targets(self, g, ch, anc_D, x, P):
        """target positions for every particle given the current particle positions (chain-relative)"""
        sk = self.sk; tg = [x[0]]; dev = np.eye(3); dirs = []
        Rdrv = self.skirt_drive(ch[0]) if g == "skirt" else None
        for i, b in enumerate(ch):
            d_rest_world = nrm(self.rest_seg[b]); d = nrm(dev @ anc_D @ self.rest_seg[b])
            if Rdrv is not None: d = Rdrv @ d
            d = nrm((1 - P["gw"]) * d + P["gw"] * d_rest_world)
            tg.append(x[i] + d * self.lens[b]); dirs.append(d)
            act = nrm(x[i + 1] - x[i]); full = min_rot(d, act)
            dev = Rot.from_rotvec(Rot.from_matrix(full).as_rotvec() * P["follow"]).as_matrix() @ dev
        return np.array(tg), dirs

    PANEL_A = {"F": 0, "FL": 45, "L": 90, "BL": 135, "B": 180, "BR": 225, "R": 270, "FR": 315}
    SKIRT_KD = 0.55   # how much of the thigh flexion the front panels (extension: back panels) follow

    def skirt_drive(self, b0):
        """rotation (world) that swings a skirt panel with the thighs: front panels follow forward thigh flexion,
        back panels follow extension, side panels follow their own thigh a little (keeps stride legs out of the panels)."""
        D = getattr(self, "curD", None)
        if D is None or "thigh.L" not in D: return None
        sk = self.sk; Dp = D["pelvis"]; a = math.radians(self.PANEL_A.get(b0.split(".")[1], 0)); ca, sa = math.cos(a), math.sin(a)
        amt = 0.0
        for sd, a_s in (("L", math.pi / 2), ("R", 1.5 * math.pi)):
            v = Dp.T @ D[f"thigh.{sd}"] @ nrm(sk.tail0[f"thigh.{sd}"] - sk.head0[f"thigh.{sd}"])
            phi = math.atan2(float(np.dot(v, FWD)), float(-np.dot(v, UP)))   # + = thigh forward
            w = 0.5 * (1 + math.cos(a - a_s))
            amt += w * (max(phi, 0.0) * max(ca, 0.0) + min(phi, 0.0) * max(-ca, 0.0)) + 0.25 * w * phi * abs(sa) * (w > 0.6)
        k = np.cross(-UP, FWD)
        return Dp @ Rot.from_rotvec(k / np.linalg.norm(k) * self.SKIRT_KD * amt).as_matrix() @ Dp.T

    def step(self, D, H, T, dt, travel=0.0):
        sk = self.sk; self.curD = D
        v_air = -FWD * travel
        for g, ch, anc in self.chains:
            P = GROUPS[g]; st = self.state[ch[0]]; x, v = st["x"], st["v"]
            w = 2 * math.pi * P["f"]
            anchor = H[ch[0]]
            if st["T"] is None:  # init on the first step: start at the targets
                x[0] = anchor
                for i, b in enumerate(ch): x[i + 1] = x[i] + D[anc] @ self.rest_seg[b]
                st["T"], _ = self.targets(g, ch, D[anc], x, P); v[:] = 0
            x_old = x.copy(); x[0] = anchor
            tg, _ = self.targets(g, ch, D[anc], x, P)
            vT = (tg - st["T"]) / dt; st["T"] = tg
            acc = w * w * (tg - x) - 2 * P["z"] * w * (v - vT) - P["cd"] * (v - v_air)
            vn = v + acc * dt; xn = x + vn * dt; xn[0] = anchor
            for i, b in enumerate(ch):
                xn[i + 1] = xn[i] + nrm(xn[i + 1] - xn[i]) * self.lens[b]
            # hard cone limit around the target direction (beyond it the output saturates anyway): keeps chains stable
            lim = math.radians(1.3 * P["mx"] / P["gain"])
            _, dirs = self.targets(g, ch, D[anc], xn, P)
            for i, b in enumerate(ch):
                d_s = nrm(xn[i + 1] - xn[i]); ang = math.acos(max(-1.0, min(1.0, float(np.dot(d_s, dirs[i])))))
                if ang > lim:
                    ax = np.cross(dirs[i], d_s); ax = ax / (np.linalg.norm(ax) + 1e-12)
                    d_new = Rot.from_rotvec(ax * lim).apply(dirs[i])
                    shift = xn[i] + d_new * self.lens[b] - xn[i + 1]
                    xn[i + 1:] += shift
            self.collide(g, ch, xn, H, T)
            st["v"] = (xn - x_old) / dt; st["v"][0] = 0; st["x"] = xn
        # skirt ring coupling (soft)
        for a, b, j, d0 in self.ring:
            xa, xb = self.state[a]["x"], self.state[b]["x"]; d = xb[j] - xa[j]; L = np.linalg.norm(d)
            if L < 1e-9: continue
            corr = 0.25 * (L - d0) / L * d
            xa[j] += corr * 0.5; xb[j] -= corr * 0.5
        for g, ch, anc in self.chains:
            x = self.state[ch[0]]["x"]
            for i, b in enumerate(ch): x[i + 1] = x[i] + nrm(x[i + 1] - x[i]) * self.lens[b]

    def collide(self, g, ch, x, H, T):
        for cb, rad in COLL.get(g, []):
            if cb.rstrip("@") not in H: continue
            A, B = coll_geom(cb, H, T)
            for i, b in enumerate(ch):
                r = min(rad, 0.97 * self.rd.get((b, cb), rad))
                d, q = seg_dist(x[i + 1], A, B)
                if d < r:
                    n = nrm(x[i + 1] - q) if d > 1e-9 else nrm(np.cross(B - A, UP))
                    x[i + 1] = q + n * r

    def output(self, D, H, T):
        """bone relative rotations for every chain bone from the particles (with per-group gain exaggeration)."""
        sk = self.sk; r = {}; pts = {}; self.curD = D
        for g, ch, anc in self.chains:
            P = GROUPS[g]; x = self.state[ch[0]]["x"].copy(); x[0] = H[ch[0]]
            tg, dirs = self.targets(g, ch, D[anc], x, P)
            # exaggerate the deviation from the target direction, segment by segment
            y = [x[0]]; Dp = D[anc]
            for i, b in enumerate(ch):
                d_t = dirs[i]; d_s = nrm(x[i + 1] - x[i])
                rv = Rot.from_matrix(min_rot(d_t, d_s)).as_rotvec() * P["gain"]
                ang = np.linalg.norm(rv); mx = math.radians(P["mx"])
                if ang > mx: rv *= mx / ang
                d_f = Rot.from_rotvec(rv).apply(d_t)
                y.append(y[-1] + d_f * self.lens[b])
            y = np.array(y); self.collide(g, ch, y, H, T)
            for i, b in enumerate(ch):
                pred = Dp @ self.rest_seg[b]; Db = min_rot(pred, y[i + 1] - y[i]) @ Dp
                r[b] = Dp.T @ Db; Dp = Db
            pts[ch[0]] = y
        return r, pts
