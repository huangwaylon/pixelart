"""Round 7 (AD / GD / TA 'close the remaining sprite gates against the REAL rendered mask').

Run (after a full render_turnaround pass has written checks.json):
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P model/solve_gates.py -- \
      --checks renders/model_round_7/checks.json [--out model/gate_fixes.json] [--keep]

For every cell listed in the checks.json gate failures (blade_outside_fail, hook_fail,
scarf_near_arm_fail, plus hook_occluded cells of LOCOMOTION Actions -- the AD ruled that the
occlusion exemption does not apply to idle / walk / run frames) this script:
  1. poses the cell (Action + frame + iso direction, exactly as render_turnaround does),
  2. renders the sprite-scale masks at 128 px with the sprite settings (no AA, sprite katana):
       * sword-only and body-only alpha masks  -> blade pixels outside the body silhouette
       * object-ID pass                        -> visible kagi pixels, blade, scarf, bare arm
  3. searches small corrections on top of the Action:
       * sword: yaw / pitch about the sword head, then roll about the blade axis (hook)
       * scarf: the scarf_clear swing family (swing about Z per ribbon, lift about X)
     and keeps the smallest correction that passes every gate with a margin (blade >= gate + 4,
     hook: largest connected kagi group >= 5 and >= 3 kagi px clear of the blade, scarf run <= 4),
  4. writes the corrections to model/gate_fixes.json (replayed by build_character.py, so a clean
     build reproduces them) and applies them to model/character.blend.
Pose-library cells (pose_*) are shared by the SE and NW renders, so both views are solved
together (worst view).  Cyclic Actions also re-key the loop-seam frame.
"""
import bpy, sys, os, json, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build_character as BC        # noqa: E402  (apply_gate_fix / sword_delta / scarf_delta)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


CHECKS = arg("--checks", os.path.join(ROOT, "renders", "model_round_7", "checks.json"))
OUTJ = arg("--out", BC.GATE_FIXES)
KEEP = "--keep" in argv          # keep (merge with) existing fixes in OUTJ
TMP = "/tmp/akane_gates"
os.makedirs(TMP, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "character.blend"))
sc = bpy.context.scene
cam = bpy.data.objects["cam"]
rig = bpy.data.objects["rig"]
DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
ISO_ORTHO = float(rig.get("iso_ortho", 7.3))
CELL = 128
PIVOT = (64, 104)
SPRITE_DROP = ("chest_cord", "corset_tabs", "chest_flower", "hair_streaks")
LOCOMOTION = ("anim_idle", "anim_walk", "anim_run", "iso_", "pose_run", "pose_walk")

# ---- object-ID groups (same as render_turnaround)
GROUPS = {"sword": ("katana_sprite",), "kagi": ("katana_sprite_kagi",), "scarf": ("scarf.L", "scarf.R"),
          "arm": ("arm.L", "arm.R", "hand.L", "hand.R")}
GID = {g: i + 1 for i, g in enumerate(GROUPS)}


def srgb_to_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


m = bpy.data.materials.new("M_gateid")
m.use_nodes = True
nt = m.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
out = nt.nodes.new("ShaderNodeOutputMaterial")
em = nt.nodes.new("ShaderNodeEmission")
oi = nt.nodes.new("ShaderNodeObjectInfo")
nt.links.new(oi.outputs["Color"], em.inputs["Color"])
nt.links.new(em.outputs[0], out.inputs["Surface"])
for o in bpy.data.objects:
    if o.type == "MESH":
        o.color = (0, 0, 0, 1)
for g, names in GROUPS.items():
    for n in names:
        if n in bpy.data.objects:
            bpy.data.objects[n].color = (srgb_to_lin(GID[g] * 40 / 255.0), 0, 0, 1)
M_ID = m

# ---- sprite render state
for ob in bpy.data.objects:
    md = ob.modifiers.get("Outline") if ob.type == "MESH" else None
    if md:
        md.show_render = False
