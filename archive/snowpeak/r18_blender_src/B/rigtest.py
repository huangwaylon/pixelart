import sys, bpy, math
sys.path.insert(0, '/tmp/indep/B/src')
import numpy as np
import scene
out = sys.argv[sys.argv.index('--') + 1]
arm = bpy.data.objects['Rig']
P = arm.pose.bones
def rot(n, x=0, y=0, z=0):
    b = P[n]; b.rotation_mode = 'XYZ'; b.rotation_euler = (math.radians(x), math.radians(y), math.radians(z))
rot('upper_arm.L', 35, 0, 18); rot('forearm.L', 55, 0, 0); rot('hand.L', 20, 0, 0)
rot('upper_arm.R', -20, 0, -10); rot('forearm.R', 30, 0, 0)
rot('thigh.R', 28, 0, 0); rot('shin.R', -45, 0, 0); rot('foot.R', 15, 0, 0)
rot('thigh.L', -6, 0, 0)
rot('spine', 0, 8, 0); rot('chest', 4, 6, 0); rot('neck', -4, 0, 4); rot('head', -8, 10, 9)
for i in range(1, 5):
    rot(f'ponytail.{i:02d}', 0, 0, 9 + 3 * i)
for s, sg in (('L', 1), ('R', -1)):
    for i in range(1, 4):
        rot(f'sidelock.{s}.{i:02d}', 6, 0, 0)
    for i in range(1, 3):
        rot(f'bowtail.{s}.{i:02d}', 10, 0, sg * 12)
for i in range(1, 4):
    rot(f'scarf_tail.{i:02d}', 8, 0, 4)
bpy.context.view_layer.update()
panels = []
for i, ang in enumerate((0, 35, 90)):
    a = math.radians(ang)
    c = scene.cam('crig', (math.sin(a) * 6, -math.cos(a) * 6, 0.82), (0, 0, 0.82), ortho=1.72)
    p = f'/tmp/indep/B/tmp/rig_{i}.png'
    scene.render_to(c, p, 560, 1024)
    panels.append(scene.over_bg(scene.load_np(p)))
scene.save_np(np.concatenate(panels, 1), out)
