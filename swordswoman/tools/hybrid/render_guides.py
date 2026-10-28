"""Hidden GUIDE renderer (hybrid pipeline).  The renders are never the visible art: they give the
artists (Gemini / Claude hand pixel work) pose, silhouette, camera, part layout and joint
positions that stay consistent across directions and frames.

Run (one heavy Blender job at a time):
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/hybrid/render_guides.py -- \
      [--blend hybrid/guide/guide.blend] [--anim NAME] [--dirs all|S,SE,..] \
      [--action ACTION | --pose POSE.json | --anim-json ANIM.json] [--frames 0-7|0,3|all] \
      [--passes clay,id,line,depth,mask,joints] [--res 1024] [--out hybrid/guide] \
      [--view iso|front|side|back] [--ortho 6.8] [--prefix f] [--hide obj1,obj2]

Inputs (pick one; default = the blend's neutral idle 'pose_idle_<DIR>'):
  --action A      an Action in the blend.  '{D}' in A is replaced by the direction; if A_<DIR> exists it
                  is used for that direction.  --frames are 0-based indices into the action's range.
  --pose P.json   one pose (format: POSE JSON below); written as frame --frames (default 0).
  --anim-json J   {"name": "slash", "frames": [pose, pose, ...]}  (or a bare list); frame i -> fNN=i.
                  A pose may be {"file": "other_pose.json"} and may give "dir_override" per direction.

Output: <out>/<anim>/<DIR>/fNN_<pass>.png (+ fNN_joints.json), camera = the exact game iso camera
(ortho, 30 deg elevation, character yawed by 45 deg per direction, world origin (feet) on the cell
pivot (64,104) -> at 1024 px: (512, 832); 8 px per sprite pixel).

POSE JSON (all keys optional; example hybrid/guide/poses/_test_features.json)
  {"base": "pose_idle_{D}",         Action to start from ({D} = direction; '<name>_<DIR>' preferred if it
                                     exists); null = rest pose.  Default pose_idle_{D} (neutral idle).
   "base_frame": 0,                  0-based frame index into the base action
   "props": {"ik_arm.L": 1, "two_hand": 1, "expr_frown": 1, "bow_face_camera": 0.85, ...}   rig custom props
   "root": {"loc": [x, y, z],        character-space offset (+X her left, -Y her front, +Z up; 1 unit = 1 H old,
                                     guide head H' = 1.16 units)  e.g. jump height, lunge
            "yaw_deg": 10,           extra body yaw on top of the direction (camera stays the game camera)
            "stretch": 0.8,          whole-body volume-preserving squash (<1) / stretch (>1) about the floor
            "scale": [sx, sy, sz]},  explicit root scale
   "bones": {"<bone>": {             applied parents-first; see hybrid/guide/rig_reference.json for names
       "rot": [x, y, z],             local XYZ euler deg, REPLACES the base rotation
       "rot_add": [x, y, z],         local XYZ euler deg, on top of the base pose (head: -X = chin up)
       "quat": [w, x, y, z],
       "rot_arm": [ax, ay, az, deg]  rotation about a character-space axis through the bone head (or a list)
       "loc": [..] | "loc_add": [..] local translation (IK targets hand_ik.*, foot_ik.*, foot_ctrl.*, cog ...)
       "loc_arm": [dx, dy, dz],      character-space translation of the posed bone
       "scale": [..],                local scale (children inherit)
       "stretch": k}},               volume-preserving along the bone's vertical axis, pivot = bone head
                                     (root/cog: floor/pelvis, spine: waist, chest, head: neck, bun, bow ...)
   "smears": [                        smear helpers (id 'smear', own mask fNN_mask_smear.png)
       {"kind": "blade", "from": "prev" | <pose dict> | "file.json", "steps": 8, "inner": 0.35, "outer": 1.0,
        "taper": 0.85, "span": [0, 1]},           ribbon swept by the blade (guard->tip fraction inner..outer)
                                                  along the slerped arc from 'from' to this pose
       {"kind": "trail", "from": "prev", "bone": "foot.R", "t": 1.0, "radius": 0.08, "steps": 8}],
                                                  tapered tube along a bone point's path (limb / run smears)
   "dir_override": {"NE": {...}}}    per-direction overrides merged over this pose
  An anim JSON is {"name": "slash", "frames": [pose, ...]}; a frame may be {"file": "k0.json", ...overrides}.
  Secondary chains: bun; bow > bow_loop.L/R; scarf.L/R.001-005; skirt.F(.001), skirt.L/R(.001/.002),
  skirt.B > skirt.tail.001-003; sleeve.L/R > sleeve_cuff.L/R; hair_lock.L/R.

Passes
  clay   neutral grey clay, camera-locked key light, AA
  id     flat colour per part, no AA.  R channel = id*10 (tools/hybrid/hylib compatible), G/B make
         the colours distinct to the eye.  Legend: <out>/id_legend.json
  line   Freestyle lines only (black on transparent): silhouette, border, crease, contour, object edges
  depth  16-bit grey, white = near.  Range in fNN_joints.json["depth_range"] (camera distance)
  mask   white silhouette on transparent, AA (smear helper excluded -> fNN_mask_smear.png when present)
  smear_mask  only the smear-helper sweep -> fNN_mask_smear.png (also written by 'mask')
  Smear 'path': [pose files] (relative to the anim JSON) = explicit swing in-betweens; the blade
         ribbon is built through them in order (oldest first), which follows the real arc.
  joints JSON: 2D px (at --res) + cell coords (/res*128) + camera depth + visibility of head, head_top,
         chin, eyes, face, hands, elbows, feet, toes, knees, hips, chest, neck, sword tip/guard/pommel,
         bow, bow loops, bun, root
"""
import bpy
import json
import math
import os
import sys
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector as V, Quaternion as Q, Euler, Matrix

