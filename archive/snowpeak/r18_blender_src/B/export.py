import bpy, bmesh
O = '/tmp/indep/B/out/'
char = bpy.data.collections['Character']
objs = [o for o in char.objects if o.type == 'MESH']
for o in objs:
    for m in o.modifiers:
        if m.type == 'SUBSURF':
            m.levels = 1 if o.name == 'Head' else 0
# convert toon node trees into Principled (base colour / texture) for interchange formats
for m in bpy.data.materials:
    if m.name == 'Outline':
        continue
    nt = m.node_tree
    img = None
    for n in nt.nodes:
        if n.type == 'TEX_IMAGE':
            img = n.image
    col = m.diffuse_color[:]
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    p = nt.nodes.new('ShaderNodeBsdfPrincipled')
    p.inputs['Base Color'].default_value = col
    p.inputs['Roughness'].default_value = 0.8
    if img:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = img
        nt.links.new(t.outputs['Color'], p.inputs['Base Color'])
    if m.name == 'Blush':
        p.inputs['Alpha'].default_value = 0.28
    nt.links.new(p.outputs[0], out.inputs[0])
bpy.ops.object.select_all(action='DESELECT')
for o in objs:
    o.hide_set(False); o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.export_scene.gltf(filepath=O + 'model.glb', export_format='GLB', use_selection=True, export_apply=True)
bpy.ops.wm.obj_export(filepath=O + 'model.obj', export_selected_objects=True, apply_modifiers=True,
                      export_materials=True, forward_axis='NEGATIVE_Z', up_axis='Y')
# stats + manifold check on evaluated export meshes
dg = bpy.context.evaluated_depsgraph_get()
tot = 0; nm_tot = 0
for o in objs:
    me = o.evaluated_get(dg).to_mesh()
    bm = bmesh.new(); bm.from_mesh(me)
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    quads = sum(1 for f in bm.faces if len(f.verts) == 4)
    me.calc_loop_triangles(); t = len(me.loop_triangles); tot += t; nm_tot += nm if o.name != 'Eyes' else 0
    print('EXP', o.name, 'tris', t, 'quads%', round(100 * quads / max(1, len(bm.faces))), 'nonmanifold_edges', nm)
    bm.free(); o.evaluated_get(dg).to_mesh_clear()
print('EXP TOTAL', tot, 'nonmanifold(excl eye planes)', nm_tot)
