import sys, bpy, math, os
sys.path.insert(0, '/tmp/indep/B/src')
import numpy as np
import scene

ver = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'vX'
what = sys.argv[sys.argv.index('--') + 2] if '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 2 else 'all'
R = '/tmp/indep/B/renders'; T = '/tmp/indep/B/tmp'
sc = bpy.context.scene
sc.eevee.taa_render_samples = 16

def view(ang, dist=6.0, z=0.80, ortho=1.72, name='cam'):
    a = math.radians(ang)
    return scene.cam(name, (math.sin(a) * dist, -math.cos(a) * dist, z), (0, 0, z), ortho=ortho)

if what in ('all', 'turn'):
    panels = []
    for i, ang in enumerate((0, 40, 90, 180)):
        p = f'{T}/turn_{i}.png'
        scene.render_to(view(ang), p, 560, 1024)
        panels.append(scene.over_bg(scene.load_np(p)))
    scene.save_np(np.concatenate(panels, 1), f'{R}/{ver}_turnaround.png')

if what in ('all', 'face'):
    panels = []
    for i, ang in enumerate((0, 35, 90)):
        p = f'{T}/face_{i}.png'
        scene.render_to(view(ang, z=1.43, ortho=0.36, name='camf'), p, 768, 768)
        panels.append(scene.over_bg(scene.load_np(p)))
    scene.save_np(np.concatenate(panels, 1), f'{R}/{ver}_face.png')

if what in ('all', 'back'):
    panels = []
    for i, ang in enumerate((150, 180, 215)):
        p = f'{T}/bk_{i}.png'
        scene.render_to(view(ang, z=1.30, ortho=0.62, name='camb'), p, 640, 640)
        panels.append(scene.over_bg(scene.load_np(p)))
    scene.save_np(np.concatenate(panels, 1), f'{R}/{ver}_hairback.png')

if what in ('all', 'ref'):
    out = []
    W, H = 620, 1006
    # ref framing: figure ~ 1.6 m spans ~71% of frame height, feet at ~86% from top
    osc = 2.25; zc = -0.14 * osc + osc / 2
    for refn, ang in (('ref4', 90), ('ref5', 0)):
        ref = scene.load_np(f'/tmp/indep/refs/{refn}.png')
        ref = scene.resize_nn(ref, W, H)
        p = f'{T}/ref_{refn}.png'
        scene.render_to(view(ang, z=zc, ortho=osc * H / H), p, W, H)
        mine = scene.over_bg(scene.load_np(p), bg=(0.73, 0.73, 0.73))
        out += [ref, mine]
    scene.save_np(np.concatenate(out, 1), f'{R}/{ver}_vs_ref4_ref5.png')
