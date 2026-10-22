"""Skeleton, semantic pose resolution (incl. leg IK + squash), and deterministic secondary-motion sim."""
import copy
import math
import numpy as np

from .mathutil import translate, scale, euler, xform_point, align_y_to

ISO_ELEVATION = math.degrees(math.atan(0.5))  # 26.565 deg, 2:1 dimetric
COS_E = math.cos(math.radians(ISO_ELEVATION))
AIR_SQUASH_PIVOT = 15.0   # airborne squash/stretch happens around body centre, grounded around feet
HEAD_SQUASH_KEEP = 0.5    # head receives only half the squash so the face stays appealing
SIM_DT = 0.005            # fixed 5 ms step; all frame durations are multiples of 10 ms


def deep_merge(base, over):
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


class Rig:
    def __init__(self, character):
        self.char = character
        self.bones = character["bones"]
        self.bone_index = {b["name"]: b for b in self.bones}
        self.head_bones = set(character.get("head_bones", ["head"]))
        b = self.bone_index
        self.thigh_len = -b["knee_L"]["offset"][1]
        self.shin_len = -b["ankle_L"]["offset"][1]

    # ------------------------------------------------------------------ pose
    def resolve(self, pose):
        """Semantic pose -> flat channel dict of bone eulers + root params (all floats, interpolatable)."""
        ch = {}
        z_world = pose["z_px"] / COS_E
        ch["z_world"] = z_world
        ch["pelvis_y"] = self.bone_index["pelvis"]["offset"][1] - pose["pelvis_drop"]
        ch["squash"] = pose["squash"]
        ch["squash_pivot"] = 0.0 if pose["plant"] else AIR_SQUASH_PIVOT

        sp, hd = pose["spine"], pose["head"]
        ch["spine"] = [sp["tilt"] * 0.5, sp["turn"] * 0.5, sp["lean"] * 0.5]
        ch["chest"] = [sp["tilt"] * 0.5, sp["turn"] * 0.5, sp["lean"] * 0.5]
        ch["neck"] = [0.0, 0.0, 0.0]
        ch["head"] = [hd["tilt"], hd["turn"], hd["roll"]]
        for side, sgn in (("L", 1), ("R", -1)):
            a = pose["arm_" + side]
            ch["shoulder_" + side] = [-a["raise"], 0.0, sgn * a["spread"]]
            ch["elbow_" + side] = [-a["elbow"], 0.0, 0.0]
            ch["hand_" + side] = [0.0, 0.0, 0.0]
        for side, sgn in (("L", 1), ("R", -1)):
            if pose["plant"]:
                hip, knee, ankle = self._leg_ik(side, ch["pelvis_y"])
            else:
                lg = pose["leg_" + side]
                hip, knee = -lg["hip"], lg["knee"]
                ankle = -(hip + knee) * 0.5 + lg["ankle"]
            spread = pose["leg_" + side].get("spread", 0)
            ch["hip_" + side] = [hip, 0.0, sgn * spread]
            # planted feet: counter-rotate the knee by 2x the hip spread so knees move in/out but the ankle stays
            # under the hip (thigh == shin length) -> pigeon-toe / knees-together poses keep 0 foot slide
            knee_z = -2.0 * sgn * spread if pose["plant"] else 0.0
            ch["knee_" + side] = [knee, 0.0, knee_z]
            ch["ankle_" + side] = [ankle, 0.0, 0.0]
        ch["root"] = [0.0, 0.0, 0.0]
        ch["pelvis"] = [0.0, 0.0, 0.0]
        return ch

    def _leg_ik(self, side, pelvis_y):
        """2-bone IK in the sagittal plane keeping the ankle at its rest spot on the ground."""
        hip_y = pelvis_y + self.bone_index["hip_" + side]["offset"][1]
        ankle_y = self.bone_index["pelvis"]["offset"][1] + self.bone_index["hip_" + side]["offset"][1] \
            - self.thigh_len - self.shin_len
        dy = hip_y - ankle_y
        dz = 0.0
        L1, L2 = self.thigh_len, self.shin_len
        D = min(max(math.hypot(dy, dz), 0.5), L1 + L2 - 1e-6)
        cos_knee = (L1 * L1 + L2 * L2 - D * D) / (2 * L1 * L2)
        knee_bend = math.pi - math.acos(max(-1, min(1, cos_knee)))
        a0 = math.atan2(dz, dy)
        a1 = math.acos(max(-1, min(1, (L1 * L1 + D * D - L2 * L2) / (2 * L1 * D))))
        flex = math.degrees(a0 + a1)
        rx_h, rx_k = -flex, math.degrees(knee_bend)
        return rx_h, rx_k, -(rx_h + rx_k)

    @staticmethod
    def blend(chans, weights):
        out = {}
        for k in chans[0]:
            if isinstance(chans[0][k], list):
                out[k] = [sum(w * c[k][i] for c, w in zip(chans, weights)) for i in range(3)]
            else:
                out[k] = sum(w * c[k] for c, w in zip(chans, weights))
        return out

    # ------------------------------------------------------------ transforms
    def world(self, ch, include_height=True):
        """Bone -> 4x4 world matrix in canonical facing (+Z), with squash and optional jump height."""
        local = {}
        for b in self.bones:
            off = list(b["offset"])
            if b["name"] == "pelvis":
                off[1] = ch["pelvis_y"]
            rx, ry, rz = ch.get(b["name"], [0, 0, 0])
            local[b["name"]] = translate(*off) @ euler(rx, ry, rz)
        raw = {}
        for b in self.bones:
            p = b["parent"]
            raw[b["name"]] = local[b["name"]] if p is None else raw[p] @ local[b["name"]]

        s = ch["squash"]
        piv = ch["squash_pivot"]
        sq = translate(0, piv, 0) @ scale(1 / math.sqrt(s), s, 1 / math.sqrt(s)) @ translate(0, -piv, 0)
        hs = s ** HEAD_SQUASH_KEEP
        head_sq = scale(1 / math.sqrt(hs), hs, 1 / math.sqrt(hs))
        lift = translate(0, ch["z_world"] if include_height else 0.0, 0)

        # Planted feet must not slide: legs only receive the vertical part of the squash.
        planted = piv < 1e-6
        leg_sq = translate(0, piv, 0) @ scale(1, s, 1) @ translate(0, -piv, 0) if planted else sq
        out = {}
        for name, m in raw.items():
            if name.split("_")[0] in ("hip", "knee", "ankle"):
                out[name] = lift @ leg_sq @ m
            elif self._is_head(name):
                origin = m[:3, 3]
                new_origin = xform_point(sq, origin)
                out[name] = lift @ translate(*new_origin) @ head_sq @ translate(*(-origin)) @ m
            else:
                out[name] = lift @ sq @ m
        return out

    def _is_head(self, name):
        while name is not None:
            if name in self.head_bones:
                return True
            name = self.bone_index[name]["parent"]
        return False


