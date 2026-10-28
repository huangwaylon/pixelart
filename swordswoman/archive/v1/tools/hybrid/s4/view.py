"""view.py OUT.png zoom x0,y0,x1,y1 img1.png img2.png ...  (128-cell sprites side by side, slate bg)"""
import sys
from PIL import Image
out, z, box = sys.argv[1], int(sys.argv[2]), [int(v) for v in sys.argv[3].split(",")]
ims = [Image.open(p).convert("RGBA") for p in sys.argv[4:]]
w, h = box[2] - box[0], box[3] - box[1]
W = Image.new("RGBA", ((w * z + 8) * len(ims), h * z), (0x24, 0x20, 0x2c, 255))
for i, im in enumerate(ims):
    if im.size[0] != 128:
        im = im.resize((128, 128), Image.BOX)
    c = im.crop(box).resize((w * z, h * z), Image.NEAREST)
    W.alpha_composite(c, (i * (w * z + 8), 0))
W.save(out)
