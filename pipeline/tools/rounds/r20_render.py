"""r20: neutral render harness for the from-scratch Blender base models (same camera/light for every track).

    Blender -b <model.blend> -P pipeline/tools/rounds/r20_render.py -- <outdir> [--tag NAME]

Contract with the model: Z up, feet at z=0, character faces -Y, HER left = +X. Every visible mesh's material has
diffuse_color (viewport colour) set to its base colour. Optional Empty "head_center" with custom prop "head_h"
(crown-to-chin, metres) frames the face close-ups. Objects whose name starts with "_" are hidden.

Writes <outdir>/<tag>_{front,q34,side,back}.png, <tag>_face_{front,q34,side}.png, <tag>_iso_<DIR>.png and
<tag>_px_<DIR>.png (aliased, character ~44 px tall), then board.py-style composition is done by r20_boards.py.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "/tmp/r20_render"
TAG = argv[argv.index("--tag") + 1] if "--tag" in argv else "m"
os.makedirs(OUT, exist_ok=True)

sc = bpy.context.scene
meshes = [o for o in sc.objects if o.type in {"MESH", "CURVE", "SURFACE", "META", "FONT"} and not o.name.startswith("_")
          and not o.hide_render]
for o in sc.objects:
    if o.name.startswith("_"):
        o.hide_render = True
dg = bpy.context.evaluated_depsgraph_get()
lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
for o in meshes:
    ev = o.evaluated_get(dg)
    for c in ev.bound_box:
        w = ev.matrix_world @ Vector(c)
        lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
H = hi.z - max(lo.z, 0.0)
cx = (lo.x + hi.x) / 2
hc = sc.objects.get("head_center")
head_c = hc.matrix_world.translation.copy() if hc else Vector((cx, 0, hi.z - 0.11 * H))
head_h = float(hc.get("head_h", 0.19 * H)) if hc else 0.19 * H

for o in [o for o in sc.objects if o.type in {"CAMERA", "LIGHT"}]:
    o.hide_render = True
cam_data = bpy.data.cameras.new("_r20cam"); cam_data.type = "ORTHO"
cam = bpy.data.objects.new("_r20cam", cam_data); sc.collection.objects.link(cam); sc.camera = cam
cam.hide_render = False

r = sc.render
r.engine = "BLENDER_WORKBENCH"
r.film_transparent = False
r.image_settings.file_format = "PNG"
sh = sc.display.shading
sh.light = "STUDIO"; sh.color_type = "MATERIAL"
sh.show_shadows = True; sh.shadow_intensity = 0.35
sh.show_cavity = False; sh.show_object_outline = False
sh.show_specular_highlight = False
sc.display.light_direction = (0.45, -0.55, 0.70)
sc.display.shadow_shift = 0.1
sh.background_type = "VIEWPORT"; sh.background_color = (0.88, 0.91, 0.95)
try:
    sc.view_settings.view_transform = "Standard"
except TypeError:
    pass


def shoot(name, az_deg, elev_deg, target, ortho, res, aa=True):
    a, e = math.radians(az_deg), math.radians(elev_deg)
    # az 0 = camera in front of her (on -Y); positive az swings the camera toward HER left (+X), so az 90 shows her
    # facing screen-left (like the approved side view) and az -90 facing screen-right ("E")
    d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    cam.location = target + d * 10.0
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    cam_data.ortho_scale = ortho
    r.resolution_x, r.resolution_y = res
    r.resolution_percentage = 100
    sc.display.render_aa = "8" if aa else "OFF"
    r.filepath = os.path.join(OUT, f"{TAG}_{name}.png")
    bpy.ops.render.render(write_still=True)


body_c = Vector((cx, 0, H * 0.5))
full = H * 1.08
for name, az in (("front", 0), ("q34", 35), ("side", 90), ("back", 180)):
    shoot(name, az, 0, body_c, full, (640, int(640 * 1.5)))
for name, az in (("face_front", 0), ("face_q34", 35), ("face_side", 90)):
    shoot(name, az, 0, head_c + Vector((0, 0, head_h * 0.1)), head_h * 2.3, (640, 640))
DIRS = [("S", 0), ("SE", 45), ("E", 90), ("NE", 135), ("N", 180), ("NW", 225), ("W", 270), ("SW", 315)]
for dn, az in DIRS:
    # iso: 16 deg elevation (project camera); S faces the viewer, E faces screen-right
    shoot(f"iso_{dn}", -az, 16, body_c, full, (360, 540))
    shoot(f"px_{dn}", -az, 16, body_c, full, (32, 48), aa=False)   # ~44 px tall character, aliased
print("R20_RENDER_DONE", OUT, "H=%.3f" % H)
