# Blender -b --factory-startup -P post.py -- IN.glb OUT.glb [--sym] [--tris 30000] [--vox 0.006] [--smooth 4] [--quad]
#                                              [--minpart 0.01]
# Post chain for Omni meshes (glb frame kept):
#   1 drop loose parts < minpart * largest part (floaters)
#   2 --sym: centre X on the main body, symmetrize +X -> -X (her left copied to her right)
#   3 voxel remesh (vox * height): manifold, watertight, fills pinholes, removes internal shells
#   4 light Laplacian-ish smooth (Smooth modifier, factor .5, N iterations) to kill marching-cubes terracing
#   5 decimate (collapse) to --tris, or --quad: QuadriFlow to ~tris/2 quads
import bpy, bmesh, sys, time
a = sys.argv[sys.argv.index("--") + 1:]
src, dst = a[0], a[1]
opt = dict(sym=False, tris=30000, vox=0.004, smooth=4, quad=False, minpart=0.01)
i = 2
while i < len(a):
    k = a[i][2:]
    if k in ('sym', 'quad'):
        opt[k] = True; i += 1
    else:
        opt[k] = type(opt[k])(a[i + 1]); i += 2
t0 = time.time()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
o = [x for x in bpy.context.scene.objects if x.type == "MESH"][0]
o.data.transform(o.matrix_world); o.parent = None
import mathutils
o.matrix_world = mathutils.Matrix.Identity(4)
for x in [x for x in bpy.context.scene.objects if x != o]:
    bpy.data.objects.remove(x)
bpy.context.view_layer.objects.active = o; o.select_set(True)
for att in list(o.data.color_attributes):
    o.data.color_attributes.remove(att)
n0 = len(o.data.polygons)

# 1 floaters
def drop_floaters(o, minpart):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
    seen = set(); comps = []
    for f in bm.faces:
        if f.index in seen: continue
        stack = [f]; comp = []; seen.add(f.index)
        while stack:
            g = stack.pop(); comp.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index); stack.append(h)
        comps.append(comp)
    big = max(len(c) for c in comps)
    drop = [f for c in comps if len(c) < minpart * big for f in c]
    bmesh.ops.delete(bm, geom=drop, context='FACES')
    bm.to_mesh(o.data); bm.free()
    return comps, big


comps, big = drop_floaters(o, opt['minpart'])
n_parts = sum(1 for c in comps if len(c) >= opt['minpart'] * big)

# height in Blender (Z up after import)
zs = [v.co.z for v in o.data.vertices]; H = max(zs) - min(zs)

# 2 symmetry
if opt['sym']:
    xs = sorted(v.co.x for v in o.data.vertices); cx = (xs[0] + xs[-1]) / 2
    o.data.transform(mathutils.Matrix.Translation((-cx, 0, 0)))
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.symmetrize(direction='POSITIVE_X', threshold=0.0005 * H)
    bpy.ops.object.mode_set(mode='OBJECT')

# 3 voxel remesh
m = o.modifiers.new("r", "REMESH"); m.mode = "VOXEL"; m.voxel_size = opt['vox'] * H; m.adaptivity = 0
bpy.ops.object.modifier_apply(modifier="r")
n_vox = len(o.data.polygons)
# 4 smooth
if opt['smooth'] > 0:
    s = o.modifiers.new("s", "SMOOTH"); s.factor = 0.5; s.iterations = opt['smooth']
    bpy.ops.object.modifier_apply(modifier="s")
# 5 reduce
if opt['quad']:
    bpy.ops.object.quadriflow_remesh(target_faces=opt['tris'] // 2, use_mesh_symmetry=opt['sym'], use_preserve_sharp=False,
                                     use_preserve_boundary=False, smooth_normals=False, seed=0)
else:
    d = o.modifiers.new("d", "DECIMATE"); d.ratio = min(1.0, opt['tris'] / max(1, sum(len(p.vertices) - 2 for p in o.data.polygons)))
    d.use_symmetry = opt['sym']; d.symmetry_axis = 'X'
    bpy.ops.object.modifier_apply(modifier="d")
drop_floaters(o, 0.05)
bpy.ops.object.shade_smooth()
nt = sum(len(p.vertices) - 2 for p in o.data.polygons)
bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", use_selection=True, export_apply=True)
print(f"POSTDONE {dst} raw_faces={n0} parts_kept={n_parts} vox_faces={n_vox} out_tris={nt} sec={time.time() - t0:.1f}", flush=True)
