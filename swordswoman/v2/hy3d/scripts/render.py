# Blender -b --factory-startup -P render.py -- IN.glb OUT_PREFIX
# Clay Workbench ortho renders: front, side(E: her right? camera +X), back, iso34 (front-left, 20deg), se (front-right, 30deg elev).
# Hunyuan glb is Y-up, faces +Z; Blender importer converts to Z-up facing -Y. Height normalised to 2, feet at 0.
import bpy, sys, math, mathutils
a = sys.argv[sys.argv.index("--") + 1:]
src, outp = a[0], a[1]
res = int(a[2]) if len(a) > 2 else 512
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
for o in objs:
    o.data.transform(o.matrix_world); o.parent = None; o.matrix_world = mathutils.Matrix.Identity(4)
bpy.context.view_layer.update()
bb = [mathutils.Vector(c) for o in objs for c in o.bound_box]
mn = mathutils.Vector([min(v[i] for v in bb) for i in range(3)]); mx = mathutils.Vector([max(v[i] for v in bb) for i in range(3)])
h = mx.z - mn.z; ctr = (mn + mx) / 2
for o in objs:
    o.data.transform(mathutils.Matrix.Scale(2.0 / h, 4) @ mathutils.Matrix.Translation(-mathutils.Vector((ctr.x, ctr.y, mn.z))))
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light = "STUDIO"; sh.color_type = "SINGLE"; sh.single_color = (0.7, 0.7, 0.7)
sh.show_cavity = True; sh.show_object_outline = True
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = res
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = 2.5
def view(name, az, el, d=6.0):
    # az: 0 = camera in front (-Y); positive az moves camera toward +X (her left)
    t = mathutils.Vector((0, 0, 1.0))
    loc = t + d * mathutils.Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)), -math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
    cam.location = loc
    cam.rotation_euler = (t - loc).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f"{outp}_{name}.png"; bpy.ops.render.render(write_still=True)
import os
if os.environ.get("VCOL"): sh.color_type = "VERTEX"; sh.show_cavity = False; sh.light = "FLAT"; sc.view_settings.view_transform = "Standard"
view("front", 0, 0); view("side", 90, 0); view("back", 180, 0); view("iso34", 40, 20); view("se", -45, 30)
print("RENDERDONE", outp)
