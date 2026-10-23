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


def lock_end_ms(frames):
    """inputLockEnd_ms: the input lock runs to the end of the last non-cancelable frame (0 if all are cancelable)."""
    last = max([i for i, f in enumerate(frames) if not f.get("cancelable", False)] + [-1])
    return sum(f["ms"] for f in frames[:last + 1])


def _frame_z(anim):
    rest_z = anim.get("rest", {}).get("z_px", 0)
    names = [f["name"] for f in anim["frames"]]
    out = []
    for f in anim["frames"]:
        if "z_px" in f:
            out.append(f["z_px"])
        elif f.get("hold_of") is not None:
            h = f["hold_of"]
            out.append(out[names.index(h) if isinstance(h, str) else h])
        else:
            out.append(rest_z)
    return out


def timing_budget(anim):
    """r14 gameplay timing gate, driven by the clip's "budget" block (GD r14_gameplay_timing.md). All times are ms from
    the clip start (an event fires at the start of its frame). Keys (all optional):
      max_total_ms, max_lock_ms, loop_ms [min, max] (cycle length),
      events {event: deadline_ms}, events_min_pct {event: min % of total},
      intervals [{"from": event, "to": event, "min": ms, "max": ms}],
      root_px_end [x, y], root_px_monotonic true, spawn_anchor_last_visible true, min_rise_px_s (cycle_rise_px / cycle),
      engine_speed_u_s (loops: treadmill foot-slide check in run_qa; retune it with the cycle length), source (note).
    Always (budget or not): skippable frames must be grounded (z_px == 0)."""
    errors, m = [], {}
    frames = anim["frames"]
    times, t = [], 0
    for f in frames:
        times.append(t)
        t += f["ms"]
    total = t
    ev = {}
    for f, tt in zip(frames, times):
        for e in f.get("events", []):
            ev.setdefault(e, tt)
    zs = _frame_z(anim)
    air_skip = [f["name"] for f, z in zip(frames, zs) if f.get("skippable") and z > 0]
    if air_skip:
        errors.append(f"skippable on airborne frames {air_skip} (GD: only ground holds may be skipped)")
    b = anim.get("budget")
    if not b:
        return {"errors": errors, "metrics": m}
    lock = lock_end_ms(frames)
    m.update(total_ms=total, lock_ms=lock, event_ms=ev)
    if "max_total_ms" in b and total > b["max_total_ms"]:
        errors.append(f"budget: total {total} ms > max {b['max_total_ms']} ms")
    if "max_lock_ms" in b and lock > b["max_lock_ms"]:
        errors.append(f"budget: input lock {lock} ms > max {b['max_lock_ms']} ms (from cancel flags)")
    if "loop_ms" in b:
        lo, hi = b["loop_ms"]
        if not lo <= total <= hi:
            errors.append(f"budget: cycle {total} ms outside {lo}-{hi} ms")
    for e, dl in b.get("events", {}).items():
        if e not in ev:
            errors.append(f"budget: event {e!r} missing")
        elif ev[e] > dl:
            errors.append(f"budget: {e} at {ev[e]} ms > deadline {dl} ms")
    for e, pct in b.get("events_min_pct", {}).items():
        if e not in ev:
            errors.append(f"budget: event {e!r} missing")
        elif 100.0 * ev[e] / total < pct:
            errors.append(f"budget: {e} at {100.0 * ev[e] / total:.1f}% < {pct}% of the clip")
    for iv in b.get("intervals", []):
        if iv["from"] not in ev or iv["to"] not in ev:
            errors.append(f"budget: interval {iv['from']}->{iv['to']}: event missing")
            continue
        d = ev[iv["to"]] - ev[iv["from"]]
        m[f"{iv['from']}->{iv['to']}_ms"] = d
        if d < iv.get("min", -1e9) or d > iv.get("max", 1e9):
            errors.append(f"budget: {iv['from']}->{iv['to']} {d} ms outside {iv.get('min', '-')}-{iv.get('max', '-')} ms")
    if "min_rise_px_s" in b:
        rate = anim.get("cycle_rise_px", 0) * 1000.0 / total
        m["rise_px_s"] = round(rate, 2)
        if rate < b["min_rise_px_s"]:
            errors.append(f"budget: climb rise {rate:.1f} px/s < {b['min_rise_px_s']} px/s")
    rp = [f.get("root_px", [0, 0]) for f in frames]
    if b.get("root_px_end") is not None and list(rp[-1]) != list(b["root_px_end"]):
        errors.append(f"budget: root_px ends at {rp[-1]}, expected {b['root_px_end']}")
    if b.get("root_px_monotonic"):
        for k in (0, 1):
            dif = [rp[i + 1][k] - rp[i][k] for i in range(len(rp) - 1)]
            if any(x > 0 for x in dif) and any(x < 0 for x in dif):
                errors.append(f"budget: root_px[{k}] not monotonic {[r[k] for r in rp]}")
    if b.get("spawn_anchor_last_visible"):
        from .rig import frame_index
        for pr in anim.get("props", []):
            if pr.get("spawn_anchor_frame") is None or pr.get("frames", "all") == "all":
                continue
            vis = sorted(frame_index(frames, v) for v in pr["frames"])
            vis += [i for i, f in enumerate(frames) if f.get("hold_of") is not None
                    and frame_index(frames, f["hold_of"]) in vis]
            sa = frame_index(frames, pr["spawn_anchor_frame"])
            if sa != max(vis):
                errors.append(f"budget: {pr.get('name')} spawn_anchor_frame {frames[sa]['name']!r} is not the last "
                              f"frame it is drawn on ({frames[max(vis)]['name']!r})")
    return {"errors": errors, "metrics": m}


