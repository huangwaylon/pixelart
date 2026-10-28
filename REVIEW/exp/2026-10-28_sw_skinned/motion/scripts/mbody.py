"""mbody.py (M): whole-body key motion per action -> pose spec at time t (seconds).

Every action is a function spec(t) built from key curves (mcurve.pkey / okey) in the character frame. Feet are planted by IK
(world ankle targets), the pelvis bob/sway is root.loc. Overlap is phase lag (shoulder -> upper arm -> forearm -> hand) plus a
dynamic head layer (msim.HeadSpring) added later.
"""
import math, numpy as np
UPV = np.array([0.0, 0.0, 1.0])
from mcurve import pkey, okey, smooth, c, s

G = 9.81


class Gait:
    """walk / run in place (treadmill). Phase p in [0,1), left heel strike at p=0, right at 0.5."""
    def __init__(self, P, poser):
        self.P = P; self.po = poser; self.zbase = 0.0
        sk = poser.sk
        self.lg = poser.leg
        self.track = {sd: poser.leg[sd]["a0"][0] * P["track"] for sd in "LR"}

    # ---------- compass-gait pelvis height: highest z at which every stance leg still reaches (0.995 L), smoothed
    def build_geo(self, n=96, sigma=0.035):
        P = self.P; po = self.po; zs = np.zeros(n); Lm = {sd: 0.995 * (po.leg[sd]["l1"] + po.leg[sd]["l2"]) for sd in "LR"}
        self.zgeo_tab = None
        for k in range(n):
            p = k / n; sp = self.spec(p * P["T"], geo_probe=True)
            r, root, sc, (D, H, T) = po.solve(sp); best = 1e9
            for sd, off in (("L", 0.0), ("R", 0.5)):
                q = (p - off) % 1.0
                if q >= P["sf"] and not (q > 1 - P.get("geo_pre", 0.0)): continue
                A = self._ank_world(sd, sp["foot"][sd])
                hip = H[f"thigh.{sd}"]; d = A - hip; dh = d - np.dot(d, UPV) * UPV
                best = min(best, float(np.dot(d, UPV) + math.sqrt(max(0.0, Lm[sd] ** 2 - np.dot(dh, dh))) + np.dot(root, UPV)))
            zs[k] = best
        # circular gaussian smoothing (removes the cusps at double support)
        x = np.arange(n) / n; out = np.zeros(n)
        for k in range(n):
            dd = (x - x[k] + 0.5) % 1.0 - 0.5; w = np.exp(-0.5 * (dd / sigma) ** 2); out[k] = (w * zs).sum() / w.sum()
        out = np.minimum(out, zs + 0.004)  # smoothing must not lift above reach (tiny tolerance)
        self.zgeo_tab = out + P.get("geo_off", 0.0)

    def zgeo(self, p):
        n = len(self.zgeo_tab); x = (p % 1.0) * n; i = int(x) % n; f = x - int(x)
        return float(self.zgeo_tab[i] * (1 - f) + self.zgeo_tab[(i + 1) % n] * f)

    def _ank_world(self, sd, f):
        if f.get("pos") is not None: return np.asarray(f["pos"], float)
        return self.po.ankle_from_pivot(sd, f["pivot"][0], f["pivot"][1], f["pitch"], f["yaw"])

    # ---------- feet
    def stance_pitch(self, u):
        P = self.P
        return float(pkey_clamped([(0, P["strike_pitch"]), (P["flat_at"], 0.0, "flat"), (P["heel_rise"], 0.0, "flat"), (1.0, P["lift_pitch"])], u))

    def foot_stance(self, side, u):
        P = self.P; a = P["a"]; Lg = self.lg[side]
        hb = Lg["ball0"][1] - Lg["heel0"][1]
        yb = Lg["ball0"][1] + a - 2 * a * u + P.get("foot_y", 0.0)          # ball ground point (moves back with the treadmill)
        ph = self.stance_pitch(u)
        x = self.track[side] + (Lg["ball0"][0] - Lg["a0"][0])
        if ph >= 0:
            piv = ("heel", np.array([x, yb - hb, 0.0]))
        else:
            piv = ("ball", np.array([x, yb, 0.0]))
        return dict(pivot=piv, pitch=ph, toe=0.0 if ph < 0 else ph, yaw=P["toe_out"])

    def foot(self, side, q):
        P = self.P; sf = P["sf"]
        if q < sf:
            f = self.foot_stance(side, q / sf)
            f["phase"] = "stance"; return f
        u = (q - sf) / (1 - sf)
        e = 1e-3
        A0 = self._ank(side, 1.0); A1 = self._ank(side, 0.0)
        v0 = (self._ank(side, 1.0) - self._ank(side, 1.0 - e)) / e * (1 - sf) / sf
        v1 = (self._ank(side, e) - self._ank(side, 0.0)) / e * (1 - sf) / sf
        v1 = v1 * P.get("strike_vel", 1.0); v0 = v0 * P.get("lift_vel", 1.0)
        u2 = u * u; u3 = u2 * u
        A = (2 * u3 - 3 * u2 + 1) * A0 + (u3 - 2 * u2 + u) * v0 + (-2 * u3 + 3 * u2) * A1 + (u3 - u2) * v1
        dz = float(okey(P["swing_dz"], u)); dy = float(okey(P["swing_dy"], u))
        A = A + self.po.wpos([0, dy, dz])
        pitch = float(okey(P["swing_pitch"], u)); toe = float(okey(P["swing_toe"], u))
        return dict(pos=A, pitch=pitch, toe=toe, yaw=P["toe_out"], phase="swing")

    def _ank(self, side, u):
        f = self.foot_stance(side, u)
        return self.po.ankle_from_pivot(side, f["pivot"][0], f["pivot"][1], f["pitch"], f["yaw"])

    # ---------- body
    def spec(self, t, geo_probe=False):
        P = self.P; p = (t / P["T"]) % 1.0
        h = (2 * p) % 1.0                       # half-cycle phase (0 = a heel strike)
        lead = 1.0 if p < 0.5 else -1.0          # +1: left leg is the one that just struck
        # pelvis bob: lowest on the DOWN, highest on the UP
        bob = float(pkey(P["bob"], h))
        if P.get("geo") and geo_probe:
            z = 0.0
        elif P.get("geo"):
            z = self.zgeo(p) - P["dip_amp"] * float(pkey(P["dip"], h))
        else:
            z = self.zbase + P["bob_amp"] * bob
        sway = P["sway"] * c(p - P["sway_ph"])  # +: toward her left (left stance at p~0.25)
        root = [-sway, P.get("root_fwd", 0) * float(pkey(P["bob"], h - 0.1)), z]
        pel_yaw = -P["pel_yaw"] * c(p - P["pel_yaw_ph"])
        pel_roll = P["pel_roll"] * c(p - P["pel_roll_ph"])
        pel_pitch = P["pel_pitch"] + P["pel_pitch_bob"] * float(pkey(P["bob"], h - 0.05))
        ch_yaw = P["ch_yaw"] * c(p - P["ch_yaw_ph"])
        ch_roll = -P["ch_roll"] * c(p - P["pel_roll_ph"] - 0.04)
        ch_pitch = P["lean"] - P["ch_pitch_bob"] * float(pkey(P["bob"], h - P["ch_bob_lag"]))
        hd_yaw = P["hd_yaw"] * c(p - P["ch_yaw_ph"] - 0.05)
        hd_roll = P["hd_roll"] * c(p - P["pel_roll_ph"] - 0.08)
        hd_pitch = P["hd_pitch"] - P["hd_pitch_bob"] * float(pkey(P["bob"], h - P["hd_bob_lag"]))
        spec = dict(root=root, pelvis=(pel_yaw, pel_pitch, pel_roll), chest=(ch_yaw, ch_pitch, ch_roll), head=(hd_yaw, hd_pitch, hd_roll))
        # arms: left arm swings forward with the right leg (p = 0.5)
        arm, sh = {}, {}
        for side, off in (("L", 0.0), ("R", 0.5)):
            ph = p - off
            sw = float(pkey(P["arm_swing"], ph - P["lag_upper"])) - P.get("arm_lean_comp", 0.0) * ch_pitch   # +fwd, measured from world vertical
            fw_ness = float(pkey(P["arm_swing"], ph - P["lag_fore"])) / max(1e-6, P["arm_amp_ref"])
            elbow = P["elbow0"] + P["elbow_amp"] * fw_ness + P["elbow_bob"] * float(pkey(P["bob"], (2 * ph - P["lag_fore"]) % 1))
            wr = P["wrist_amp"] * (float(pkey(P["arm_swing"], ph - P["lag_hand"])) - float(pkey(P["arm_swing"], ph - P["lag_fore"]))) / max(1e-6, P["arm_amp_ref"])
            abd = P["abd0"] + P["abd_amp"] * abs(sw) / max(1e-6, P["arm_amp_ref"])
            arm[side] = dict(swing=sw, abd=abd, cross=(P["cross"] * max(0, sw) - P.get("cross_back", 0.0) * max(0, -sw)) / max(1e-6, P["arm_amp_ref"]), elbow=elbow, wrist=P["wrist0"] + wr,
                             twist=P.get("twist", 0), elbow_in=P.get("elbow_in", 0) * max(0, fw_ness))
            sh[side] = (P.get("sh_elev0", 0.0) + P["sh_elev"] * max(0.0, sw / P["arm_amp_ref"]) + P["sh_bob"] * float(pkey(P["bob"], h - 0.12)),
                        P.get("sh_fwd0", 0.0) + P["sh_fwd"] * sw / P["arm_amp_ref"])
        spec["arm"] = arm; spec["shoulder"] = sh
        feet = {}
        for side, off in (("L", 0.0), ("R", 0.5)):
            q = (p - off) % 1.0; f = self.foot(side, q)
            f["knee_yaw"] = P.get("knee_out", 0.0); feet[side] = f
        spec["foot"] = feet
        sq = float(pkey(P["bob"], h - P["sq_lag"]))
        spec["scale"] = {"chest": (1 - P["sq_chest"] * 0.5 * sq, 1 + P["sq_chest"] * sq),
                         "head": (1 - P["sq_head"] * 0.5 * float(pkey(P["bob"], h - P["sq_lag"] - 0.1)), 1 + P["sq_head"] * float(pkey(P["bob"], h - P["sq_lag"] - 0.1)))}
        spec["travel"] = 2 * P["a"] / (P["sf"] * P["T"])   # m/s (for air drag on the secondary)
        return spec


