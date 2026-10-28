"""S5 r3 RETRACE: action keys re-drawn by Claude on S3's lock3-era h4 compositor (tools/hybrid/h4 kit + cels; head
stamps from hybrid/lock3, verified by verify_lock.py). Gemini pixel-native poses (hybrid/S5_pixelnative/r3/pose) are
acting refs only. FX are NOT drawn here: fxpass.py draws them after the body.

retrace.py ANIM [names...]   ANIM in slash_SE jump_E   (specs: tools/hybrid/s5r3/anims/<ANIM>.py)
  -> hybrid/S5_pixelnative/r3/base/<name>.png + <name>_owner.npy (layer ownership) + <name>_meta.json
Head acting: fs['act'] may be a tuple ('squash', 'back') -> the lock3 act stamps applied in order (each is a lock3
stamp transform; composition = integer row/col moves only)."""
import sys, os, json, importlib.util
import numpy as np
from PIL import Image
ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
sys.path.insert(0, f'{ROOT}/tools/hybrid/h4'); sys.path.insert(0, f'{ROOT}/tools/hybrid/s5r3')
import kit, heads as HEADS
OUT = f'{ROOT}/hybrid/S5_pixelnative/r3/base'
_head0 = HEADS.head
FIXLOG = set()
def act_fixed(g, d, a):
    """lock3 act stamps; 'back' on facing dirs is re-done WITHOUT the np.roll wrap: lock3's heads.act('back') clears
    column 0 instead of the wrapped column, which leaves a stray 1 px K column at the far edge (rows 0..face_top-4)
    and strips the hair outline at column 0 (visible in hybrid/lock3/head_E_act-back.png). Corrected here to the
    stamp's stated intent (crown rows 1 px against facing, '.' fill); reported to the lead as a lock3.1 fix."""
    f = HEADS.FACING[d]
    if a in ('back', 'down') and f:
        s = -f if a == 'back' else f                   # back: crown against facing; down: crown toward facing
        out = g.copy(); H, W = g.shape; ft = HEADS.face_top(g)
        for y in range(0, ft - 3):
            r = list(g[y]); r = (r[1:] + ['.']) if s < 0 else (['.'] + r[:-1]); out[y] = r
        FIXLOG.add(f'head_{d} act-{a}: no-wrap shift (lock3 np.roll wrap bug)')
        return out
    return HEADS.act(g, d, a)
def head_multi(d, e='calm', t=0, a=None):
    if a is None: return _head0(d, e, t, None)
    g = HEADS.tilt(HEADS.expr(HEADS.base(d), d, e), t)
    acts = a if isinstance(a, (tuple, list)) else (a,)
    if HEADS.FACING[d] and any(x in ('back', 'down') for x in acts):   # 1 px pad so the crown shift keeps its outline
        g = np.hstack([np.full((g.shape[0], 1), '.', dtype=g.dtype), g, np.full((g.shape[0], 1), '.', dtype=g.dtype)])
    for x in acts: g = act_fixed(g, d, x)
    return g
def padded(d, a):
    acts = a if isinstance(a, (tuple, list)) else ((a,) if a else ())
    return bool(HEADS.FACING[d]) and any(x in ('back', 'down') for x in acts)
HEADS.head = head_multi

def load_spec(anim):
    if anim == 'bonus':            # S3 r3 run/dash BODY (S3 owns run/dash poses); S3's fx are stripped, S5 draws its own
        os.chdir(ROOT)
        p = f'{ROOT}/tools/hybrid/h4/anims/bonus_SE.py'
        s = importlib.util.spec_from_file_location('s3bonus', p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
        class W:
            @staticmethod
            def frames():
                out = {}
                for k, fs in m.FRAMES.items():
                    fs = dict(fs); fs.pop('fx', None); fs['meta'] = dict(src='S3 h4 anims/bonus_SE.py (fx stripped)'); out[k] = fs
                return out
        return W
    p = f'{ROOT}/tools/hybrid/s5r3/anims/{anim}.py'
    s = importlib.util.spec_from_file_location('s5r3_' + anim, p)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m

def render(fs):
    fs = dict(fs); meta = fs.pop('meta', {}); patches = fs.pop('patch', [])
    hd = fs.get('head_dir', kit.load_cel(fs['base']).HEAD[0])
    if padded(hd, fs.get('act')):
        hx, hy = fs.get('head', (0, 0)); fs['head'] = (hx - 1, hy)
    a, info = kit.render(fs)
    import patch as PT
    for pt in patches:
        if pt[0] == 'spec': PT.spec(a, pt[1], pt[2] if len(pt) > 2 else 'over')
        else: PT.apply(a, *pt)
    return np.ascontiguousarray(a).copy(), info, meta

if __name__ == '__main__':
    anim = sys.argv[1]; only = sys.argv[2:]
    m = load_spec(anim); os.makedirs(OUT, exist_ok=True)
    for name, fs in m.frames().items():
        if only and name not in only: continue
        a, info, meta = render(fs)
        Image.fromarray(a).save(f'{OUT}/{name}.png')
        own = info['owner'].astype(str)
        np.save(f'{OUT}/{name}_owner.npy', own)
        meta = dict(meta, head=list(info['head']), shift=list(info['shift']), head_fixes=sorted(FIXLOG))
        json.dump(meta, open(f'{OUT}/{name}_meta.json', 'w'), indent=1)
        print('wrote', name)
