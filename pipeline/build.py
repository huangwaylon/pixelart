"""Build entry point.

    python -m pipeline.build --anim jump            # full build -> builds/jump_<hash>/ and out/jump/
    python -m pipeline.build --anim jump --verify   # also re-render and assert byte-identical output
"""
import argparse
import math
import glob
import hashlib
import json
import os
import shutil
import sys
import time

import numpy as np

from .palette import Palette
from .frames import Scene, idx_hash, load_override, apply_override
from . import export as ex
from .qa import run_qa, qa_markdown
from .reference import build_reference, guide_data, grounding_sheet

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPELINE_VERSION = "1.0"
RELEASE = False
PREVIEW_HEADROOM = 24   # px above the 64px cell in baked previews (apex z is 20px)


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def load_variant(name):
    with open(os.path.join(ROOT, "data", "variants", f"{name}.json")) as f:
        spec = json.load(f)
    base = spec.pop("extends", None)
    if base:   # variants may extend another variant (outfit/colour studies on a chosen body)
        from .rig import deep_merge
        spec = deep_merge(load_variant(base), spec)
    return spec


def variant_inputs(spec):
    """(character_path_or_None, palette_path) for a variant spec or the classic hand-authored files."""
    if spec is None:
        return os.path.join(ROOT, "data", "character.json"), os.path.join(ROOT, "data", "palette.json")
    return None, os.path.join(ROOT, "data", "palettes", f"{spec['palette']}.json")


def overrides_key(anim, variant):
    return anim if variant is None else os.path.join("variants", variant, anim)


def input_files(anim, variant=None):
    spec = load_variant(variant) if variant else None
    char_path, pal_path = variant_inputs(spec)
    files = [p for p in (char_path, pal_path) if p] + [os.path.join(ROOT, "data", "animations", f"{anim}.json")]
    if variant:
        files += sorted(glob.glob(os.path.join(ROOT, "data", "variants", "*.json")))
    files += sorted(glob.glob(os.path.join(ROOT, "pipeline", "*.py")))
    files += sorted(glob.glob(os.path.join(ROOT, "data", "faces", "*.json")))
    files += sorted(glob.glob(os.path.join(ROOT, "data", "props", "*.json")))
    files += sorted(glob.glob(os.path.join(ROOT, "overrides", overrides_key(anim, variant), "*", "*.json")))
    return files


def build_id(anim, variant=None):
    h = hashlib.sha256(PIPELINE_VERSION.encode())
    hashes = {}
    for f in input_files(anim, variant):
        rel = os.path.relpath(f, ROOT)
        hashes[rel] = sha(f)
        h.update(rel.encode() + hashes[rel].encode())
    return h.hexdigest()[:12], hashes


def render_all(scene, anim_name, ov_key=None):
    base, final, ov_meta = {}, {}, {}
    n = len(scene.anim.keys)
    for d in scene.dirs:
        base[d], final[d] = [], []
        for i in range(n):
            b = scene.render_base(i, d)
            base[d].append(b)
            ov = load_override(os.path.join(ROOT, "overrides"), ov_key or anim_name, d, i)
            if ov:
                h = idx_hash(b)
                ov_meta[f"{d}_{i + 1:02d}"] = {"pixels": len(ov.get("px", [])), "stale": ov.get("base_hash") != h,
                                              "note": ov.get("note", ""), "reasons": len(ov.get("reasons", [])),
                                              "coords": [[x, y] for x, y, _ in ov.get("px", [])]}
                final[d].append(apply_override(b, ov))
            else:
                final[d].append(b)
    return base, final, ov_meta


