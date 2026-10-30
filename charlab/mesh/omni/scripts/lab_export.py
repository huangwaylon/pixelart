"""Export charlab lab procedural models as Omni controls.

Usage: venv/bin/python -I lab_export.py ID TIER_PRESET OUT_DIR      e.g. schoolgirl detailed_compact work/lab
Writes OUT_DIR/<ID>_<preset>.glb     (glb frame: Y up, faces +Z, her left +X; vertex colours from the palette)
       OUT_DIR/<ID>_<preset>_pose.txt (Omni 51-bone skeleton, demo bone layout, normalised like the mesh: bbox centre,
                                       longest extent -> 2*0.98)
Lab frame: Z up, faces -Y, +X her left -> glb (x, z, -y).
"""
import sys, os, json
import numpy as np, trimesh

LAB = '/Users/waylonhuang/Documents/other/pixelart/charlab/lab/work'
DEMO = '/Users/waylonhuang/Documents/other/pixelart/.models/hy_omni/src_omni_mlx/demos/pose'
cid, var, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
z = np.load(f'{LAB}/{cid}/{var}/model.npz'); J = json.load(open(f'{LAB}/{cid}/{var}/model.json'))
to_glb = lambda p: np.stack([p[..., 0], p[..., 2], -p[..., 1]], -1)
V = to_glb(z['V'].astype(np.float64)); F = z['F']
pal = J['palette']
cols = np.array([[int(pal[m[0]][i:i + 2], 16) for i in (1, 3, 5)] + [255] if m[0] in pal else [200, 200, 200, 255] for m in J['mats']], np.uint8)
fc = cols[np.clip(z['fmat'], 0, len(cols) - 1)]
mesh = trimesh.Trimesh(V, F, face_colors=fc, process=False)
name = f'{cid}_{var.split("_")[1]}'
mesh.export(f'{out}/{name}.glb')

# skeleton
B = {b['name']: (to_glb(np.array(b['head'])), to_glb(np.array(b['tail']))) for b in J['bones']}
lo, hi = V.min(0), V.max(0); c = (lo + hi) / 2; s = 2 * 0.98 / (hi - lo).max()
demo = json.load(open(f'{DEMO}/a_pose_bone.json')); names = list(demo)
dj = {n: np.array(v[0]) for n, v in demo.items()}
dtxt = np.loadtxt(f'{DEMO}/a_pose_bone.txt')
hc = to_glb(np.array(J['head_c']))
eye_y = J['eye_z']; sp = J['face']['eye_spacing'] * J['H'] / 2
newj = {
    'Upper Body': B['hips'][0], 'Lower Body': B['hips'][0] - [0, 0.02, 0], 'Upper Body 2': B['chest'][0],
    'Neck': B['neck'][0], 'Head': B['head'][0],
    'Eye.R': np.array([-sp, eye_y, hc[2] + J['head_r'][1] * 0.9]), 'Eye.L': np.array([sp, eye_y, hc[2] + J['head_r'][1] * 0.9]),
}
for side, S in (('R', 'R'), ('L', 'L')):
    newj[f'Shoulder.{side}'] = B[f'shoulder.{S}'][0]; newj[f'Arm.{side}'] = B[f'upper_arm.{S}'][0]
    newj[f'Elbow.{side}'] = B[f'forearm.{S}'][0]; newj[f'Wrist.{side}'] = B[f'hand.{S}'][0]
    newj[f'Foot.{side}'] = B[f'thigh.{S}'][0]; newj[f'Knee.{side}'] = B[f'shin.{S}'][0]; newj[f'Ankle.{side}'] = B[f'foot.{S}'][0]
    # fingers: demo offsets from wrist, rotated so demo forearm dir -> our forearm dir, scaled by hand length
    dw, de = dj[f'Wrist.{side}'], dj[f'Elbow.{side}']; ow, oe = newj[f'Wrist.{side}'], newj[f'Elbow.{side}']
    hand_len = np.linalg.norm(B[f'hand.{S}'][1] - B[f'hand.{S}'][0])
    a, b = (dw - de) / np.linalg.norm(dw - de), (ow - oe) / np.linalg.norm(ow - oe)
    v = np.cross(a, b); cth = a @ b; K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    Rm = np.eye(3) + K + K @ K / (1 + cth)
    fscale = hand_len / np.linalg.norm(dj[f'Middle3.{side}'] - dw)
    FT = (lambda dw, ow, Rm, fscale: (lambda p: ow + Rm @ (p - dw) * fscale))(dw, ow, Rm, fscale)
    newj['_ft' + side] = FT
    for n in names:
        if n.endswith('.' + side) and any(n.startswith(f) for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')):
            newj[n] = FT(dj[n])
FTs = {'R': newj.pop('_ftR'), 'L': newj.pop('_ftL')}
assert set(newj) == set(names), set(names) - set(newj)
N = lambda p: (p - c) * s
Q = np.zeros_like(dtxt)
for i, row in enumerate(dtxt):
    n0 = names[i]
    Q[i, :3] = N(newj[n0])
    p = row[3:]; n1 = min(names, key=lambda m: np.linalg.norm(dj[m] - p))
    if np.linalg.norm(dj[n1] - p) < 5e-3:
        Q[i, 3:] = N(newj[n1])
    elif n0 == 'Head':
        Q[i, 3:] = N(B['head'][1])
    elif n0.startswith('Ankle'):
        Q[i, 3:] = N(B['toe.' + n0[-1]][1])
    elif n0[-2:] in ('.R', '.L') and (n0.startswith('Wrist') or any(n0.startswith(f) for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))):
        Q[i, 3:] = N(FTs[n0[-1]](p))
    else:
        Q[i, 3:] = Q[i, :3] + (p - dj[n0])
np.savetxt(f'{out}/{name}_pose.txt', Q)
print('lab', name, 'tris', len(F), 'height', hi[1] - lo[1], 'bbox xyz norm', np.round((hi - lo) / (hi - lo).max(), 3))