for mat in bpy.data.materials:
    if mat.node_tree:
        for n in mat.node_tree.nodes:
            if n.name == "rim_thresh":
                n.inputs[1].default_value = 2.0
bpy.data.objects["katana"].hide_render = True
for n in ("katana_sprite", "katana_sprite_kagi"):
    bpy.data.objects[n].hide_render = False
for n in SPRITE_DROP:
    bpy.data.objects[n].hide_render = True
r = sc.render
# masks only need the silhouettes / object colours: Workbench (flat, object colour, no AA) is ~10x
# faster than EEVEE and rasterises the same geometry at the same camera
r.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "FLAT"
sc.display.shading.color_type = "OBJECT"
sc.display.render_aa = "OFF"
r.film_transparent = True
sc.view_settings.view_transform = "Standard"
r.resolution_x = r.resolution_y = CELL
r.resolution_percentage = 100
r.filter_size = 0.0
sc.eevee.taa_render_samples = 1
r.image_settings.file_format = "PNG"
r.image_settings.color_mode = "RGBA"


def cam_iso(direction):
    el = math.radians(30)
    cam.rotation_euler = (math.pi / 2 - el, 0, 0)
    cam.data.ortho_scale = ISO_ORTHO
    cam.data.shift_x = cam.data.shift_y = 0
    fwd = BC.V((0, math.cos(el), -math.sin(el)))
    up = BC.V((0, math.sin(el), math.cos(el)))
    lift = (PIVOT[1] - CELL / 2) / (CELL / ISO_ORTHO)
    cam.location = up * lift - fwd * 20
    rig.rotation_euler = (0, 0, math.radians(DIRS.index(direction) * 45.0))


def read_png(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]
    bpy.data.images.remove(img)
    return px


def render_to(path):
    r.filepath = path
    bpy.ops.render.render(write_still=True)
    return read_png(path)


# speed: the heavy subdivided shells (hair cap ~212k verts, skirt, sleeves) dominate every
# depsgraph evaluation; their subdivision is switched off for the search (silhouette error well
# under 1 px at 17.5 px / H).  The parts the gates measure keep theirs.
KEEP_SUBSURF = ("katana_sprite", "katana_sprite_kagi", "scarf.L", "scarf.R", "arm.L", "arm.R", "hand.L", "hand.R")
for o in bpy.data.objects:
    if o.type == "MESH" and o.name not in KEEP_SUBSURF:
        for md in o.modifiers:
            if md.type == "SUBSURF":
                md.show_render = False
                md.show_viewport = False
MESHES = [o for o in bpy.data.objects if o.type == "MESH"]
BASE_HIDE = {o.name: o.hide_render for o in MESHES}


def render_masks(need_body=True):
    """-> dict(sword alpha, body alpha, ids)"""
    res = {}
    a = render_to(os.path.join(TMP, "id.png"))      # Workbench OBJECT colour = the id colour
    ids = np.rint(a[..., 0] * 255.0 / 40.0).astype(int)   # PNG stores sRGB: R = id * 40 / 255
    ids[a[..., 3] < 0.5] = 0
    res["ids"] = ids
    for o in MESHES:
        o.hide_render = BASE_HIDE[o.name] or not o.name.startswith("katana_sprite")
    res["sword"] = render_to(os.path.join(TMP, "sw.png"))[..., 3] > 0.5
    if need_body:
        for o in MESHES:
            o.hide_render = BASE_HIDE[o.name] or o.name.startswith("katana")
        res["body"] = render_to(os.path.join(TMP, "bd.png"))[..., 3] > 0.5
    for o in MESHES:
        o.hide_render = BASE_HIDE[o.name]
    return res


