"""f3d_layout.py (F, round 5): one face layout on the 3D head that reads in S, SE and E.
The m96 masters are not mutually consistent in 3D (the SE/E masters draw the eyes and mouth further to the side than the S master would put them
on a real head), so a pure S-calibrated texture puts the SE/E features too far toward the front, where they foreshorten to ~1 px.
Here every face landmark (eye centres + corners, brows, mouth, blush, nose) gets the texture position that minimises the weighted screen error
against the master landmarks in S, SE and E together (rest pose, measured through R's renderer with a UV-coded texture: out/calR/rest_<V>),
then a thin-plate warp maps the S design coordinates through these control points.  -> face/f3d/layout.json (used by f3d_lib.to_px)
   python f3d_layout.py [wS wSE wE]"""
import os, sys, json
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy.interpolate import RBFInterpolator
HERE = os.path.dirname(os.path.abspath(__file__)); EXP = os.path.dirname(os.path.dirname(HERE))
W = dict(zip(('S', 'SE', 'E'), [float(x) for x in (sys.argv[1:4] if len(sys.argv) >= 4 else (1.0, 1.0, 0.6))]))
# landmark: S design (m96 S px centre) -> master targets in SE / E (None = not visible in that view)
LM = {
    'eyeL':   [(59, 52), (65, 53), (75, 52)], 'eyeL_o': [(56, 51.5), (62, 52.5), (72.2, 51.5)], 'eyeL_i': [(61, 51.2), (67, 52.2), (77, 51.2)],
    'eyeR':   [(69, 52), (74, 53), None], 'eyeR_o': [(72, 51.5), (76, 52.5), None], 'eyeR_i': [(67, 51.2), (72.4, 52.2), None],
    'browL':  [(59.5, 47.6), (65.5, 48.6), (75.5, 47.6)], 'browR': [(68.5, 47.6), (74, 48.6), None],
    'mouth':  [(64, 57.5), (69, 58.5), (76, 57.5)], 'blushL': [(59, 56), (64, 57), (74, 56)], 'blushR': [(69, 56), (73.5, 57), None],
    'nose':   [(63.5, 55), (71.5, 56), None],
}


def view_map(V):
    al = json.load(open(f'{EXP}/rig/align.json'))[V]; lift = (al['dx'] - al.get('reg_dx', al['dx']), al['dy'] - al.get('reg_dy', al['dy']))
    a = np.array(Image.open(f'{HERE}/out/calR/rest_{V}_f00_guide.png').convert('RGBA')).astype(float)
    m = (a[..., 3] > 250) & (np.abs(a[..., 2] - 77) <= 2); ys, xs = np.nonzero(m)
    sx = (xs + .5) / 8 - 32 + al['dx'] - lift[0]; sy = (ys + .5) / 8 - 32 + al['dy'] - lift[1]
    uv = np.c_[a[ys, xs, 0] / 255 * 1024, a[ys, xs, 1] / 255 * 1024]
    return cKDTree(uv), np.c_[sx, sy], cKDTree(np.c_[sx, sy]), uv


def main():
    maps = {V: view_map(V) for V in ('S', 'SE', 'E')}
    ctrl_d, ctrl_t, rep = [], [], {}
    for name, tg in LM.items():
        # start: the S position of the landmark, search a window in texture space
        tS, sS, kS, uvS = maps['S']; _, i = kS.query(tg[0]); u0, v0 = uvS[i]
        best = None
        for du in range(-320, 321, 6):
            for dv in range(-200, 201, 6):
                u, v = u0 + du, v0 + dv; err = 0.0; detail = {}
                for k, V in enumerate(('S', 'SE', 'E')):
                    if tg[k] is None or W[V] == 0: continue
                    tuv, sxy, _, _ = maps[V]; d, j = tuv.query((u, v))
                    e2 = 9.0 if d > 8 else float(((sxy[j] - np.array(tg[k])) ** 2).sum())   # not visible there -> 3 px penalty
                    err += W[V] * e2; detail[V] = round(float(np.sqrt(e2)), 2)
                if best is None or err < best[0]: best = (err, u, v, detail)
        ctrl_d.append(tg[0]); ctrl_t.append(best[1:3]); rep[name] = {'tex': [round(best[1]), round(best[2])], 'err_px': best[3], 'S_only_tex': [round(u0), round(v0)]}
    # anchor the rest of the face to the S calibration: a ring of design points around the features
    tS, sS, kS, uvS = maps['S']
    for c in np.linspace(50, 78, 8):
        for r in (42.5, 61.5):
            _, i = kS.query((c, r)); ctrl_d.append((c, r)); ctrl_t.append(tuple(uvS[i]))
    for r in np.linspace(44, 60, 5):
        for c in (50.5, 77.5):
            _, i = kS.query((c, r)); ctrl_d.append((c, r)); ctrl_t.append(tuple(uvS[i]))
    json.dump({'weights': W, 'ctrl_design': [list(map(float, p)) for p in ctrl_d], 'ctrl_tex': [list(map(float, p)) for p in ctrl_t], 'landmarks': rep},
              open(f'{HERE}/layout.json', 'w'), indent=1)
    for k, v in rep.items(): print(k, v)


if __name__ == '__main__':
    main()
