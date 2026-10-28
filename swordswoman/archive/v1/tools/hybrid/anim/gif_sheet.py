"""Explode a GIF into a contact sheet + per-frame durations (study tool)."""
import sys
from PIL import Image, ImageSequence, ImageDraw
src, out = sys.argv[1], sys.argv[2]
im = Image.open(src)
frames, durs = [], []
for f in ImageSequence.Iterator(im):
    frames.append(f.convert("RGB").copy()); durs.append(f.info.get("duration", 0))
# dedupe consecutive identical frames into holds
segs = []
for f, d in zip(frames, durs):
    if segs and list(segs[-1][0].getdata()) == list(f.getdata()):
        segs[-1][1] += d
    else:
        segs.append([f, d])
print(src, "raw", len(frames), "unique", len(segs), "ms", [s[1] for s in segs])
sc = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
w, h = int(frames[0].width * sc), int(frames[0].height * sc)
cols = min(8, len(segs)); rows = (len(segs) + cols - 1) // cols
sheet = Image.new("RGB", (cols * w, rows * (h + 14)), "white")
dr = ImageDraw.Draw(sheet)
for i, (f, d) in enumerate(segs):
    x, y = (i % cols) * w, (i // cols) * (h + 14)
    sheet.paste(f.resize((w, h), Image.NEAREST), (x, y + 14))
    dr.text((x + 2, y), f"{i}: {d}ms", fill="black")
sheet.save(out)