def shift(mk, dy, dx):
    H, W = mk.shape
    o = np.zeros_like(mk)
    ys0, ys1 = max(0, -dy), min(H, H - dy)
    xs0, xs1 = max(0, -dx), min(W, W - dx)
    o[ys0:ys1, xs0:xs1] = mk[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
    return o


def dilate(mk, rr):
    o = mk.copy()
    for dy in range(-rr, rr + 1):
        for dx in range(-rr, rr + 1):
            o |= shift(mk, dy, dx)
    return o


def comp_sizes(mk):
    """8-connected component sizes (numpy label propagation)."""
    H, W = mk.shape
    big = H * W + 1
    lab = np.where(mk, np.arange(H * W).reshape(H, W), big)
    for _ in range(H * W):
        new = lab
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy or dx:
                    new = np.where(mk & shift(mk, dy, dx), np.minimum(new, np.where(shift(mk, dy, dx), shift(lab, dy, dx), big)), new)
        if np.array_equal(new, lab):
            break
        lab = new
    if not mk.any():
        return []
    _, cnt = np.unique(lab[mk], return_counts=True)
    return sorted(cnt.tolist(), reverse=True)


def metrics(ms, need_blade):
    ids = ms["ids"]
    kg = ids == GID["kagi"]
    blade = (ids == GID["sword"])
    cs = comp_sizes(kg)
    big = cs[0] if cs else 0
    free = int((kg & ~dilate(blade, 1)).sum())
    conn = big >= 0.8 * kg.sum() if kg.any() else False
    out_ = {"hook_big": big, "hook_free": free, "hook_ok": bool(big >= 5 and conn and free >= 3),
            "hook_gate": bool(big >= 3 and conn and free >= 2)}      # the sprite gate itself (no margin)
    if "body" in ms:
        out_["blade_out"] = int((ms["sword"] & ~ms["body"]).sum())
        out_["blade_ok"] = out_["blade_out"] >= need_blade + 4
    arm = ids == GID["arm"]
    near = (ids == GID["scarf"]) & dilate(arm, 2)
    cs = comp_sizes(near)
    out_["scarf_run"] = cs[0] if cs else 0
    out_["scarf_ok"] = out_["scarf_run"] <= 4
    return out_


# ---------------------------------------------------------------- cell parsing
def action_frames(an):
    """Frames exactly as render_turnaround renders them: idle / walk cycles and cyclic timed
    Actions play frame_start .. frame_end - 1 (frame_end = loop seam), the rest .. frame_end."""
    act = bpy.data.actions[an]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    if an.startswith(("anim_idle", "anim_walk")):
        return list(range(f0, f1)), True
    base = an
    cycd = json.loads(rig.get("cycles", "{}"))
    cyclic = bool(cycd.get(an, {}).get("cyclic", False))
    return (list(range(f0, f1)) if cyclic else list(range(f0, f1 + 1))), cyclic


def parse(tag):
    """cell tag (no _64) -> (action, [frames to key], [directions to check])"""
    if tag.startswith("iso_"):
        d = tag[4:]
        an = f"pose_idle_{d}" if f"pose_idle_{d}" in bpy.data.actions else "pose_idle"
        return an, [1], [d]
    if tag == "pose_test":
        return "pose_sword_ready", [1], ["SE", "NW"]
    if tag.startswith("pose_"):
        body, d = tag.rsplit("_", 1)
        return body, [1], ["SE", "NW"]
    if tag.startswith("anim_"):
        body, fk = tag.rsplit("_f", 1)
        base, d = body.rsplit("_", 1)
        van = f"{base}_{d}" if f"{base}_{d}" in bpy.data.actions else base
        frames, cyclic = action_frames(van)
        k = int(fk)
        f = frames[k]
        keyf = [f]
        if cyclic and k == 0:
            keyf.append(int(bpy.data.actions[van].frame_range[1]))      # loop seam == frame 1
        return van, keyf, [d]
    return None


# ---------------------------------------------------------------- solving
def set_cell(an, f):
    rig.animation_data.action = bpy.data.actions[an]
    sc.frame_set(f)
    bpy.context.view_layer.update()
    basis = {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy(), pb.scale.copy()) for pb in rig.pose.bones}
    props = {k: rig[k] for k in rig.keys() if isinstance(rig[k], float)}
    rig.animation_data.action = None          # renders keep the manual pose
    return basis, props


