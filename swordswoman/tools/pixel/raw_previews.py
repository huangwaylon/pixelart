"""Preview GIFs of raw (uncleaned) model-round animation frames: 8-direction 2x4 grid at 4x.

    .venv/bin/python tools/pixel/raw_previews.py renders/model_round_9 pixel/gifs/raw_round9
"""
import glob, os, re, sys
from PIL import Image, ImageDraw

DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
anims = sorted({re.match(r"anim_(.+?)_(?:S|SE|E|NE|N|NW|W|SW)_f\d+_64\.png", os.path.basename(p)).group(1)
                for p in glob.glob(f"{src}/anim_*_f*_64.png")
                if re.match(r"anim_(.+?)_(?:S|SE|E|NE|N|NW|W|SW)_f\d+_64\.png", os.path.basename(p))})
Z, BG = 4, (120, 128, 112)
for anim in anims:
    frames = {d: sorted(glob.glob(f"{src}/anim_{anim}_{d}_f*_64.png"), key=lambda p: int(re.search(r"_f(\d+)_", p).group(1))) for d in DIRS}
    n = max(len(v) for v in frames.values())
    w, h = Image.open(frames["S"][0]).size
    out_frames = []
    for k in range(n):
        sheet = Image.new("RGB", (4 * w * Z, 2 * (h * Z + 14)), BG)
        dr = ImageDraw.Draw(sheet)
        for i, d in enumerate(DIRS):
            if not frames[d]:
                continue
            im = Image.open(frames[d][k % len(frames[d])]).convert("RGBA").resize((w * Z, h * Z), Image.NEAREST)
            x, y = (i % 4) * w * Z, (i // 4) * (h * Z + 14)
            sheet.paste(im, (x, y + 14), im)
            dr.text((x + 4, y + 1), d, fill=(255, 255, 255))
        out_frames.append(sheet)
    path = f"{out}/{anim}_8dir_4x.gif"
    out_frames[0].save(path, save_all=True, append_images=out_frames[1:], duration=110, loop=0, disposal=2)
    print(path, n, "frames")
