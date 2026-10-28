# sheet.py OUT.png LABEL=PREFIX ...   -> rows: front side back iso34 se + se@56px (x6 nearest)
import sys
from PIL import Image, ImageDraw
out = sys.argv[1]; rows = [x.split("=", 1) for x in sys.argv[2:]]
V = ["front", "side", "back", "iso34", "se"]; S = 256; G = (128, 128, 128)
def onbg(im, s):
    im = im.convert("RGBA"); bg = Image.new("RGBA", im.size, G + (255,)); bg.alpha_composite(im); return bg.convert("RGB").resize((s, s), Image.LANCZOS)
def pix(im, H=56):
    im = im.convert("RGBA"); bb = im.getbbox(); c = im.crop(bb)
    w = max(1, round(c.width * H / c.height)); small = c.resize((w, H), Image.BOX)
    al = small.split()[3].point(lambda v: 255 if v > 110 else 0); small.putalpha(al)
    cell = Image.new("RGBA", (64, 64), G + (255,)); cell.alpha_composite(small, ((64 - w) // 2, 64 - H - 2))
    return cell.convert("RGB").resize((S, S), Image.NEAREST)
W = 140 + S * (len(V) + 1)
sheet = Image.new("RGB", (W, S * len(rows) + 20), (40, 40, 40)); d = ImageDraw.Draw(sheet)
for i, n in enumerate(V + ["se 56px"]): d.text((140 + i * S + 4, 4), n, fill="white")
for r, (lab, p) in enumerate(rows):
    y = 20 + r * S; d.text((4, y + S // 2), lab, fill="white")
    for i, v in enumerate(V):
        try: sheet.paste(onbg(Image.open(f"{p}_{v}.png"), S), (140 + i * S, y))
        except Exception as e: d.text((140 + i * S + 4, y + 20), "missing", fill="red")
    try: sheet.paste(pix(Image.open(f"{p}_se.png")), (140 + len(V) * S, y))
    except Exception: pass
sheet.save(out); print("sheet", out, sheet.size)
