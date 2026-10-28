"""mrig.py (M): skeleton loading, Blender bone-matrix math, FK, quaternion helpers, stand-in skeleton.

Conventions (CONTRACT.md): Z up, character faces +Y, metres, ground Z=0.
Pose semantics (Blender): pose_world(b) = pose_world(parent) @ (B_parent^-1 @ B_b) @ L_b, B = rest matrix (vec_roll_to_mat3).
We author r_b = relative rotation in *rest armature axes* (rotation applied in the parent's frame as if the parent were at rest):
  D_b = D_parent @ r_b  (D = world delta from rest), and  L_b = B_b^-1 @ r_b @ B_b.
"""
import json, os, math
import numpy as np
try:
    from scipy.spatial.transform import Rotation as Rot
except ImportError:  # Blender's python
    Rot = None


def rodrigues(axis, ang):
    k = np.asarray(axis, float); k = k / (np.linalg.norm(k) + 1e-15); K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(os.path.dirname(HERE))
RIG_JSON = os.path.join(EXP, "rig", "rest_skeleton.json")
STANDIN = os.path.join(EXP, "motion", "standin_skeleton.json")

UP = np.array([0.0, 0.0, 1.0]); FWD = np.array([0.0, 1.0, 0.0])


def nrm(v):
    v = np.asarray(v, float); n = np.linalg.norm(v); return v / n if n > 1e-12 else v


def axang(axis, deg):
    a = nrm(axis); return Rot.from_rotvec(a * math.radians(deg)).as_matrix()


def swing(frm, to, ang_deg):
    """rotation (about axis frm x to) turning direction frm toward direction to by ang_deg."""
    ax = np.cross(frm, to)
    if np.linalg.norm(ax) < 1e-9: return np.eye(3)
    return axang(ax, ang_deg)


def min_rot(a, b):
    """minimal rotation taking unit vector a onto b."""
    a = nrm(a); b = nrm(b); ax = np.cross(a, b); s = np.linalg.norm(ax); c = float(np.dot(a, b))
    if s < 1e-10:
        if c > 0: return np.eye(3)
        p = nrm(np.cross(a, [1, 0, 0] if abs(a[0]) < 0.9 else [0, 1, 0])); return Rot.from_rotvec(p * math.pi).as_matrix()
    return Rot.from_rotvec(ax / s * math.atan2(s, c)).as_matrix()


def vec_roll_to_mat3(vec, roll):
    """Blender's vec_roll_to_mat3_normalized (armature.cc), returns 3x3 with columns = bone X, Y, Z axes."""
    x, y, z = nrm(vec)
    SAFE, CRIT = 6.1e-3, 2.5e-4
    theta = 1.0 + y; theta_alt = x * x + z * z
    M = np.zeros((3, 3))  # M[row, col]
    if theta > SAFE or theta_alt > CRIT * CRIT:
        if theta <= SAFE: theta = theta_alt * 0.5 + theta_alt * theta_alt * 0.125
        # Blender bMatrix[col][row]
        M[0, 0] = 1 - x * x / theta; M[1, 0] = -x; M[2, 0] = -x * z / theta
        M[0, 1] = x; M[1, 1] = y; M[2, 1] = z
        M[0, 2] = -x * z / theta; M[1, 2] = -z; M[2, 2] = 1 - z * z / theta
    else:
        M = np.diag([-1.0, -1.0, 1.0])
    return rodrigues(nrm(vec), roll) @ M


def quat_wxyz(M):
    q = Rot.from_matrix(M).as_quat()  # x y z w
    q = np.array([q[3], q[0], q[1], q[2]])
    if q[0] < 0: q = -q
    return [round(float(v), 6) for v in q]


def mat_from_wxyz(q):
    w, x, y, z = q; return Rot.from_quat([x, y, z, w]).as_matrix()