# ---------------------------------------------------------------- animation
class Animation:
    def __init__(self, anim, rig):
        self.anim = anim
        self.rig = rig
        rest = anim["rest"]
        self.poses = [deep_merge(rest, {k: v for k, v in f.items() if k in rest}) for f in anim["frames"]]
        self.rest_ch = rig.resolve(rest)
        self.keys = [rig.resolve(p) for p in self.poses]
        self.times = []
        t = 0
        for f in anim["frames"]:
            self.times.append(t)
            t += f["ms"]
        self.total_ms = t

    def channels_at(self, t_ms):
        """Smooth (Catmull-Rom) interpolation between key poses; holds rest before start / after end."""
        lead = self.anim.get("qa", {}).get("lead_in_ms", 40)
        if t_ms <= 0:
            if t_ms <= -lead:
                return self.rest_ch
            u = (t_ms + lead) / lead
            u = u * u * (3 - 2 * u)          # ease rest -> first key so chains don't jerk on frame 1
            return Rig.blend([self.rest_ch, self.keys[0]], [1 - u, u])
        times = self.times + [self.total_ms]
        keys = self.keys + [self.rest_ch]
        if t_ms >= self.total_ms:
            return self.rest_ch
        i = max(j for j in range(len(times)) if times[j] <= t_ms)
        u = (t_ms - times[i]) / (times[i + 1] - times[i])
        p0 = keys[max(i - 1, 0)]
        p1, p2 = keys[i], keys[i + 1]
        p3 = keys[min(i + 2, len(keys) - 1)]
        u2, u3 = u * u, u * u * u
        w = [(-u3 + 2 * u2 - u) / 2, (3 * u3 - 5 * u2 + 2) / 2, (-3 * u3 + 4 * u2 + u) / 2, (u3 - u2) / 2]
        return Rig.blend([p0, p1, p2, p3], w)


