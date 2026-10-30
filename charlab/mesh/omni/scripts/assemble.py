# Blender -b --factory-startup -P assemble.py -- BODY.glb HEAD.glb OUT.glb HEAD_FRAC NECK_FRAC [--vox 0.004] [--sym]
# Parts assembly: cut the body at the neck line (NECK_FRAC of the height from the top, from head_crop.py), cap it,
# scale the separately generated head so its height = HEAD_FRAC * body height (the head crop spans top -> neck+2%),
# place it on top (top aligned, x centred on the body head, z centred on the body head), then union by voxel remesh.
# Also writes OUT_parts.glb (body + head as two separate objects, before the union) for rigid-part rigging.
import bpy, bmesh, sys, mathutils
a = sys.argv[sys.argv.index("--") + 1:]
body_p, head_p, out = a[0], a[1], a[2]; head_frac, neck_frac = float(a[3]), float(a[4])
vox = 0.004; sym = '--sym' in a
if '--vox' in a: vox = float(a[a.index('--vox') + 1])
bpy.ops.wm.read_factory_settings(use_empty=True)


def load(p, name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=p)
    new = [o for o in bpy.data.objects if o not in before]
    ms = [o for o in new if o.type == 'MESH']
    o = ms[0]
    o.data.transform(o.matrix_world); o.parent = None; o.matrix_world = mathutils.Matrix.Identity(4)
    for x in new:
        if x != o: bpy.data.objects.remove(x)
    o.name = name
    for att in list(o.data.color_attributes): o.data.color_attributes.remove(att)
    return o


def bounds(o, sel=None):
    vs = [v.co for v in o.data.vertices if sel is None or sel(v.co)]
    mn = mathutils.Vector([min(v[i] for v in vs) for i in range(3)]); mx = mathutils.Vector([max(v[i] for v in vs) for i in range(3)])
    return mn, mx


body = load(body_p, 'body'); head = load(head_p, 'head')
bmn, bmx = bounds(body); H = bmx.z - bmn.z
z_neck = bmx.z - neck_frac * H
hmn0, hmx0 = bounds(body, lambda c: c.z > z_neck)
# cut + cap body slightly above the neck (cap ends up inside the new head)
z_cut = z_neck + 0.01 * H
bpy.context.view_layer.objects.active = body; body.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.bisect(plane_co=(0, 0, z_cut), plane_no=(0, 0, 1), clear_outer=True, use_fill=True)
bpy.ops.object.mode_set(mode='OBJECT'); body.select_set(False)
# place head
hmn, hmx = bounds(head); s = head_frac * H / (hmx.z - hmn.z)
c_head = (hmn + hmx) / 2
tgt_xy = ((hmn0.x + hmx0.x) / 2, (hmn0.y + hmx0.y) / 2)
head.data.transform(mathutils.Matrix.Scale(s, 4))
hmn, hmx = bounds(head)
head.data.transform(mathutils.Matrix.Translation((tgt_xy[0] - (hmn.x + hmx.x) / 2, tgt_xy[1] - (hmn.y + hmx.y) / 2, bmx.z - hmx.z)))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=out.replace('.glb', '_parts.glb'), export_format='GLB', use_selection=True)
# union
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
o = bpy.context.view_layer.objects.active
m = o.modifiers.new('r', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = vox * H; bpy.ops.object.modifier_apply(modifier='r')
if sym:
    xs = sorted(v.co.x for v in o.data.vertices); cx = (xs[0] + xs[-1]) / 2
    o.data.transform(mathutils.Matrix.Translation((-cx, 0, 0)))
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.symmetrize(direction='POSITIVE_X'); bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True)
print('ASSEMBLED', out, 'head scale %.3f' % s, 'faces', len(o.data.polygons), flush=True)
