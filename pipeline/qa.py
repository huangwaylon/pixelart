"""Automated QA. Errors fail the build (unless --allow-qa-fail); warnings are reported for review."""
import numpy as np


def _bbox(idx):
    ys, xs = np.nonzero(idx >= 0)
    if len(ys) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def orphan_count(idx, protected=None):
    """Pixels with no same-colour 8-neighbour (excluding outline colour and protected mask)."""
    H, W = idx.shape
    pad = np.full((H + 2, W + 2), -9, int)
    pad[1:-1, 1:-1] = idx
    same = np.zeros((H, W), bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            same |= pad[1 + dy:H + 1 + dy, 1 + dx:W + 1 + dx] == idx
    orphan = (idx >= 0) & ~same
    if protected is not None:
        orphan &= ~protected
    return int(orphan.sum())


def run_qa(scene, final, overrides_meta, palette, release=False):
    errors, warnings, metrics = [], [], {}
    lim = {"max_height_delta_px": 2, "max_orphans": 0, "min_margin_px": 2}
    lim.update(scene.anim_data.get("qa", {}))
    W, H = scene.size
    n = len(scene.anim.keys)
    face_cols = {palette.special[k] for k in ("eye", "mouth", "blush", "catchlight") if k in palette.special}

    # 1. palette / alpha compliance (indices must be valid)
    for d, frames in final.items():
        for i, f in enumerate(frames):
            bad = (f >= len(palette.rgb)) | (f < -1)
            if bad.any():
                errors.append(f"{d} f{i + 1}: {int(bad.sum())} off-palette pixels")

    # 2. bounds: nothing touches the cell edge; top margin >= 2px
    for d, frames in final.items():
        for i, f in enumerate(frames):
            bb = _bbox(f)
            if bb is None:
                errors.append(f"{d} f{i + 1}: empty frame")
                continue
            x0, y0, x1, y1 = bb
            m = lim["min_margin_px"]
            if x0 < m or y0 < m or x1 > W - 1 - m or y1 > H - 1 - m:
                errors.append(f"{d} f{i + 1}: margin < {m}px, bbox {bb}")

    # 3. foot slide: planted frames keep ankles on the same pixel per direction
    slide = 0.0
    planted = [i for i in range(n) if scene.anim.poses[i]["plant"]]
    for d in scene.dirs if planted else ():      # clips without planted frames (climb, fall) have no foot slide
        pts = np.array([np.array(scene.ankle_px(i, d)).reshape(-1) for i in planted])
        slide = max(slide, float(np.abs(pts - pts[0]).max()))
    metrics["foot_slide_px"] = round(slide, 3)
    if slide >= 0.5:
        errors.append(f"foot slide {slide:.2f}px in planted frames (must be < 0.5)")

    # 4. height consistency across directions per frame (silhouette rows)
    worst = (0, None)
    heights = {}
    for i in range(n):
        hs = []
        for d in scene.dirs:
            # body-only silhouette: secondary motion (pom/scarf) legitimately differs per facing
            bb = scene.body_bbox.get((d, i)) or _bbox(final[d][i])
            hs.append(bb[3] - bb[1] + 1 if bb else 0)
        heights[i] = hs
        spread = max(hs) - min(hs)
        if spread > worst[0]:
            worst = (spread, i)
    metrics["max_height_delta_px"] = worst[0]
    metrics["standing_height_px"] = {d: heights[n - 1][k] for k, d in enumerate(scene.dirs)}
    if worst[0] > lim["max_height_delta_px"]:
        errors.append(f"body silhouette height differs by {worst[0]}px across directions at frame {worst[1] + 1}")

    # 5. orphan pixels (face decals excluded: their 1px features are deliberate)
    total_orphans = 0
    per = {}
    for d, frames in final.items():
        for i, f in enumerate(frames):
            prot = np.isin(f, list(face_cols))
            for y, x in scene.deliberate.get((d, i), ()):
                prot[y, x] = True          # generator-placed design elements (boot soles)
            for x, y in overrides_meta.get(f"{d}_{i + 1:02d}", {}).get("coords", []):
                prot[y, x] = True          # hand-placed with a recorded reason = deliberate
            c = orphan_count(f, prot)
            total_orphans += c
            if c:
                per[f"{d}_{i + 1}"] = c
    metrics["orphan_pixels_total"] = total_orphans
    metrics["orphan_pixels_worst"] = sorted(per.items(), key=lambda kv: -kv[1])[:5]
    if total_orphans > lim["max_orphans"]:
        errors.append(f"{total_orphans} orphan pixels (limit {lim['max_orphans']}); worst {metrics['orphan_pixels_worst'][:3]}")

    # 6a. secondary motion must never penetrate the body (user: "the scarf can't penetrate when jumping")
    from .rig import body_primitives
    pen = 0
    worst = {}
    for i, t in enumerate(scene.anim.times):
        worlds = scene.rig.world(scene.anim.keys[i])
        body = [bp for bp in body_primitives(scene.rig, worlds)
                if bp["group"] in ("torso", "arm_L", "arm_R", "leg_L", "leg_R", "head") and bp["material"] != "scarf"]
        for c in scene.char.get("chains", []):
            pts = scene.chains[t][c["name"]]
            for bp in body:
                Mi = np.linalg.inv(bp["M"])
                la = Mi[:3, :3] @ pts[0] + Mi[:3, 3]
                if la @ la < 1.15:
                    continue
                samples = [pts[k] + (pts[k + 1] - pts[k]) * f for k in range(len(pts) - 1) for f in (0.25, 0.5, 0.75, 1.0)]
                for q in samples:
                    lq = Mi[:3, :3] @ q + Mi[:3, 3]
                    if lq @ lq < 1.0:           # chain centre-line inside a body part
                        pen += 1
                        worst[c["name"]] = worst.get(c["name"], 0) + 1
    metrics["chain_penetrations"] = pen
    metrics["chain_penetrations_by_chain"] = worst
    if pen:
        (errors if scene.char.get("sim", {}).get("body_collide") else warnings).append(
            f"secondary motion penetrates the body at {pen} sample points: {worst}")

    # 6c. loop seam: secondary motion must be periodic (state at t=total == state at t=0)
    if scene.anim_data.get("loop"):
        a, b = scene.chains.get(0), scene.chains.get(scene.anim.total_ms)
        if a and b:
            seam = max((float(np.abs(a[k] - b[k]).max()) for k in a), default=0.0) * scene.cam.ppu
            metrics["loop_seam_px"] = round(seam, 2)
            if seam > lim.get("max_loop_seam_px", 1.0):
                errors.append(f"loop seam {seam:.2f}px (secondary motion not periodic; limit {lim.get('max_loop_seam_px', 1.0)})")

    # 6b. line-art metrics (Japanese research rules 1-4, 12): jaggies + colours per frame
    from .render import jaggy_count
    jag = {f"{d}_{i + 1:02d}": jaggy_count(f) for d, fr in final.items() for i, f in enumerate(fr)}
    metrics["jaggies_total"] = sum(jag.values())
    metrics["jaggies_worst"] = sorted(jag.items(), key=lambda kv: -kv[1])[:5]
    cpf = [len(set(np.unique(f[f >= 0]).tolist())) for fr in final.values() for f in fr]
    metrics["max_colours_per_frame"] = max(cpf)
    if max(cpf) > 16:
        warnings.append(f"a frame uses {max(cpf)} colours (target <= 16)")

    # 6. colour count
    used = set()
    for frames in final.values():
        for f in frames:
            used |= set(np.unique(f[f >= 0]).tolist())
    metrics["colours_used"] = len(used)
    if len(palette.rgb) > 32:
        errors.append("palette exceeds 32 colours")

    # 7. stale overrides
    stale = [k for k, v in overrides_meta.items() if v.get("stale")]
    metrics["overrides"] = len(overrides_meta)
    if stale:
        (errors if release else warnings).append(
            f"stale overrides (base changed since painted; re-approve with override --approve): {', '.join(stale)}")

    # 8. timing
    metrics["total_ms"] = scene.anim.total_ms
    air = [scene.anim.times[i] for i in range(n) if scene.anim.poses[i]["z_px"] > 0]
    metrics["airborne_at_ms"] = air[0] if air else None

    return {"pass": not errors, "errors": errors, "warnings": warnings, "metrics": metrics}


def qa_markdown(report):
    lines = [f"# QA report — {'PASS' if report['pass'] else 'FAIL'}", ""]
    for k in ("errors", "warnings"):
        lines.append(f"## {k.title()} ({len(report[k])})")
        lines += [f"- {e}" for e in report[k]] or ["- none"]
        lines.append("")
    lines.append("## Metrics")
    for k, v in report["metrics"].items():
        lines.append(f"- **{k}**: {v}")
    return "\n".join(lines) + "\n"
