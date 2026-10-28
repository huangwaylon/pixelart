# Blender -b --factory-startup -P render_parts.py -- OUT_PREFIX MODE RES a.glb b.glb ...
# MODE: vcol (flat vertex colours), ids (random flat colour per part = seam check), explode (ids, parts pushed out from centre)
# Views: front, side (camera at her left), back, se (iso 30deg el, camera front-right az -45). Height normalised to 2, feet at 0.
import bpy, sys, math, mathutils, random, os
a = sys.argv[sys.argv.index("--") + 1:]
outp, mode, res, files = a[0], a[1], int(a[2]), a[3:]
bpy.ops.wm.read_factory_settings(use_empty=True)
objs = []
for f in files:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=f)
    new = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    for o in new:
        o.data.transform(o.matrix_world); o.parent = None; o.matrix_world = mathutils.Matrix.Identity(4); o.name = os.path.basename(f)[:-4]
    objs += new
bpy.context.view_layer.update()
bb = [o.matrix_world @ mathutils.Vector(c) for o in objs for c in o.bound_box]
mn = mathutils.Vector([min(v[i] for v in bb) for i in range(3)]); mx = mathutils.Vector([max(v[i] for v in bb) for i in range(3)])
h = mx.z - mn.z; ctr = (mn + mx) / 2
for o in objs:
    o.data.transform(mathutils.Matrix.Scale(2.0 / h, 4) @ mathutils.Matrix.Translation(-mathutils.Vector((ctr.x, ctr.y, mn.z))))
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = res
sc.view_settings.view_transform = "Standard"
sh.show_object_outline = True; sh.object_outline_color = (0.1, 0.07, 0.12)
for o in objs: o.data.update()
if mode == 'pose':
    # rigid 1:1 bone test: pivots from part bboxes (after normalisation; Z up, faces -Y, her left = +X)
    bpy.context.view_layer.update()
    def bbx(o):
        vs = [v.co for v in o.data.vertices]; return [min(v[i] for v in vs) for i in range(3)], [max(v[i] for v in vs) for i in range(3)]
    by = {o.name: o for o in objs}
    def rot(o, piv, axis, deg):
        M = mathutils.Matrix.Translation(piv) @ mathutils.Matrix.Rotation(math.radians(deg), 4, axis) @ mathutils.Matrix.Translation(-piv)
        o.data.transform(M)
    PJ = None
    if os.environ.get('PIVOTS'):
        import json
        NM = mathutils.Matrix.Scale(2.0 / h, 4) @ mathutils.Matrix.Translation(-mathutils.Vector((ctr.x, ctr.y, mn.z)))
        PJ = {k: NM @ mathutils.Vector((v['pivot'][0], -v['pivot'][2], v['pivot'][1])) for k, v in json.load(open(os.environ['PIVOTS'])).items()}
    for n, o in by.items():
        lo, hi = bbx(o)
        if n.startswith('arm_') and PJ and n in PJ:
            rot(o, PJ[n], 'Y', -55 if n.endswith('L') else 40); continue
        if n.startswith('arm_'):
            s = 1 if n.endswith('L') else -1  # L = +X
            piv = mathutils.Vector(((lo[0] if s > 0 else hi[0]), (lo[1] + hi[1]) / 2, hi[2] - 0.03))
            rot(o, piv, 'Y', -55 if n.endswith('L') else 40)
        if n.startswith('leg_') or n.startswith('boot_'):
            pass
    # legs + boots swing together about the hip
    for side, deg in (('L', 30), ('R', -25)):
        if f'leg_{side}' in by:
            lo, hi = bbx(by[f'leg_{side}']); piv = mathutils.Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, hi[2] - 0.04))
            if PJ and f'leg_{side}' in PJ: piv = PJ[f'leg_{side}']
            for k in (f'leg_{side}', f'boot_{side}'):
                if k in by: rot(by[k], piv, 'X', deg)
    for n in ('head', 'bow', 'bun', 'hair'):
        if 'head' in by and n in by:
            lo, hi = bbx(by['head']); piv = mathutils.Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2] + 0.02))
            if PJ and 'head' in PJ: piv = PJ['head']
            rot(by[n], piv, 'Y', 12)
    mode = 'vcol'
if mode == 'vcol':
    sh.light = "FLAT"; sh.color_type = "VERTEX"; sh.show_cavity = False
else:
    random.seed(3); sh.light = "STUDIO"; sh.color_type = "OBJECT"; sh.show_cavity = True
    pal = [(0.9, 0.3, 0.3), (0.3, 0.7, 0.9), (0.95, 0.8, 0.2), (0.4, 0.85, 0.4), (0.8, 0.45, 0.9), (0.95, 0.55, 0.2), (0.3, 0.4, 0.9), (0.6, 0.9, 0.8), (0.9, 0.6, 0.7), (0.6, 0.6, 0.3), (0.5, 0.3, 0.2), (0.9, 0.9, 0.9), (0.2, 0.6, 0.5)]
    for i, o in enumerate(sorted(objs, key=lambda o: o.name)): o.color = (*pal[i % len(pal)], 1)
    if mode == 'explode':
        bpy.context.view_layer.update()
        for o in objs:
            c = sum((mathutils.Vector(v.co) for v in o.data.vertices), mathutils.Vector()) / len(o.data.vertices)
            d = c - mathutils.Vector((0, 0, 1.0)); d.y *= 0.3
            o.location = d * 0.35
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = 2.9 if mode == 'explode' else 2.55
def view(name, az, el, d=6.0):
    t = mathutils.Vector((0, 0, 1.0))
    loc = t + d * mathutils.Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)), -math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
    cam.location = loc; cam.rotation_euler = (t - loc).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f"{outp}_{name}.png"; bpy.ops.render.render(write_still=True)
view("front", 0, 0); view("side", 90, 0); view("back", 180, 0); view("se", -45, 30)
if os.environ.get("EXTRA"): view("se_el0", -45, 0); view("se_az30", -30, 30)
print("RENDERDONE", outp)
