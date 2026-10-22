"""Engine export: transparent 1x spritesheet (frames in one row) + JSON {frameSize, frames}."""
import json, os
from PIL import Image
from pipeline import pixgrid
NAMES = ["neutral", "smile", "laugh", "surprised", "sad", "angry", "embarrassed", "determined", "worried", "content"]
OUT = "00_REVIEW/r13_anime_pixel/bust"
os.makedirs(OUT, exist_ok=True)
sheet = Image.new("RGBA", (96 * len(NAMES), 96), (0, 0, 0, 0))
for k, n in enumerate(NAMES):
    img, _ = pixgrid.load(f"art/hand/S4/bust/{k + 1:02d}_{n}.pix")
    sheet.paste(pixgrid.to_image(img), (96 * k, 0))
sheet.save(os.path.join(OUT, "bust_spritesheet.png"))
json.dump({"image": "bust_spritesheet.png", "frameSize": [96, 96], "frames": NAMES},
          open(os.path.join(OUT, "bust_spritesheet.json"), "w"), indent=1)
print("wrote", OUT)