def pkey_clamped(keys, u):
    from mcurve import okey
    return okey(keys, u)


# ---------------------------------------------------------------- parameter sets
WALK = dict(
    # ROUND 2 (owner: elegant, confident, feminine; >=1 px or held; snappier with holds): poised chibi model walk
    T=0.84, frame_ms=[90, 120, 90, 120], sf=0.60, a=0.20, track=0.62, toe_out=6.0, geo=True, geo_pre=0.0, geo_off=0.0, foot_y=0.0,
    # key phases (half cycle): contact 0, DOWN .214 (held 120 ms), PASSING .5, UP .714 (held 120 ms)
    dip=[(0.0, 0.15), (0.214, 1.0), (0.5, 0.55), (0.714, 0.0, "flat"), (0.9, 0.05)], dip_amp=0.018,
    strike_pitch=18.0, flat_at=0.2, heel_rise=0.32, lift_pitch=-40.0, arm_lean_comp=0.0,
    strike_vel=0.5, lift_vel=1.0, knee_out=-3.0,
    swing_dz=[(0, 0), (0.30, 0.09), (0.62, 0.06), (1.0, 0.0)], swing_dy=[(0, 0), (0.35, -0.01), (0.75, 0.03), (1.0, 0.0)],
    swing_pitch=[(0, -40.0), (0.3, -45.0), (0.65, -18.0), (1.0, 18.0)], swing_toe=[(0, 0.0), (0.2, -25.0), (0.65, -15.0), (1.0, 18.0)],
    bob=[(0.0, -0.35), (0.214, -1.0, "flat"), (0.5, 0.2), (0.714, 1.0, "flat"), (0.9, 0.35)], bob_amp=0.026,
    sway=0.026, sway_ph=0.27, pel_yaw=6.0, pel_yaw_ph=0.02, pel_roll=5.5, pel_roll_ph=0.2, pel_pitch=2.0, pel_pitch_bob=1.0,
    ch_yaw=4.0, ch_yaw_ph=0.06, ch_roll=3.5, lean=-4.0, ch_pitch_bob=1.0, ch_bob_lag=0.08,
    hd_yaw=3.0, hd_roll=-6.0, hd_pitch=-7.0, hd_pitch_bob=2.0, hd_bob_lag=0.25,
    arm_swing=[(0.0, -20.0), (0.5, 26.0)], arm_amp_ref=26.0, lag_upper=0.04, lag_fore=0.0, lag_hand=0.13,
    elbow0=22.0, elbow_amp=26.0, elbow_bob=4.0, wrist0=10.0, wrist_amp=22.0, abd0=-16.0, abd_amp=0.0, cross=18.0, cross_back=14.0, elbow_in=10.0,
    sh_elev=3.0, sh_bob=-1.5, sh_fwd=4.0, sh_elev0=-3.0, sh_fwd0=-5.0,
    sq_chest=0.03, sq_head=0.01, sq_lag=0.04,
)