class Skel:
    def __init__(self, path=None):
        if path is None: path = RIG_JSON if os.path.exists(RIG_JSON) else STANDIN
        self.path = path
        d = json.load(open(path))
        d = {k: v for k, v in d.items() if not k.startswith("_")}
        self.d = d
        self.head0 = {k: np.array(v["head"], float) for k, v in d.items()}
        self.tail0 = {k: np.array(v["tail"], float) for k, v in d.items()}
        self.parent = {k: v.get("parent") for k, v in d.items()}
        self.B = {k: vec_roll_to_mat3(self.tail0[k] - self.head0[k], float(v.get("roll", 0.0))) for k, v in d.items()}
        order, seen = [], set()
        def visit(n):
            if n in seen: return
            p = self.parent[n]
            if p and p in d: visit(p)
            seen.add(n); order.append(n)
        for n in d: visit(n)
        self.order = order
        self.children = {k: [c for c in order if self.parent[c] == k] for k in d}
        # character frame: right axis from the thighs (R side)
        xr = self.head0["thigh.R"][0] - self.head0["thigh.L"][0]
        self.RIGHT = np.array([1.0 if xr > 0 else -1.0, 0, 0]); self.LEFT = -self.RIGHT
        self.side = {"L": self.LEFT, "R": self.RIGHT}

    def has(self, n): return n in self.d

    def fk(self, r, loc=(0, 0, 0), scale=None):
        """r: {bone: 3x3 relative rot (rest armature axes)}; returns D (world delta), H (head), T (tail) dicts."""
        loc = np.asarray(loc, float); scale = scale or {}
        D, H, T, S = {}, {}, {}, {}
        for n in self.order:
            p = self.parent[n]
            rn = r.get(n, np.eye(3))
            sc = scale.get(n)
            Sl = np.eye(3) if sc is None else self.B[n] @ np.diag(sc) @ self.B[n].T  # local scale in armature axes
            if p is None or p not in D:
                D[n] = rn; H[n] = self.head0[n] + loc; S[n] = Sl
            else:
                D[n] = D[p] @ rn
                H[n] = H[p] + D[p] @ S[p] @ (self.head0[n] - self.head0[p])
                S[n] = S[p] @ Sl if sc is not None else S[p]
            T[n] = H[n] + D[n] @ S[n] @ (self.tail0[n] - self.head0[n])
        return D, H, T

    def local_quat(self, n, rn):
        return quat_wxyz(self.B[n].T @ rn @ self.B[n])

    def rel_from_local(self, n, q):
        return self.B[n] @ mat_from_wxyz(q) @ self.B[n].T


