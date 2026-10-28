# Author extra Omni skeleton poses by rotating arm chains of pose_rest (Omni frame: Y up, face +Z, char right at -X)
import json, numpy as np, sys
src = '/Users/waylonhuang/Documents/other/pixelart/.models/hy_omni/poses/pose_rest'
out = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/hy3d/poses/'
names = list(json.load(open(src + '.json'))); P = np.loadtxt(src + '.txt')
def rotmat(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b); v = np.cross(a, b); c = a @ b
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); return np.eye(3) + K + K @ K / (1 + c)
def aim(Q, side, target):
    idx = [i for i, n in enumerate(names) if n.endswith('.' + side) and not n.startswith(('Shoulder', 'Eye'))]
    arm = names.index('Arm.' + side); wr = names.index('Wrist.' + side)
    piv = Q[arm, :3].copy(); R = rotmat(Q[wr, :3] - piv, np.array(target, float))
    for i in idx:
        for s in (0, 3): Q[i, s:s+3] = R @ (Q[i, s:s+3] - piv) + piv
    return Q
poses = {
  'pose_arms_up': {'R': (-0.35, 0.94, 0.0), 'L': (0.35, 0.94, 0.0)},
  'pose_slash_extend': {'R': (-0.5, 0.15, 0.85), 'L': (0.6, -0.3, -0.7)},
  'pose_tpose': {'R': (-1, 0, 0), 'L': (1, 0, 0)},
}
for k, d in poses.items():
    Q = P.copy()
    for s, t in d.items(): Q = aim(Q, s, t)
    np.savetxt(out + k + '.txt', Q); print(k, Q[names.index('Wrist.R'), :3].round(2), Q[names.index('Wrist.L'), :3].round(2))
