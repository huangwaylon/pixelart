"""Animation-director pose preview + converter (hybrid/anim/poses/*.json -> rig-native poses + guide renders).

Run (one heavy Blender job at a time; check `pgrep -f Blender`):
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/hybrid/anim/pose_preview.py -- \
      [--poses hybrid/anim/poses] [--only GLOB] [--dirs SE,E] [--out hybrid/anim/preview] [--px 256] [--fast]

Reads model/character.blend READ ONLY (never saved).  Pose helpers (aim, rotate_world, pose_feet,
pose_two_hand, set_sword_dir, idle_scarf, run_scarf, dir_turn ...) are imported from
model/build_character.py (its main() is behind __name__ guard, so nothing is rebuilt).

Pose JSON format ("dirpose/1", see hybrid/ANIM_DIRECTION.md section 9):
  {"format": "dirpose/1", "name": "slash_k0", "dirs": ["SE"], "ops": [[op, args...], ...], "intent": {...}}
Ops are applied in order, in CHARACTER space (she faces -Y, +X = her LEFT = katana hand, +Z up,
units = H-ish rig units, 1 sprite px ~ 0.059 vertical / 0.051 horizontal):
  ["base", pose_name]                       stored rig pose (rig["poses"]: rest, idle_<D>, walk_contact, ...)
  ["move", bone, [dx,dy,dz]]                armature-space translate (cog bounce / drop)
  ["rot", bone, "X"|"Y"|"Z"|[ax,ay,az], deg] world-axis rotation (X+: top tips FORWARD; Z+: front turns to her LEFT;
                                            Y+: top tips to her LEFT)
  ["feet", side, [x,y,z], yaw, heel_lift, toe_lift]    IK foot control (armature space)
  ["knee", side, [fx,fy,fz]]                knee pole direction
  ["two_hand", [cx,cy,cz], [dx,dy,dz], [ex,ey,ez], elbow_out]   both hands on the tsuka; handle centre, blade dir, edge hint
  ["hand_l", [x,y,z], yaw, [px,py,pz]]      one-handed left (sword) hand IK target + elbow pole
  ["sword", az, de]                         blade direction: azimuth from +X toward +Y (deg; -90 = forward), de = down angle
  ["chain", bone_prefix, axis, [deg...]]    successive world rotations down a chain (scarf.L, scarf.R, skirt.tail, skirt.L ...)
  ["scarf_hang", phase, walk, sway] / ["scarf_run", phase]   the rig's ribbon solvers
  ["aimdir", bone, [dx,dy,dz]]              aim a bone along a direction
  ["scale", bone, [sx,sy,sz]]               GUIDE-ONLY squash/stretch (cog or chest); painted for real in pixels
  ["props", {"expr_frown": 1, ...}]
Writes:
  <out>/<name>_<DIR>.png   colour guide render (no AA) at --px (cell 128 scaled), feet pivot at (64,104)*px/128
  <out>/sheet_<group>.png  contact sheets per pose-name prefix
  hybrid/anim/poses/rig/<name>.json   rig-native pose ({bone: [qw,qx,qy,qz,lx,ly,lz]}, "_props", "_scale"),
                           captured BEFORE the per-direction presentation turn (dir_turn), same as the rig's poses.
"""
import bpy, sys, os, json, math, glob, fnmatch, importlib.util
from mathutils import Vector as V, Matrix

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


POSEDIR = os.path.join(ROOT, arg("--poses", "hybrid/anim/poses"))
OUT = os.path.join(ROOT, arg("--out", "hybrid/anim/preview"))
ONLY = arg("--only", "*")
DIRS_OVERRIDE = arg("--dirs")
PX = int(arg("--px", "256"))
FAST = "--fast" in argv
CAPTURE_ALL = "--dirs-only" not in argv      # capture all 8 directions for the TA format
NO_RENDER = "--no-render" in argv
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(POSEDIR, "rig"), exist_ok=True)
os.makedirs(os.path.join(POSEDIR, "ta"), exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "model", "character.blend"))
spec = importlib.util.spec_from_file_location("bc", os.path.join(ROOT, "model", "build_character.py"))
bc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bc)

sc = bpy.context.scene
cam = bpy.data.objects["cam"]
rig = bpy.data.objects["rig"]
rig.animation_data_create() if rig.animation_data is None else None
rig.animation_data.action = None
RIG_POSES = json.loads(rig["poses"])
# speed: viewport modifiers (subsurf/solidify/shrinkwrap) re-evaluate on every view_layer.update() during
# posing; renders use show_render, so switching the viewport copies off changes nothing in the output
for ob in bpy.data.objects:
    for m in getattr(ob, "modifiers", []):
        if m.type != "ARMATURE":
            m.show_viewport = False
DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
ISO_ORTHO = float(rig.get("iso_ortho", 6.5))
CELL = 128
PIVOT = (64, 104)
try:
    bc.IDLE_SWORD_DIR.update(json.loads(rig.get("idle_sword_dir", "{}")))
except Exception:
    pass


def upd():
    bpy.context.view_layer.update()


def clear():
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    for k in bc.POSE_PROPS:
        rig[k] = bc.PROP_DEFAULTS.get(k, 0.0)
    rig.update_tag()
    upd()


def apply_rig_pose(name):
    p = RIG_POSES[name]
    for bn, v in p.items():
        if bn.startswith("_"):
            continue
        pb = rig.pose.bones[bn]
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = v[:4]
        pb.location = v[4:7]
    for k, v in p.get("_props", {}).items():
        rig[k] = float(v)
    rig.update_tag()
    upd()


AX = {"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}
CHAINS = {
    "scarf.L": bc.scarf_names("L"), "scarf.R": bc.scarf_names("R"),
    "skirt.tail": ["skirt.tail.001", "skirt.tail.002", "skirt.tail.003"],
    "skirt.L": ["skirt.L", "skirt.L.001", "skirt.L.002"], "skirt.R": ["skirt.R", "skirt.R.001", "skirt.R.002"],
    "skirt.F": ["skirt.F", "skirt.F.001"],
}


def run_ops(ops, d):
    yaw = DIRS.index(d) * 45.0
    for op in ops:
        k = op[0]
        if k == "base":
            apply_rig_pose(op[1].replace("{D}", d))
        elif k == "clear":
            clear()
        elif k == "move":
            bc.move(rig, op[1], op[2])
        elif k == "rot":
            ax = AX[op[2]] if isinstance(op[2], str) else op[2]
            bc.rotate_world(rig, op[1], ax, math.radians(op[3]))
        elif k == "feet":
            bc.pose_feet(rig, op[1], op[2], yaw=op[3] if len(op) > 3 else 0.0,
                         heel_lift=op[4] if len(op) > 4 else 0.0, toe_lift=op[5] if len(op) > 5 else 0.0)
        elif k == "knee":
            bc.aim_pole_knee(rig, op[1], op[2])
        elif k == "two_hand":
            bc.pose_two_hand(rig, op[1], op[2], edge_hint=V(op[3]) if len(op) > 3 and op[3] else V((0, 0, -1)),
                             elbow_out=op[4] if len(op) > 4 else 0.45)
        elif k == "hand_l":
            bc.set_props(rig, ik_arm__L=1)
            bc.place_ctrl(rig, "hand_ik.L", loc=op[1], yaw=op[2])
            bc.place_ctrl(rig, "elbow_pole.L", loc=op[3])
        elif k == "sword":
            bc.set_sword_dir(rig, op[1], op[2], yaw=yaw)
        elif k == "chain":
            bc.curve_chain(rig, CHAINS[op[1]], AX[op[2]] if isinstance(op[2], str) else op[2], op[3])
        elif k == "scarf_hang":
            bc.idle_scarf(rig, *op[1:])
        elif k == "scarf_run":
            bc.run_scarf(rig, *op[1:])
        elif k == "aimdir":
            upd()
            h = rig.pose.bones[op[1]].matrix.translation.copy()
            bc.aim(rig, op[1], h + V(op[2]))
        elif k == "scale":
            rig.pose.bones[op[1]].scale = op[2]
            upd()
        elif k == "props":
            for pk, pv in op[1].items():
                rig[pk] = float(pv)
            rig.update_tag()
            upd()
        else:
            raise ValueError(f"unknown op {op}")
    upd()


def capture():
    out = bc.capture_pose(rig)
    sc_ = {pb.name: [round(x, 4) for x in pb.scale] for pb in rig.pose.bones
           if (V(pb.scale) - V((1, 1, 1))).length > 1e-4}
    if sc_:
        out["_scale"] = sc_
    return out


def cam_iso(d):
    el = math.radians(30)
    cam.rotation_euler = (math.pi / 2 - el, 0, 0)
    cam.data.ortho_scale = ISO_ORTHO
    cam.data.shift_x = cam.data.shift_y = 0
    fwd = V((0, math.cos(el), -math.sin(el)))
    up = V((0, math.sin(el), math.cos(el)))
    lift = (PIVOT[1] - CELL / 2) / (CELL / ISO_ORTHO)
    cam.location = up * lift - fwd * 20
    rig.rotation_euler = (0, 0, math.radians(DIRS.index(d) * 45.0))


def blade_px():
    """Screen px (in the 128 cell, y down) of the blade: hilt (guard), 45 %, 70 % and tip, plus hands.
    Smear arcs are drawn through the tip track of consecutive keys (ANIM_DIRECTION.md section 4)."""
    from bpy_extras.object_utils import world_to_camera_view
    upd()
    mw = rig.matrix_world
    pb = rig.pose.bones["sword"]
    M = mw @ pb.matrix
    L = rig.data.bones["sword"].length
    ydir = (M.to_3x3() @ V((0, 1, 0))).normalized()
    base = M.translation + ydir * (bc.KATANA_OFF + bc.GUARD_Y)
    tip = M.translation + ydir * L
    def px(w):
        c = world_to_camera_view(sc, cam, w)
        return [round(c.x * CELL, 1), round((1 - c.y) * CELL, 1)]
    out = {"guard": px(base), "b45": px(base + (tip - base) * 0.45), "b70": px(base + (tip - base) * 0.70), "tip": px(tip)}
    for h in ("hand.L", "hand.R"):
        out[h] = px(mw @ rig.pose.bones[h].head)
    out["head_top"] = px(mw @ rig.pose.bones["bun"].tail)
    return out


def set_sprite_look():
    for n, hide in (("katana", True), ("katana_sprite", False), ("katana_sprite_kagi", False)):
        if n in bpy.data.objects:
            bpy.data.objects[n].hide_render = hide
    for n in ("chest_cord", "corset_tabs", "chest_flower", "hair_streaks"):
        if n in bpy.data.objects:
            bpy.data.objects[n].hide_render = True
    r = sc.render
    r.resolution_x = r.resolution_y = PX
    r.resolution_percentage = 100
    r.film_transparent = True
    r.filter_size = 0.0
    try:
        sc.eevee.taa_render_samples = 1
    except Exception:
        pass
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGBA"


set_sprite_look()
files = sorted(glob.glob(os.path.join(POSEDIR, "*.json")))
done = []
for fp in files:
    P = json.load(open(fp))
    if P.get("format") != "dirpose/1":
        continue
    name = P["name"]
    if not fnmatch.fnmatch(name, ONLY):
        continue
    dirs = DIRS_OVERRIDE.split(",") if DIRS_OVERRIDE else P.get("dirs", ["SE"])
    captured = None
    per_dir = {}
    for d in (DIRS if CAPTURE_ALL else dirs):
        clear()
        rig.rotation_euler = (0, 0, math.radians(DIRS.index(d) * 45.0))
        upd()
        run_ops(P["ops"], d)
        if captured is None:
            captured = capture()
        if not P.get("no_dir_turn"):
            bc.dir_turn(rig, d, scarf=not P.get("keep_scarf", False))
        upd()
        per_dir[d] = capture()
        cam_iso(d)
        upd()
        path = os.path.join(OUT, f"{name}_{d}.png")
        json.dump(blade_px(), open(path[:-4] + ".json", "w"))      # all 8 directions (cheap)
        if d not in dirs or NO_RENDER:
            continue
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        done.append(path)
        print("[pose_preview]", path)
    json.dump({"name": name, "source": os.path.relpath(fp, ROOT), "pose": captured},
              open(os.path.join(POSEDIR, "rig", f"{name}.json"), "w"), indent=1)
    # TA guide-rig format (tools/hybrid/render_guides.py --pose): full absolute pose per direction
    def ta_bones(c):
        out = {}
        for bn, v in c.items():
            if bn.startswith("_"):
                continue
            out[bn] = {"quat": v[:4], "loc": v[4:7]}
        for bn, sv in c.get("_scale", {}).items():
            out.setdefault(bn, {"quat": [1, 0, 0, 0], "loc": [0, 0, 0]})["scale"] = sv
        return out
    first = (["SE"] if "SE" in per_dir else list(per_dir))[0]
    ta = {"format": "ta-pose (render_guides.py)", "name": name, "source": os.path.relpath(fp, ROOT),
          "base": None, "props": per_dir[first].get("_props", {}), "bones": ta_bones(per_dir[first]),
          "dir_override": {d: {"props": c.get("_props", {}), "bones": ta_bones(c)} for d, c in per_dir.items() if d != first},
          "note": "absolute pose (base None -> reset, then every bone set); dir_override holds the per-direction "
                  "presentation turn + camera-flat blade roll; intent: " + json.dumps(P.get("intent", {}))}
    json.dump(ta, open(os.path.join(POSEDIR, "ta", f"{name}.json"), "w"))
print("[pose_preview] rendered", len(done))