def make_standin(out=STANDIN):
    """H2 armature (rigs/H2/rig_parts.blend) joints, rotated 180 deg about Z so the character faces +Y (.L = -X), cleaned to a
    connected chain, plus guessed secondary chains on the head, sleeves and skirt."""
    B = {}
    def bone(n, h, t, par, roll=0.0): B[n] = {"head": [round(float(v), 4) for v in h], "tail": [round(float(v), 4) for v in t], "roll": roll, "parent": par}
    L = -1.0  # x sign of the character's left side
    bone("root", (0, 0, 0), (0, 0.3, 0), None)
    bone("pelvis", (0, 0, 0.83), (0, 0, 0.94), "root")
    bone("spine", (0, 0, 0.94), (0, 0, 1.05), "pelvis")
    bone("chest", (0, 0, 1.05), (0, 0, 1.21), "spine")
    bone("neck", (0, 0, 1.21), (0, 0, 1.38), "chest")
    bone("head", (0, 0.0, 1.38), (0, 0.0, 1.75), "neck")
    for s, sg in (("L", L), ("R", -L)):
        hx = 0.08 * sg
        bone(f"thigh.{s}", (hx, 0.01, 0.83), (hx, 0.0, 0.447), "pelvis")
        bone(f"shin.{s}", (hx, 0.0, 0.447), (hx, -0.005, 0.19), f"thigh.{s}")
        bone(f"foot.{s}", (hx, -0.005, 0.19), (hx, 0.10, 0.035), f"shin.{s}")
        bone(f"toe.{s}", (hx, 0.10, 0.035), (hx, 0.16, 0.025), f"foot.{s}")
        bone(f"shoulder.{s}", (0.04 * sg, 0.0, 1.17), (0.18 * sg, -0.01, 1.165), "chest")
        bone(f"upper_arm.{s}", (0.18 * sg, -0.01, 1.165), (0.235 * sg, -0.0, 1.02), f"shoulder.{s}")
        bone(f"forearm.{s}", (0.235 * sg, 0.0, 1.02), (0.265 * sg, 0.01, 0.875), f"upper_arm.{s}")
        bone(f"hand.{s}", (0.265 * sg, 0.01, 0.875), (0.285 * sg, 0.015, 0.80), f"forearm.{s}")
        # bell sleeves: hang from the forearm, open below the wrist
        bone(f"sleeve.{s}.1", (0.245 * sg, -0.01, 0.99), (0.275 * sg, -0.02, 0.89), f"forearm.{s}")
        bone(f"sleeve.{s}.2", (0.275 * sg, -0.02, 0.89), (0.31 * sg, -0.03, 0.80), f"sleeve.{s}.1")
        # side locks (3)
        bone(f"hair_side.{s}.1", (0.22 * sg, 0.10, 1.66), (0.245 * sg, 0.12, 1.57), "head")
        bone(f"hair_side.{s}.2", (0.245 * sg, 0.12, 1.57), (0.25 * sg, 0.125, 1.48), f"hair_side.{s}.1")
        bone(f"hair_side.{s}.3", (0.25 * sg, 0.125, 1.48), (0.245 * sg, 0.12, 1.40), f"hair_side.{s}.2")
        # bow lobes from the knot (back-top of the head)
        bone(f"bow.{s}.1", (0.03 * sg, -0.17, 1.88), (0.11 * sg, -0.18, 1.92), "bow_knot")
        bone(f"bow.{s}.2", (0.11 * sg, -0.18, 1.92), (0.18 * sg, -0.18, 1.90), f"bow.{s}.1")
    for c, x in (("L", 0.10 * L), ("C", 0.0), ("R", -0.10 * L)):
        bone(f"hair_front.{c}.1", (x, 0.17, 1.76), (x * 1.1, 0.25, 1.68), "head")
        bone(f"hair_front.{c}.2", (x * 1.1, 0.25, 1.68), (x * 1.15, 0.275, 1.60), f"hair_front.{c}.1")
    bone("hair_back.1", (0, -0.20, 1.70), (0, -0.25, 1.60), "head")
    bone("hair_back.2", (0, -0.25, 1.60), (0, -0.26, 1.50), "hair_back.1")
    bone("hair_back.3", (0, -0.26, 1.50), (0, -0.24, 1.41), "hair_back.2")
    bone("bun", (0, -0.15, 1.86), (0, -0.20, 1.96), "head")
    bone("bow_knot", (0, -0.16, 1.87), (0, -0.19, 1.90), "head")
    # skirt: 8 panels, waist ring r .13 @ .93, mid r .19 @ .80, hem r .25 @ .66 (flared)
    dirs = {"F": 0, "FL": 45, "L": 90, "BL": 135, "B": 180, "BR": 225, "R": 270, "FR": 315}  # deg from front toward her left
    for k, a in dirs.items():
        t = math.radians(a); v = np.array([L * math.sin(t), math.cos(t), 0.0])
        depth = 0.85 + 0.15 * abs(math.cos(t))  # skirt slightly shallower front/back
        p0 = v * 0.12 * depth + [0, 0, 0.93]; p1 = v * 0.185 * depth + [0, 0, 0.80]; p2 = v * 0.245 * depth + [0, 0, 0.665]
        bone(f"skirt.{k}.1", p0, p1, "pelvis"); bone(f"skirt.{k}.2", p1, p2, f"skirt.{k}.1")
    B["_doc"] = "M stand-in (H2 joints, faces +Y, .L=-X). Replace by rig/rest_skeleton.json when R exports it."
    json.dump(B, open(out, "w"), indent=1)
    return out


if __name__ == "__main__":
    print(make_standin()); s = Skel(STANDIN); print(len(s.order), "bones; RIGHT", s.RIGHT)
    # self-test: local quat round trip
    rr = {n: Rot.random(random_state=i).as_matrix() for i, n in enumerate(s.order)}
    for n in s.order:
        q = s.local_quat(n, rr[n]); assert np.allclose(s.rel_from_local(n, q), rr[n], atol=1e-5)
    print("roundtrip ok")