def treadmill_slide(scene, speed):
    """Loops moved by the engine at a constant speed (world u/s): a stance foot (ankle within stance_eps of its lowest
    point on both keys) must travel back exactly speed * frame_ms between consecutive keys, whatever the (uneven) frame
    durations are. Returns the worst residual in px (canonical-forward offset x ppu, i.e. the E/W screen worst case)."""
    lim = scene.anim_data.get("qa", {})
    eps = lim.get("stance_eps", 0.6)
    frames = scene.anim_data["frames"]
    n = len(frames)
    ws = [scene.rig.world(k, include_height=False) for k in scene.anim.keys]
    worst = 0.0
    for side in ("L", "R"):
        p = np.array([w["ankle_" + side][:3, 3] for w in ws])
        y0 = p[:, 1].min()
        for i in range(n if scene.anim_data.get("loop") else n - 1):
            j = (i + 1) % n
            if p[i, 1] - y0 < eps and p[j, 1] - y0 < eps:
                res = abs((p[j, 2] - p[i, 2]) + speed * frames[i]["ms"] / 1000.0) * scene.cam.ppu
                worst = max(worst, res)
    return worst


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

    # 3b. r14 treadmill: stance feet vs engine speed, valid for uneven frame durations (budget.engine_speed_u_s)
    speed = (scene.anim_data.get("budget") or {}).get("engine_speed_u_s")
    if speed:
        tm = treadmill_slide(scene, float(speed))
        metrics["treadmill_slide_px"] = round(tm, 3)
        if tm > 0.5:
            errors.append(f"treadmill foot slide {tm:.2f}px vs engine speed {speed} u/s (must be <= 0.5; keep stance "
                          f"frames uniform or re-solve the feet)")

    # 3c. r14 squash/stretch range: normal keys 0.86-1.15, "smear": true keys 0.84-1.18
    rng, srng = lim.get("squash_range", [0.86, 1.15]), lim.get("smear_squash_range", [0.84, 1.18])
    for i, f in enumerate(scene.anim_data["frames"]):
        sq = scene.anim.poses[i]["squash"]
        lo, hi = srng if f.get("smear") else rng
        if not lo <= sq <= hi:
            (errors if f.get("smear") else warnings).append(
                f"f{i + 1} {f['name']}: squash {sq} outside {lo}-{hi}{' (smear)' if f.get('smear') else ''}")

    # 4. height consistency across directions per frame (silhouette rows); "smear" frames are exempt
    smear = {i for i, f in enumerate(scene.anim_data["frames"]) if f.get("smear")}
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
        if i in smear:
            continue
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

    # 7b. HD model: every sprite-LOD ("lod": "all") feature must be at least 1 px, else mark it "lod": "ref"
    if scene.char.get("model") == "hd":
        from .sdf import subpixel_features
        sub = subpixel_features(scene.char, scene.cam.ppu)
        metrics["hd_subpixel_features"] = len(sub)
        if sub:
            warnings.append(f"{len(sub)} lod:all HD features < 1 px (use lod ref): {sub[:8]}")

    # 8. timing (+ r14 budget gate: violations are errors -> build exit 1, and the --release gate fails)
    tb = timing_budget(scene.anim_data)
    errors += tb["errors"]
    if tb["metrics"]:
        metrics["budget"] = tb["metrics"]
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
