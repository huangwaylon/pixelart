"""Build entry point: blender -b -P build.py -- <tag> [parts]"""
import sys, os, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import lib, head, render
for m in (lib, head, render):
    importlib.reload(m)

ROOT = '/tmp/indep/A'
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
TAG = argv[0] if argv else 'dev'
PARTS = argv[1].split(',') if len(argv) > 1 else ['all']


def materials():
    T, F = lib.toon_mat, lib.flat_mat
    return dict(
        skin=T('Skin', '#FCD6B4', '#EBA586', thresh=0.22),
        skin_sh=F('SkinShadow', '#E39A80'),
        neck_sh=F('NeckShadow', '#EBA586'),
        hair=T('Hair', '#A85A3A', '#6E3C3A', '#D08658', thresh=0.30, hl_thresh=1.08),
        teal=T('Teal', '#2A8C8E', '#1C4C54', '#6ACBB6', thresh=0.30, hl_thresh=1.0),
        coat=T('Coat', '#F2E6CE', '#D2BFA4', thresh=0.30),
        rust=T('Rust', '#A85A3A', '#7A3E30', thresh=0.30),
        belt=T('Belt', '#6E3C3A', '#4A2828', thresh=0.30),
        gold=T('Gold', '#E2A434', '#A8701E', '#F8D880', thresh=0.30, hl_thresh=0.95),
        tights=T('Tights', '#45435E', '#2E2C44', thresh=0.30),
        boots=T('Boots', '#6E3C3A', '#4A2828', '#8E5440', thresh=0.30, hl_thresh=1.02),
        fur=T('Fur', '#F2E6CE', '#D2BFA4', thresh=0.30),
        sclera=F('EyeWhite', '#FBFBFF'),
        sclera_sh=F('EyeWhiteShadow', '#C9CFE6'),
        iris=F('Iris', '#2C9696'),
        iris_dark=F('IrisDark', '#1C4C54'),
        iris_light=F('IrisLight', '#6ACBB6'),
        pupil=F('Pupil', '#14283A'),
        white=F('Highlight', '#FFFFFF'),
        lash=F('Lash', '#20223E'),
        crease=F('LidCrease', '#C88870'),
        brow=F('Brow', '#6E3C3A'),
        mouth=F('Mouth', '#A8505A'),
        lip=F('Lip', '#F2A69A'),
        blush=F('Blush', '#F9BCA6'),
    )


def main():
    lib.reset()
    lib.MATS.clear()
    mats = materials()
    ol = lib.outline_mat()
    objs = {}
    hd = head.build(mats); objs['Head'] = hd
    bpy.context.view_layer.update()
    eyes = head.build_face_decals(hd, mats); objs['Eyes'] = eyes
    if 'all' in PARTS or 'body' in PARTS:
        import body; importlib.reload(body)
        objs.update(body.build(mats))
    if 'all' in PARTS or 'outfit' in PARTS:
        import outfit; importlib.reload(outfit)
        objs.update(outfit.build(mats))
    if 'all' in PARTS or 'hair' in PARTS:
        import hair; importlib.reload(hair)
        objs.update(hair.build(mats, hd))
    # outlines
    for name, ob in objs.items():
        if name in ('Eyes',):
            continue
        lib.add_outline(ob, ol, 0.0018 if name != 'Head' else 0.0012)
    render.setup_scene()
    rd = os.path.join(ROOT, 'renders')
    if 'noface' not in PARTS:
        render.face(TAG, rd)
    if 'noturn' not in PARTS:
        render.turnaround(TAG, rd)
    if 'detail' in PARTS:
        render.detail(TAG, rd)
    if 'cmp' in PARTS:
        render.ref_compare(TAG, rd, '/tmp/indep/refs')
    if 'export' in PARTS:
        export(objs)
    else:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'out', f'{TAG}.blend'))


def export(objs):
    out = os.path.join(ROOT, 'out')
    for ob in objs.values():
        for m in ob.modifiers:
            if m.name == 'Outline':
                m.show_viewport = False; m.show_render = False
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    tot = 0; lines = []
    for name, ob in objs.items():
        ev = ob.evaluated_get(dg); me = ev.to_mesh()
        me.calc_loop_triangles(); n = len(me.loop_triangles)
        ev.to_mesh_clear(); tot += n
        lines.append(f'{name}: {n}')
    lines.append(f'TOTAL: {tot}')
    open(os.path.join(out, 'tricount.txt'), 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    for o in bpy.context.scene.objects:
        o.select_set(o.name in [x.name for x in objs.values()])
    bpy.context.view_layer.objects.active = objs['Head']
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, 'model.glb'), export_format='GLB', use_selection=True,
                              export_apply=True)
    bpy.ops.wm.obj_export(filepath=os.path.join(out, 'model.obj'), export_selected_objects=True,
                          apply_modifiers=True, export_materials=True, forward_axis='NEGATIVE_Z', up_axis='Y')
    for ob in objs.values():
        for m in ob.modifiers:
            if m.name == 'Outline':
                m.show_viewport = True; m.show_render = True
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, 'model.blend'))


main()
