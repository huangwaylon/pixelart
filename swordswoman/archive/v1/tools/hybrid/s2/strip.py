"""quick review strip: sprites at zoom on slate with the baseline (104) and pivot (64) marked."""
import sys
from PIL import Image, ImageDraw
out = sys.argv[1]; files = sys.argv[2:]; z = 4; crop = (8, 16, 120, 120)
w, h = crop[2] - crop[0], crop[3] - crop[1]
c = Image.new("RGB", (len(files) * w * z, h * z), (36, 32, 44))
d = ImageDraw.Draw(c)
for i, f in enumerate(files):
    im = Image.open(f).convert("RGBA").crop(crop).resize((w * z, h * z), Image.NEAREST)
    c.paste(im, (i * w * z, 0), im)
    x = i * w * z + (64 - crop[0]) * z
    d.line([(x, 0), (x, 6)], fill=(0, 255, 255)); d.line([(i * w * z, (105 - crop[1]) * z), ((i + 1) * w * z, (105 - crop[1]) * z)], fill=(0, 160, 200))
c.save(out)
