"""Compose a frame for (direction, frame): body + chains -> pixels -> outline -> face -> overrides."""
import hashlib
import json
import os

import numpy as np

from .mathutil import rot_y, translate, xform_point
from .rig import Rig, Animation, ChainSim, body_primitives, chain_primitives, frame_index
from .render import (render_pixels, add_outline, remove_lone_pixels, despeckle, DIRECTION_YAW, Camera,
                     pixel_perfect_outline, selout_outline, regularize_silhouette)
from .face import apply_face, apply_face_cels
from .pixelrules import apply_rules, apply_post_outline, pom_cel, angel_ring, ALL_RULES, POST_OUTLINE_RULES
from .fx import shadow_frame, fx_frames


def resolve_holds(anim):
    """r14 "hold_of" frames inherit the non-pose placement of their source (root_px, per-frame prop placement) unless
    they set their own; the pose itself is reused in rig.Animation. Returns the clip unchanged when there are no holds."""
    frames = anim.get("frames", [])
    if not any(f.get("hold_of") is not None for f in frames):
        return anim
    out = []
    for f in frames:
        if f.get("hold_of") is not None:
            src = out[frame_index(frames, f["hold_of"])] if frame_index(frames, f["hold_of"]) < len(out) else None
            if src is None:
                raise ValueError(f'frame {f["name"]}: hold_of {f["hold_of"]!r} must reference an earlier frame')
            f = dict({k: src[k] for k in ("root_px", "prop") if k in src}, **f)
            if src.get("smear") and "smear" not in f:
                f["smear"] = True          # holding a smear pose keeps its squash allowance / QA exemption (no FX)
        out.append(f)
    return dict(anim, frames=out)


def idx_hash(idx):
    return hashlib.sha1(np.ascontiguousarray(idx.astype(np.int16)).tobytes()).hexdigest()[:16]


