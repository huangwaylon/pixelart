"""Render the Pixal3D 4-view mesh (proportions match the Gemini illustration) from the iso game camera
(ortho, 30 deg elevation) in 8 directions, same scale. Output: hybrid/guide/p3d_iso/p3d_<DIR>.png (768^2,
transparent, flat texture colour) + sheet_4x2.png (white bg) used as the layout guide for the lock turnaround.
Run: Blender -b --factory-startup -P tools/hybrid/render_p3d_iso.py"""
import bpy, math, os
from mathutils import Vector as V
ROOT = "/Users/waylonhuang/Documents/other/pixelart/swordswoman"
OUT = ROOT + "/hybrid/guide/p3d_iso"; os.makedirs(OUT, exist_ok=True)
GLB = ROOT + "/model/ai_ref/pixal3d/best/akane_pixal3d_mv4_gemfix_s42-r1024-8k.glb"
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
bpy.ops.import_scene.gltf(filepath=GLB)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
root = bpy.data.objects.new("pivot", None); bpy.context.scene.collection.objects.link(root)
dg = bpy.context.evaluated_depsgraph_get()
mn = V((1e9,) * 3); mx = V((-1e9,) * 3)
for o in meshes:
    for c in o.bound_box:
        w = o.matrix_world @ V(c); mn = V(map(min, mn, w)); mx = V(map(max, mx, w))
print("bbox", mn, mx)
H = mx.z - mn.z
tops = [o for o in bpy.data.objects if o.parent is None and o != root]
for o in tops: o.parent = root
root.location = (0, 0, 0)
# centre feet on origin
for o in tops: o.location = o.location - V(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "FLAT"; sc.display.shading.color_type = "TEXTURE"
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = 768
camd = bpy.data.cameras.new("cam"); camd.type = "ORTHO"; camd.ortho_scale = H * 1.55
cam = bpy.data.objects.new("cam", camd); sc.collection.objects.link(cam); sc.camera = cam
el = math.radians(30); D = 30; zc = H * 0.5
cam.location = (0, -D * math.cos(el), zc + D * math.sin(el)); cam.rotation_euler = (math.radians(60), 0, 0)
DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
for k, d in enumerate(DIRS):
    root.rotation_euler = (0, 0, math.radians(45 * k))
    sc.render.filepath = f"{OUT}/p3d_{d}.png"; bpy.ops.render.render(write_still=True)
print("done")