def restore(basis, props):
    for n, (l, q, s_) in basis.items():
        pb = rig.pose.bones[n]
        pb.location, pb.rotation_quaternion, pb.scale = l, q, s_
    for k, v in props.items():
        rig[k] = v
    rig.update_tag()
    bpy.context.view_layer.update()


def eval_views(dirs, need, sword=None, scarf=None, basis=None, props=None, need_body=True):
    res = []
    for d in dirs:
        restore(basis, props)
        if sword:
            BC.sword_delta(rig, *sword)
        if scarf:
            BC.scarf_delta(rig, *scarf)
        crossed = BC.scarf_crossed(rig)
        cam_iso(d)
        # the body silhouette barely changes while only the sword / ribbons move: rendered once
        # per (cell, view) and cached (the final check is the full sprite pipeline re-render)
        ms = render_masks(need_body and d not in BODY_CACHE)
        if "body" in ms:
            BODY_CACHE[d] = ms["body"]
        elif d in BODY_CACHE:
            ms["body"] = BODY_CACHE[d]
        mt = metrics(ms, need[d])
        mt["scarf_crossed"] = crossed
        res.append(mt)
    return res


SWORD_YP = [(0, 0), (15, 0), (-15, 0), (0, 15), (0, -15), (25, 0), (-25, 0), (15, 15), (-15, 15),
            (15, -15), (-15, -15), (0, 25), (0, -25), (35, 0), (-35, 0), (30, 20), (-30, 20), (30, -20),
            (-30, -20), (50, 0), (-50, 0)]
ROLLS = [0, 20, -20, 40, -40, 60, -60, 90, -90, 120, -120, 150, -150, 180]
SCARF_C = [(0, 0, 0)] + [c for c in ((zl, zr, xl) for xl in (0, 20, -20, 35) for (zl, zr) in
                                      ((0, 0), (-12, 12), (25, -25), (-25, 25), (25, 25), (-25, -25), (40, -40),
                                       (-40, 40), (40, 40), (-40, -40), (60, -60))) if any(c)]


BODY_CACHE = {}
SCARF_PASS = 5       # search target (gate 6): one pixel of margin for the EEVEE vs Workbench raster


def eval_group(views, need, sword=None, scarf=None, need_body=True, arm=None):
    """views: list of (frame, dir, basis, props) -> metrics per view"""
    res = []
    for (f, d, basis, props) in views:
        restore(basis, props)
        if arm:
            BC.arm_delta(rig, arm)
        if sword:
            BC.sword_delta(rig, *sword)
        if scarf:
            BC.scarf_delta(rig, *scarf)
        crossed = BC.scarf_crossed(rig)
        cam_iso(d)
        ms = render_masks(need_body and (f, d) not in BODY_CACHE)
        if "body" in ms:
            BODY_CACHE[(f, d)] = ms["body"]
        elif (f, d) in BODY_CACHE:
            ms["body"] = BODY_CACHE[(f, d)]
        mt = metrics(ms, need)
        mt["scarf_crossed"] = crossed
        mt["f"], mt["d"] = f, d
        res.append(mt)
    return res


