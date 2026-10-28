"""Render turnaround + isometric views of model/character.blend.

Run:
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P model/render_turnaround.py [-- --round N] [-- --quick]

Writes renders/model_round_N/:
  ortho_front/side/back/34.png (1024)    relaxed idle pose (Action pose_idle)
  iso_<DIR>.png (512)                    iso game camera, ortho, 30 deg elevation, transparent
  iso_<DIR>_64.png (128x128 cell)        rendered directly at sprite scale (char ~56 px tall,
                                         feet pivot at (64,104) per design bible section 5),
                                         no AA, sprite katana variant, exact palette colours,
                                         inverted hull OFF + pipeline 1 px exterior outline
  pose_test.png (512) + pose_test_64.png sword_ready (refs/2) from iso SE
  pose_<name>_<DIR>.png                  walk_contact / jump_apex / run_stride / overhead from SE + NW
  checks.json                            automated per-direction sprite checks (blade/hook pixels,
                                         blade outside the body silhouette, palette, semi-alpha)
  sheet.png, sheet_readability.png       contact sheets (make_sheet.py)
"""
import bpy, sys, os, json, math, subprocess
from mathutils import Vector as V, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ROUND = 2
if "--round" in argv:
    ROUND = int(argv[argv.index("--round") + 1])
QUICK = "--quick" in argv
OUT = os.path.join(ROOT, "renders", f"model_round_{ROUND}") if not QUICK else "/tmp/akane_quick"
os.makedirs(OUT, exist_ok=True)
MASKDIR = os.path.join(OUT, "_masks")
os.makedirs(MASKDIR, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "character.blend"))
sc = bpy.context.scene
cam = bpy.data.objects["cam"]
rig = bpy.data.objects["rig"]

DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
ISO_ORTHO = 6.5          # world units (H) across a 128 px cell => ~19.7 px / H
CELL = 128
PIVOT = (64, 104)


def set_outline(px_world):
    for ob in bpy.data.objects:
        m = ob.modifiers.get("Outline") if ob.type == "MESH" else None
        if m:
            m.show_render = px_world > 0
            m.thickness = px_world * ob.get("outline_px", 1.5)


def set_sword(sprite):
    bpy.data.objects["katana"].hide_render = sprite
    bpy.data.objects["katana_sprite"].hide_render = not sprite


def apply_pose(name):
    """Poses are stored as 1-frame Actions (pose library) named pose_<name>."""
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = bpy.data.actions[f"pose_{name}"]
    sc.frame_set(1)
    bpy.context.view_layer.update()


def idle_for(d):
    """Idle pose for an iso direction (E/W use the per-direction idle_<D> variants)."""
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


def cam_ortho(view, scale=3.7, zc=1.55):
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


def render_sprite(path):
    """128 cell at sprite scale: no AA, sprite katana, no inverted hull.  The raw render goes to
    _masks/raw_<name>; sprite_post.py adds the pipeline 1 px outline and writes <name>."""
    set_sword(True)
    set_outline(0)
    render(os.path.join(MASKDIR, "raw_" + os.path.basename(path)), CELL, aa=False)


def render_masks(tag):
    """Sword-only and body-only alpha masks at sprite scale (for the automated checks)."""
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    state = {o.name: o.hide_render for o in meshes}
    set_sword(True)
    set_outline(0)
    for o in meshes:
        o.hide_render = state[o.name] or o.name != "katana_sprite"
    render(os.path.join(MASKDIR, f"{tag}_sword.png"), CELL, aa=False)
    for o in meshes:
        o.hide_render = state[o.name] or o.name.startswith("katana")
    render(os.path.join(MASKDIR, f"{tag}_body.png"), CELL, aa=False)
    for o in meshes:
        o.hide_render = state[o.name]


apply_pose("idle")
# ---- orthographic turnaround (1024)
set_sword(False)
for v in (("front", "side", "back", "34") if not QUICK else ("front", "side", "back")):
    idle_for({"front": "S", "side": "W", "back": "N", "34": "SW"}[v])   # side = seen from her left
    cam_ortho(v)
    set_outline(3.7 / 1024 * 1.6)
    render(os.path.join(OUT, f"ortho_{v}.png"), 1024)

# ---- iso 8 directions (512, AA) and sprite-scale (128 cell, no AA, sprite katana)
for d in (DIRS if not QUICK else ["S", "E", "SE", "NW", "N"]):
    idle_for(d)
    cam_iso(d)
    set_sword(False)
    set_outline(ISO_ORTHO / 512 * 1.1)
    render(os.path.join(OUT, f"iso_{d}.png"), 512)
    render_sprite(os.path.join(OUT, f"iso_{d}_64.png"))
    render_masks(f"iso_{d}")

# ---- pose tests (rig proof)
POSE_SHOTS = [("sword_ready", "SE", "pose_test")]
for pn in ("walk_contact", "jump_apex", "run_stride", "overhead"):
    for d in ("SE", "NW"):
        POSE_SHOTS.append((pn, d, f"pose_{pn}_{d}"))
if QUICK:
    POSE_SHOTS = POSE_SHOTS[:1] + [("walk_contact", "SE", "pose_walk_contact_SE"),
                                   ("jump_apex", "SE", "pose_jump_apex_SE")]
for pn, d, fn in POSE_SHOTS:
    apply_pose(pn)
    cam_iso(d)
    set_sword(False)
    set_outline(ISO_ORTHO / 512 * 1.1)
    render(os.path.join(OUT, f"{fn}.png"), 512)
    render_sprite(os.path.join(OUT, f"{fn}_64.png"))
# sword_ready front/side orthos (shows the two-handed grip clearly)
apply_pose("sword_ready")
set_sword(False)
for v in ("front", "side"):
    cam_ortho(v)
    set_outline(3.7 / 512 * 1.6)
    render(os.path.join(OUT, f"pose_test_{v}.png"), 512)
apply_pose("rest")
rig.rotation_euler = (0, 0, 0)

py = os.path.join(ROOT, ".venv", "bin", "python")
subprocess.run([py, os.path.join(HERE, "sprite_post.py"), OUT], check=False)
subprocess.run([py, os.path.join(HERE, "make_sheet.py"), OUT, str(ROUND)], check=False)
print("[done]", OUT)
