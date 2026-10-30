# Blender -b --factory-startup -P render.py -- OUT_DIR [--res 384] A.glb B.glb ...
# Clay (Workbench, flat-ish studio + cavity + outline) ortho renders: front / q34 / side / back for each mesh,
# plus vertex-colour renders (suffix _col) if the mesh carries colours. Height normalised to 2, feet at 0.
# Hunyuan glb: Y up, faces +Z -> Blender importer: Z up, faces -Y.
import bpy, sys, math, mathutils, os
a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]; a = a[1:]
res = 384
if a and a[0] == '--res':
    res = int(a[1]); a = a[2:]
os.makedirs(out, exist_ok=True)
VIEWS = [("front", 0, 0), ("q34", 45, 10), ("side", 90, 0), ("back", 180, 0)]


def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.view_settings.view_transform = "Standard"
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = "ORTHO"; cam.data.ortho_scale = 2.3
    return sc, cam


for src in a:
    sc, cam = setup()
    bpy.ops.import_scene.gltf(filepath=src)
    objs = [o for o in sc.objects if o.type == "MESH"]
    for o in objs:
        o.data.transform(o.matrix_world); o.parent = None; o.matrix_world = mathutils.Matrix.Identity(4)
    for o in [o for o in sc.objects if o.type != "MESH" and o.name != "cam"]:
        bpy.data.objects.remove(o)
    bb = [mathutils.Vector(c) for o in objs for c in o.bound_box]
    mn = mathutils.Vector([min(v[i] for v in bb) for i in range(3)]); mx = mathutils.Vector([max(v[i] for v in bb) for i in range(3)])
    h = mx.z - mn.z; ctr = (mn + mx) / 2
    for o in objs:
        o.data.transform(mathutils.Matrix.Scale(2.0 / h, 4) @ mathutils.Matrix.Translation(-mathutils.Vector((ctr.x, ctr.y, mn.z))))
        for p in o.data.polygons: p.use_smooth = False
    has_col = any(len(o.data.color_attributes) for o in objs) or any(
        o.active_material and o.active_material.node_tree and any(n.type == 'TEX_IMAGE' for n in o.active_material.node_tree.nodes) for o in objs)
    base = os.path.splitext(os.path.basename(src))[0]
    sh = sc.display.shading
    passes = [("", "SINGLE")] + ([("_col", "VERTEX" if any(len(o.data.color_attributes) for o in objs) else "TEXTURE")] if has_col else [])
    for suf, ctype in passes:
        sh.light = "STUDIO" if suf == "" else "FLAT"
        sh.color_type = ctype; sh.single_color = (0.72, 0.72, 0.72)
        sh.show_cavity = suf == ""; sh.cavity_type = "WORLD"
        sh.show_object_outline = True
        for name, az, el in VIEWS:
            t = mathutils.Vector((0, 0, 1.0)); d = 6.0
            loc = t + d * mathutils.Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)),
                                            -math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
            cam.location = loc
            cam.rotation_euler = (t - loc).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = f"{out}/{base}{suf}_{name}.png"
            bpy.ops.render.render(write_still=True)
    print("RENDERDONE", base, flush=True)