def add_release_smears(scene, palette, props):
    """Throw readability (animation r2): a 2-frame snow smear from shoulder to hand on the release event frame
    and the next, drawn into the (direction-dependent) prop layer in front of the body."""
    rel = [i for i, f in enumerate(scene.anim_data["frames"]) if "throw_release" in f.get("events", [])]
    if not rel or not any(pr.get("smear", True) for pr in scene.anim_data.get("props", [])):
        return
    core, edge = palette.index["snow_3"], palette.index["snow_1"]
    n = len(scene.anim.keys)
    for d in scene.dirs:
        for k, i in enumerate([rel[0], rel[0] + 1]):
            if i >= n:
                continue
            _, worlds = scene.primitives(i, d)
            bone = scene.anim_data["props"][0].get("bone", "hand_R")
            b = "hand_R" if bone == "carry" else bone
            sh = scene.cam.project(worlds["shoulder_R" if b == "hand_R" else "shoulder_L"][:3, 3], scene.pivot)
            hd = scene.cam.project(worlds[b][:3, 3], scene.pivot)
            img = props["front"][d][i]
            H, W = img.shape
            steps = 6
            for t in range(steps + 1):
                u = 0.35 + 0.65 * t / steps if k == 0 else 0.6 + 0.4 * t / steps   # second frame: shorter tail
                x = sh[0] + (hd[0] - sh[0]) * u
                y = sh[1] + (hd[1] - sh[1]) * u - 1.5 * math.sin(math.pi * u)        # slight arc
                xi, yi = int(math.floor(x)), int(math.floor(y))
                for dx, dy, c in ((0, 0, core), (1, 0, edge), (0, 1, edge)):
                    if 0 <= xi + dx < W and 0 <= yi + dy < H and img[yi + dy, xi + dx] < 0:
                        img[yi + dy, xi + dx] = c
            if props["layer"][d][i] in (None, "back"):
                props["layer"][d][i] = "front" if props["layer"][d][i] is None else "split"
            if "smear" not in props["ids"][i]:
                props["ids"][i] = props["ids"][i] + ["smear"]


def anchors_for(scene):
    """Projected hand / carry pixel anchors per direction and frame (engine spawns projectiles here)."""
    out = {"hand_L": {}, "hand_R": {}, "carry": {}}
    for d in scene.dirs:
        for k in out:
            out[k][d] = []
        for i in range(len(scene.anim.keys)):
            _, worlds = scene.primitives(i, d)
            pl = scene.cam.project(worlds["hand_L"][:3, 3], scene.pivot)
            pr = scene.cam.project(worlds["hand_R"][:3, 3], scene.pivot)
            out["hand_L"][d].append([round(pl[0], 1), round(pl[1], 1)])
            out["hand_R"][d].append([round(pr[0], 1), round(pr[1], 1)])
            out["carry"][d].append([round((pl[0] + pr[0]) / 2, 1), round((pl[1] + pr[1]) / 2, 1)])
    return out


