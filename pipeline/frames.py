"""Compose a frame for (direction, frame): body + chains -> pixels -> outline -> face -> overrides."""
import hashlib
import json
import os

import numpy as np

from .mathutil import rot_y, translate, xform_point
from .rig import Rig, Animation, ChainSim, body_primitives, chain_primitives
from .render import (render_pixels, add_outline, remove_lone_pixels, despeckle, DIRECTION_YAW, Camera,
                     pixel_perfect_outline, selout_outline, regularize_silhouette)
from .face import apply_face, apply_face_cels
from .pixelrules import apply_rules, apply_post_outline, pom_cel, angel_ring, ALL_RULES, POST_OUTLINE_RULES
from .fx import shadow_frame, fx_frames


def idx_hash(idx):
    return hashlib.sha1(np.ascontiguousarray(idx.astype(np.int16)).tobytes()).hexdigest()[:16]


class Scene:
    """Everything needed to render one animation; built once per build."""

    def __init__(self, character, anim, palette):
        self.char, self.anim_data, self.palette = character, anim, palette
        self.rig = Rig(character)
        self.anim = Animation(anim, self.rig)
        self.size = tuple(anim["frame_size"])
        self.pivot = tuple(anim["pivot"])
        self.dirs = anim["directions"]
        # Character camera may be a few degrees lower than the 2:1 world camera so faces read (AD/GD call).
        rnd = character.get("render", {})
        self.cam = Camera(rnd.get("camera_elevation", 26.565), rnd.get("ppu", 1.0))
        extra = [self.anim.total_ms] if anim.get("loop") else []
        self.chains = ChainSim(self.rig, self.anim).run(self.anim.times + extra)
        # resolve shared prop references once, so metadata/frame info/rendering all see the full definition
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        resolved = []
        for pr in anim.get("props", []):
            if pr.get("ref"):
                with open(os.path.join(root, "data", "props", f"{pr['ref']}.json")) as fh:
                    pr = dict(json.load(fh), **{k: v for k, v in pr.items() if k != "ref"}, ref=pr["ref"])
            resolved.append(pr)
        if resolved:
            self.anim_data = dict(anim, props=resolved)
        self.deliberate = {}    # (dir, frame) -> {(y, x)} designed 1-2px elements (e.g. boot soles) for QA
        self.body_bbox = {}     # (dir, frame) -> bbox of body pixels (excl. pom/scarf/hair chains) for QA
        self.events = [(ev, self.anim.times[i]) for i, f in enumerate(anim["frames"]) for ev in f.get("events", [])]
        # "model": "hd" -> SDF parts + sphere tracing (pipeline/sdf.py); legacy variants keep the analytic raycaster
        self.model = character.get("model", "legacy")
        self.tracer = None
        if self.model == "hd":
            from . import sdf
            self.tracer = sdf

    def frame_info(self, i):
        f = self.anim_data["frames"][i]
        pose = self.anim.poses[i]
        return {"index": i, "name": f["name"], "duration_ms": f["ms"], "z_px": self.z_px(i),
                "phase": f.get("phase", ""), "events": f.get("events", []),
                "cancelable": bool(f.get("cancelable", False)), "face": pose["face"],
                "root_px": f.get("root_px", [0, 0]),
                "props": [pr["name"] for pr in self.anim_data.get("props", []) if pr.get("frames", "all") == "all"
                          or f["name"] in pr.get("frames", []) or i in pr.get("frames", [])],
                "planted": bool(pose["plant"])}

    def z_px(self, i):
        return int(round(self.anim.poses[i]["z_px"] * self.cam.ppu))

    def primitives(self, i, direction, in_place=True, lod="all"):
        """Posed render primitives. `lod` ("all" sprites | "ref" hi-res refs) only affects HD parts."""
        ch = self.anim.keys[i]
        worlds = self.rig.world(ch, include_height=True)
        drop = translate(0, -ch["z_world"], 0) if in_place else np.eye(4)
        face_m = rot_y(DIRECTION_YAW[direction]) @ drop
        if self.tracer is not None:
            body_c = xform_point(worlds["spine"], [0, 0, 0])
            parts = self.tracer.pose_parts(self.char, worlds, self.chains[self.anim.times[i]], body_c, face_m, lod=lod,
                                           subdiv=self.char.get("render", {}).get("smooth_chains", 1))
            props = self._prop_prims(i, worlds)
            for p in props:
                p["M"] = face_m @ p["M"]
            return parts + self.tracer.legacy_to_parts(props), {k: face_m @ v for k, v in worlds.items()}
        prims = body_primitives(self.rig, worlds)
        body_c = xform_point(worlds["spine"], [0, 0, 0])
        for c in self.char.get("chains", []):
            prims += chain_primitives(c, self.chains[self.anim.times[i]][c["name"]], body_c,
                                      subdiv=self.char.get("render", {}).get("smooth_chains", 1))
        if getattr(self, "prop_mode", "baked") == "baked":
            prims += self._prop_prims(i, worlds)
        for p in prims:
            p["M"] = face_m @ p["M"]
        return prims, {k: face_m @ v for k, v in worlds.items()}

    def render_props(self, i, direction):
        self._cur_dir = direction
        """Prop-only layer for the engine (prop_mode 'separate'): (idx, layer 'front'|'back', ids)."""
        from .render import render_pixels, add_outline
        ch = self.anim.keys[i]
        worlds = self.rig.world(ch, include_height=True)
        drop = translate(0, -ch["z_world"], 0)
        face_m = rot_y(DIRECTION_YAW[direction]) @ drop
        props = self._prop_prims(i, worlds)
        W, H = self.size
        if not props:
            empty = np.full((H, W), -1, int)
            return (empty, empty.copy()), None, []
        for p in props:
            p["M"] = face_m @ p["M"]
        pix = render_pixels(props, self.palette, self.size, self.pivot, cam=self.cam, cast_shadows=False)
        fill = despeckle(pix.idx)
        idx = add_outline(fill, self.palette.special["outline"])
        ids = sorted({p["name"].split("_")[0] if p["name"][-1].isdigit() else p["name"] for p in props})
        # per-pixel depth split against the body (AD r2: rope behind the head, crate in front)
        bd = getattr(self, "body_depth", {}).get((direction, i))
        if bd is None:
            bd = np.full((H, W), np.inf)
        front_m = (fill >= 0) & (pix.depth < bd - 0.05)
        back_m = (fill >= 0) & ~front_m
        ol = (idx >= 0) & (fill < 0)
        for y, x in zip(*np.nonzero(ol)):          # outline pixels follow the adjacent prop pixels' side
            nb_f = sum(1 for a, b in ((0, 1), (0, -1), (1, 0), (-1, 0)) if 0 <= y + a < H and 0 <= x + b < W and front_m[y + a, x + b])
            nb_b = sum(1 for a, b in ((0, 1), (0, -1), (1, 0), (-1, 0)) if 0 <= y + a < H and 0 <= x + b < W and back_m[y + a, x + b])
            (front_m if nb_f >= nb_b else back_m)[y, x] = True
        front = np.where(front_m, idx, -1)
        back = np.where(back_m, idx, -1)
        layer = "split" if front_m.any() and back_m.any() else ("front" if front_m.any() else "back")
        return (front, back), layer, ids

    def _prop_prims(self, i, worlds):
        """Props held by the character (snowball, crate, ...): attached to a bone, visible on listed frames.
        anim "props": [{"name", "bone", "offset", "radii", "rot", "material", "frames": [names or indices]}]"""
        out = []
        names = [f["name"] for f in self.anim_data["frames"]]
        for pr in self.anim_data.get("props", []):
            # (refs to data/props/*.json are resolved in __init__)
            vis = pr.get("frames", "all")
            if vis != "all" and i not in [names.index(v) if isinstance(v, str) else v for v in vis]:
                continue
            from .mathutil import euler, scale
            if pr["bone"] == "carry":      # virtual bone: midpoint of both hands, oriented like the chest
                base = worlds["chest"].copy()
                base[:3, 3] = (worlds["hand_L"][:3, 3] + worlds["hand_R"][:3, 3]) / 2
                worlds = dict(worlds, carry=base)
            B = worlds[pr["bone"]]
            fo = self.anim_data["frames"][i].get("prop") or {}
            if "offset" in fo or "rot" in fo:
                # per-frame placement (one declaration per clip): move/rotate the whole rigid prop about its centre
                o0 = pr.get("offset", [0, 0, 0])
                B = B @ translate(*fo.get("offset", o0)) @ euler(*fo.get("rot", [0, 0, 0])) @ translate(*[-v for v in o0])
            M = B @ translate(*pr.get("offset", [0, 0, 0]))
            M = M @ euler(*pr.get("rot", [0, 0, 0])) @ scale(*pr["radii"])
            out.append({"name": pr["name"], "M": M, "material": pr.get("material", "prop"), "group": "prop"})
            for k, part in enumerate(pr.get("parts", [])):      # extra shapes (e.g. crate lid, snowball shading)
                hide_dir = pr.get("hide_tags_by_dir", {}).get(getattr(self, "_cur_dir", ""), [])
                if part.get("tag") and (part["tag"] in fo.get("hide", []) or part["tag"] in hide_dir):
                    continue                                    # per-frame hidden part (e.g. slack crate ropes)
                Mk = B @ translate(*part["offset"]) @ euler(*part.get("rot", [0, 0, 0])) @ scale(*part["radii"])
                out.append({"name": f'{pr["name"]}_{k}', "M": Mk, "material": part.get("material", pr.get("material", "prop")),
                            "group": "prop", "clip_all": part.get("clip_all", [])})
        return out

    def render_base(self, i, direction, expression=None):
        rnd = self.char.get("render", {})
        v2 = bool(rnd.get("v2", False))
        rules = rnd.get("rules", ALL_RULES + POST_OUTLINE_RULES) if v2 else []
        prims, worlds = self.primitives(i, direction)
        pom = None
        if v2 and rnd.get("pom_part", True):
            # pom-pom is a hand-style pixel part placed at the simulated 3D position (no shading flicker)
            for p in prims:
                if p["name"] == "pom_tip":
                    pom = p
            prims = [p for p in prims if p is not pom]
        la = rnd.get("lineart") or {}
        hs = None
        if rnd.get("hair_style"):
            # stylized hair: designed clump lines + highlight ring defined on the 3D head (same in every view)
            hs = dict(rnd["hair_style"])
            face = self.char["face"]
            hs.update(head_M=worlds[face["bone"]], center=face["center"], radius=face["radii"][0], ppu=self.cam.ppu,
                      materials={p_["material"] for p_ in prims if p_["material"].startswith("hair")})
        pix = render_pixels(prims, self.palette, self.size, self.pivot, cam=self.cam,
                            smooth=la.get("smooth", 0.0), line_min_run=la.get("line_min_run", 1),
                            no_face_lines=la.get("no_face_lines", False), hair_style=hs, tracer=self.tracer)
        if not hasattr(self, "body_depth"):
            self.body_depth = {}
        self.body_depth[(direction, i)] = pix.depth.copy()    # for depth-splitting props (front/back strips)
        chain_names = {c["name"] for c in self.char.get("chains", [])}
        body_ids = [k for k, g in enumerate(pix.group_names) if g not in chain_names]
        ys, xs = np.nonzero(np.isin(pix.group, body_ids))
        if len(ys):
            self.body_bbox[(direction, i)] = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
        idx = despeckle(remove_lone_pixels(pix.idx), max_island=3 if v2 else 2,
                        material=pix.material if v2 else None)
        pix.material = np.where(idx >= 0, pix.material, None)
        face = self.char["face"]
        expr = expression or self.anim.poses[i]["face"]
        if v2:
            info = {}
            apply_face(idx, pix, worlds[face["bone"]], face, expr, self.palette, self.pivot, self.cam, v2=True, info=info)
            # back view = head's forward axis points away from the camera (not "no eye found")
            fwd = worlds[face["bone"]][:3, 2]
            facing_cam = float(np.dot(fwd / np.linalg.norm(fwd), self.cam.to_cam))
            idx = apply_rules(idx, pix, self.palette, rules, facing_cam > -0.15)
        if pom is not None:
            c = pom["M"][:3, 3]
            r = float(np.linalg.norm(pom["M"][:3, 0]))
            px, py = self.cam.project(c, self.pivot)
            head_x = self.cam.project(worlds["head"][:3, 3], self.pivot)[0]
            # unlit only while rising with the pom dragged >2px onto the shadow side of the dome
            # (AD rule 5 table: NW/W/SW f3-5); otherwise the designed highlight is always on
            zs = [p_["z_px"] for p_ in self.anim.poses]
            rising = i + 1 < len(zs) and zs[i + 1] > zs[i]
            cel = pom_cel(r * self.cam.ppu, self.palette, lit=not (rising and (px - head_x) > 2.0))
            d = self.cam.depth(c) - r
            h, w = cel.shape
            x0, y0 = int(round(px - w / 2.0)), int(round(py - h / 2.0))
            H, W = idx.shape
            pom_hi_px = []
            hi = self.palette.index[self.palette.ramps["pom"][-1]]
            for yy in range(h):
                for xx in range(w):
                    X, Y = x0 + xx, y0 + yy
                    if cel[yy, xx] >= 0 and 0 <= X < W and 0 <= Y < H and (idx[Y, X] < 0 or pix.depth[Y, X] > d):
                        idx[Y, X] = cel[yy, xx]
                        pix.material[Y, X] = "pom"
                        if cel[yy, xx] == hi:
                            pom_hi_px.append((Y, X))
        if la.get("angel_ring") and self.char.get("generated_from", {}).get("outfit", {}).get("hat", "beanie") in ("none", "earmuffs", "beret"):
            hair_mat = next((p_["material"] for p_ in self.char["primitives"] if p_["name"] == "hair_cap"), "hair")
            idx = angel_ring(idx, pix, self.palette, hair_mat)
        if la.get("regularize"):
            # accessories are deliberate small shapes: never shave them off as "bumps"
            protect = np.isin(pix.material, ["ribbon", "pom", "scarf"]) | np.isin(
                pix.group, [k for k, g in enumerate(pix.group_names) if g == "ahoge"])
            idx = regularize_silhouette(idx, protect=protect)
            pix.material = np.where(idx >= 0, pix.material, None)
        mode = la.get("outline", "selout" if la.get("selout") else "dark")
        # outline modes (r10 comparison): dark | selout | open | colored | none
        if mode != "none":
            idx = add_outline(idx, self.palette.special["outline"])
        if la.get("pixel_perfect") and mode != "none":
            idx = pixel_perfect_outline(idx, {self.palette.special["outline"]}, exterior=pix.material == None)  # noqa: E711
        if mode in ("selout", "open", "colored"):
            idx = selout_outline(idx, pix.material, self.palette, mode=mode)
        if v2:
            idx = apply_post_outline(idx, self.palette, [r for r in rules if r != "grounded_soles"])
        if rnd.get("face_hd"):
            from .face_hd import apply_face_hd
            idx = apply_face_hd(idx, self.palette, worlds[face["bone"]], face, self._face_cels(rnd["face_hd"]), expr,
                                self.pivot, self.cam)
        elif rnd.get("face_cels"):
            # v3: designed face cels (consistent in every view) instead of procedural eye placement
            cels = self._face_cels(rnd["face_cels"])
            idx, _ = apply_face_cels(idx, self.palette, worlds[face["bone"]], face, cels, expr, self.pivot, self.cam)
            self.deliberate[(direction, i)] = self.deliberate.get((direction, i), set()) | getattr(
                apply_face_cels, "last_stamped", set())
        else:
            idx = apply_face(idx, pix, worlds[face["bone"]], face, expr, self.palette, self.pivot, self.cam, v2=v2)
        # decals can split shading bands into 1-2px fragments; clean again with face + outline colours protected
        keep = {self.palette.special[k] for k in ("eye", "catchlight", "mouth", "blush", "outline") if k in self.palette.special}
        if v2:
            skin_ids = {self.palette.index[n] for n in self.palette.ramps["skin"]}
            idx = despeckle(idx, keep=keep, material=pix.material)          # 1) merge within each part
            skin_base = skin_ids - {self.palette.index[self.palette.ramps["skin"][0]]}
            idx = despeckle(idx, keep=keep | skin_base)                     # 2) remaining specks; base skin stays
            # skin pixels touching eye/lash pixels are designed face spacing, not orphans
            eye_c = {self.palette.special.get(k) for k in ("eye", "catchlight", "outline")}
            Hh, Ww = idx.shape
            spacing = set()
            for yy, xx in zip(*np.nonzero(np.isin(idx, list(skin_ids)))):
                if any(0 <= yy + a < Hh and 0 <= xx + b < Ww and idx[yy + a, xx + b] in eye_c
                       for a, b in ((0, 1), (0, -1), (1, 0), (-1, 0))):
                    spacing.add((int(yy), int(xx)))
            self.deliberate[(direction, i)] = self.deliberate.get((direction, i), set()) | spacing
        else:
            idx = despeckle(idx, keep=keep)
        if pom is not None:
            vis = [(Y, X) for Y, X in pom_hi_px if idx[Y, X] >= 0 and idx[Y, X] != self.palette.special["outline"]]
            if len(vis) >= 2:                    # designed highlight survives cleanup (by position), never as 1px
                for Y, X in vis:
                    idx[Y, X] = hi
        if v2 and "grounded_soles" in rules:
            # last step: a 1-2px sole is a deliberate design element, so it must not be "despeckled" away
            soles = set()
            boot_mask = np.isin(pix.material, ["boots", "boot_cuff"])
            # the rig part mask is render-time; grow it 1px so outline-adjacent boot pixels are included
            grown = boot_mask.copy()
            grown[1:, :] |= boot_mask[:-1, :]; grown[:-1, :] |= boot_mask[1:, :]
            grown[:, 1:] |= boot_mask[:, :-1]; grown[:, :-1] |= boot_mask[:, 1:]
            grown &= ~np.isin(pix.material, ["mitten", "scarf", "coat", "coat_trim", "skirt"])
            idx = apply_post_outline(idx, self.palette, ["grounded_soles"], deliberate=soles, part_mask=grown)
            self.deliberate[(direction, i)] = self.deliberate.get((direction, i), set()) | soles
        return idx

    def _face_cels(self, name):
        if not hasattr(self, "_cels"):
            root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            with open(os.path.join(root, "data", "faces", f"{name}.json")) as f:
                self._cels = json.load(f)
        return self._cels

    def render_shadow(self, i):
        zmax = max(p_["z_px"] for p_ in self.anim.poses) or 1
        return shadow_frame(self.size, self.pivot, self.anim.poses[i]["z_px"], self.palette, z_max=zmax,
                            ppu=self.cam.ppu, spec=self.char.get("shadow"))

    def render_fx(self, i):
        return fx_frames(self.events, self.anim.times[i], self.size, self.pivot, self.palette, ppu=self.cam.ppu)

    def ankle_px(self, i, direction):
        """Projected ankle positions (for foot-slide QA)."""
        _, worlds = self.primitives(i, direction)
        pts = [worlds[b][:3, 3] * np.array([1, 0, 1]) for b in ("ankle_L", "ankle_R")]   # ground contact
        return [self.cam.project(p, self.pivot) for p in pts]


# ------------------------------------------------------------------ overrides
def override_path(root, anim, direction, i):
    return os.path.join(root, anim, direction, f"{i:02d}.json")


def load_override(root, anim, direction, i):
    p = override_path(root, anim, direction, i)
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


def apply_override(idx, ov):
    out = idx.copy()
    H, W = out.shape
    for x, y, v in ov.get("px", []):
        if 0 <= x < W and 0 <= y < H:
            out[y, x] = v
    return out
