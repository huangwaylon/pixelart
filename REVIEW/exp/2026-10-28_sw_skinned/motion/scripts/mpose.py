"""mpose.py (M): turn a high-level pose spec into per-bone relative rotations (rest armature axes) + FK.

Spec (all angles in degrees, character axes: RIGHT, FWD=+Y, UP=+Z):
  root:   [x_right, y_fwd, z_up] translation (metres) of the whole body (feet are IK-planted, so this is the pelvis bob/sway)
  pelvis/chest/head: (yaw +left, pitch +forward, roll +toward her right)  WORLD orientation
  spine_mix, neck_mix: where the spine/neck sit between pelvis/chest and chest/head (0.5)
  shoulder[s] = (elev +up, fwd +forward)
  arm[s] = dict(swing +fwd, abd +out, cross +inward(yaw of swing plane), elbow flex +, wrist flex +fwd, wrist_out)
  foot[s] = dict(pos=world ankle target or None, pivot=('heel'|'ball'|'toe', world xyz), pitch +toes-up, toe (world toe pitch), yaw +out, knee_yaw)
  scale = {bone: (s_side, s_along)}
"""
import numpy as np, math
from mrig import axang, swing, min_rot, nrm, UP, FWD


def slerp_m(A, B, t):
    from scipy.spatial.transform import Rotation as R, Slerp
    r = R.from_matrix(np.stack([A, B])); return Slerp([0, 1], r)([t]).as_matrix()[0]


HEAD_PITCH_MIN = -2.0   # deg (+ = chin down)
NECK_FWD = 4.0         # deg, natural forward neck angle