def write_build(anim_name, scene, palette, base, final, ov_meta, bid, hashes, out_dir, props=None):
    W, H = scene.size
    n = len(scene.anim.keys)
    infos = [scene.frame_info(i) for i in range(n)]
    durations = [inf["duration_ms"] for inf in infos]
    shadows = [scene.render_shadow(i) for i in range(n)]
    fx = [scene.render_fx(i) for i in range(n)]
    lock_end = sum(inf["duration_ms"] for inf in infos[:max([i for i, inf in enumerate(infos)
                                                             if not inf["cancelable"]] + [-1]) + 1])

    # --- game deliverables
    ex.save_png(palette.to_rgba(ex.sheet(final, scene.dirs, scene.size)), f"{out_dir}/{anim_name}_sheet.png")
    ex.save_png(palette.to_rgba(ex.sheet(base, scene.dirs, scene.size)), f"{out_dir}/editor/{anim_name}_sheet_base.png")
    ex.save_png(palette.to_rgba(ex.strip(shadows, scene.size)), f"{out_dir}/{anim_name}_shadow.png")
    ex.save_png(palette.to_rgba(ex.strip([f[0] for f in fx], scene.size)), f"{out_dir}/{anim_name}_fx_back.png")
    ex.save_png(palette.to_rgba(ex.strip([f[1] for f in fx], scene.size)), f"{out_dir}/{anim_name}_fx_front.png")
    meta = {
        "animation": anim_name, "buildId": bid, "buildHash": bid, "pipelineVersion": PIPELINE_VERSION,
        "inputLockEnd_ms": lock_end, "cameraElevation": scene.cam.elevation,
        "loop": bool(scene.anim_data.get("loop", False)),
        "cycle_rise_px": scene.anim_data.get("cycle_rise_px", 0),
        "rise_weights": scene.anim_data.get("rise_weights"),
        "engine_notes": scene.anim_data.get("engine_notes", ""),
        "root_px_mode": "cumulative offset from clip start",
        "props": [{k: v for k, v in pr.items() if k in ("name", "ref", "bone", "offset", "release_event", "spawn_anchor_frame")}
                  for pr in scene.anim_data.get("props", [])],
        "image": f"{anim_name}_sheet.png", "frameSize": [W, H], "pivot": list(scene.pivot),
        "layout": "rows=directions, cols=frames, no padding",
        "directions": scene.dirs, "paletteId": palette.data["name"],
        "palette": palette.hex, "totalMs": scene.anim.total_ms,
        "layers": {"shadow": f"{anim_name}_shadow.png", "fxBack": f"{anim_name}_fx_back.png",
                   "fxFront": f"{anim_name}_fx_front.png",
                   "note": "shadow/fx strips are direction-independent, same frame size & pivot; draw shadow+fxBack "
                           "under the character, fxFront over it; offset only the character by z_px"},
        "frames": [{k: v for k, v in inf.items() if k != "planted"} for inf in infos],
        "anchors": anchors_for(scene),
    }
    if scene.anim_data.get("derived"):
        meta["derivedFrom"] = {"clip": scene.anim_data["derived"]["clip"], "frames": scene.anim_data["derived"]["frames"]}
    if props is not None:
        meta["layers"]["propBack"] = f"{anim_name}_prop_back.png"
        meta["layers"]["propFront"] = f"{anim_name}_prop_front.png"
        meta["layers"]["note"] += ("; props are depth-split per pixel: draw propBack BEHIND the character and propFront IN FRONT "
                                   "(same grid/pivot; offset both by z_px like the body)")
        for k, f in enumerate(meta["frames"]):
            f["prop"] = {"ids": props["ids"][k], "visible": bool(props["ids"][k]),
                         "layer": {d: props["layer"][d][k] for d in scene.dirs}}
    with open(f"{out_dir}/{anim_name}_sheet.json", "w") as f:
        json.dump(meta, f, indent=2, sort_keys=True)

    # --- previews (baked z offset, shadow + fx, snow ground)
    if props is not None:
        ex.save_png(palette.to_rgba(ex.sheet(props["front"], scene.dirs, scene.size)), f"{out_dir}/{anim_name}_prop_front.png")
        ex.save_png(palette.to_rgba(ex.sheet(props["back"], scene.dirs, scene.size)), f"{out_dir}/{anim_name}_prop_back.png")
        view = {}
        for d in scene.dirs:
            view[d] = []
            for i in range(n):
                body = final[d][i].copy()
                pb, pf = props["back"][d][i], props["front"][d][i]
                m = (pb >= 0) & (body < 0)
                body[m] = pb[m]                      # back strip: only where the body doesn't cover it
                body[pf >= 0] = pf[pf >= 0]          # front strip: over the body
                view[d].append(body)
    else:
        view = final
    ch = H + int(round(PREVIEW_HEADROOM * scene.cam.ppu))
    gs = max(2, int(round(256 / W)))   # preview upscale so every resolution is shown ~256px wide
    baked = {d: [ex.baked_frame(view[d][i], shadows[i], fx[i][0], fx[i][1], infos[i]["z_px"], palette,
                                scene.size, scene.pivot, ch) for i in range(n)] for d in scene.dirs}
    for d in scene.dirs:
        ex.gif(baked[d], durations, palette, f"{out_dir}/preview/{anim_name}_{d}.gif", scale=gs)
        # slow-motion version for review (4x slower)
        ex.gif(baked[d], [t * 4 for t in durations], palette, f"{out_dir}/preview/slowmo/{anim_name}_{d}_slow.gif", scale=gs)
    compass = [ex.compass_frame(baked, i, (W, ch), palette) for i in range(n)]
    ex.gif(compass, durations, palette, f"{out_dir}/preview/{anim_name}_8dir.gif", scale=max(1, gs - 1))
    ex.gif(compass, [t * 4 for t in durations], palette, f"{out_dir}/preview/slowmo/{anim_name}_8dir_slow.gif", scale=max(1, gs - 1))
    bk = {d: [ex.baked_frame(view[d][i], shadows[i], fx[i][0], fx[i][1], infos[i]["z_px"], palette, scene.size,
                             scene.pivot, ch, background=False) for i in range(n)] for d in scene.dirs}
    ex.save_png(palette.to_rgba(ex.sheet(bk, scene.dirs, (W, ch))), f"{out_dir}/preview/{anim_name}_sheet_baked.png")
    ex.distance_test(final, [d for d in ("S", "SE", "E", "NE", "N", "NW") if d in scene.dirs][:5], palette, scene.size, f"{out_dir}/preview/distance_test.png")
    ex.greyscale_check(final, scene.dirs, palette, scene.size, f"{out_dir}/preview/greyscale_check.png")
    ex.contact_sheet(view, scene.dirs, infos, palette, scene.size, f"{out_dir}/preview/{anim_name}_contact_sheet.png", scale=gs)

    # --- QA + manifest + input snapshot
    report = run_qa(scene, final, ov_meta, palette, release=RELEASE)
    with open(f"{out_dir}/qa_report.json", "w") as f:
        json.dump(report, f, indent=2, sort_keys=True)
    with open(f"{out_dir}/qa_report.md", "w") as f:
        f.write(qa_markdown(report))
    manifest = {"buildId": bid, "animation": anim_name, "pipelineVersion": PIPELINE_VERSION,
                "inputs": hashes, "overrides": ov_meta, "qaPass": report["pass"],
                "frameHashes": {d: [idx_hash(f) for f in base[d]] for d in scene.dirs}}
    with open(f"{out_dir}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    snap = os.path.join(out_dir, "inputs")
    for rel in hashes:
        if rel.startswith("pipeline"):
            continue
        os.makedirs(os.path.dirname(os.path.join(snap, rel)), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, rel), os.path.join(snap, rel))
    return report


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--anim", default="jump")
    ap.add_argument("--verify", action="store_true", help="re-render and assert identical pixels")
    ap.add_argument("--no-reference", action="store_true")
    ap.add_argument("--variant", help="build data/variants/<name>.json via the character generator")
    ap.add_argument("--release", action="store_true", help="ship gate: stale/unreviewed overrides are errors")
    a = ap.parse_args(argv)
    global RELEASE
    RELEASE = a.release
    t0 = time.time()
    bid, hashes = build_id(a.anim, a.variant)
    spec = load_variant(a.variant) if a.variant else None
    char_path, pal_path = variant_inputs(spec)
    palette = Palette(pal_path)
    if spec and spec.get("material_bands"):
        # variant-level shading thresholds per material (e.g. keep hair one dark mass + a thin shine)
        palette.data.setdefault("material_bands", {}).update(spec["material_bands"])
    if spec and spec.get("ramp_overrides"):
        # variant-level colour tweaks (names must exist in the master palette)
        for mat, names in spec["ramp_overrides"].items():
            missing = [c for c in names if c not in palette.index]
            if missing:
                raise ValueError(f"ramp_overrides.{mat}: unknown colours {missing}")
            palette.ramps[mat] = names
    with open(os.path.join(ROOT, "data", "animations", f"{a.anim}.json")) as f:
        anim = json.load(f)
    if anim.get("derived"):
        # derived clip: frames sliced from another animation (e.g. land = jump_sc f10-f14)
        dv = anim["derived"]
        with open(os.path.join(ROOT, "data", "animations", f"{dv['clip']}.json")) as f:
            src = json.load(f)
        keep = {k: anim[k] for k in ("name", "loop", "derived", "props", "conventions") if k in anim}
        anim = dict(src, **keep)
        a0, a1 = dv["frames"]
        anim["frames"] = [dict(f, **dv.get("overrides", {}).get(f["name"], {})) for f in src["frames"][a0:a1 + 1]]
        if dv.get("rest_from_first"):
            anim["rest"] = src["rest"]
    if spec:
        from .chargen import build as gen_character
        character = gen_character(spec)
        if "frame" in spec:
            anim["frame_size"], anim["pivot"] = spec["frame"]["size"], spec["frame"]["pivot"]
        for k, v in spec.get("anim", {}).items():
            anim[k] = v
        patch = spec.get("anim_patch", {})        # per-variant pose tuning, merged by frame name
        if patch:
            from .rig import deep_merge
            if "rest" in patch:
                anim["rest"] = deep_merge(anim["rest"], patch["rest"])
            for f in anim["frames"]:
                if f["name"] in patch.get("frames", {}):
                    f.update(deep_merge(f, patch["frames"][f["name"]]))
    else:
        with open(char_path) as f:
            character = json.load(f)
    scene = Scene(character, anim, palette)
    ov_key = overrides_key(a.anim, a.variant)
    props = None
    if anim.get("props"):
        scene.prop_mode = "separate"            # GD r11: props are their own layers, never baked into the body
    base, final, ov_meta = render_all(scene, a.anim, ov_key)     # renders the body first (depth for the split)
    if anim.get("props"):
        props = {"front": {}, "back": {}, "layer": {}, "ids": []}
        for d in scene.dirs:
            props["front"][d], props["back"][d], props["layer"][d] = [], [], []
            for i in range(len(scene.anim.keys)):
                (pf, pb), lay, ids = scene.render_props(i, d)
                props["front"][d].append(pf)
                props["back"][d].append(pb)
                props["layer"][d].append(lay)
                if d == scene.dirs[0]:
                    props["ids"].append(ids)
        add_release_smears(scene, palette, props)
    tag = a.anim if not a.variant else f"{a.variant}_{a.anim}"
    out_dir = os.path.join(ROOT, "builds", *(["variants"] if a.variant else []), f"{tag}_{bid}")
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    report = write_build(a.anim, scene, palette, base, final, ov_meta, bid, hashes, out_dir, props=props)
    os.makedirs(os.path.join(out_dir, "guide"), exist_ok=True)
    with open(os.path.join(out_dir, "guide", "guide.json"), "w") as f:
        json.dump(guide_data(scene), f)
    if not a.no_reference:
        build_reference(scene, palette, os.path.join(out_dir, "reference"))
        grounding_sheet(scene, palette, final, os.path.join(out_dir, "reference", "grounding_3d_vs_pixel.png"))
        if getattr(scene, "model", "legacy") == "hd":
            # HD reference model: printable/viewable meshes (rest pose + jump apex)
            from .meshexport import export_poses
            with open(os.path.join(out_dir, "reference", "model_meshes.json"), "w") as f:
                json.dump(export_poses(scene, palette, os.path.join(out_dir, "reference")), f, indent=2)

    if a.verify:
        scene2 = Scene(character, anim, palette)
        _, final2, _ = render_all(scene2, a.anim, ov_key)
        same = all(np.array_equal(final[d][i], final2[d][i]) for d in final for i in range(len(final[d])))
        print("determinism check:", "IDENTICAL" if same else "MISMATCH")
        if not same:
            sys.exit(2)

    if spec:
        with open(os.path.join(out_dir, "inputs", "character_generated.json"), "w") as f:
            json.dump(character, f, indent=1)
    vdir = a.variant if a.anim == "jump" else f"{a.variant}__{a.anim}"     # one output folder per animation
    latest = os.path.join(ROOT, "out", a.anim) if not a.variant else os.path.join(ROOT, "out", "variants", vdir)
    if os.path.exists(latest):
        shutil.rmtree(latest)
    shutil.copytree(out_dir, latest)
    with open(os.path.join(ROOT, "builds", f"latest_{tag}.json"), "w") as f:
        json.dump({"buildId": bid, "dir": os.path.relpath(out_dir, ROOT)}, f, indent=2)
    print(f"build {tag}_{bid} in {time.time() - t0:.1f}s  QA: {'PASS' if report['pass'] else 'FAIL'}")
    for e in report["errors"]:
        print("  ERROR", e)
    for w in report["warnings"]:
        print("  warn ", w)
    print("  metrics", json.dumps(report["metrics"]))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
