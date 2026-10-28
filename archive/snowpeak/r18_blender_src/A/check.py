import bpy, bmesh
bpy.ops.wm.open_mainfile(filepath='/tmp/indep/A/out/model.blend')
dg = bpy.context.evaluated_depsgraph_get()
for ob in bpy.data.objects:
    if ob.type != 'MESH' or ob.hide_render: continue
    for m in ob.modifiers:
        if m.name == 'Outline': m.show_viewport = False
dg.update()
for ob in bpy.data.objects:
    if ob.type != 'MESH' or ob.hide_render: continue
    me = ob.evaluated_get(dg).to_mesh()
    bm = bmesh.new(); bm.from_mesh(me)
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    print('CHK', ob.name, 'faces', len(bm.faces), 'nonmanifold_edges', nm)
    bm.free()
