"""S5 r2 RETRACE: Gemini-acted key poses re-drawn by Claude on the S3 r2 shared body cels (tools/hybrid/h3 kit +
cels + lock2 head v2). Every body pixel comes from the S3 cel primitives (@leg @cuff @limb @skirt @katana @ribbon,
torso/collar rows, layer offsets and xf squash/stretch/shear); the Gemini pose is only the acting reference.
FX (smears, spark, dust, speed lines) are drawn by tools/hybrid/s5r2/fx.py AFTER the body, protected from the face.

retrace.py ANIM [names...]        ANIM in slash_SE jump_E walk_SE (specs in tools/hybrid/s5r2/anims/<ANIM>.py)
   -> hybrid/S5_pixelnative/r2/sprite/<name>.png (+ _4x.png, _hires.png = Gemini hi-res pose ref, _pose.png =
      cell-scale pose ref, _cmp.png = pose ref | retrace onion view)"""
import sys, os, importlib.util, shutil
import numpy as np
from PIL import Image, ImageDraw
ROOT = '/Users/waylonhuang/Documents/other/pixelart/swordswoman'
sys.path.insert(0, f'{ROOT}/tools/hybrid/h3'); sys.path.insert(0, f'{ROOT}/tools/hybrid/s5r2')
import kit, fx as FX, deorphan
OUT = os.environ.get('S5_OUT', f'{ROOT}/hybrid/S5_pixelnative/r2/sprite')
POSE = f'{ROOT}/hybrid/S5_pixelnative/r2/pose'

def load_spec(anim):
    p = f'{ROOT}/tools/hybrid/s5r2/anims/{anim}.py'
    s = importlib.util.spec_from_file_location('s5spec_' + anim, p)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m

def render(fs):
    fs = dict(fs); fxops = fs.pop('s5fx', [])
    a, info = kit.render(fs)
    a = np.ascontiguousarray(a).copy()
    protect = info['owner'] == 'HEAD'
    if fs.get('deorphan', True): a, info['orphans_fixed'] = deorphan.clean(a, protect)
    for op in fxops:
        fn = getattr(FX, op[0]); kw = dict(op[2]) if len(op) > 2 else {}
        if op[0] in ('crescent', 'spark', 'limb_smear'): kw.setdefault('protect', protect)
        fn(a, *op[1], **kw)
    return a, info

def onion(spr, pose, path, z=6, box=(16, 16, 112, 112)):
    def bg(im):
        b = Image.new('RGBA', im.size, (84, 132, 66, 255)); b.alpha_composite(im); return b
    s = Image.fromarray(spr).crop(box); p = Image.open(pose).convert('RGBA').crop(box) if os.path.exists(pose) else Image.new('RGBA', s.size)
    pa = np.array(p).astype(float); pa[..., 3] *= 0.45; ghost = Image.fromarray(pa.astype(np.uint8))
    ov = bg(ghost); m = np.array(s)[..., 3] > 0
    ova = np.array(ov); sa = np.array(s)
    # outline of the retrace in cyan over the ghost
    edge = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    ova[edge] = (0, 255, 255, 255)
    W = s.width * z
    im = Image.new('RGBA', (W * 3, s.height * z))
    im.paste(bg(p).resize((W, s.height * z), Image.NEAREST), (0, 0))
    im.paste(Image.fromarray(ova).resize((W, s.height * z), Image.NEAREST), (W, 0))
    im.paste(bg(s).resize((W, s.height * z), Image.NEAREST), (2 * W, 0))
    d = ImageDraw.Draw(im)
    for i in range(0, s.width + 1, 8):
        for k in range(3):
            d.line([(k * W + i * z, 0), (k * W + i * z, 4)], fill='yellow'); d.text((k * W + i * z + 1, 4), str(box[0] + i), fill='yellow')
    for j in range(0, s.height + 1, 8):
        d.line([(2 * W, j * z), (2 * W + 4, j * z)], fill='yellow'); d.text((2 * W + 5, j * z), str(box[1] + j), fill='yellow')
    im.save(path)

if __name__ == '__main__':
    anim = sys.argv[1]; only = sys.argv[2:]
    m = load_spec(anim); os.makedirs(OUT, exist_ok=True)
    for name, fs in m.frames().items():
        if only and name not in only: continue
        a, info = render(fs)
        Image.fromarray(a).save(f'{OUT}/{name}.png')
        np.save(f'{OUT}/../work/{name}_head.npy', info['owner'] == 'HEAD')
        Image.fromarray(a).resize((512, 512), Image.NEAREST).save(f'{OUT}/{name}_4x.png')
        if os.path.exists(f'{POSE}/{name}_hires.png'): shutil.copy(f'{POSE}/{name}_hires.png', f'{OUT}/{name}_hires.png')
        if os.path.exists(f'{POSE}/{name}.png'): shutil.copy(f'{POSE}/{name}.png', f'{OUT}/{name}_pose.png')
        onion(a, f'{POSE}/{name}.png', f'{OUT}/../work/{name}_cmp.png' if os.path.isdir(f'{OUT}/../work') else f'/tmp/{name}_cmp.png')
        print('wrote', name)
