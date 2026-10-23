import sys, bpy, time
sys.path.insert(0, '/tmp/indep/B/src')
from common import *
import numpy as np
import head, body, hair, scene, rig

t0 = time.time()
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = scene.setup_scene()

def C(name):
    c = bpy.data.collections.new(name); sc.collection.children.link(c); return c
char = C('Character'); lines = C('Proxies')

M = dict(
    skin=toon_mat('Skin', '#FCD6B4', '#EBA586', t_shadow=0.12),
    lash=toon_mat('Lash', '#20223E', '#20223E', emit_only=True),
    brow=toon_mat('Brow', '#6E3C3A', '#6E3C3A', emit_only=True),
    crease=toon_mat('LidCrease', '#D9937A', '#D9937A', emit_only=True),
    blush=toon_mat('Blush', '#FAC1A5', '#FAC1A5', emit_only=True),
    mouth=toon_mat('Mouth', '#9A4C46', '#9A4C46', emit_only=True),
    hair=toon_mat('Hair', '#A85A3A', '#6E3C3A', t_shadow=0.30),
    hair_hi=toon_mat('HairHighlight', '#C67A4E', '#A85A3A', t_shadow=0.30),
    teal=toon_mat('TealSatin', '#2A8C8E', '#1C4C54', hi='#6ACBB6', t_shadow=0.30, t_hi=0.975),
    knit=toon_mat('TealKnit', '#2A8C8E', '#1C4C54', t_shadow=0.30),
    teal_dark=toon_mat('TealDark', '#1C4C54', '#143840', t_shadow=0.30),
    coat=toon_mat('Coat', '#F2E6CE', '#D2BFA4', t_shadow=0.30),
    rust=toon_mat('Rust', '#A85A3A', '#7C3E2C', t_shadow=0.30),
    belt=toon_mat('Belt', '#6E3C3A', '#4E2A2A', t_shadow=0.30),
    gold=toon_mat('Gold', '#E2A434', '#B07A20', hi='#F6D27A', t_shadow=0.30, t_hi=0.9),
    tights=toon_mat('Tights', '#45435E', '#2E2C44', t_shadow=0.30),
    boots=toon_mat('Boots', '#6E3C3A', '#4E2A2A', t_shadow=0.30),
    fur=toon_mat('Fur', '#F2E6CE', '#D2BFA4', t_shadow=0.30),
    sole=toon_mat('Sole', '#3E2628', '#2E1C1E', t_shadow=0.30),
)
outline = toon_mat('Outline', '#4A2C26', '#4A2C26', outline=True)
outline_teal = toon_mat('OutlineTeal', '#163C42', '#163C42', outline=True)

objs = {}
objs['Head'] = head.build_head(M, char)
objs['Eyes'], objs['FaceLines'] = head.build_eyes(M, char)
for o in (objs['Eyes'],):
    if o.users_collection and o.users_collection[0] != char:
        for c in o.users_collection: c.objects.unlink(o)
        char.objects.link(o)
objs['Body'] = body.build_body(M, char)
objs['Tights'] = body.build_tights(M, char)
objs['Boots'] = body.build_boots(M, char)
objs['Coat'] = body.build_coat(M, char)
objs['Belt'] = body.build_belt_buttons(M, char)
objs['Scarf'] = body.build_scarf(M, char)
objs['Mittens'] = body.build_mittens(M, char)
objs['Hair_Cap'] = hair.build_cap(M, char)
objs['Hair_Bangs'] = hair.build_bangs(M, char)
objs['Hair_Highlight'] = bpy.data.objects['Hair_Highlight']
objs['Hair_SideLocks'] = hair.build_sidelocks(M, char)
objs['Hair_Back'] = hair.build_back(M, char)
objs['Hair_Ponytail'], pt_axis = hair.build_ponytail(M, char)
objs['Hair_Strands'] = hair.build_strands(M, char)
objs['Bow'] = hair.build_bow(M, char, pt_axis)
objs['Brows'] = head.build_brows(M, char, [objs['Hair_Bangs'], objs['Head']])
hp = hair.hair_proxy(lines)
for n in ('Hair_Cap', 'Hair_Bangs', 'Hair_Back'):
    hair.transfer_normals(objs[n], hp)
