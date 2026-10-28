# test sheet: r11 slash9_ parts in context, one frame per new part pose (labels name the part)
import importlib.util, os, sys
spec = importlib.util.spec_from_file_location('slash', os.path.join(os.path.dirname(__file__), 'slash.py'))
s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
L = {f['label']: f for f in s.slash}
T = [dict(L['coil'], label='torso_csq'), dict(L['swingA'], label='torso_str+head_drag+sm1'),
     dict(L['SMEAR'], label='sm2'), dict(L['impact'], label='lunge set+sm3+spark0'),
     dict(L['hitstop2'], label='shout_fwd+spark2'), dict(L['follow'], label='head_fwd+sk_lunge2')]
for f in T: f['ms'] = 400
ACTIONS = {'test_slash9': (T, False)}
CELLS = {'test_slash9': dict(cell=(92, 76), ground=(46, 62))}