RUN = dict(
    # ROUND 2: light, springy, upright (lean from hips/ankles <= 8 deg), arms ~90 deg with an elegant swing
    T=0.56, frame_ms=[60, 80, 60, 80], frame_off=0.0, arm_lean_comp=0.7, sf=0.30, a=0.20, track=0.45, toe_out=4.0, foot_y=0.0,
    strike_pitch=10.0, flat_at=0.2, heel_rise=0.38, lift_pitch=-55.0,
    strike_vel=0.4, lift_vel=0.5,
    swing_dz=[(0, 0), (0.15, 0.17), (0.4, 0.28), (0.62, 0.28), (0.85, 0.10), (1.0, 0.0)], swing_dy=[(0, 0), (0.15, -0.06), (0.62, 0.14), (0.85, 0.09), (1.0, 0.0)],
    swing_pitch=[(0, -55.0), (0.3, -65.0), (0.7, -20.0), (1.0, 10.0)], swing_toe=[(0, 0.0), (0.25, -40.0), (0.7, -15.0), (1.0, 10.0)],
    # half cycle: contact 0, DOWN .214 (held 80 ms), push-off .5, FLIGHT .714 (held 80 ms)
    bob=[(0.0, 0.3), (0.214, -1.0, "flat"), (0.5, 0.6), (0.714, 1.0, "flat"), (0.9, 0.65)], bob_amp=0.03,
    sway=0.012, sway_ph=0.2, pel_yaw=6.0, pel_yaw_ph=0.0, pel_roll=4.0, pel_roll_ph=0.12, pel_pitch=7.0, pel_pitch_bob=1.5,
    ch_yaw=7.0, ch_yaw_ph=0.03, ch_roll=3.0, lean=8.0, ch_pitch_bob=2.0, ch_bob_lag=0.08,
    hd_yaw=-4.0, hd_roll=-5.0, hd_pitch=-7.0, hd_pitch_bob=2.0, hd_bob_lag=0.25,
    arm_swing=[(0.0, -40.0), (0.5, 48.0)], arm_amp_ref=48.0, lag_upper=0.03, lag_fore=0.0, lag_hand=0.12,
    elbow0=88.0, elbow_amp=12.0, elbow_bob=4.0, wrist0=14.0, wrist_amp=18.0, abd0=-15.0, abd_amp=0.0, cross=20.0, cross_back=16.0, elbow_in=18.0,
    sh_elev=5.0, sh_bob=-2.5, sh_fwd=6.0, sh_elev0=-2.0, sh_fwd0=-4.0,
    sq_chest=0.05, sq_head=0.025, sq_lag=0.05, knee_out=0.0,
)


