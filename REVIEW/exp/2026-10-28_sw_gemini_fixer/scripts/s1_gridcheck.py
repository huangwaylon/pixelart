"""Grid sanity check: for each baseline input, reconstruct with the detected grid and with a forced square grid
(step_y, step_y) and (step_x, step_x); measure round-trip error (fixer output nearest-upscaled back to input size vs input,
mean abs RGB error over the foreground). Fixer venv. -> work/base/gridcheck.json"""
import sys, os, json, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixlib as F
from pixelfixer.reconstruct import reconstruct

E = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
B = json.load(open(E + 'work/base/baseline.json'))


def rt(rgba, sx, sy):
    h, w = rgba.shape[:2]
    cols, rows = int(round(w / sx)), int(round(h / sy))
    out = reconstruct(rgba, sx, sy, cols, rows)
    up = np.array(Image.fromarray(out).resize((w, h), Image.NEAREST)).astype(float)
    m, _ = F.bgmask(rgba[..., :3])
    return float(np.abs(up[..., :3] - rgba[..., :3])[m].mean()), cols, rows


res = []
for b in B:
    if 'error' in b: continue
    rgba = np.array(Image.open(b['in']).convert('RGBA'))
    sx, sy = b['step_x'], b['step_y']
    r = {'name': b['name'], 'det': [round(sx, 3), round(sy, 3)]}
    r['err_det'], *_ = rt(rgba, sx, sy)
    best = (r['err_det'], 'det', sx, sy)
    for tag, s in [('sq_y', sy), ('sq_x', sx), ('int_y', round(sy))]:
        e, c, rr = rt(rgba, s, s)
        r['err_' + tag] = e
        if e < best[0] - 0.3: best = (e, tag, s, s)
    r['best'] = best[1]; r['best_step'] = [round(best[2], 3), round(best[3], 3)]
    print(r); res.append(r)
json.dump(res, open(E + 'work/base/gridcheck.json', 'w'), indent=1)