# ---------------------------------------------------------------- secondary
class ChainSim:
    """Verlet chains (scarf, braids, pom) simulated once in canonical space at a fixed timestep.
    Deterministic: no randomness, fixed dt, fixed iteration counts."""

    def __init__(self, rig, animation):
        self.rig = rig
        self.anim = animation
        self.chains = rig.char.get("chains", [])
        self.colliders = rig.char.get("colliders", [])
        sim = rig.char.get("sim", {})
        # body_collide: chains collide with the real body ellipsoids (coat, arms, legs, head) -> no penetration
        self.body_collide = sim.get("body_collide", False)
        self.collide_groups = set(sim.get("collide_groups", ["torso", "arm_L", "arm_R", "leg_L", "leg_R", "head"]))

    def _anchor_and_rest(self, chain, worlds):
        m = worlds[chain["anchor_bone"]]
        a = xform_point(m, chain["anchor"])
        d = m[:3, :3] @ np.asarray(chain["rest_dir"], float)
        d /= np.linalg.norm(d)
        rest = [a + d * chain["seg_len"] * i for i in range(chain["segments"] + 1)]
        return a, rest

    def run(self, sample_times_ms):
        pre = self.anim.anim.get("preroll_ms", 1000)
        t = -pre
        worlds = self.rig.world(self.anim.channels_at(t))
        state = {}
        for c in self.chains:
            _, rest = self._anchor_and_rest(c, worlds)
            state[c["name"]] = (np.array(rest), np.array(rest))
        samples = {}
        targets = sorted(set(sample_times_ms))
        ti = 0
        end = max(targets) if targets else 0
        steps = int(round((end + pre) / (SIM_DT * 1000)))
        for step in range(steps + 1):
            t = -pre + step * SIM_DT * 1000
            while ti < len(targets) and abs(targets[ti] - t) < 1e-6:
                samples[targets[ti]] = {k: v[0].copy() for k, v in state.items()}
                ti += 1
            worlds = self.rig.world(self.anim.channels_at(t + SIM_DT * 1000))
            cols = [(xform_point(worlds[c["bone"]], c["center"]), c["radius"]) for c in self.colliders]
            body = []
            if self.body_collide:
                for bp in body_primitives(self.rig, worlds):
                    if bp["group"] in self.collide_groups and bp["material"] != "scarf":
                        M3, tr = bp["M"][:3, :3], bp["M"][:3, 3]
                        body.append((bp["name"], M3, np.linalg.inv(M3), tr, np.linalg.norm(M3, axis=0).min()))
            for c in self.chains:
                cur, prev = state[c["name"]]
                anchor, rest = self._anchor_and_rest(c, worlds)
                rest = np.array(rest)
                acc = np.zeros_like(cur)
                acc[:, 1] -= c["gravity"]
                acc += c["stiffness"] * (rest - cur)
                nxt = cur + (cur - prev) * (1 - c["damping"]) + acc * SIM_DT * SIM_DT
                nxt[0] = anchor
                L = c["seg_len"]
                for _ in range(6):
                    for i in range(len(nxt) - 1):
                        d = nxt[i + 1] - nxt[i]
                        n = np.linalg.norm(d)
                        if n < 1e-9:
                            continue
                        corr = d * (1 - L / n)
                        if i == 0:
                            nxt[i + 1] -= corr
                        else:
                            nxt[i] += corr * 0.5
                            nxt[i + 1] -= corr * 0.5
                    for i in range(1, len(nxt)):
                        for cc, r in cols:
                            rr = r + c.get("thickness", 1.0) * 0.5
                            v = nxt[i] - cc
                            dist = np.linalg.norm(v)
                            if dist < rr and dist > 1e-9:
                                nxt[i] = cc + v / dist * rr
                    if body and c.get("collide", True):
                        self._collide_body(c, nxt, body, anchor)
                        # the ground is solid too: nothing hangs through the floor (feet are at y=0 when grounded)
                        floor = worlds["root"][1, 3] + c.get("thickness", 1.0) * 0.5 + 0.4
                        nxt[1:, 1] = np.maximum(nxt[1:, 1], floor)
                    if c.get("max_swing"):
                        self._limit_swing(c, nxt, rest)
                state[c["name"]] = (nxt, cur)
        return samples


    def _collide_body(self, chain, pts, body, anchor):
        """Push chain points (and segment midpoints) out of every body ellipsoid that doesn't contain the anchor."""
        margin = max(max(chain.get("widths", [1.0])), chain.get("thickness", 1.0)) * 0.5 + 0.3   # ribbon half-width
        for name, M3, Mi, tr, rmin in body:
            la = Mi @ (anchor - tr)
            if la @ la < 1.15:                       # the chain is rooted in/at this part (e.g. scarf on the neck)
                continue
            lim = 1.0 + margin / rmin
            for i in range(1, len(pts)):
                for q in (pts[i], (pts[i] + pts[i - 1]) * 0.5):
                    loc = Mi @ (q - tr)
                    d = float(np.sqrt(loc @ loc))
                    if 1e-9 < d < lim:
                        push = M3 @ (loc / d * lim) + tr - q
                        pts[i] += push if q is pts[i] else push * 0.5

    @staticmethod
    def _limit_swing(chain, pts, rest):
        """Keep each segment within max_swing degrees of its rest direction (consistent side/angle)."""
        lim = math.radians(chain["max_swing"])
        for i in range(1, len(pts)):
            seg = pts[i] - pts[i - 1]
            L = np.linalg.norm(seg)
            r = rest[i] - rest[i - 1]
            rn = np.linalg.norm(r)
            if L < 1e-9 or rn < 1e-9:
                continue
            u, d = seg / L, r / rn
            c = float(np.clip(u @ d, -1, 1))
            if math.acos(c) > lim:
                perp = u - c * d
                pn = np.linalg.norm(perp)
                perp = perp / pn if pn > 1e-9 else np.array([1.0, 0, 0])
                pts[i] = pts[i - 1] + (math.cos(lim) * d + math.sin(lim) * perp) * L