def auto_base(g, n=48):
    """lower the pelvis base so no planted/landing leg over-extends (largest reach -> 0.9995 of leg length)."""
    for _ in range(6):
        worst = 0.0
        for k in range(n):
            sp = g.spec(k / n * g.P["T"]); g.po.solve(sp)
            for sd in "LR":   # only planted legs set the pelvis height; a reaching swing leg just straightens (IK clamps)
                if sp["foot"][sd].get("phase") == "stance": worst = max(worst, g.po.over_side[sd])
        if worst <= 1e-4: break
        g.zbase -= worst * 1.05
    return g.zbase


# ---------------------------------------------------------------- idle
class Idle:
    """2.4 s loop: weight on L (hold) -> transfer -> weight on R (hold) -> transfer back; 2 breaths; head tilt/look."""
    def __init__(self, poser, T=2.4):
        self.po = poser; self.T = T; self.zbase = 0.0
        L = poser.leg
        self.feet = {sd: L[sd]["a0"].copy() for sd in "LR"}
        for sd in "LR":
            self.feet[sd][0] *= 1.05  # R2: feminine stance, feet close but clearly apart (never merging)
        self.feet["L"][1] += 0.03; self.feet["R"][1] -= 0.02   # slight stagger (free foot forward)

    def w(self, t):
        """weight: +1 = on her left leg, -1 = on her right (overshoots ~10% on each settle)"""
        x = (t / self.T) % 1.0
        return float(okey([(0, 1.0), (0.22, 1.0, "flat"), (0.40, -1.07), (0.48, -0.98), (0.55, -1.0, "flat"), (0.72, -1.0, "flat"), (0.90, 1.07), (0.97, 0.99), (1.0, 1.0)], x))

    def spec(self, t):
        T = self.T; x = (t / T) % 1.0
        w = self.w(t); w_l = self.w(t - 0.12); w_ll = self.w(t - 0.25)   # upper body lags 1 frame, arms 2 frames
        br = 0.5 - 0.5 * c(2 * x - 0.08)                   # breath 0..1, 2 per loop (period 1.2 s), peaks ~ f1 / f7
        br_l = 0.5 - 0.5 * c(2 * x - 0.16)
        z = float(okey([(0, 0.005), (0.05, 0.0), (0.22, 0.0, "flat"), (0.29, -0.010), (0.335, -0.016, "flat"), (0.40, 0.007), (0.47, 0.0, "flat"),
                        (0.72, 0.0, "flat"), (0.79, -0.010), (0.835, -0.016, "flat"), (0.90, 0.007), (0.97, 0.0, "flat"), (1.0, 0.005)], x))
        root = [-0.085 * w, 0.0, self.zbase - 0.008 + z + 0.006 * br]
        pel = (-3.0 * w, 1.0, 11.0 * w)                      # stance hip up/out: tilt down toward the free side
        chest = (2.0 * w_l, -6.0 - 4.0 * br, -6.0 * w_l)     # R2: chest lifted; contrapposto counter-tilt; lifts more on the inhale
        look = float(okey([(0, 0), (0.22, 0.0, "flat"), (0.28, -4.0), (0.34, -9.0), (0.40, -15.0), (0.47, -20.0), (0.55, -17.0, "flat"), (0.74, -17.0, "flat"), (0.82, -6.0), (0.88, 2.0), (0.94, 0.0), (1.0, 0)], x))
        nod = float(okey([(0, 0), (0.30, 0.0), (0.36, 6.0), (0.46, -3.0), (0.55, 0.0), (0.8, 2.0), (0.9, -1.5), (1.0, 0)], x))
        head = (look, -7.0 + 0.6 * nod - 2.0 * br_l, 8.0 * self.w(t - 0.18) - 1.5 * w_l)   # chin slightly up; tilt toward the free hip, lags the body
        arm, sh = {}, {}
        for sd, sg in (("L", 1.0), ("R", -1.0)):
            stance = max(0.0, sg * w_ll)    # this arm's side carries the weight
            if sd == "R":   # R2: right hand rests lightly at the front of the obi (elbow soft and close)
                arm[sd] = dict(swing=2.0 + 4.0 * sg * (w_ll - w_l), abd=1.0 + 2.0 * br_l, elbow=98.0 + 4.0 * br_l, elbow_in=50.0,
                               wrist=20.0 + 6.0 * s(2 * x - 0.4), cross=0.0, wrist_out=-25.0)
            else:           # left arm relaxed along the skirt, soft wrist, sways 2 frames late
                arm[sd] = dict(swing=2.0 + 7.0 * sg * (w_ll - w_l) + 3.0 * s(2 * x - 0.3), abd=-21.0 + 4.0 * sg * w_ll + 2.0 * br_l,
                               elbow=26.0 + 6.0 * (1 - stance) + 4.0 * br_l, wrist=16.0 + 8.0 * sg * (w_ll - w_l) + 4.0 * s(2 * x - 0.4),
                               cross=0.0, wrist_out=-14.0)
            sh[sd] = (-2.0 + 7.0 * br - 2.5 * sg * w_l, -5.0)   # shoulders back and down, rise on the breath
        feet = {}
        for sd, sg in (("L", 1.0), ("R", -1.0)):
            free = max(0.0, -sg * w)  # 1 when this leg is free
            feet[sd] = dict(pos=None, pitch=-30.0 * free, toe=0.0, yaw=10.0, knee_yaw=-9.0 * free)   # free knee relaxes inward
            feet[sd]["pivot"] = ("ball", self._ballg(sd))
        sq = float(okey([(0, 0.006), (0.05, 0.0), (0.30, 0.0), (0.335, -0.03), (0.40, 0.012), (0.47, 0.0), (0.80, 0.0), (0.835, -0.03), (0.90, 0.012), (0.97, 0.0), (1.0, 0.006)], x))
        return dict(root=root, pelvis=pel, chest=chest, head=head, arm=arm, shoulder=sh, foot=feet,
                    scale={"chest": (1 + 0.02 * br - 0.6 * sq, 1 + 0.05 * br + sq), "head": (1.0, 1.0)}, travel=0.0)

    def _ballg(self, sd):
        L = self.po.leg[sd]; a = self.feet[sd]
        return np.array([a[0] + L["ball0"][0] - L["a0"][0], a[1] + L["ball0"][1] - L["a0"][1], 0.0])


