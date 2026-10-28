"""Render turnaround + isometric views of model/character.blend (round 6).

Run:
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P model/render_turnaround.py [-- --round N] [-- --quick]

Writes renders/model_round_N/:
  ortho_front/side/back/34.png (1024)    relaxed idle pose (Actions pose_idle_<D>)
  iso_<DIR>.png (512)                    iso game camera, ortho, 30 deg elevation, transparent
  iso_<DIR>_64.png (128x128 cell)        rendered directly at sprite scale (char ~58 px tall,
                                         feet pivot at (64,104) per design bible section 5),
                                         no AA, sprite katana variant, exact palette colours,
                                         inverted hull + material rim OFF; sprite_post.py adds the
                                         1 px exterior outline, the clean pink rim and the clean-up
  pose_test.png (512) + pose_test_64.png sword_ready (refs/2) from iso SE (+ front/side orthos)
  pose_<name>_<DIR>.png (+ _64)          walk_contact / jump_apex / run_stride / overhead /
                                         attack_slash_mid from SE + NW
  anim_<idle|walk>_SE.png (+ _64)        keyframed 8-frame cycles, every frame, as strips
  _masks/                                raw cells, sword-only / body-only masks and the object-ID
                                         pass (material override, exact colours) for sprite_post
  checks.json, sheet.png, sheet_readability.png
"""
import bpy, sys, os, json, math, subprocess
from mathutils import Vector as V

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ROUND = 8
if "--round" in argv:
    ROUND = int(argv[argv.index("--round") + 1])
QUICK = "--quick" in argv
ISO_ONLY = "--iso" in argv          # round 4: fast iteration (orthos + 8 iso + sprite cells only)
NO_ANIM = "--noanim" in argv        # round 4: everything except the 8-direction cycle cells
OUT = os.path.join(ROOT, "renders", f"model_round_{ROUND}") if not QUICK else "/tmp/akane_quick"
os.makedirs(OUT, exist_ok=True)
MASKDIR = os.path.join(OUT, "_masks")
os.makedirs(MASKDIR, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "character.blend"))
sc = bpy.context.scene
cam = bpy.data.objects["cam"]
rig = bpy.data.objects["rig"]

DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
ISO_ORTHO = float(rig.get("iso_ortho", 6.5))   # round 4: 7.3 H across a 128 px cell => 17.5 px / H
CELL = 128
PIVOT = (64, 104)

# ---------------------------------------------------------------- object-ID pass groups
ID_GROUPS = {
    "hair": ("hair_cap", "bangs", "hair_strands", "hair_streaks"), "sheen": ("hair_sheen",),
    "bun": ("bun", "bun_sheen", "bun_crease"),   # round 5: own id -> bun/skull separation in sprite_post
    "bow": ("bow",), "face": ("head", "face_decals"), "ear": ("ears",), "corset": ("corset",),
    "buckles": ("corset_buckles",), "pouch": ("belt_pouch", "corset_tabs"), "skirt": ("skirt_outer",),
    "skirt_under": ("skirt_under",), "sleeve": ("sleeve.L", "sleeve.R", "sleeve_band.L", "sleeve_band.R"),
    "ornament": ("arm_ornament.R",), "scarf": ("scarf.L", "scarf.R"), "sword": ("katana_sprite", "katana"),
    "arm": ("arm.L", "arm.R"), "hand": ("hand.L", "hand.R"),
    # round 5: legs split per side (SW leg separation in sprite_post)
    "leg_L": ("leg.L", "foot.L", "shoe.L"), "leg_R": ("leg.R", "foot.R", "shoe.R"), "collar": ("collar", "choker"),
    "torso": ("body_torso", "neck", "bodice", "chest_flower", "chest_cord"),
    "shorts": ("shorts",), "thigh_strap": ("thigh_strap.L",),
    "kagi": ("katana_sprite_kagi",),          # round 4: own id -> hook_px check + steel[0] outline
}
GROUP_ID = {g: i + 1 for i, g in enumerate(ID_GROUPS)}


def srgb_to_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def make_id_material():
    m = bpy.data.materials.new("M_objid")
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
    for g, names in ID_GROUPS.items():
        for n in names:
            o = bpy.data.objects.get(n)
            if o:
                o.color = (srgb_to_lin(GROUP_ID[g] * 10 / 255.0), 0, 0, 1)
    return m