ROOT = "/Users/waylonhuang/Documents/other/pixelart/swordswoman"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None):
    if name in argv:
        return argv[argv.index(name) + 1]
    return default


def flag(name):
    return name in argv


def rel(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
BLEND = rel(arg("--blend", "hybrid/guide/guide.blend"))
OUT = rel(arg("--out", "hybrid/guide"))
RES = int(arg("--res", "1024"))
VIEW = arg("--view", "iso")
PASSES = arg("--passes", "clay,id,line,depth,mask,joints").split(",")
dirs_arg = arg("--dirs", "all")
RUN_DIRS = DIRS if dirs_arg == "all" else dirs_arg.split(",")
PREFIX = arg("--prefix", "f")
CELL = 128
PIVOT = (64, 104)

bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene
vl = bpy.context.view_layer
cam = sc.camera or bpy.data.objects["cam"]
rig = bpy.data.objects["rig"]
ISO_ORTHO = float(arg("--ortho", rig.get("iso_ortho", 7.3)))
LANDMARKS = json.loads(rig.get("landmarks", "{}"))
GUIDE_META = json.loads(rig.get("guide_meta", "{}"))

# ------------------------------------------------------------------ part groups (id pass)
# order = id (1-based); colour = (id*10, G, B) so R alone decodes the id.
PARTS = [
    ("hair",        ("hair_bob", "hair_cap", "bangs", "hair_strands", "hair_streaks", "hair_sheen"), (90, 20)),
    ("bun",         ("bun", "bun_sheen", "bun_crease"), (230, 120)),
    ("bow",         ("bow",), (10, 255)),
    ("face",        ("head", "face_decals"), (200, 255)),
    ("ear",         ("ears",), (200, 150)),
    ("collar",      ("collar", "choker"), (30, 120)),
    ("torso",       ("body_torso", "neck", "bodice", "chest_flower", "chest_cord"), (160, 90)),
    ("corset",      ("corset", "corset_buckles", "corset_tabs", "belt_pouch"), (90, 220)),
    ("skirt",       ("skirt_outer",), (40, 60)),
    ("skirt_under", ("skirt_under",), (10, 140)),
    ("shorts",      ("shorts", "thigh_strap.L"), (250, 20)),
    ("sleeve_L",    ("sleeve.L", "sleeve_band.L"), (200, 30)),
    ("sleeve_R",    ("sleeve.R", "sleeve_band.R", "arm_ornament.R"), (110, 250)),
    ("arm_L",       ("arm.L",), (240, 120)),
    ("arm_R",       ("arm.R",), (60, 250)),
    ("hand_L",      ("hand.L",), (140, 10)),
    ("hand_R",      ("hand.R",), (10, 80)),
    ("leg_L",       ("leg.L",), (180, 230)),
    ("leg_R",       ("leg.R",), (230, 60)),
    ("shoe_L",      ("shoe.L", "foot.L"), (20, 20)),
    ("shoe_R",      ("shoe.R", "foot.R"), (90, 120)),
    ("scarf_L",     ("scarf.L",), (220, 250)),
    ("scarf_R",     ("scarf.R",), (150, 200)),
    ("sword",       ("katana",), (250, 250)),
    ("smear",       ("smear_blade", "smear_trail"), (100, 100)),
]
PART_OF = {o: p for p, objs, _ in PARTS for o in objs}
PART_ID = {p: i + 1 for i, (p, _, _) in enumerate(PARTS)}
PART_RGB = {p: (PART_ID[p] * 10, g, b) for p, _, (g, b) in PARTS}
SPRITE_DROP = ("chest_cord", "chest_flower", "hair_streaks")   # bible: [DROP] on sprites
HIDE_ALWAYS = ("katana_sprite", "katana_sprite_kagi", "saya", "hair_proxy", "head_collider")

for n in HIDE_ALWAYS + SPRITE_DROP:
    o = bpy.data.objects.get(n)
    if o:
        o.hide_render = True
for ob in bpy.data.objects:                     # inverted-hull outlines off (they inflate silhouettes)
    if ob.type == "MESH":
        for m in ob.modifiers:
            if m.name == "Outline":
                m.show_render = False
for n in (arg("--hide", "") or "").split(","):    # debug: hide objects by name
    if n and bpy.data.objects.get(n):
        bpy.data.objects[n].hide_render = True
k = bpy.data.objects.get("katana")
if k:
    k.hide_render = False
BASE_HIDE = {o.name: o.hide_render for o in bpy.data.objects}


# ------------------------------------------------------------------ materials
def emis_mat(name, color=None, objinfo=False, depth=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    if objinfo:
        oi = nt.nodes.new("ShaderNodeObjectInfo")
        nt.links.new(oi.outputs["Color"], em.inputs["Color"])
    elif depth:
        cd = nt.nodes.new("ShaderNodeCameraData")
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.name = "range"
        nt.links.new(cd.outputs["View Z Depth"], mr.inputs["Value"])
        mr.inputs["To Min"].default_value = 1.0
        mr.inputs["To Max"].default_value = 0.0
        mr.clamp = True
        nt.links.new(mr.outputs["Result"], em.inputs["Color"])
    else:
        em.inputs["Color"].default_value = color
    return m


def clay_mat():
    m = bpy.data.materials.new("G_clay")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    d = nt.nodes.new("ShaderNodeBsdfDiffuse")
    d.inputs["Color"].default_value = (0.30, 0.30, 0.30, 1)
    nt.links.new(d.outputs[0], out.inputs["Surface"])
    return m


def holdout_mat():
    m = bpy.data.materials.new("G_holdout")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    h = nt.nodes.new("ShaderNodeHoldout")
    nt.links.new(h.outputs[0], out.inputs["Surface"])
    return m


M_ID = emis_mat("G_id", objinfo=True)
M_MASK = emis_mat("G_mask", color=(1, 1, 1, 1))
M_DEPTH = emis_mat("G_depth", depth=True)
M_CLAY = clay_mat()
M_HOLD = holdout_mat()
for ob in bpy.data.objects:
    if ob.type == "MESH":
        p = PART_OF.get(ob.name)
        c = PART_RGB[p] if p else (0, 0, 0)
        ob.color = (c[0] / 255.0, c[1] / 255.0, c[2] / 255.0, 1)

os.makedirs(OUT, exist_ok=True)
json.dump({"encoding": "R channel = id * 10 (exact, no AA); G/B only make the colours distinct",
           "background": "alpha 0", "unknown": "R=0 (part not in the legend)",
           "parts": {p: {"id": PART_ID[p], "rgb": list(PART_RGB[p]), "hex": "#%02x%02x%02x" % PART_RGB[p],
                         "objects": list(objs)} for p, objs, _ in PARTS},
           "groups": PART_ID},
          open(os.path.join(OUT, "id_legend.json"), "w"), indent=1)

# ------------------------------------------------------------------ freestyle (line pass)
sc.render.use_freestyle = False
sc.render.line_thickness_mode = "ABSOLUTE"
sc.render.line_thickness = max(1.0, RES / 512.0)
fs = vl.freestyle_settings
fs.crease_angle = math.radians(120)
fs.as_render_pass = False
ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new("guide")
ls.select_by_visibility = True
ls.visibility = "VISIBLE"
ls.select_by_edge_types = True
for a in ("select_silhouette", "select_border", "select_crease", "select_contour", "select_external_contour"):
    setattr(ls, a, True)
for a in ("select_material_boundary", "select_suggestive_contour", "select_ridge_valley", "select_edge_mark"):
    setattr(ls, a, False)
ls.linestyle.color = (0, 0, 0)
ls.linestyle.thickness = max(1.0, RES / 512.0)
ls.linestyle.alpha = 1.0


# ------------------------------------------------------------------ camera
def cam_view(direction, yaw_extra=0.0):
    cam.data.type = "ORTHO"
    cam.data.shift_x = cam.data.shift_y = 0
    if VIEW == "iso":
        el = math.radians(30)
        cam.rotation_euler = (math.pi / 2 - el, 0, 0)
        cam.data.ortho_scale = ISO_ORTHO
        fwd = V((0, math.cos(el), -math.sin(el)))
        up = V((0, math.sin(el), math.cos(el)))
        lift = (PIVOT[1] - CELL / 2) / (CELL / ISO_ORTHO)      # world origin -> pivot row
        cam.location = up * lift - fwd * 20
        rig.rotation_euler = (0, 0, math.radians(DIRS.index(direction) * 45.0 + yaw_extra))
    else:                                                       # measurement orthos (no yaw)
        D, zc = 20, float(arg("--zc", "1.62"))
        cam.data.ortho_scale = float(arg("--oscale", "3.9"))
        rig.rotation_euler = (0, 0, 0)
        rot = {"front": (math.pi / 2, 0, 0), "back": (math.pi / 2, 0, math.pi), "side": (math.pi / 2, 0, math.pi / 2)}[VIEW]
        loc = {"front": (0, -D, zc), "back": (0, D, zc), "side": (D, 0, zc)}[VIEW]
        cam.rotation_euler = rot
        cam.location = loc
    vl.update()


# ------------------------------------------------------------------ pose application
POSE_PROPS = ["ik_leg.L", "ik_leg.R", "ik_arm.L", "ik_arm.R", "two_hand", "skirt_follow",
              "expr_wide", "expr_frown", "expr_smile", "expr_hurt", "bow_face_camera"]
DEFAULT_PROPS = {"ik_leg.L": 1.0, "ik_leg.R": 1.0, "ik_arm.L": 0.0, "ik_arm.R": 0.0, "two_hand": 0.0,
                 "skirt_follow": 1.0, "expr_wide": 0.0, "expr_frown": 0.0, "expr_smile": 0.0, "expr_hurt": 0.0,
                 "bow_face_camera": 0.85}
PB_ORDER = []


def _order():
    seen = []

    def walk(b):
        seen.append(b.name)
        for c in b.children:
            walk(c)
    for b in rig.data.bones:
        if b.parent is None:
            walk(b)
    return seen


PB_ORDER = _order()


def reset_pose():
    if rig.animation_data:
        rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)
    for k_, v in DEFAULT_PROPS.items():
        if k_ in rig.keys():
            rig[k_] = v
    for c in ("to_sheath",):
        con = rig.pose.bones["sword"].constraints.get(c) if "sword" in rig.pose.bones else None
        if con:
            con.influence = 0.0
    vl.update()


def action_for(name, d):
    name = name.replace("{D}", d)
    for cand in (f"{name}_{d}", name, f"pose_{name}_{d}", f"pose_{name}"):
        if cand in bpy.data.actions:
            return bpy.data.actions[cand]
    raise KeyError(f"no action {name} for {d}")


def action_frames(act):
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    return list(range(f0, f1 + 1))


def capture():
    """bone locals + props of the current evaluated state"""
    st = {"bones": {}, "props": {}}
    for pb in rig.pose.bones:
        q = pb.rotation_quaternion if pb.rotation_mode == "QUATERNION" else pb.matrix_basis.to_quaternion()
        st["bones"][pb.name] = (V(pb.location), Q(q), V(pb.scale))
    for k_ in POSE_PROPS:
        if k_ in rig.keys():
            st["props"][k_] = float(rig[k_])
    return st


def restore(st):
    if rig.animation_data:
        rig.animation_data.action = None
    for n, (l, q, s) in st["bones"].items():
        pb = rig.pose.bones[n]
        pb.rotation_mode = "QUATERNION"
        pb.location, pb.rotation_quaternion, pb.scale = l, q, s
    for k_, v in st["props"].items():
        rig[k_] = v
    vl.update()


def apply_action(act, frame):
    reset_pose()
    rig.animation_data_create()
    rig.animation_data.action = act
    sc.frame_set(frame)
    vl.update()
    st = capture()
    restore(st)                       # detach the action so pose overrides stick


def load_pose(p, base_dir):
    if isinstance(p, str):
        path = rel(p) if not os.path.exists(p) else p
        return load_pose(json.load(open(path)), os.path.dirname(path))
    if "file" in p:
        f = p["file"]
        path = f if os.path.isabs(f) else os.path.join(base_dir, f)
        q = load_pose(json.load(open(path)), os.path.dirname(path))
        q = dict(q)
        q.update({k_: v for k_, v in p.items() if k_ != "file"})
        return q
    return p


def vertical_axis(bone_name):
    """local axis index of the bone most aligned with armature +Z (rest)"""
    M = rig.data.bones[bone_name].matrix_local.to_3x3()
    cols = [abs(M.col[i].z) for i in range(3)]
    return cols.index(max(cols))


def apply_pose_dict(p, d):
    """see POSE JSON format (hybrid/guide/POSE_FORMAT.md)"""
    if "dir_override" in p and d in p["dir_override"]:
        p = dict(p)
        ov = p.pop("dir_override")[d]
        for k_, v in ov.items():
            if isinstance(v, dict) and isinstance(p.get(k_), dict):
                merged = dict(p[k_])
                merged.update(v)
                p[k_] = merged
            else:
                p[k_] = v
    base = p.get("base", "pose_idle_{D}")
    if base:
        act = action_for(base, d)
        fr = action_frames(act)
        apply_action(act, fr[min(int(p.get("base_frame", 0)), len(fr) - 1)])
    else:
        reset_pose()
    for k_, v in p.get("props", {}).items():
        rig[k_] = float(v)
    vl.update()
    bones = p.get("bones", {})
    root = p.get("root")
    if root:
        bones = dict(bones)
        r = dict(bones.get("root", {}))
        if "loc" in root:
            r["loc_arm"] = root["loc"]
        if "stretch" in root:
            r["stretch"] = root["stretch"]
        if "scale" in root:
            r["scale"] = root["scale"]
        bones["root"] = r
    for name in PB_ORDER:                           # parents first
        if name not in bones:
            continue
        spec = bones[name]
        pb = rig.pose.bones[name]
        pb.rotation_mode = "QUATERNION"
        if "rot" in spec:                           # local XYZ euler deg, replaces
            pb.rotation_quaternion = Euler([math.radians(a) for a in spec["rot"]], "XYZ").to_quaternion()
        if "quat" in spec:
            pb.rotation_quaternion = Q(spec["quat"])
        if "rot_add" in spec:                       # local XYZ euler deg, on top of base
            pb.rotation_quaternion = pb.rotation_quaternion @ Euler([math.radians(a) for a in spec["rot_add"]], "XYZ").to_quaternion()
        if "loc" in spec:
            pb.location = V(spec["loc"])
        if "loc_add" in spec:
            pb.location = pb.location + V(spec["loc_add"])
        if "scale" in spec:
            pb.scale = V(spec["scale"])
        if "stretch" in spec:                       # volume-preserving along the bone's vertical axis
            kk = float(spec["stretch"])
            ax = vertical_axis(name)
            s = [1 / math.sqrt(kk)] * 3
            s[ax] = kk
            pb.scale = V([a * b for a, b in zip(pb.scale, s)])
        vl.update()
        if "rot_arm" in spec or "loc_arm" in spec:  # armature (character) space, about the bone head
            M = pb.matrix.copy()
            if "rot_arm" in spec:
                ra = spec["rot_arm"]                  # [ax, ay, az, deg] or list of them (applied in order)
                ra = ra if isinstance(ra[0], list) else [ra]
                for r_ in ra:
                    R = Matrix.Rotation(math.radians(r_[3]), 4, V(r_[:3]).normalized())
                    t = M.translation.copy()
                    M = R @ M
                    M.translation = t
            if "loc_arm" in spec:
                M.translation = M.translation + V(spec["loc_arm"])
            pb.matrix = M
            vl.update()
    vl.update()
    vl.update()
    return p


def interp_states(a, b, t):
    out = {"bones": {}, "props": {}}
    for n in a["bones"]:
        la, qa, sa = a["bones"][n]
        lb, qb, sb = b["bones"][n]
        out["bones"][n] = (la.lerp(lb, t), qa.slerp(qb, t), sa.lerp(sb, t))
    for k_ in a["props"]:
        out["props"][k_] = a["props"][k_] + (b["props"].get(k_, a["props"][k_]) - a["props"][k_]) * t
    return out


# ------------------------------------------------------------------ landmarks / joints
def lm_world(name):
    """landmark (bone, rest-space point) -> current world position"""
    if name not in LANDMARKS:
        return None
    bname, p = LANDMARKS[name]
    pb = rig.pose.bones[bname]
    b = rig.data.bones[bname]
    return rig.matrix_world @ (pb.matrix @ (b.matrix_local.inverted() @ V(p)))


def bone_pt(bname, t=0.0):
    pb = rig.pose.bones[bname]
    return rig.matrix_world @ pb.head.lerp(pb.tail, t)


JOINT_DEF = {
    "root": lambda: rig.matrix_world @ V((0, 0, 0)),
    "hips": lambda: bone_pt("hips"), "chest": lambda: bone_pt("chest"), "neck": lambda: bone_pt("neck"),
    "head": lambda: lm_world("head_center") or bone_pt("head", 0.4),
    "head_top": lambda: lm_world("head_top") or bone_pt("head", 1.0),
    "chin": lambda: lm_world("chin") or bone_pt("head", 0.0),
    "face": lambda: lm_world("face") or bone_pt("head", 0.3),
    "eye_L": lambda: lm_world("eye_L"), "eye_R": lambda: lm_world("eye_R"),
    "mouth": lambda: lm_world("mouth"),
    "bun": lambda: lm_world("bun") or bone_pt("bun", 0.6),
    "bow": lambda: lm_world("bow") or bone_pt("bow"),
    "bow_loop_L": lambda: lm_world("bow_loop_L"), "bow_loop_R": lambda: lm_world("bow_loop_R"),
    "shoulder_L": lambda: bone_pt("upper_arm.L"), "shoulder_R": lambda: bone_pt("upper_arm.R"),
    "elbow_L": lambda: bone_pt("forearm.L"), "elbow_R": lambda: bone_pt("forearm.R"),
    "wrist_L": lambda: bone_pt("hand.L"), "wrist_R": lambda: bone_pt("hand.R"),
    "hand_L": lambda: bone_pt("hand.L", 0.5), "hand_R": lambda: bone_pt("hand.R", 0.5),
    "knee_L": lambda: bone_pt("shin.L"), "knee_R": lambda: bone_pt("shin.R"),
    "foot_L": lambda: bone_pt("foot.L"), "foot_R": lambda: bone_pt("foot.R"),
    "ankle_L": lambda: bone_pt("foot.L"), "ankle_R": lambda: bone_pt("foot.R"),
    "toe_L": lambda: bone_pt("toe.L", 1.0), "toe_R": lambda: bone_pt("toe.R", 1.0),
    "heel_L": lambda: lm_world("heel_L"), "heel_R": lambda: lm_world("heel_R"),
    "sword_pommel": lambda: lm_world("sword_pommel"), "sword_guard": lambda: lm_world("sword_guard"),
    "sword_tip": lambda: lm_world("sword_tip"), "sword_hook": lambda: lm_world("sword_hook"),
    "scarf_tip_L": lambda: bone_pt("scarf.L.005", 1.0), "scarf_tip_R": lambda: bone_pt("scarf.R.005", 1.0),
    "sleeve_tip_L": lambda: bone_pt(GUIDE_META.get("sleeve_tip_L", "sleeve.L"), 1.0),
    "sleeve_tip_R": lambda: bone_pt(GUIDE_META.get("sleeve_tip_R", "sleeve.R"), 1.0),
    "skirt_tail_tip": lambda: bone_pt("skirt.tail.003", 1.0),
}
ALIASES = {"guard": "sword_guard", "tip": "sword_tip"}


def project(p):
    c = world_to_camera_view(sc, cam, p)
    return [round(c.x * RES, 2), round((1 - c.y) * RES, 2)], c.z


JOINT_OWNER = {   # a joint is 'visible' if the first surface the camera ray meets belongs to its own part
    "eye": ("face_decals", "head"), "mouth": ("face_decals", "head"), "face": ("face_decals", "head"),
    "chin": ("head", "face_decals"), "head": ("hair_bob", "head", "face_decals", "bun", "bow"),
    "bun": ("bun", "bun_crease", "bun_sheen"), "bow": ("bow",), "hand_L": ("hand.L",), "hand_R": ("hand.R",),
    "wrist_L": ("hand.L", "arm.L"), "wrist_R": ("hand.R", "arm.R"), "elbow_L": ("arm.L", "sleeve.L"),
    "elbow_R": ("arm.R", "sleeve.R"), "shoulder_L": ("arm.L", "body_torso", "sleeve_band.L"),
    "shoulder_R": ("arm.R", "body_torso", "sleeve_band.R"), "knee_L": ("leg.L",), "knee_R": ("leg.R",),
    "foot_L": ("shoe.L", "foot.L", "leg.L"), "foot_R": ("shoe.R", "foot.R", "leg.R"), "ankle": ("shoe", "foot", "leg"),
    "toe_L": ("shoe.L", "foot.L"), "toe_R": ("shoe.R", "foot.R"), "heel_L": ("shoe.L",), "heel_R": ("shoe.R",),
    "sword": ("katana",), "scarf_tip_L": ("scarf.L",), "scarf_tip_R": ("scarf.R",),
    "sleeve_tip_L": ("sleeve.L",), "sleeve_tip_R": ("sleeve.R",), "skirt": ("skirt_outer", "skirt_under"),
    "hips": ("body_torso", "corset", "shorts", "skirt_outer", "belt_pouch", "corset_tabs", "corset_buckles"),
    "chest": ("body_torso", "bodice", "corset", "collar", "chest_flower"), "neck": ("neck", "collar", "choker", "body_torso"),
    "root": (),
}


def visible(p, dg, name=""):
    cdir = cam.matrix_world.to_3x3() @ V((0, 0, -1))
    origin = p - cdir * 50.0
    start = origin
    for _ in range(12):                  # skip render-hidden helpers (colliders, proxies)
        hit, loc, nrm, idx, ob, _m = sc.ray_cast(dg, start, cdir, distance=60.0)
        if not hit or (loc - origin).length >= 50.0 - 0.04:
            return True
        if ob is not None and ob.hide_render:
            start = loc + cdir * 1e-3
            continue
        break
    owners = next((v for k_, v in sorted(JOINT_OWNER.items(), key=lambda kv: -len(kv[0])) if name.startswith(k_)), ())
    return bool(ob and ob.name.split(".0")[0] in owners or (ob and ob.name in owners))


def joints_now():
    dg = bpy.context.evaluated_depsgraph_get()
    out = {}
    for n, fn in JOINT_DEF.items():
        try:
            p = fn()
        except KeyError:
            p = None
        if p is None:
            continue
        xy, depth = project(p)
        out[n] = {"px": xy, "cell": [round(xy[0] / RES * CELL, 2), round(xy[1] / RES * CELL, 2)],
                  "depth": round(depth, 4), "visible": visible(p, dg, n), "world": [round(c, 4) for c in p]}
    for a, b in ALIASES.items():
        if b in out:
            out[a] = out[b]
    return out


# ------------------------------------------------------------------ smear helpers
def _smear_obj(name):
    ob = bpy.data.objects.get(name)
    if ob is None:
        me = bpy.data.meshes.new(name)
        ob = bpy.data.objects.new(name, me)
        sc.collection.objects.link(ob)
    ob.parent = None
    ob.matrix_world = Matrix.Identity(4)
    return ob


def build_smears(smears, state_from, state_to, d):
    """smears: list of {kind: blade|trail, from: pose (or 'prev'), steps, inner, outer, bone, t, radius}
    Sweeps are built in world space from poses interpolated (slerp) between 'from' and this frame,
    so a blade smear follows the true arc.  Returns list of smear objects (shown this frame)."""
    objs = []
    for si, sm in enumerate(smears):
        kind = sm.get("kind", "blade")
        steps = int(sm.get("steps", 8))
        span = sm.get("span", [0.0, 1.0])            # fraction of the from->to interpolation covered
        pts = []
        samples = []
        if sm.get("path"):                           # explicit swing-path poses (true arc, not a slerp)
            for pf in sm["path"]:
                apply_pose_dict(load_pose(pf if os.path.isabs(pf) else os.path.join(SMEAR_BASE, pf), SMEAR_BASE), d)
                samples.append(capture())
        else:
            for i in range(steps + 1):
                t = span[0] + (span[1] - span[0]) * i / steps
                samples.append(interp_states(state_from, state_to, t))
        for st_ in samples:
            restore(st_)
            if kind == "blade":
                g = lm_world("sword_guard")
                tip = lm_world("sword_tip")
                a = g.lerp(tip, float(sm.get("inner", 0.35)))
                b = g.lerp(tip, float(sm.get("outer", 1.0)))
                pts.append((a, b))
            else:
                bn = sm.get("bone", "hand.L")
                pts.append(bone_pt(bn, float(sm.get("t", 1.0))))
        restore(state_to)
        name = "smear_blade" if kind == "blade" else "smear_trail"
        if si:
            name = f"{name}.{si:03d}"
            PART_OF[name] = "smear"
        ob = _smear_obj(name)
        me = bpy.data.meshes.new(name + "_m")
        verts, faces = [], []
        if kind == "blade":
            # ribbon; the leading edge (latest sample) is full width, the tail tapers toward the outer
            # edge (classic crescent smear)
            taper = float(sm.get("taper", 0.85))
            n = len(pts)
            for i, (a, b) in enumerate(pts):
                age = 1 - i / max(1, n - 1)                 # 1 = oldest
                a2 = a.lerp(b, taper * age)
                verts += [a2, b]
            for i in range(n - 1):
                faces.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
        else:
            r0 = float(sm.get("radius", 0.08))
            ring = 8
            n = len(pts)
            for i, p in enumerate(pts):
                fwd = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)])
                fwd = fwd.normalized() if fwd.length > 1e-6 else V((0, 0, 1))
                up = V((0, 0, 1)) if abs(fwd.z) < 0.9 else V((1, 0, 0))
                x = fwd.cross(up).normalized()
                y = fwd.cross(x).normalized()
                r = r0 * (0.15 + 0.85 * i / max(1, n - 1))
                for j in range(ring):
                    a = 2 * math.pi * j / ring
                    verts.append(p + (x * math.cos(a) + y * math.sin(a)) * r)
            for i in range(n - 1):
                for j in range(ring):
                    j2 = (j + 1) % ring
                    faces.append((i * ring + j, i * ring + j2, (i + 1) * ring + j2, (i + 1) * ring + j))
        me.from_pydata([tuple(v) for v in verts], [], faces)
        me.update()
        old = ob.data
        ob.data = me
        if old and old.users == 0:
            bpy.data.meshes.remove(old)
        c = PART_RGB["smear"]
        ob.color = (c[0] / 255.0, c[1] / 255.0, c[2] / 255.0, 1)
        sol = ob.modifiers.get("thick") or ob.modifiers.new("thick", "SOLIDIFY")
        sol.thickness = 0.01
        ob.hide_render = False
        objs.append(ob)
    vl.update()
    return objs


