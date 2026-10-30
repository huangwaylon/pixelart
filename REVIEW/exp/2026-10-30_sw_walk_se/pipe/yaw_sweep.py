"""yaw_sweep.py [yaws...]  (Amendment 1, step 1): rest-pose silhouette IoU vs the master EC0_SE_96 for SE body yaw cheats.
For each yaw (and head_yaw_off 0 / -10) render_lock.py renders the rest guide pass with rig_lock.blend; the 1x silhouette
(8x coverage >= .5, + the 1 px outline ring the chain draws) is compared with the master's opaque mask at the best shift (+-10 px);
that shift is also the registration (dx, dy) for lock_view.json. Writes yaw_sweep.json; prints the table."""
import os, sys, json, subprocess, itertools
import numpy as np, cv2
from PIL import Image
from scipy import ndimage as nd
H = os.path.dirname(os.path.abspath(__file__)); ROOT = '/Users/waylonhuang/Documents/other/pixelart'
B = '/Applications/Blender.app/Contents/MacOS/Blender'
MAST = np.asarray(Image.open(ROOT + '/swordswoman/v2/m96/masters/EC0_SE_96.png').convert('RGBA'))[..., 3] > 127
MG = np.array([list(l.rstrip('\n')) for l in open(ROOT + '/swordswoman/v2/m96/masters/EC0_SE_96.txt') if l.strip('\n')])
CLS = {'skin': 'sSmk', 'red': 'eER', 'obi': 'QOo'}  # interior classes: where the face, dress front and obi band sit (the turn)
MCLS = {c: np.isin(MG, list(v)) for c, v in CLS.items()}
GCOL = {'skin': [(248, 218, 194)], 'red': [(192, 59, 61), (142, 34, 44), (232, 96, 79)], 'obi': [(69, 56, 73)]}


def sil(yaw, hoff, tmp):
    env = dict(os.environ, LOCK_YAW=str(yaw), LOCK_HEAD_YAW_OFF=str(hoff), LOCK_DX='0', LOCK_DY='0', LOCK_KINDS='guide')
    subprocess.run([B, '-b', os.environ.get('LOCK_RIG', H + '/rig_lock.blend'), '-P', H + '/render_lock.py', '--', 'rest', 'SE', tmp], env=env, capture_output=True)
    g = cv2.imread(os.path.join(tmp, 'rest_SE_f00_guide.png'), cv2.IMREAD_UNCHANGED)[256:1280, 256:1280]; a = g[..., 3] > 127
    m = a.reshape(128, 8, 128, 8).mean((1, 3)) >= .5; rgb = g[..., [2, 1, 0]].astype(int)
    cl = {c: (np.min([np.abs(rgb - np.array(k)).sum(-1) for k in ks], 0) < 12).reshape(128, 8, 128, 8).mean((1, 3)) >= .5 for c, ks in GCOL.items()}
    return m | nd.binary_dilation(m, nd.generate_binary_structure(2, 1)), cl


def iou(m):
    best = (0, 0, 0)
    for dy, dx in itertools.product(range(-10, 11), range(-10, 11)):
        s = np.roll(np.roll(m, dy, 0), dx, 1); v = (s & MAST).sum() / (s | MAST).sum()
        if v > best[0]: best = (float(v), dx, dy)
    return best


if __name__ == '__main__':
    yaws = [float(x) for x in sys.argv[1:]] or [-10, -15, -20, -25, -30, -35]
    tmp = H + '/work/yaw_sweep'; os.makedirs(tmp, exist_ok=True); rows = []
    for yaw in yaws:
        for hoff in [float(x) for x in os.environ.get('HOFFS', '0,-10').split(',')]:
            m, cl = sil(yaw, hoff, tmp); v, dx, dy = iou(m)
            ci = {c: round(float((np.roll(np.roll(cl[c], dy, 0), dx, 1) & MCLS[c]).sum() / max(1, (np.roll(np.roll(cl[c], dy, 0), dx, 1) | MCLS[c]).sum())), 3) for c in CLS}
            ys, xs = np.nonzero(m); rows.append({'yaw': yaw, 'head_yaw_off': hoff, 'iou': round(v, 4), 'class_iou': ci, 'class_mean': round(float(np.mean(list(ci.values()))), 3), 'dx': dx, 'dy': dy, 'w': int(np.ptp(xs) + 1), 'h': int(np.ptp(ys) + 1)})
            print(rows[-1], flush=True)
    ys, xs = np.nonzero(MAST); print('master w/h', np.ptp(xs) + 1, np.ptp(ys) + 1)
    json.dump({'master_wh': [int(np.ptp(xs) + 1), int(np.ptp(ys) + 1)], 'rows': rows}, open(H + '/yaw_sweep.json', 'w'), indent=1)