class Scene:
    """Everything needed to render one animation; built once per build."""

    def __init__(self, character, anim, palette):
        anim = resolve_holds(anim)
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
        info = {"index": i, "name": f["name"], "duration_ms": f["ms"], "z_px": self.z_px(i),
                "phase": f.get("phase", ""), "events": f.get("events", []),
                "cancelable": bool(f.get("cancelable", False)), "face": pose["face"],
                "root_px": f.get("root_px", [0, 0]),
                "props": [pr["name"] for pr in self.anim_data.get("props", []) if self.prop_visible(pr, i)],
                "planted": bool(pose["plant"])}
        # r14 opt-in flags: only written when set, so older clips export byte-identical JSON
        for k in ("skippable", "loop_while_held", "smear"):
            if f.get(k):
                info[k] = True
        if f.get("hold_of") is not None:
            info["hold_of"] = self.anim_data["frames"][frame_index(self.anim_data["frames"], f["hold_of"])]["name"]
        return info

    def prop_visible(self, pr, i):
        """Prop "frames": "all" or a list of frame names / indices; a hold_of frame shows what its source shows."""
        vis = pr.get("frames", "all")
        if vis == "all":
            return True
        frames = self.anim_data["frames"]
        idx = {frame_index(frames, v) for v in vis}
        if i in idx:
            return True
        ref = frames[i].get("hold_of")
        return ref is not None and frame_index(frames, ref) in idx

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
                                           subdiv=self.char.get("render", {}).get("smooth_chains", 1),
                                           clip=self.anim_data.get("name"))
            props = self._prop_prims(i, worlds) if getattr(self, "prop_mode", "baked") == "baked" else []
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
        # the body's 1 px outline ring has no depth (outline is added after the raycast): give it the depth of the
        # body fill it wraps, so a prop behind the body never draws over the body's outline (crate band over legs)
        bd = _dilate_depth(bd)
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
        for pr in self.anim_data.get("props", []):
            # (refs to data/props/*.json are resolved in __init__)
            if not self.prop_visible(pr, i):
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
            n0 = len(out)
            out.append({"name": pr["name"], "M": M, "material": pr.get("material", "prop"), "group": "prop"})
            for k, part in enumerate(pr.get("parts", [])):      # extra shapes (e.g. crate lid, snowball shading)
                hide_dir = pr.get("hide_tags_by_dir", {}).get(getattr(self, "_cur_dir", ""), [])
                if part.get("tag") and (part["tag"] in fo.get("hide", []) or part["tag"] in hide_dir):
                    continue                                    # per-frame hidden part (e.g. slack crate ropes)
                Mk = B @ translate(*part["offset"]) @ euler(*part.get("rot", [0, 0, 0])) @ scale(*part["radii"])
                out.append({"name": f'{pr["name"]}_{k}', "M": Mk, "material": part.get("material", pr.get("material", "prop")),
                            "group": "prop", "clip_all": part.get("clip_all", [])})
            ro = pr.get("rest_on")
            if ro:
                # prop data "rest_on": {"bone", "y", "max_gap"}: an overhead load never rides higher above the head top
                # (bone-local y) than max_gap (world units); press / lockout / push poses otherwise float it 1 px off
                top = float((worlds[ro["bone"]] @ np.array([0.0, float(ro["y"]), 0.0, 1.0]))[1])
                bottom = float(M[1, 3] - np.sqrt((M[1, :3] ** 2).sum()))
                excess = bottom - top - float(ro["max_gap"])
                if excess > 0:
                    for o in out[n0:]:
                        o["M"] = translate(0, -excess, 0) @ o["M"]
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
        for ma, mb in rnd.get("separate_materials", []):
            idx = _separate_materials(idx, pix, self.palette, ma, mb)
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
            if rnd.get("face_eyes"):          # opt-in: each eye at its own projected modelled eye (HD variant)
                from .face import apply_face_eyes
                idx, _ = apply_face_eyes(idx, self.palette, worlds[face["bone"]], face, cels, expr, self.pivot, self.cam,
                                         rnd["face_eyes"], material=pix.material)
            else:
                idx, _ = apply_face_cels(idx, self.palette, worlds[face["bone"]], face, cels, expr, self.pivot, self.cam)
            self.deliberate[(direction, i)] = self.deliberate.get((direction, i), set()) | getattr(
                apply_face_cels, "last_stamped", set())
        else:
            idx = apply_face(idx, pix, worlds[face["bone"]], face, expr, self.palette, self.pivot, self.cam, v2=v2)
        # decals can split shading bands into 1-2px fragments; clean again with face + outline colours protected
        keep = {self.palette.special[k] for k in ("eye", "catchlight", "mouth", "blush", "outline") if k in self.palette.special}
        if v2:
            skin_ids = {self.palette.index[n] for n in self.palette.ramps["skin"]}
            pre_ds = idx.copy()
            idx = despeckle(idx, keep=keep, material=pix.material)          # 1) merge within each part
            skin_base = skin_ids - {self.palette.index[self.palette.ramps["skin"][0]]}
            idx = despeckle(idx, keep=keep | skin_base)                     # 2) remaining specks; base skin stays
            if rnd.get("face_eyes"):
                # despeckle must not grow the eyes: a 1-2 px skin gap between eye and hairline stays skin
                face_ink = np.isin(idx, [self.palette.special[k] for k in ("eye", "catchlight") if k in self.palette.special])
                grown = face_ink & np.isin(pre_ds, list(skin_ids))
                idx[grown] = pre_ds[grown]
            if la.get("keep_selout_runs"):
                idx = _restore_outline_runs(idx, pre_ds, pix.material, la["keep_selout_runs"], self.palette)
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
        if la.get("ring_trim"):
            idx = self._ring_trim(idx, pix, la["ring_trim"])
        if la.get("skin_edge_dark"):
            idx = self._skin_edge(idx, pix)
        if rnd.get("bow_shine"):
            idx = self._bow_shine(idx, pix, worlds, rnd["bow_shine"], direction, i)
        if rnd.get("final_orphan_pass"):
            idx = self._final_orphans(idx, direction, i)
        return idx

    def _final_orphans(self, idx, direction, i):
        """Opt-in last pass: a pixel with no same-colour 8-neighbour (left by the opt-in edge / highlight passes) takes
        the most common colour of its opaque 4-neighbours. Face colours and deliberate pixels are never touched."""
        pal = self.palette
        keep = {pal.special[k] for k in ("eye", "catchlight", "mouth", "blush") if k in pal.special}
        dl = self.deliberate.get((direction, i), set())
        H, W = idx.shape
        out = idx.copy()
        for _ in range(2):
            changed = False
            for y in range(H):
                for x in range(W):
                    v = out[y, x]
                    if v < 0 or v in keep or (y, x) in dl:
                        continue
                    if any(0 <= y + a < H and 0 <= x + b < W and (a or b) and out[y + a, x + b] == v
                           for a in (-1, 0, 1) for b in (-1, 0, 1)):
                        continue
                    nb = [int(out[y + a, x + b]) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))
                          if 0 <= y + a < H and 0 <= x + b < W and out[y + a, x + b] >= 0]
                    if nb:
                        out[y, x] = max(sorted(set(nb)), key=nb.count)
                        changed = True
            if not changed:
                break
        return out

    def _ring_trim(self, idx, pix, spec):
        """Opt-in (lineart.ring_trim: {"margin", "min_run"}): the hair highlight (top hair tone) stops `margin` px inside
        the silhouette and short runs (< min_run px: seams, crown specks) fall back to the base hair tone."""
        pal = self.palette
        H, W = idx.shape
        mats = {m for m in pal.ramps if m.startswith("hair")}
        out = idx.copy()
        for m in mats:
            r = pal.ramps[m]
            if len(r) < 3:
                continue
            hi, base = pal.index[r[-1]], pal.index[r[1]]
            hm = (idx == hi) & (np.isin(pix.material, [m]) | np.equal(pix.material, None))
            if not hm.any():
                continue
            if spec.get("fill_gaps"):               # close 1-2 px clump-line breaks inside the arc (same row)
                g = int(spec["fill_gaps"])
                for y in range(1, H - 1):
                    row = out[y]
                    x = 0
                    while x < W:
                        if row[x] == hi:
                            x1 = x + 1
                            while x1 < W and row[x1] == base and x1 - x - 1 < g + 1:
                                x1 += 1
                            n = x1 - x - 1
                            if 1 <= n <= g and x1 < W and row[x1] == hi and all(
                                    (out[y - 1, xx] == hi or out[y + 1, xx] == hi) and pix.material[y, xx] == m
                                    for xx in range(x + 1, x1)):
                                out[y, x + 1:x1] = hi
                            x = x1 if x1 > x + 1 else x + 1
                        else:
                            x += 1
                idx = out.copy()
                hm = (idx == hi) & (np.isin(pix.material, [m]) | np.equal(pix.material, None))
            ext = (idx < 0) | (np.equal(pix.material, None) & (idx != hi))
            k = int(spec.get("margin", 2))
            near = np.zeros_like(ext)
            for a in range(-k, k + 1):
                for b in range(-k, k + 1):
                    sh = np.zeros_like(ext)
                    ys0, ys1 = max(a, 0), H + min(a, 0)
                    xs0, xs1 = max(b, 0), W + min(b, 0)
                    sh[ys0 - a:ys1 - a, xs0 - b:xs1 - b] = ext[ys0:ys1, xs0:xs1]
                    near |= sh
            out[hm & near] = base
            if spec.get("stop_at"):                    # and 1 px clear of the bow (no seam rust beside the loops)
                st_m = np.isin(pix.material, list(spec["stop_at"])) & (idx >= 0)
                nb = np.zeros_like(st_m)
                nb[1:, :] |= st_m[:-1, :]; nb[:-1, :] |= st_m[1:, :]; nb[:, 1:] |= st_m[:, :-1]; nb[:, :-1] |= st_m[:, 1:]
                out[hm & nb] = base
            hm = (out == hi) & (np.isin(pix.material, [m]) | np.equal(pix.material, None))
            seen = np.zeros_like(hm)
            for y0, x0 in zip(*np.nonzero(hm)):
                if seen[y0, x0]:
                    continue
                comp, st = [], [(y0, x0)]
                seen[y0, x0] = True
                while st:
                    y, x = st.pop()
                    comp.append((y, x))
                    for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                        if 0 <= yy < H and 0 <= xx < W and hm[yy, xx] and not seen[yy, xx]:
                            seen[yy, xx] = True
                            st.append((yy, xx))
                if len(comp) < int(spec.get("min_run", 3)):
                    for c in comp:
                        out[c] = base
        return out

    def _skin_edge(self, idx, pix):
        """Opt-in (lineart.skin_edge_dark): the exterior line along the face is the dark outline on both cheeks (the lit
        side sel-out gave the near cheek a soft skin_0 edge, the far cheek a dark one); a skin_0 exterior pixel whose
        fill neighbour is no longer skin (back-view head skin turned hair) takes the hair line colour."""
        pal = self.palette
        sl = pal.index[pal.data.get("line_colors", {}).get("skin") or pal.ramps["skin"][0]]
        skin = {pal.index[c] for c in pal.ramps["skin"]} | {pal.special[k] for k in ("eye", "catchlight", "blush", "mouth")
                                                              if k in pal.special}
        hair_mat = next((m for m in pal.ramps if m.startswith("hair")), "hair")
        hair = {pal.index[c] for c in pal.ramps[hair_mat]}
        hl = pal.index[pal.data.get("line_colors", {}).get(hair_mat) or pal.ramps[hair_mat][0]]
        ol = pal.special["outline"]
        H, W = idx.shape
        out = idx.copy()
        ext = (idx == sl) & np.equal(pix.material, None)
        for y, x in zip(*np.nonzero(ext)):
            nb = [idx[y + a, x + b] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))
                  if 0 <= y + a < H and 0 <= x + b < W and pix.material[y + a, x + b] is not None]
            if any(v in skin for v in nb):
                out[y, x] = ol
            elif any(v in hair for v in nb):
                out[y, x] = hl

        def lone(y, x, im):
            return im[y, x] >= 0 and not any(0 <= y + a < H and 0 <= x + b < W and (a or b) and im[y + a, x + b] == im[y, x]
                                             for a in (-1, 0, 1) for b in (-1, 0, 1))
        for _ in range(4):                      # never create an orphan: a lone recoloured edge pixel stays as it was
            bad = [(y, x) for y, x in zip(*np.nonzero(out != idx))
                   if lone(y, x, out) or any(lone(y + a, x + b, out) and not lone(y + a, x + b, idx)
                                             for a in (-1, 0, 1) for b in (-1, 0, 1) if 0 <= y + a < H and 0 <= x + b < W)]
            if not bad:
                break
            for y, x in bad:
                out[y, x] = idx[y, x]
        return out

    def _bow_shine(self, idx, pix, worlds, spec, direction, i):
        """Opt-in designed bow volume (render.bow_shine): on each visible loop (connected fill of `material`, >= min_px)
        a 2 px `hi` highlight on its upper-front (top row, light side = screen left) and one `fold` pixel at the end
        nearest the knot. Placed after all cleanup, recorded as deliberate (the shading bands alone never produce it)."""
        pal = self.palette
        mat = spec.get("material", "ribbon")
        fill = pal.index[spec.get("fill", pal.ramps[mat][1])]
        hi, fold = pal.index[spec["hi"]], pal.index[spec["fold"]]
        knot_mat = spec.get("knot", "hatcuff")
        H, W = idx.shape
        m = (idx == fill) & (pix.material == mat)
        ky, kx = np.nonzero(pix.material == knot_mat)
        if len(kx):
            kc = (float(ky.mean()), float(kx.mean()))
        else:
            hx, hy = self.cam.project(worlds["head"][:3, 3], self.pivot)
            kc = (hy, hx)
        seen = np.zeros_like(m)
        out = idx.copy()
        dl = self.deliberate.setdefault((direction, i), set())
        used = set(np.unique(idx[idx >= 0]).tolist())
        if hi not in used and len(used) >= int(spec.get("max_colours", 16)):
            hi = fill                                  # palette budget: no highlight in an already 16-colour frame
        for y0 in range(H):
            for x0 in range(W):
                if not m[y0, x0] or seen[y0, x0]:
                    continue
                comp, st = [], [(y0, x0)]
                seen[y0, x0] = True
                while st:
                    y, x = st.pop()
                    comp.append((y, x))
                    for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                        if 0 <= yy < H and 0 <= xx < W and m[yy, xx] and not seen[yy, xx]:
                            seen[yy, xx] = True
                            st.append((yy, xx))
                if len(comp) < int(spec.get("min_px", 7)):
                    continue
                cs = set(comp)
                top = min(y for y, _ in comp)
                row = sorted(x for y, x in comp if y == top)
                far_x = -1 if abs(row[0] - kc[1]) > abs(row[-1] - kc[1]) else 1       # highlight away from the knot
                x = row[0] if far_x < 0 else row[-1]
                pts = [(top, x)]
                nb = (top, x - far_x) if (top, x - far_x) in cs else (top + 1, x) if (top + 1, x) in cs else None
                if nb:
                    pts.append(nb)
                for p_ in pts:
                    out[p_] = hi
                    dl.add(p_)
                cand = [c for c in comp if c not in pts and out[c] == fill]
                ring = {(p_[0] + a_, p_[1] + b_) for p_ in pts for a_ in (-1, 0, 1) for b_ in (-1, 0, 1)
                        if 0 <= p_[0] + a_ < H and 0 <= p_[1] + b_ < W and out[p_[0] + a_, p_[1] + b_] == fill}
                cand = sorted(set(cand) | ring)
                for c in cand:                 # never strand a 1 px fill pixel beside the highlight
                    if not any(out[c[0] + a_, c[1] + b_] == fill for a_ in (-1, 0, 1) for b_ in (-1, 0, 1)
                               if (a_ or b_) and 0 <= c[0] + a_ < H and 0 <= c[1] + b_ < W):
                        out[c] = hi
                        dl.add(c)
                cand = [c for c in cand if out[c] == fill]
                if cand and len(comp) >= int(spec.get("fold_min_px", 12)):
                    f = min(cand, key=lambda c: ((c[0] - kc[0]) ** 2 + (c[1] - kc[1]) ** 2, c))
                    out[f] = fold
                    dl.add(f)
        return out

    def temporal_hold(self, frames, direction, th):
        """Opt-in 1-frame flicker hold for near-static loops (render.temporal_hold: {"clips", "colors", "rows"}):
        in the top `rows` rows of the body (crown + bow), a pixel whose colour differs from the previous and next
        frame, which agree, takes their colour when both colours are in `colors` (no silhouette change) and the
        result is not an orphan. Sub-pixel head bob otherwise toggles clump seams / bow edges at 220 ms."""
        ids = {self.palette.index[c] for c in th["colors"]}
        n = len(frames)
        out = [f.copy() for f in frames]
        H, W = frames[0].shape
        for i in range(n):
            a, b, c = frames[(i - 1) % n], frames[i], frames[(i + 1) % n]
            bb = self.body_bbox.get((direction, i))
            if bb is None:
                continue
            y1 = min(bb[1] + int(th.get("rows", 12)), H)
            for y in range(max(bb[1] - 2, 0), y1):
                for x in range(W):
                    if a[y, x] == c[y, x] and b[y, x] != a[y, x] and a[y, x] in ids and b[y, x] in ids:
                        out[i][y, x] = a[y, x]
            o = out[i]

            def lone(y, x, im):
                return im[y, x] >= 0 and not any(0 <= y + p < H and 0 <= x + q < W and (p or q) and im[y + p, x + q] == im[y, x]
                                                 for p in (-1, 0, 1) for q in (-1, 0, 1))
            for _ in range(4):                               # never create an orphan (changed pixel or a neighbour)
                bad = [(y, x) for y in range(max(bb[1] - 3, 0), min(y1 + 1, H)) for x in range(W)
                       if lone(y, x, o) and not lone(y, x, b)]
                if not bad:
                    break
                for y, x in bad:
                    for p in (-1, 0, 1):
                        for q in (-1, 0, 1):
                            if 0 <= y + p < H and 0 <= x + q < W:
                                o[y + p, x + q] = b[y + p, x + q]
        return out

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