def hide_smears():
    for ob in bpy.data.objects:
        if ob.name.startswith(("smear_blade", "smear_trail")):
            ob.hide_render = True


# ------------------------------------------------------------------ render passes
def render_to(path, aa=True, raw=False, depth16=False):
    r = sc.render
    r.resolution_x = r.resolution_y = RES
    r.resolution_percentage = 100
    r.film_transparent = True
    r.filter_size = 1.5 if aa else 0.0
    sc.eevee.taa_render_samples = 16 if aa else 1
    sc.view_settings.view_transform = "Raw" if raw else "Standard"
    sc.view_settings.look = "None"
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGBA"
    r.image_settings.color_depth = "16" if depth16 else "8"
    r.dither_intensity = 0.0
    r.filepath = path
    bpy.ops.render.render(write_still=True)


def set_world(strength):
    w = sc.world
    if w and w.node_tree:
        bg = w.node_tree.nodes.get("Background")
        if bg:
            bg.inputs[0].default_value = (1, 1, 1, 1)
            bg.inputs[1].default_value = strength


def render_frame(base, d, smear_objs):
    cam_dist = (cam.matrix_world.inverted() @ (rig.matrix_world @ V((0, 0, 1.4)))).z
    near, far = -cam_dist - 1.8, -cam_dist + 1.8
    M_DEPTH.node_tree.nodes["range"].inputs["From Min"].default_value = near
    M_DEPTH.node_tree.nodes["range"].inputs["From Max"].default_value = far
    out = {}
    if "clay" in PASSES:                       # body only; the smear sweep is its own pass (smear_mask)
        vl.material_override = M_CLAY
        for o in smear_objs:
            o.hide_render = True
        set_world(0.12)
        render_to(base + "_clay.png")
        set_world(0.0)
        for o in smear_objs:
            o.hide_render = False
    if "color" in PASSES:                      # optional: the model's own toon materials (debug only)
        vl.material_override = None
        render_to(base + "_color.png")
    if "id" in PASSES:
        vl.material_override = M_ID
        render_to(base + "_id.png", aa=False, raw=True)
    if "depth" in PASSES:
        vl.material_override = M_DEPTH
        render_to(base + "_depth.png", aa=True, raw=True, depth16=True)
    if "mask" in PASSES or "smear_mask" in PASSES:
        vl.material_override = M_MASK
        for o in smear_objs:
            o.hide_render = True
        if "mask" in PASSES:
            render_to(base + "_mask.png", aa=True, raw=True)
        if smear_objs:
            meshes = [o for o in bpy.data.objects if o.type == "MESH"]
            st = {o.name: o.hide_render for o in meshes}
            for o in meshes:
                o.hide_render = True
            for o in smear_objs:
                o.hide_render = False
            render_to(base + "_mask_smear.png", aa=True, raw=True)
            for o in meshes:
                o.hide_render = st[o.name]
        for o in smear_objs:
            o.hide_render = False
    if "line" in PASSES:
        vl.material_override = M_HOLD
        sc.render.use_freestyle = True
        render_to(base + "_line.png", aa=True)
        sc.render.use_freestyle = False
    vl.material_override = None
    out["depth_range"] = {"near": round(near, 3), "far": round(far, 3), "encoding": "16-bit grey, 1 = near (camera View Z)"}
    return out


