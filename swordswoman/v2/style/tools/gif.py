"""gif.py out.gif scale f1.txt:ms f2.txt:ms ...  -> GIF on mid-grey + contact sheet out_sheet.png (1x row + scaled row)"""
import sys
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/style/tools')
from pk import read, to_img
from PIL import Image
out, s = sys.argv[1], int(sys.argv[2])
fr = [a.rsplit(':', 1) for a in sys.argv[3:]]
ims = [to_img(read(f), s, True).convert('RGB') for f, _ in fr]
ds = [int(d) for _, d in fr]
ims[0].save(out, save_all=True, append_images=ims[1:], duration=ds, loop=0, disposal=2)
one = [to_img(read(f), 1, True).convert('RGB') for f, _ in fr]
W = sum(i.width for i in ims); H = ims[0].height + one[0].height + 4
S = Image.new('RGB', (W, H), (128, 128, 128)); x = 0
for a, b in zip(one, ims): S.paste(a, (x, 0)); S.paste(b, (x, one[0].height + 4)); x += b.width
S.save(out.replace('.gif', '_sheet.png')); print(out, S.size)
