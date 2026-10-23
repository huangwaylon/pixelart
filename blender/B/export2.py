"""Bake LOD0/1/2 (modifiers applied, no outlines/proxies/lights), convert materials, export GLB/OBJ/FBX."""
import bpy, bmesh
import numpy as np
O = '/tmp/indep/B/out/'
char = bpy.data.collections['Character']
arm = bpy.data.objects['Rig']
src = [o for o in char.objects if o.type == 'MESH']

def tri_count(me):
    me.calc_loop_triangles(); return len(me.loop_triangles)

# ---- materials -> Principled base colour (+ eye textures)
for m in bpy.data.materials:
    if m.name.startswith('Outline'):
        continue
    nt = m.node_tree; img = None
    for n in nt.nodes:
        if n.type == 'TEX_IMAGE':
            img = n.image
    col = m.diffuse_color[:]
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); p = nt.nodes.new('ShaderNodeBsdfPrincipled')
    p.inputs['Base Color'].default_value = col; p.inputs['Roughness'].default_value = 0.85
    if img:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; nt.links.new(t.outputs['Color'], p.inputs['Base Color'])
    nt.links.new(p.outputs[0], out.inputs[0])

def bake(o, head_level):
    for m in o.modifiers:
        if m.type == 'ARMATURE' or m.name == 'Outline':
            m.show_viewport = False
        if m.type == 'SUBSURF':
            m.levels = head_level if o.name == 'Head' else 0
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    while len(me.materials) and me.materials[-1].name.startswith('Outline'):
        me.materials.pop()
    return me

lod_cols = {}
for k in range(3):
    c = bpy.data.collections.new(f'LOD{k}'); bpy.context.scene.collection.children.link(c); lod_cols[k] = c

base = {}
for o in src:
    me = bake(o, 1)
    base[o.name] = me
tot0 = sum(tri_count(m) for m in base.values())
print('LOD0 raw', tot0)

targets = {0: 80000, 1: 40000, 2: 15000}
keep_small = ('Eyes', 'FaceLines', 'Brows', 'Hair_Highlight')
made = {0: [], 1: [], 2: []}
for k, target in targets.items():
    small = sum(tri_count(base[n]) for n in base if n.startswith(keep_small))
    big = tot0 - small
    ratio = min(1.0, (target - small) / big)
    for n, me0 in base.items():
        me = me0.copy(); me.name = f'{n}_LOD{k}'
        ob = bpy.data.objects.new(f'{n}_LOD{k}', me)
        lod_cols[k].objects.link(ob)
        for g in bpy.data.objects[n].vertex_groups:
            ob.vertex_groups.new(name=g.name)
        ob.parent = arm
        if ratio < 0.999 and not n.startswith(keep_small):
            r = ratio
            if n == 'Head':
                r = min(1.0, ratio * 1.35)       # protect the face silhouette
            if n == 'Body':
                r = ratio * 0.6                  # hidden under the coat
            dm = ob.modifiers.new('Decimate', 'DECIMATE'); dm.ratio = r; dm.use_collapse_triangulate = False
            with bpy.context.temp_override(object=ob, active_object=ob):
                bpy.ops.object.modifier_apply(modifier='Decimate')
        am = ob.modifiers.new('Armature', 'ARMATURE'); am.object = arm
        made[k].append(ob)
    print(f'LOD{k}', sum(tri_count(o.data) for o in made[k]), 'ratio', round(ratio, 3))

# hide source + proxies from export, export per LOD
def select_only(objs):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.hide_set(False); o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]

for k in range(3):
    select_only(made[k] + [arm])
    name = 'model.glb' if k == 0 else f'model_LOD{k}.glb'
    bpy.ops.export_scene.gltf(filepath=O + name, export_format='GLB', use_selection=True, export_apply=False,
                              export_skins=True, export_animations=False)
select_only(made[0])
bpy.ops.wm.obj_export(filepath=O + 'model.obj', export_selected_objects=True, apply_modifiers=False,
                      export_materials=True, forward_axis='NEGATIVE_Z', up_axis='Y')
select_only(made[0] + [arm])
bpy.ops.export_scene.fbx(filepath=O + 'model.fbx', use_selection=True, object_types={'ARMATURE', 'MESH'},
                         use_mesh_modifiers=False, add_leaf_bones=False, bake_anim=False, path_mode='COPY', embed_textures=True)

# QA on LOD0
for k in range(3):
    nm = 0; q = 0; f = 0; tris = 0
    for o in made[k]:
        bm = bmesh.new(); bm.from_mesh(o.data)
        nm += sum(1 for e in bm.edges if not e.is_manifold)
        q += sum(1 for fc in bm.faces if len(fc.verts) == 4); f += len(bm.faces)
        tris += tri_count(o.data); bm.free()
    uv = all(len(o.data.uv_layers) > 0 for o in made[k])
    print(f'QA LOD{k} tris {tris} quads% {round(100*q/f)} nonmanifold {nm} uvs {uv}')
for o in made[0]:
    print('OBJ', o.name, tri_count(o.data), [m.name for m in o.data.materials], len(o.vertex_groups))
# keep only LOD collections + rig in the lod blend
for o in list(char.objects):
    if o.type == 'MESH':
        bpy.data.objects.remove(o)
for c in list(bpy.data.collections):
    if c.name == 'Proxies':
        for o in list(c.objects):
            bpy.data.objects.remove(o)
        bpy.data.collections.remove(c)
for o in list(bpy.data.objects):
    if o.type in ('LIGHT', 'CAMERA'):
        bpy.data.objects.remove(o)
lod_cols[1].hide_render = lod_cols[2].hide_render = True
bpy.ops.wm.save_as_mainfile(filepath=O + 'model_lods.blend', compress=True)