M_ID = make_id_material()
json.dump({"groups": GROUP_ID, "encoding": "R channel = id * 10"}, open(os.path.join(MASKDIR, "id_groups.json"), "w"))
RIM_NODES = [(m, n) for m in bpy.data.materials if m.node_tree for n in m.node_tree.nodes if n.name == "rim_thresh"]


def set_rim(on):
    for m, n in RIM_NODES:
        n.inputs[1].default_value = 0.78 if on else 2.0


def set_outline(px_world):
    for ob in bpy.data.objects:
        m = ob.modifiers.get("Outline") if ob.type == "MESH" else None
        if m:
            m.show_render = px_world > 0
            m.thickness = px_world * ob.get("outline_px", 1.5)


def set_sword(sprite):
    bpy.data.objects["katana"].hide_render = sprite
    for n in ("katana_sprite", "katana_sprite_kagi"):
        bpy.data.objects[n].hide_render = not sprite


def apply_action(name, frame=1):
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = bpy.data.actions[name]
    sc.frame_set(frame)
    bpy.context.view_layer.update()


def apply_pose(name):
    """Poses are stored as 1-frame Actions (pose library) named pose_<name>."""
    apply_action(f"pose_{name}")


def idle_for(d):
    name = f"idle_{d}"
    apply_pose(name if f"pose_{name}" in bpy.data.actions else "idle")


def render(path, res_x, res_y=None, aa=True):
    r = sc.render
    r.resolution_x = res_x
    r.resolution_y = res_y or res_x
    r.resolution_percentage = 100
    r.filter_size = 1.5 if aa else 0.0
    sc.eevee.taa_render_samples = 16 if aa else 1
    r.filepath = path
    bpy.ops.render.render(write_still=True)
    print("[render]", path)


def cam_ortho(view, scale=3.9, zc=1.62):
    cam.data.ortho_scale = scale
    cam.data.shift_x = cam.data.shift_y = 0
    rig.rotation_euler = (0, 0, 0)
    D = 20
    if view == "front":
        cam.rotation_euler = (math.pi / 2, 0, 0)
        cam.location = (0, -D, zc)
    elif view == "back":
        cam.rotation_euler = (math.pi / 2, 0, math.pi)
        cam.location = (0, D, zc)
    elif view == "side":      # from HER LEFT (+X): she faces screen-left
        cam.rotation_euler = (math.pi / 2, 0, math.pi / 2)
        cam.location = (D, 0, zc)
    elif view == "34":        # front-left three-quarter, 10 deg elevation
        el = math.radians(10)
        cam.rotation_euler = (math.pi / 2 - el, 0, math.radians(45))
        d = V((math.sin(math.radians(45)) * math.cos(el), -math.cos(math.radians(45)) * math.cos(el), math.sin(el)))
        cam.location = V((0, 0, zc)) + d * D


def cam_iso(direction):
    el = math.radians(30)
    cam.rotation_euler = (math.pi / 2 - el, 0, 0)
    cam.data.ortho_scale = ISO_ORTHO
    cam.data.shift_x = cam.data.shift_y = 0
    fwd = V((0, math.cos(el), -math.sin(el)))
    up = V((0, math.sin(el), math.cos(el)))
    px_per_h = CELL / ISO_ORTHO
    lift = (PIVOT[1] - CELL / 2) / px_per_h       # world origin lands on pivot row
    cam.location = up * lift - fwd * 20
    yaw = DIRS.index(direction) * 45.0           # character rotates, camera stays
    rig.rotation_euler = (0, 0, math.radians(yaw))


# round 4 (AD 'S chest cluster'): the chest flower is dropped on sprites too; sprite_post keeps
# <= 3 red[3] highlight pixels merged with the arm-flower cluster instead
SPRITE_DROP = ("chest_cord", "corset_tabs", "chest_flower", "hair_streaks")


def render_sprite(path, masks=True):
    """128 cell at sprite scale: no AA, sprite katana, no inverted hull, no material rim.  The raw
    render goes to _masks/raw_<name>; sprite_post.py does outline + rim + clean-up."""
    tag = os.path.basename(path)[:-4]
    set_sword(True)
    set_outline(0)
    set_rim(False)
    for n in SPRITE_DROP:            # bible: [DROP] on sprites (chest cord + gem)
        bpy.data.objects[n].hide_render = True
    render(os.path.join(MASKDIR, "raw_" + os.path.basename(path)), CELL, aa=False)
    if masks:
        render_masks(tag)
    for n in SPRITE_DROP:
        bpy.data.objects[n].hide_render = False
    set_rim(True)