# ------------------------------------------------------------------ jobs
def frame_jobs():
    """yields (frame_index, kind, payload)"""
    if arg("--pose"):
        fi = int(arg("--frames", "0"))
        yield fi, "pose", load_pose(rel(arg("--pose")), os.path.dirname(rel(arg("--pose"))))
        return
    if arg("--anim-json"):
        path = rel(arg("--anim-json"))
        J = json.load(open(path))
        frames = J["frames"] if isinstance(J, dict) else J
        sel = arg("--frames", "all")
        idx = range(len(frames)) if sel == "all" else parse_frames(sel, len(frames))
        for i in idx:
            yield i, "pose", load_pose(frames[i], os.path.dirname(path))
        return
    if arg("--action"):
        yield from (("ACTION", arg("--action"), arg("--frames", "0")),)
        return
    yield 0, "pose", {"base": "pose_idle_{D}"}


def parse_frames(sel, n):
    if sel == "all":
        return list(range(n))
    out = []
    for part in sel.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return [i for i in out if i < n]


SMEAR_BASE = os.path.dirname(rel(arg("--anim-json") or arg("--pose") or "x"))
ANIM = arg("--anim") or (arg("--action", "idle").replace("{D}", "").replace("pose_", "").replace("anim_", "").strip("_")
                         if not arg("--anim-json") else
                         ((json.load(open(rel(arg("--anim-json")))) if True else {}).get("name") if isinstance(json.load(open(rel(arg("--anim-json")))), dict) else None)
                         or os.path.splitext(os.path.basename(arg("--anim-json")))[0])