def solve_group(label, an, eval_frames, keyf, dirs, want, need, loco):
    """One correction for the whole group: every (frame, dir) view must pass.  Cyclic locomotion
    Actions are solved as ONE group over all their frames, so the fix is the same on every frame
    (no per-frame jitter in the loop)."""
    BODY_CACHE.clear()
    views = []
    for f in eval_frames:
        basis, props = set_cell(an, f)
        for d in dirs:
            views.append((f, d, basis, props))
    base = eval_group(views, need)
    log = {"cell": label, "action": an, "frames": keyf, "dirs": dirs, "want": sorted(want),
           "before": base}
    sword = None
    arm_fix = None
    if "blade" in want or "hook" in want:
        if "hook" in want:
            cands = [(yw, pt, rl) for (yw, pt) in SWORD_YP[:(len(SWORD_YP) if "--wide" in argv else 9)] for rl in ROLLS]
        else:
            cands = [(yw, pt, rl) for (yw, pt) in SWORD_YP for rl in (0, 30, -30)]
        cands.sort(key=lambda c: abs(c[0]) + abs(c[1]) + 0.3 * abs(c[2]))
        best = None
        arm_used = None
        # one-handed frames: if no blade correction alone works, the sword arm is also
        # abducted out from the body (15 / 30 / 45 deg) -- never for two-handed grips
        two_hand = any(float(v[3].get("two_hand", 0.0)) > 0.5 for v in views)
        arms = (None,) if two_hand else (None, [-15, 0], [0, 20], [0, -20], [-30, 0], [0, 35], [0, -35],
                                           [-20, 20], [-20, -20], [-45, 0])
        for arm in arms:
            body_saved = dict(BODY_CACHE)
            if arm:
                BODY_CACHE.clear()          # the arm moves the body silhouette
            for (yw, pt, rl) in cands:
                res = eval_group(views, need, sword=(yw, pt, rl), arm=arm)
                ok_b = all(x.get("blade_out", 99) >= need + (4 if "blade" in want else 0) for x in res)
                ok_h = all(x["hook_ok"] or (not loco and not b["hook_ok"] and "hook" not in want)
                           for x, b in zip(res, base))
                ok_s = all(x["scarf_run"] <= max(6, b["scarf_run"]) for x, b in zip(res, base))
                ok = ok_b and ok_h and ok_s
                score = sum(min(x.get("blade_out", 0), need + 6) for x in res) + \
                    3 * sum(min(x["hook_free"], 6) + min(x["hook_big"], 8) for x in res)
                key = (ok, -(abs(yw) + abs(pt) + 0.3 * abs(rl) + (sum(abs(v) for v in arm) if arm else 0)) if ok else score)
                if best is None or key > best[0]:
                    best = (key, (yw, pt, rl), res)
                    arm_used = arm
                if ok:
                    break
            if best and best[0][0]:
                break
            BODY_CACHE.clear()
            BODY_CACHE.update(body_saved)
        # fallback (nothing passes): keep the best only if it does not turn an occluded guard
        # into a partially visible failing hook or lower the blade count
        improve = best and (best[0][0] or (
            all(x["hook_gate"] or not ("hook" in want or loco) for x in best[2])
            and all(x.get("blade_out", 0) >= need for x in best[2])))
        if improve and (tuple(best[1]) != (0, 0, 0) or arm_used):
            sword = list(best[1])
            arm_fix = arm_used
        log["sword"] = sword
        log["arm"] = arm_fix
        log["sword_ok"] = bool(best[0][0]) if best else False
        log["after_sword"] = best[2] if best else None
    scarf = None
    if "scarf" in want:
        best = None
        for c in SCARF_C:
            res = eval_group(views, need, sword=sword, scarf=c if any(c) else None, need_body=False, arm=arm_fix)
            ok = all(x["scarf_run"] <= SCARF_PASS and not x["scarf_crossed"] for x in res)
            worst = max(x["scarf_run"] + 1000 * x["scarf_crossed"] for x in res)
            cost = abs(c[0]) + abs(c[1]) + abs(c[2])
            key = (ok, -cost if ok else -(worst * 100 + sum(x["scarf_run"] for x in res) + 0.01 * cost))
            if best is None or key > best[0]:
                best = (key, c, res)
            if ok:
                break
        if best and any(best[1]):
            worst = max(x["scarf_run"] + 1000 * x["scarf_crossed"] for x in best[2])
            worst0 = max(x["scarf_run"] for x in base)
            # fallback (nothing reaches the search target): keep the best one only if it meets the
            # gate (<= 6) everywhere or at least lowers the worst run
            if best[0][0] or worst <= 6 or worst < worst0:
                scarf = list(best[1])
        log["scarf"] = scarf
        log["after_scarf"] = best[2] if best else None
    restore(*views[0][2:]) if views else None
    if sword is None and scarf is None:
        log["fix"] = None
        return log
    log["fix"] = {"action": an, "frames": keyf, "arm": arm_fix, "sword": sword, "scarf": scarf, "cell": label}
    return log


