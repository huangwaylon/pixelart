"""render the 8 turn_* keys from the S3 r2 shared cels (h3 kit) into the S5 r2 sprite dir (reused, not re-posed)"""
import sys, os
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools/hybrid/h3')
import kit
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools/hybrid/s5r2')
from PIL import Image
import deorphan
out = sys.argv[1]
for d in ['S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW']:
    a, info = kit.render(dict(base=f'turn_{d}'))
    a, n = deorphan.clean(a, info['owner'] == 'HEAD'); print(d, 'orphans merged', n)
    Image.fromarray(a).save(f'{out}/turn_{d}.png')
    import numpy as np; np.save(f'{out}/../work/turn_{d}_head.npy', info['owner'] == 'HEAD')
    Image.fromarray(a).resize((512, 512), Image.NEAREST).save(f'{out}/turn_{d}_4x.png')
print('turns ok')
