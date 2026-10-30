"""export.py OUTDIR WORKDIR/<act>_<VIEW>.json  -- 4x GIF (gifio: loop=0, >= 20 ms, exact palette, mid-grey bg) + 1x strip of fNN.png."""
import sys, os, json
from PIL import Image
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned/render')
from gifio import write_gif  # noqa: E402
BG = (110, 110, 110)
outd, jp = sys.argv[1], sys.argv[2]; info = json.load(open(jp)); n = len(info['frames']); tag = os.path.basename(jp)[:-5]
ims = [Image.open(os.path.join(outd, f'f{i:02d}.png')).convert('RGBA') for i in range(n)]
durs = write_gif(os.path.join(outd, f'{tag}_4x.gif'), ims, [f['ms'] for f in info['frames']], bg=BG, scale=4)
st = Image.new('RGBA', (128 * n, 128), (0, 0, 0, 0))
for i, im in enumerate(ims): st.alpha_composite(im, (128 * i, 0))
st.save(os.path.join(outd, f'{tag}_strip1x.png'))
print('EXPORT', tag, 'gif ms', durs)
