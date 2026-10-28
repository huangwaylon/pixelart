# qa_view.py: Blender -b -P qa_view.py -- body.npz OUTPREFIX  : flat matid renders of the unposed body (H2 frame) through the game cameras,
# 192 cell at 4x (pivot 96,152; PPU 52.608 per 1x px) -> OUTPREFIX_<V>.png
import bpy, sys, math, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; d = np.load(a[0], allow_pickle=True); out = a[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
MATS = {'hair': (61, 50, 53), 'dress': (192, 59, 61), 'skin': (248, 218, 194), 'sleeve': (142, 34, 44), 'socks': (38, 42, 71),
        'boots': (42, 34, 42), 'bow': (232, 96, 79), 'obi': (69, 56, 73), 'eyes': (85, 128, 162)}
me = bpy.data.meshes.new("b"); me.from_pydata([tuple(v) for v in d["V"]], [], [tuple(f) for f in d["F"]])
ca = me.color_attributes.new("Color", "BYTE_COLOR", "CORNER"); fm = d["fmat"]
for p in me.polygons:
    c = [x / 255 for x in MATS[fm[p.index]]] + [1]
    for li in p.loop_indices: ca.data[li].color_srgb = c
o = bpy.data.objects.new("b", me); sc = bpy.context.scene; sc.collection.objects.link(o)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
CELL, PIV, PPU, SC = 192, (96, 152), 52.608, 4
cam.data.type = "ORTHO"; cam.data.ortho_scale = CELL / PPU; cam.data.shift_x = 0.5 - PIV[0] / CELL; cam.data.shift_y = PIV[1] / CELL - 0.5
sc.render.resolution_x = sc.render.resolution_y = CELL * SC; sc.render.film_transparent = True; sc.view_settings.view_transform = "Standard"
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "FLAT"; sh.color_type = "VERTEX"; sc.display.render_aa = "OFF"
AZ = {"SE": (-1, -1), "E": (-1, 0), "S": (0, -1)}
for v, az in AZ.items():
    c = Vector((*az, 0)).normalized(); el = math.radians(30); loc = Vector((c.x * math.cos(el), c.y * math.cos(el), math.sin(el))) * 10
    cam.location = loc; cam.rotation_euler = (-loc).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = f"{out}_{v}.png"; bpy.ops.render.render(write_still=True)
