"""concat images horizontally: strip.py out.png a.png b.png ... (scale with --h N)"""
import sys
from PIL import Image
args = sys.argv[1:]; h = None
if args[0] == "--h": h = int(args[1]); args = args[2:]
out, ims = args[0], [Image.open(a).convert("RGB") for a in args[1:]]
if h: ims = [i.resize((int(i.width * h / i.height), h)) for i in ims]
W = sum(i.width for i in ims); H = max(i.height for i in ims)
o = Image.new("RGB", (W, H), "white"); x = 0
for i in ims: o.paste(i, (x, 0)); x += i.width
o.save(out)