def render_masks(tag):
    """Object-ID pass (occlusion-correct) + sword-only / body-only alpha masks at sprite scale."""
    vl = bpy.context.view_layer
    vl.material_override = M_ID
    render(os.path.join(MASKDIR, f"{tag}_id.png"), CELL, aa=False)
    vl.material_override = None
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    state = {o.name: o.hide_render for o in meshes}
    for o in meshes:
        o.hide_render = state[o.name] or not o.name.startswith("katana_sprite")
    render(os.path.join(MASKDIR, f"{tag}_sword.png"), CELL, aa=False)
    for o in meshes:
        o.hide_render = state[o.name] or o.name.startswith("katana")
    render(os.path.join(MASKDIR, f"{tag}_body.png"), CELL, aa=False)
    for o in meshes:
        o.hide_render = state[o.name]


# ---- round 7: --cells FILE re-renders ONLY the listed sprite cells (one tag per line, e.g.
# anim_run_E_f0 / pose_run_stride_NW / iso_SE), then re-runs sprite_post + make_sheet.  Used after
# model/solve_gates.py, so only the re-solved cells are rendered again.
CELLS = None
if "--cells" in argv:
    CELLS = [l.strip().replace("_64", "") for l in open(argv[argv.index("--cells") + 1]) if l.strip()]


def setup_cell(tag):
    if tag.startswith("iso_"):
        d = tag[4:]
        idle_for(d)
        cam_iso(d)
        return True
    if tag == "pose_test":
        apply_pose("sword_ready")
        cam_iso("SE")
        return True
    if tag == "pose_sword_ready_NW":
        apply_pose("sword_ready")
        cam_iso("NW")
        return True
    if tag.startswith("pose_"):
        body, d = tag.rsplit("_", 1)
        apply_action(body)
        cam_iso(d)
        return True
    if tag.startswith("anim_"):
        body, fk = tag.rsplit("_f", 1)
        base, d = body.rsplit("_", 1)
        an = f"{base}_{d}" if f"{base}_{d}" in bpy.data.actions else base
        act = bpy.data.actions[an]
        f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        cyc = json.loads(rig.get("cycles", "{}")).get(base, {})
        cyclic = base in ("anim_idle", "anim_walk") or cyc.get("cyclic", False)
        frames = list(range(f0, f1)) if cyclic else list(range(f0, f1 + 1))
        apply_action(an, frames[int(fk)])
        cam_iso(d)
        return True
    return False


if CELLS is not None:
    for tag in CELLS:
        if setup_cell(tag):
            if tag.startswith(("iso_", "pose_")):     # the 512 AA view of the same pose too
                set_sword(False)
                set_outline(ISO_ORTHO / 512 * 1.1)
                render(os.path.join(OUT, f"{tag}.png"), 512)
            render_sprite(os.path.join(OUT, f"{tag}_64.png"))
    py = os.path.join(ROOT, ".venv", "bin", "python")
    subprocess.run([py, os.path.join(HERE, "sprite_post.py"), OUT], check=False)
    subprocess.run([py, os.path.join(HERE, "make_sheet.py"), OUT, str(ROUND)], check=False)
    print("[done cells]", len(CELLS), OUT)
    sys.exit(0)

# ---- orthographic turnaround (1024)
set_sword(False)
for v in (("front", "side", "back", "34") if not QUICK else ("front", "side", "back")):
    idle_for({"front": "S", "side": "W", "back": "N", "34": "SW"}[v])   # side = seen from her left
    cam_ortho(v)
    set_outline(3.9 / 1024 * 1.6)
    render(os.path.join(OUT, f"ortho_{v}.png"), 1024)

# ---- iso 8 directions (512, AA) and sprite-scale (128 cell, no AA, sprite katana)
for d in (DIRS if not QUICK else ["S", "SE", "E", "NE", "N"]):
    idle_for(d)
    cam_iso(d)
    set_sword(False)
    set_outline(ISO_ORTHO / 512 * 1.1)
    render(os.path.join(OUT, f"iso_{d}.png"), 512)
    render_sprite(os.path.join(OUT, f"iso_{d}_64.png"))

