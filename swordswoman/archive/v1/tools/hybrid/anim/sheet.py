"""Contact sheet of guide renders: sheet.py out.png [--cols N] [--scale S] img1.png img2.png ...
Grey bg, label on top, pivot baseline (row 104 of the 128 cell) drawn as a faint line."""
import sys
from PIL import Image, ImageDraw
args = sys.argv[1:]
out = args.pop(0)
cols, scale = 8, 1.0
if "--cols" in args:
    i = args.index("--cols"); cols = int(args[i + 1]); del args[i:i + 2]
if "--scale" in args:
    i = args.index("--scale"); scale = float(args[i + 1]); del args[i:i + 2]
ims = [Image.open(p).convert("RGBA") for p in args]
w, h = int(ims[0].width * scale), int(ims[0].height * scale)
rows = (len(ims) + cols - 1) // cols
S = Image.new("RGBA", (cols * w, rows * (h + 12)), (92, 88, 100, 255))
d = ImageDraw.Draw(S)
for k, (p, im) in enumerate(zip(args, ims)):
    x, y = (k % cols) * w, (k // cols) * (h + 12)
    by = y + 12 + int(h * 104 / 128)
    d.line([(x, by), (x + w - 1, by)], fill=(120, 116, 128, 255))
    S.alpha_composite(im.resize((w, h), Image.NEAREST), (x, y + 12))
    d.text((x + 2, y), p.split("/")[-1][:-4][-30:], fill=(255, 255, 255, 255))
S.save(out)