def _separate_materials(idx, pix, palette, ma, mb):
    """Opt-in (render.separate_materials: [[a, b], ...]): where two parts that share fill colours touch (bow loop vs
    raised teal mitten), the nearer pixel takes its material's line colour so they never fuse into one shape."""
    out = idx.copy()
    H, W = idx.shape
    mat, dep = pix.material, pix.depth
    lc = palette.data.get("line_colors", {})
    for y in range(H):
        for x in range(W):
            m = mat[y, x]
            if m not in (ma, mb) or idx[y, x] < 0:
                continue
            other = mb if m == ma else ma
            for a, b in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                yy, xx = y + a, x + b
                if 0 <= yy < H and 0 <= xx < W and mat[yy, xx] == other and idx[yy, xx] >= 0 and dep[y, x] < dep[yy, xx]:
                    out[y, x] = palette.index[lc.get(m) or palette.ramps[m][0]]
                    break
    return out


def _restore_outline_runs(idx, pre, material, mats, palette):
    """Opt-in (render.lineart.keep_selout_runs: [materials]): short sel-out runs on the exterior outline of these
    materials (e.g. the 2-3 px teal_0 line over a bow loop poking above the head) are line art, not speckle; give them
    back after despeckle when the restored pixel has a same-colour 8-neighbour (never creates an orphan)."""
    out = idx.copy()
    H, W = idx.shape
    ext = (pre >= 0) & np.equal(material, None) & (pre != idx)
    near = np.zeros_like(ext)
    fill = {palette.index[c] for m_ in mats for c in palette.ramps[m_][1:]}
    m = np.isin(material, list(mats)) & np.isin(idx, list(fill))       # still a visible fill pixel of that part
    near[1:, :] |= m[:-1, :]; near[:-1, :] |= m[1:, :]; near[:, 1:] |= m[:, :-1]; near[:, :-1] |= m[:, 1:]
    lines = [palette.index[palette.data.get("line_colors", {}).get(m_) or palette.ramps[m_][0]] for m_ in mats]
    ext &= near & np.isin(pre, lines) & np.isin(idx, list(fill))    # the line was absorbed into the part's fill
    pts = list(zip(*np.nonzero(ext)))
    for y, x in pts:
        out[y, x] = pre[y, x]

    def lone(y, x):
        return out[y, x] >= 0 and not any(0 <= y + a < H and 0 <= x + b < W and (a or b) and out[y + a, x + b] == out[y, x]
                                          for a in (-1, 0, 1) for b in (-1, 0, 1))
    for _ in range(3):                       # never leave an orphan (restored pixel or a neighbour it isolates)
        bad = [(y, x) for y, x in pts if out[y, x] != idx[y, x] and (lone(y, x) or any(
            lone(y + a, x + b) for a in (-1, 0, 1) for b in (-1, 0, 1) if 0 <= y + a < H and 0 <= x + b < W))]
        if not bad:
            break
        for y, x in bad:
            out[y, x] = idx[y, x]
    return out


def _dilate_depth(bd):
    """1 px dilation of a depth map into its empty (inf) border: each empty pixel takes the nearest (min) finite depth
    of its 8 neighbours."""
    H, W = bd.shape
    pad = np.full((H + 2, W + 2), np.inf)
    pad[1:-1, 1:-1] = bd
    nb = np.full((H, W), np.inf)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                nb = np.minimum(nb, pad[1 + dy:H + 1 + dy, 1 + dx:W + 1 + dx])
    return np.where(np.isfinite(bd), bd, nb)


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
