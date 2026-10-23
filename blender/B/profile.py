import sys, bpy, math
sys.path.insert(0, '/tmp/indep/B/src')
import numpy as np
import scene
ver = sys.argv[sys.argv.index('--') + 1]
R = '/tmp/indep/B/renders'; T = '/tmp/indep/B/tmp'

def hide_hair(flag):
    for o in bpy.data.collections['Character'].objects:
        if o.name.startswith('Hair') or o.name in ('Bow', 'Brows'):
            o.hide_render = flag

def shot(ang, z, osc, w, h, name):
    a = math.radians(ang)
    c = scene.cam('cprof', (math.sin(a) * 3, 0.012 - math.cos(a) * 3, z), (0, 0.012, z), ortho=osc)
    p = f'{T}/{name}.png'
    scene.render_to(c, p, w, h)
    return scene.over_bg(scene.load_np(p))

# E (her left, camera +X), W (her right, camera -X), 3/4, plus hairless E/W for form reading
panels = [shot(90, 1.42, 0.34, 600, 600, 'pE'), shot(-90, 1.42, 0.34, 600, 600, 'pW'), shot(-35, 1.42, 0.34, 600, 600, 'pQ')]
hide_hair(True)
bald = [shot(90, 1.40, 0.25, 600, 600, 'pEb'), shot(-90, 1.40, 0.25, 600, 600, 'pWb'), shot(-30, 1.40, 0.25, 600, 600, 'pQb')]
hide_hair(False)
scene.save_np(np.concatenate([np.concatenate(panels, 1), np.concatenate(bald, 1)], 0), f'{R}/{ver}_profile_set.png')

# side by side with ref6 head profile (she faces screen-right in ref6 -> our W view), matched head height
ref = scene.load_np('/tmp/indep/refs/ref6.png')
H = ref.shape[0]
crop = ref[H - 480:H - 150, 800:1150]          # rows are bottom-up
crop = scene.resize_nn(crop, 600, 566)
mine = shot(-90, 1.425, 0.36, 600, 566, 'pW2')
scene.save_np(np.concatenate([crop, mine], 1), f'{R}/{ver}_profile_vs_ref6.png')

# sprite-size thumbnail (96 px tall) of the full figure in profile, upscaled x4 nearest for viewing
a = math.radians(-90)
c = scene.cam('cth', (math.sin(a) * 6, -math.cos(a) * 6, 0.82), (0, 0, 0.82), ortho=1.72)
scene.render_to(c, f'{T}/th.png', 54, 96)
th = scene.over_bg(scene.load_np(f'{T}/th.png'))
scene.save_np(th, f'{R}/{ver}_profile_96px.png')
# head-only thumbnail too (96 px)
scene.render_to(scene.cam('cth2', (-3, 0, 1.43), (0, 0, 1.43), ortho=0.34), f'{T}/th2.png', 96, 96)
th2 = scene.over_bg(scene.load_np(f'{T}/th2.png'))
big = np.concatenate([scene.resize_nn(th, 216, 384), scene.resize_nn(np.concatenate([th2, th2[:0]], 0), 384, 384)], 1)
scene.save_np(big, f'{R}/{ver}_profile_96px_x4.png')