# ---------------------------------------------------------------- jump (one-shot)
class Jump:
    """standing jump in place (r2). Timeline (s): 0 stand, .00-.14 crouch (anticipation), hold to .22, .26 launch in-between,
    take-off .30 (toes, arms overhead), apex ~.52 (tuck, arms up-and-out V), fall, land .74, squash .80, overshoot onto toes .90, settle 1.0-1.2."""
    T0, T1 = 0.30, 0.74     # takeoff, landing
    def __init__(self, poser):
        self.po = poser; self.zbase = 0.0
        self.feet = {sd: poser.leg[sd]["a0"].copy() for sd in "LR"}
        for sd in "LR": self.feet[sd][0] *= 0.85   # R2: feet together, graceful

    def pel_z(self, t):
        T0, T1 = self.T0, self.T1
        if t < T0:
            return float(okey([(0, -0.01), (0.05, -0.004), (0.14, -0.10), (0.22, -0.105, "flat"), (0.26, -0.02), (0.30, 0.08)], t))
        if t > T1:
            return float(okey([(T1, -0.01), (0.82, -0.12, "flat"), (0.95, 0.04), (1.03, -0.02), (1.14, -0.01)], t))
        u = (t - T0) / (T1 - T0); z0, z1, Hpk = 0.08, -0.01, 0.33
        return z0 + (z1 - z0) * u + 4 * Hpk * u * (1 - u)   # pure ballistic: fast launch, slow apex, fast fall (spacing 50/30/15)

    def spec(self, t):
        po = self.po; T0, T1 = self.T0, self.T1
        z = self.pel_z(t)
        root = [0.0, -0.02 * float(okey([(0, 0), (0.14, 1), (0.26, 1), (0.30, 0)], t)), self.zbase + z]
        lean = float(okey([(0, -4), (0.14, 10.0), (0.22, 11.0, "flat"), (0.26, 2.0), (0.30, -10.0), (0.40, -12.0), (0.46, -13.0), (0.52, -12.0), (0.60, -6.0), (0.66, 0.0),
                           (0.74, 2.0), (0.82, 6.0, "flat"), (0.95, -8.0), (1.03, 6.0), (1.14, 2.0), (1.2, 2.0)], t))
        hd = float(okey([(0, -6), (0.14, 0.0), (0.22, -1.0), (0.30, -14.0), (0.40, -12.0), (0.52, -12.0), (0.66, -4.0), (0.74, -2.0), (0.84, 2.0),
                         (0.95, -10.0), (1.03, -5.0), (1.11, -6.0), (1.2, -6.0)], t))
        spec = dict(root=root, pelvis=(0, 4 + 1.1 * max(lean, 0) + 0.9 * min(lean, 0), 0), chest=(0, lean, 0), head=(0, hd, 0), spine_mix=0.6)   # hips hinge, chest stays open
        sw = float(okey([(0, 2), (0.14, -50.0), (0.22, -58.0, "flat"), (0.26, 50.0), (0.30, 172.0), (0.36, 170.0), (0.44, 150.0), (0.52, 130.0),
                         (0.60, 120.0), (0.66, 95.0), (0.71, 70.0), (0.74, 45.0), (0.82, 10.0), (0.95, 14.0), (1.03, -6.0), (1.14, 2.0)], t))
        abd = float(okey([(0, -12), (0.14, 0), (0.30, 10), (0.44, 42), (0.52, 50), (0.60, 46), (0.68, 36), (0.74, 28), (0.82, 22), (0.95, 18), (1.03, -4), (1.14, -12)], t))
        el = float(okey([(0, 20), (0.14, 28), (0.26, 14), (0.30, 8), (0.36, 10), (0.44, 22), (0.52, 26), (0.64, 34), (0.74, 30), (0.82, 40), (0.95, 22), (1.03, 26), (1.14, 20)], t))
        wr = float(okey([(0, 6), (0.16, -20), (0.26, -30), (0.32, 25), (0.5, 15), (0.66, -15), (0.74, -10), (0.80, 25), (0.92, -8), (1.2, 6)], t))
        asym = float(okey([(0, 0), (0.30, 0.6), (0.48, 1.0), (0.66, 0.8), (0.84, 0.2), (1.0, 0)], t))   # one arm high, one lower (graceful, not twinned)
        arm = {sd: dict(swing=sw + (22 if sd == "L" else -22) * asym, abd=0.75 * abd + (6 if sd == "R" else 0), elbow=el + 8, elbow_in=10.0, wrist=wr + 8, wrist_out=-10, cross=0) for sd in "LR"}
        she = float(okey([(0, 0), (0.14, -4), (0.30, 12), (0.52, 12), (0.74, 6), (0.80, -6), (0.92, 2), (1.2, 0)], t))
        spec["arm"] = arm; spec["shoulder"] = {sd: (she, 0) for sd in "LR"}
        feet = {}
        for sd in "LR":
            if t <= T0 - 0.03 or t >= T1:
                ph = (float(okey([(0, 0), (0.22, 0, "flat"), (T0 - 0.03, -40.0)], t)) if t < T1 else
                      float(okey([(T1, -22.0), (T1 + 0.035, 0.0, "flat"), (0.86, 0.0, "flat"), (0.95, -32.0), (1.02, 0.0, "flat"), (1.2, 0.0)], t)))
                feet[sd] = dict(pivot=("ball", self._ballg(sd)), pitch=ph, toe=0.0, yaw=6.0)
            else:
                u = (t - (T0 - 0.03)) / (T1 - (T0 - 0.03))
                lift = float(okey([(0, 0.0), (0.1, 0.0), (0.3, 0.14), (0.5, 0.20), (0.68, 0.08), (0.9, 0.0, "flat"), (1.0, 0.0)], u)) + (0.05 if sd == "L" else 0.0) * float(okey([(0, 0), (0.45, 1), (0.85, 0)], u))
                fwd = float(okey([(0, 0.0), (0.45, -0.07), (0.7, -0.02), (1.0, 0.0)], u))   # lower legs sweep back at the apex (arched line) + (-0.02 if sd == "R" else 0.0) * float(okey([(0, 0), (0.5, 1), (0.9, 0)], u))
                ph = float(okey([(0, -40.0), (0.15, -55.0), (0.5, -55.0), (0.8, -35.0), (1.0, -22.0)], u))   # toes pointed in the air
                base = po.ankle_from_pivot(sd, "ball", self._ballg(sd), ph, 6.0)
                feet[sd] = dict(pos=base + po.wpos([0, fwd, max(0.0, z - 0.03) + lift]), pitch=ph, toe=ph + float(okey([(0, 0), (0.3, -10), (1, 0)], u)), yaw=6.0)
            feet[sd]["knee_yaw"] = -2.0   # knees together
        spec["foot"] = feet
        sqc = float(okey([(0, 0), (0.14, -0.04), (0.22, -0.05), (0.28, 0.05), (0.36, 0.06), (0.52, 0.02), (0.70, 0.03), (0.80, -0.06), (0.90, 0.03), (1.0, -0.01), (1.15, 0)], t))
        sqh = float(okey([(0, 0), (0.18, -0.03), (0.32, 0.03), (0.5, 0.0), (0.76, 0.0), (0.84, -0.045), (0.94, 0.025), (1.05, 0.0)], t))
        spec["scale"] = {"chest": (1 - 0.5 * sqc, 1 + sqc), "head": (1 - 0.5 * sqh, 1 + sqh)}
        spec["travel"] = 0.0
        return spec

    def _ballg(self, sd):
        L = self.po.leg[sd]; a = self.feet[sd]
        return np.array([a[0] + L["ball0"][0] - L["a0"][0], a[1] + L["ball0"][1] - L["a0"][1], 0.0])
