"""Render turnaround + isometric views of model/character.blend.

Run:
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P model/render_turnaround.py [-- --round N]

Writes renders/model_round_N/:
  ortho_front/side/back/34.png (1024)    rest pose (relaxed A-pose idle)
  iso_<DIR>.png (512)                    iso game camera, ortho, 30 deg elevation, transparent
  iso_<DIR>_64.png (128x128 cell)        rendered directly at sprite scale (char ~56 px tall,
                                         feet pivot at (64,104) per design bible section 5),
                                         no AA, sprite katana variant, exact palette colours
  pose_test.png (512) + pose_test_64.png sword_ready pose from iso SE
  sheet.png                               contact sheet (built with .venv PIL via make_sheet.py)
"""
import bpy, sys, os, json, math, subprocess
from mathutils import Vector as V, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ROUND = 1
if "--round" in argv:
    ROUND = int(argv[argv.index("--round") + 1])
QUICK = "--quick" in argv
OUT = os.path.join(ROOT, "renders", f"model_round_{ROUND}") if not QUICK else "/tmp/akane_quick"
os.makedirs(OUT, exist_ok=True)

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
            m.thickness = px_world * ob.get("outline_px", 1.5)


def set_sword(sprite):
    bpy.data.objects["katana"].hide_render = sprite
    bpy.data.objects["katana_sprite"].hide_render = not sprite


def apply_pose(name):
    poses = json.loads(rig["poses"])
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
    for bn, v in poses.get(name, {}).items():
        pb = rig.pose.bones[bn]
        pb.rotation_quaternion = Quaternion(v[:4])
        pb.location = V(v[4:7])
    bpy.context.view_layer.update()


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


apply_pose("rest")
# ---- orthographic turnaround (1024)
set_sword(False)
for v in (("front", "side", "back", "34") if not QUICK else ("front", "side", "back")):
    cam_ortho(v)
    set_outline(3.7 / 1024 * 1.6)
    render(os.path.join(OUT, f"ortho_{v}.png"), 1024)

# ---- iso 8 directions (512, AA) and sprite-scale (128 cell, no AA, sprite katana)
for d in (DIRS if not QUICK else ["SE", "NW"]):
    cam_iso(d)
    set_sword(False)
    set_outline(ISO_ORTHO / 512 * 1.1)
    render(os.path.join(OUT, f"iso_{d}.png"), 512)
    set_sword(True)
    set_outline(ISO_ORTHO / CELL * 0.62)
    render(os.path.join(OUT, f"iso_{d}_64.png"), CELL, aa=False)

# ---- pose test (rig proof): sword_ready from iso SE
apply_pose("sword_ready")
cam_iso("SE")
set_sword(False)
set_outline(ISO_ORTHO / 512 * 1.1)
render(os.path.join(OUT, "pose_test.png"), 512)
set_sword(True)
set_outline(ISO_ORTHO / CELL * 0.62)
render(os.path.join(OUT, "pose_test_64.png"), CELL, aa=False)
if QUICK:
    set_sword(False)
    for v in ("front", "side"):
        cam_ortho(v)
        set_outline(3.7 / 512 * 1.6)
        render(os.path.join(OUT, f"pose_{v}.png"), 512)
apply_pose("rest")
rig.rotation_euler = (0, 0, 0)

py = os.path.join(ROOT, ".venv", "bin", "python")
subprocess.run([py, os.path.join(HERE, "make_sheet.py"), OUT, str(ROUND)], check=False)
print("[done]", OUT)