import numpy as _np
_ax = _np.array(objs['Hair_Ponytail']['axis'])
pp = hair.tube_proxy('PonytailNormalProxy', _ax, _np.interp(_np.linspace(0, 1, len(_ax)), [0, 0.1, 0.4, 0.8, 1], [0.01, 0.035, 0.06, 0.05, 0.03]), lines)
hair.transfer_normals(objs['Hair_Ponytail'], pp, 0.7)

# shrinkwrap pass: keep coat bodice snug on the torso (vertex group = bodice rows)
coat = objs['Coat']
vg = coat.vertex_groups.new(name='bodice')
idx = [v.index for v in coat.data.vertices if 1.0 < v.co.z < 1.215 and abs(v.co.x) < 0.125]
vg.add(idx, 1.0, 'REPLACE')
sw = coat.modifiers.new('Shrinkwrap', 'SHRINKWRAP')
import numpy as _np
prx = join_parts('TorsoProxy', [loft([body.torso_ring(r[1], r[2], r[3], r[4], r[0]) for r in body.TORSO], True, True, True) + (0,)], [M['skin']], coll=lines)
recalc_normals(prx); prx.hide_render = True; prx.hide_viewport = True
sw.target = prx; sw.wrap_method = 'NEAREST_SURFACEPOINT'; sw.wrap_mode = 'OUTSIDE_SURFACE'
sw.offset = body.COAT_OFF; sw.vertex_group = 'bodice'
for _ in range(2):
    bpy.ops.object.select_all(action='DESELECT')
coat.modifiers.move(len(coat.modifiers) - 1, 0)

for name, o in objs.items():
    if name in ('Eyes', 'FaceLines', 'Bow') or name.startswith('Hair'):
        o.visible_shadow = False

per = {'Head': 0.0007, 'Hair_Strands': 0.0004, 'Belt': 0.0005, 'Mittens': 0.0008, 'Bow': 0.0008,
       'Hair_Bangs': 0.0007, 'Hair_SideLocks': 0.0007, 'Boots': 0.0010, 'Scarf': 0.0009, 'Hair_Highlight': 0.0}
for n, o in objs.items():
    if n in ('Eyes', 'FaceLines', 'Body', 'Hair_Highlight', 'Brows'):
        continue
    om = scene.add_outline(o, outline_teal if n in ('Bow', 'Scarf', 'Mittens') else outline, per.get(n, 0.0009))
    if n == 'Head':
        om.vertex_group = 'outline'
# apply the coat shrinkwrap pass (bake it into the cage before skinning), drop the torso proxy
with bpy.context.temp_override(object=coat, active_object=coat):
    bpy.ops.object.modifier_apply(modifier='Shrinkwrap')
bpy.data.objects.remove(prx)
# UVs
rig.unwrap(objs)
# rig + weights
arm, chains = rig.build_armature(objs, char)
rep = rig.skin_all(objs, arm, chains)
print('SKIN', rep)
for pn in ('FaceNormalProxy', 'HairNormalProxy'):
    rig.parent_to_bone(bpy.data.objects[pn], arm, 'head')
# ponytail normal proxy follows the ponytail chain
pp_ = bpy.data.objects['PonytailNormalProxy']
Vp = np.array([v.co[:] for v in pp_.data.vertices])
bn_, Wp = rig.chain_weights(Vp, chains['ponytail'][1], chains['ponytail'][0], 'head', 0.06)
rig.set_weights(pp_, bn_, Wp)
pp_.parent = arm
am_ = pp_.modifiers.new('Armature', 'ARMATURE'); am_.object = arm
with bpy.context.temp_override(object=pp_):
    bpy.ops.object.modifier_move_to_index(modifier='Armature', index=0)
bpy.ops.wm.save_as_mainfile(filepath='/tmp/indep/B/out/model.blend', compress=True)
# stats
dg = bpy.context.evaluated_depsgraph_get()
tot = 0
for n, o in objs.items():
    me = o.evaluated_get(dg).to_mesh()
    me.calc_loop_triangles(); t = len(me.loop_triangles); tot += t
    print('STAT', n, len(me.vertices), t)
    o.evaluated_get(dg).to_mesh_clear()
print('STAT TOTAL_TRIS(render levels)', tot, 'time', round(time.time() - t0, 1))