if arg("--pose") and not arg("--anim"):
    ANIM = os.path.splitext(os.path.basename(arg("--pose")))[0]
if VIEW != "iso":
    ANIM = f"{ANIM}_{VIEW}"
    RUN_DIRS = [RUN_DIRS[0]]

summary = []
jobs = list(frame_jobs())
for d in RUN_DIRS:
    cam_view(d)
    odir = os.path.join(OUT, ANIM, d if VIEW == "iso" else VIEW)
    os.makedirs(odir, exist_ok=True)
    prev_state = None
    expanded = []
    for j in jobs:
        if j[0] == "ACTION":
            act = action_for(j[1], d)
            fr = action_frames(act)
            for i in parse_frames(j[2], len(fr)):
                expanded.append((i, "action", (act, fr[i])))
        else:
            expanded.append(j)
    for fi, kind, payload in expanded:
        hide_smears()
        yaw_extra = 0.0
        smears = []
        if kind == "action":
            apply_action(*payload)
        else:
            p = apply_pose_dict(payload, d)
            yaw_extra = float(p.get("root", {}).get("yaw_deg", 0.0)) if p.get("root") else 0.0
            smears = p.get("smears", p.get("smear", []))
            if isinstance(smears, dict):
                smears = [smears]
        if yaw_extra:
            cam_view(d, yaw_extra)
        state = capture()
        smear_objs = []
        if smears:
            for sm in smears:
                src = sm.get("from", "prev")
                if sm.get("path"):
                    sfrom = None
                elif src == "prev":
                    sfrom = prev_state
                else:
                    apply_pose_dict(load_pose(src, os.path.dirname(rel(arg("--anim-json") or arg("--pose") or "x"))), d)
                    sfrom = capture()
                    restore(state)
                if sfrom is None and not sm.get("path"):
                    continue
                smear_objs += build_smears([sm], sfrom, state, d)
        restore(state)
        base = os.path.join(odir, f"{PREFIX}{fi:02d}")
        info = render_frame(base, d, smear_objs) if any(x in PASSES for x in ("clay", "color", "id", "line", "depth", "mask", "smear_mask")) else {}
        if "joints" in PASSES:
            J = {"dir": d, "frame": fi, "view": VIEW, "space": "px", "size": [RES, RES], "cell": CELL,
                 "pivot_px": [PIVOT[0] * RES / CELL, PIVOT[1] * RES / CELL], "iso_ortho": ISO_ORTHO,
                 "px_per_H": round(RES / ISO_ORTHO, 3) if VIEW == "iso" else None,
                 "joints": joints_now(), **info,
                 "smears": [o.name for o in smear_objs]}
            json.dump(J, open(base + "_joints.json", "w"), indent=1)
        hide_smears()
        prev_state = state
        if yaw_extra:
            cam_view(d)
        summary.append(base)
        print("[guide]", base, flush=True)
print("[guide done]", len(summary), "frames ->", os.path.join(OUT, ANIM))
