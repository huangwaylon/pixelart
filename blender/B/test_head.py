import sys, bpy
sys.path.insert(0, '/tmp/indep/B/src')
for k in list(sys.modules):
    if k in ('common', 'head', 'scene'):
        del sys.modules[k]
from common import *
import head, scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = scene.setup_scene()
mats = dict(skin=toon_mat('Skin', '#FCD6B4', '#EBA586', t_shadow=0.12), lip=toon_mat('Lip', '#F2A08C', '#E07F70', t_shadow=0.22),
            lash=toon_mat('Lash', '#20223E', '#20223E', emit_only=True), brow=toon_mat('Brow', '#6E3C3A', '#6E3C3A', emit_only=True),
            crease=toon_mat('Crease', '#D9937A', '#D9937A', emit_only=True), blush=toon_mat('Blush', '#F48C80', '#F48C80', emit_only=True, alpha=0.40),
            mouth=toon_mat('Mouth', '#9A4C46', '#9A4C46', emit_only=True))
h = head.build_head(mats, None)
e, f = head.build_eyes(mats, None)
ol = toon_mat('Outline', '#3A2630', '#3A2630', outline=True)
scene.make_outlines([h], ol, 0.0009)
import math
for nm, ang in (('f', 0), ('q', 40), ('s', 90)):
    a = math.radians(ang)
    c = scene.cam('C' + nm, (math.sin(a) * 2, -math.cos(a) * 2, 1.43), (0, 0, 1.43), ortho=0.32)
    scene.render_to(c, f'/tmp/indep/B/tmp/head_{nm}.png', 400, 400)
imgs = [scene.over_bg(scene.load_np(f'/tmp/indep/B/tmp/head_{n}.png')) for n in 'fqs']
import numpy as np
scene.save_np(np.concatenate(imgs, 1), sys.argv[-1])