def chain_primitives(chain, pts, body_center):
    """Render primitives for one simulated chain (points in canonical space)."""
    prims = []
    widths = chain.get("widths", [1.0])
    if chain.get("draw_segments", True):
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            mid = (a + b) / 2
            seg = b - a
            out = mid - body_center
            out[1] = 0
            hint = out if np.linalg.norm(out) > 1e-6 else np.array([0, 0, 1.0])
            R = align_y_to(seg, hint)
            w = widths[min(i, len(widths) - 1)]
            half = np.linalg.norm(seg) / 2 + 0.7
            M = translate(*mid) @ R @ scale(w, half, chain.get("thickness", 1.0))
            prims.append({"name": f'{chain["name"]}_{i}', "M": M, "material": chain["material"],
                          "group": chain.get("group", chain["name"])})
    tip = chain.get("tip")
    if tip:
        r = tip["radius"]
        M = translate(*pts[-1]) @ scale(r, r, r)
        prims.append({"name": chain["name"] + "_tip", "M": M, "material": tip["material"], "group": chain["name"]})
    return prims


def body_primitives(rig, worlds):
    prims = []
    for p in rig.char["primitives"]:
        M = worlds[p["bone"]] @ translate(*p["center"]) @ euler(*p.get("rot", [0, 0, 0])) @ scale(*p["radii"])
        prims.append({"name": p["name"], "M": M, "material": p["material"], "group": p.get("group", p["bone"]),
                      "clip_all": p.get("clip_all", []), "clip_any": p.get("clip_any", [])})
    return prims