def main():
    ch = json.load(open(CHECKS))
    sm = ch["_summary"]
    want = {}
    for k in sm.get("blade_outside_fail", []):
        want.setdefault(k[:-3], set()).add("blade")
    for k in sm.get("hook_fail", []):
        want.setdefault(k[:-3], set()).add("hook")
    for k in sm.get("hook_occluded", []):
        if k.startswith(LOCOMOTION):
            want.setdefault(k[:-3], set()).add("hook")
    for k in sm.get("scarf_near_arm_fail", []):
        want.setdefault(k[:-3], set()).add("scarf")
    # groups: cyclic locomotion Actions (idle / walk / run) -> ONE fix over all frames; pose_*
    # cells -> one Action shared by the SE + NW renders; everything else per cell (frame)
    groups = {}
    for tag, w in want.items():
        p = parse(tag)
        if p is None:
            continue
        an, keyf, dirs = p
        if an.startswith(("anim_idle", "anim_walk", "anim_run")) and "--nogroup" not in argv:
            frames, cyc = action_frames(an)
            seam = [int(bpy.data.actions[an].frame_range[1])] if cyc else []
            k = (an, "all")
            g = groups.setdefault(k, dict(label=f"{an} (all frames)", an=an, eval=frames, keyf=frames + seam,
                                          dirs=dirs, want=set(), loco=True))
        else:
            k = (an, tuple(keyf))
            g = groups.setdefault(k, dict(label=tag, an=an, eval=keyf[:1], keyf=keyf, dirs=dirs, want=set(),
                                          loco=tag.startswith(LOCOMOTION)))
        g["want"] |= w
    fixes = []
    if KEEP and os.path.exists(OUTJ):
        fixes = json.load(open(OUTJ)).get("fixes", [])
    logs = []
    for k in sorted(groups):
        g = groups[k]
        need = 35 if g["label"].startswith("iso_") else 30
        lg = solve_group(g["label"], g["an"], g["eval"], g["keyf"], g["dirs"], g["want"], need, g["loco"])
        print("[gates]", g["label"], sorted(g["want"]), "->", lg.get("fix"))
        logs.append(lg)
        if lg.get("fix"):
            # fixes are deltas on top of the current blend -> appended in solve order and
            # replayed in that order by the build (a second solve of the same frames stacks)
            fixes.append(lg["fix"])
    json.dump({"note": "round 7 render-in-the-loop gate fixes (model/solve_gates.py); replayed by "
                       "build_character.py after the pose / cycle solves",
               "fixes": fixes}, open(OUTJ, "w"), indent=1)
    json.dump(logs, open(os.path.join(os.path.dirname(CHECKS), "gate_solve_log.json"), "w"), indent=1, default=str)
    if "--dry" in argv:
        print(f"[gates] dry run: {len(logs)} cells solved, fixes -> {OUTJ} (blend not saved)")
        return
    # apply the NEW fixes to the saved blend (the build replays the whole file next time)
    bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "character.blend"))
    rig2 = bpy.data.objects["rig"]
    n = 0
    for lg in logs:
        if lg.get("fix"):
            n += BC.apply_gate_fix(rig2, lg["fix"])
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "character.blend"), compress=True)
    print(f"[gates] {len(logs)} cells solved, {n} fixes applied, {len(fixes)} in {OUTJ}")


main()