class Poser:
    def __init__(self, sk):
        self.sk = sk; s = sk
        self.RIGHT = s.RIGHT; self.LEFT = s.LEFT
        self.YAW = np.cross(FWD, self.LEFT)       # +yaw turns front toward her left
        self.PITCH = np.cross(UP, FWD)            # +pitch leans an up-bone forward
        self.ROLL = np.cross(UP, self.RIGHT)      # +roll tilts an up-bone toward her right
        self.TOEUP = np.cross(FWD, UP)            # +pitch lifts the toes (foot bones)
        self.leg = {}
        for side in "LR":
            h0 = s.head0[f"thigh.{side}"]; k0 = s.head0[f"shin.{side}"]; a0 = s.head0[f"foot.{side}"]
            ball0 = s.head0[f"toe.{side}"]; tip0 = s.tail0[f"toe.{side}"]
            heel0 = np.array([a0[0], a0[1] - 0.035, 0.0]); ballg0 = np.array([ball0[0], ball0[1], 0.0]); tipg0 = np.array([tip0[0], tip0[1], 0.0])
            self.leg[side] = dict(h0=h0, k0=k0, a0=a0, l1=np.linalg.norm(k0 - h0), l2=np.linalg.norm(a0 - k0),
                                  heel0=heel0, ball0=ballg0, tip0=tipg0)
        self.overreach = 0.0

    def W(self, ypr, lean_yaw=0.0):
        """lean_yaw (deg, + toward her left): the pitch (lean) axis is turned about UP, so the lean tips toward a direction other
        than straight forward. Used as a per-view cheat so a forward lean reads on screen in 3/4 views."""
        y, p, r = ypr
        pa = self.PITCH if not lean_yaw else axang(UP, lean_yaw * (1 if np.dot(self.YAW, UP) > 0 else -1)) @ self.PITCH
        return axang(self.YAW, y) @ axang(pa, p) @ axang(self.ROLL, r)

    def wpos(self, v):
        v = np.asarray(v, float); return v[0] * self.RIGHT + v[1] * FWD + v[2] * UP

    def foot_rot(self, pitch, yaw, side):
        out = self.RIGHT if side == "R" else self.LEFT
        yawm = axang(UP, yaw * (1 if np.dot(np.cross(FWD, out), UP) > 0 else -1))  # +yaw = toe out
        return yawm @ axang(self.TOEUP, pitch), yawm

    def ankle_from_pivot(self, side, pivot_kind, pivot_w, pitch, yaw):
        Lg = self.leg[side]; Df, _ = self.foot_rot(pitch, yaw, side)
        p0 = {"heel": Lg["heel0"], "ball": Lg["ball0"], "toe": Lg["tip0"]}[pivot_kind]
        return np.asarray(pivot_w, float) - Df @ (p0 - Lg["a0"])

    def solve(self, spec):
        sk = self.sk; r = {}
        ly = spec.get("lean_yaw", 0.0)
        hy, hp, hr = spec.get("head", (0, 0, 0)); hp = max(hp, HEAD_PITCH_MIN)   # R5: never chin-up / head tipped back
        Wp = self.W(spec.get("pelvis", (0, 0, 0)), ly); Wc = self.W(spec.get("chest", (0, 0, 0)), ly); Wh = self.W((hy, hp, hr))
        Ws = slerp_m(Wp, Wc, spec.get("spine_mix", 0.5)); Wn = slerp_m(Wc, Wh, spec.get("neck_mix", 0.45))
        # R5: the neck angles naturally forward (the head keeps its own world orientation); more if the chest leans back,
        # so the skull centre always sits over / ahead of the neck base in profile
        cp = math.degrees(math.atan2(float(np.dot(Wc @ UP, FWD)), float(np.dot(Wc @ UP, UP))))
        nf = spec.get("neck_fwd", NECK_FWD) + max(0.0, -cp) * 0.9
        Wn = axang(self.PITCH, nf) @ Wn
        r["pelvis"] = Wp; r["spine"] = Wp.T @ Ws; r["chest"] = Ws.T @ Wc; r["neck"] = Wc.T @ Wn; r["head"] = Wn.T @ Wh
        for side in "LR":
            out = self.side_vec(side)
            if sk.has(f"shoulder.{side}"):
                el, fw = spec.get("shoulder", {}).get(side, (0, 0))
                d0 = sk.tail0[f"shoulder.{side}"] - sk.head0[f"shoulder.{side}"]
                r[f"shoulder.{side}"] = swing(d0, UP, el) @ swing(d0, FWD, fw)
            a = spec.get("arm", {}).get(side, {})
            ud = nrm(sk.tail0[f"upper_arm.{side}"] - sk.head0[f"upper_arm.{side}"])
            fd = nrm(sk.tail0[f"forearm.{side}"] - sk.head0[f"forearm.{side}"])
            hd = nrm(sk.tail0[f"hand.{side}"] - sk.head0[f"hand.{side}"])
            inward = -out
            fwd_sw = axang(UP, a.get("cross", 0) * (1 if np.dot(np.cross(FWD, inward), UP) > 0 else -1)) @ FWD  # swing plane yawed inward
            Rabd = swing(ud, out, a.get("abd", 0)); ud1 = Rabd @ ud
            Rsw = axang(np.cross(-UP, fwd_sw), a.get("swing", 0))   # shoulder flexion about the (yawed) lateral axis: sagittal swing
            r[f"upper_arm.{side}"] = Rsw @ Rabd @ axang(ud, a.get("twist", 0))
            r[f"forearm.{side}"] = swing(fd, FWD, a.get("elbow", 0)) @ swing(fd, inward, a.get("elbow_in", 0))
            r[f"hand.{side}"] = swing(hd, FWD, a.get("wrist", 0)) @ swing(hd, out, a.get("wrist_out", 0))
        sc = {}
        for b, v in spec.get("scale", {}).items():
            if sk.has(b): sc[b] = [v[0], v[1], v[0]]
        root = self.wpos(spec.get("root", (0, 0, 0)))
        D, H, T = sk.fk(r, root, sc)
        # legs: analytic 2-bone IK in world space
        self.overreach = 0.0; self.over_side = {}
        for side in "LR":
            f = spec["foot"][side]; Lg = self.leg[side]
            Df, yawm = self.foot_rot(f.get("pitch", 0), f.get("yaw", 0), side)
            A = np.asarray(f["pos"], float) if f.get("pos") is not None else self.ankle_from_pivot(side, f["pivot"][0], f["pivot"][1], f.get("pitch", 0), f.get("yaw", 0))
            Hh = H[f"thigh.{side}"]; l1, l2 = Lg["l1"], Lg["l2"]
            d = A - Hh; dist = np.linalg.norm(d); dn = d / dist
            mx = 0.9995 * (l1 + l2); self.overreach = max(self.overreach, dist - mx); self.over_side[side] = dist - mx
            dist_c = min(max(dist, 0.25 * (l1 + l2)), mx)
            out_s = self.side_vec(side); ksg = 1 if np.dot(np.cross(FWD, out_s), UP) > 0 else -1
            pole = axang(UP, ksg * f.get("knee_yaw", 0)) @ FWD   # +knee_yaw = knee points outward (both sides)
            pole = Wp @ pole if f.get("knee_follow_pelvis", True) else pole
            fp = nrm(pole - np.dot(pole, dn) * dn)
            ca = (l1 * l1 + dist_c * dist_c - l2 * l2) / (2 * l1 * dist_c); ca = min(1, max(-1, ca))
            K = Hh + dn * l1 * ca + fp * l1 * math.sqrt(1 - ca * ca)
            A_eff = Hh + dn * dist_c
            N1 = nrm(np.cross(fp, dn))
            dn0 = nrm(Lg["a0"] - Lg["h0"]); fp0 = nrm(FWD - np.dot(FWD, dn0) * dn0); N0 = nrm(np.cross(fp0, dn0))
            def frame(dv, n):
                dv = nrm(dv); n = nrm(n - np.dot(n, dv) * dv); return np.stack([dv, n, np.cross(dv, n)], 1)
            Dth = frame(K - Hh, N1) @ frame(Lg["k0"] - Lg["h0"], N0).T
            Dsh = frame(A_eff - K, N1) @ frame(Lg["a0"] - Lg["k0"], N0).T
            Dtoe = yawm @ axang(self.TOEUP, f.get("toe", f.get("pitch", 0)))
            r[f"thigh.{side}"] = D["pelvis"].T @ Dth
            r[f"shin.{side}"] = Dth.T @ Dsh
            r[f"foot.{side}"] = Dsh.T @ Df
            if sk.has(f"toe.{side}"): r[f"toe.{side}"] = Df.T @ Dtoe
        D, H, T = sk.fk(r, root, sc)
        return r, root, sc, (D, H, T)

    def side_vec(self, side): return self.RIGHT if side == "R" else self.LEFT
