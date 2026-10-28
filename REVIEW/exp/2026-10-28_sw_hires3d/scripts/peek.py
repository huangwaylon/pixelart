# peek.py CLIP I : hi-res style previews (1024 crop -> 512) for eyeballing
import sys; sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_hires3d/scripts')
import hx, numpy as np
from PIL import Image
F = hx.load(sys.argv[1], int(sys.argv[2])); ims = []
for k, f in hx.STYLES.items():
    img, al = f(F); a = img.copy(); a[~al] = hx.BG; ims.append(Image.fromarray(a.astype(np.uint8)).resize((512, 512), Image.LANCZOS))
W = Image.new('RGB', (512 * len(ims), 512))
for i, im in enumerate(ims): W.paste(im, (512 * i, 0))
W.save(hx.EXP + 'tmp/peek.png')