# ---- pose tests (rig proof)
POSE_SHOTS = [("sword_ready", "SE", "pose_test"), ("sword_ready", "NW", "pose_sword_ready_NW")]
for pn in ("walk_contact", "jump_apex", "run_stride", "overhead", "attack_slash_mid"):
    if f"pose_{pn}" not in bpy.data.actions:
        continue
    for d in ("SE", "NW"):
        POSE_SHOTS.append((pn, d, f"pose_{pn}_{d}"))
if ISO_ONLY:
    POSE_SHOTS = POSE_SHOTS[:1]
if QUICK:
    POSE_SHOTS = POSE_SHOTS[:1] + [s for s in POSE_SHOTS if s[1] == "SE" and s[0] in ("run_stride", "jump_apex")]
for pn, d, fn in POSE_SHOTS:
    apply_pose(pn)
    cam_iso(d)
    set_sword(False)
    set_outline(ISO_ORTHO / 512 * 1.1)
    render(os.path.join(OUT, f"{fn}.png"), 512)
    render_sprite(os.path.join(OUT, f"{fn}_64.png"))
apply_pose("sword_ready")
set_sword(False)
for v in ("front", "side"):
    cam_ortho(v)
    set_outline(3.9 / 512 * 1.6)
    render(os.path.join(OUT, f"pose_test_{v}.png"), 512)

# ---- keyframed cycles (animation proof).  Round 4 (GD/TA): every frame in ALL 8 directions at
# sprite scale (per-direction Actions anim_<idle|walk>_<D>), plus 256 px renders for SE
if not QUICK and not ISO_ONLY and not NO_ANIM:
    for base in ("anim_idle", "anim_walk"):
        for d in DIRS:
            an = f"{base}_{d}" if f"{base}_{d}" in bpy.data.actions else base
            if an not in bpy.data.actions:
                continue
            act = bpy.data.actions[an]
            f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
            for f in range(f0, f1):
                apply_action(an, f)
                cam_iso(d)
                if d == "SE":
                    set_sword(False)
                    set_outline(ISO_ORTHO / 256 * 1.1)
                    render(os.path.join(MASKDIR, f"{base}_SE_f{f - f0}.png"), 256)
                render_sprite(os.path.join(OUT, f"{base}_{d}_f{f - f0}_64.png"), masks=True)

# ---- round 5 (TA): timed Actions (run 8f cyclic, jump 3-phase 8f, slash 6f, overhead slash 8f),
# every frame from iso SE at 256 + sprite scale, and the overhead slash also from NW
TIMED = ("anim_run", "anim_jump", "anim_slash", "anim_overhead_slash")
if not QUICK and not ISO_ONLY:
    for an in TIMED:
        if an not in bpy.data.actions:
            continue
        act = bpy.data.actions[an]
        cyc = json.loads(rig.get("cycles", "{}")).get(an, {})
        f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        frames = range(f0, f1) if cyc.get("cyclic", False) else range(f0, f1 + 1)
        # round 6 (TA 'direction coverage'): every timed Action in ALL 8 directions, using the
        # per-direction variant anim_<x>_<D> (presentation turn + per-frame sword fixes); 256 px
        # strips for SE and NW
        for d in DIRS:
            van = f"{an}_{d}" if f"{an}_{d}" in bpy.data.actions else an
            for k, f in enumerate(frames):
                apply_action(van, f)
                cam_iso(d)
                if d in ("SE", "NW"):
                    set_sword(False)
                    set_outline(ISO_ORTHO / 256 * 1.1)
                    render(os.path.join(MASKDIR, f"{an}_{d}_f{k}.png"), 256)
                render_sprite(os.path.join(OUT, f"{an}_{d}_f{k}_64.png"), masks=True)

rig.animation_data.action = bpy.data.actions["pose_rest"]
sc.frame_set(1)
rig.rotation_euler = (0, 0, 0)

py = os.path.join(ROOT, ".venv", "bin", "python")
subprocess.run([py, os.path.join(HERE, "sprite_post.py"), OUT], check=False)
subprocess.run([py, os.path.join(HERE, "make_sheet.py"), OUT, str(ROUND)], check=False)
print("[done]", OUT)
