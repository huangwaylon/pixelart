"""r20: compose the r20_render.py outputs into review boards.

    .venv/bin/python -m pipeline.tools.r20_boards <render_dir> <tag> [<out_dir>]

Writes <tag>_turnaround.png, <tag>_faces.png, <tag>_iso8.png, <tag>_px8_x6.png (and <tag>_sheet.png = all of them
stacked) into out_dir (default: render_dir).
"""
import os
import sys

from PIL import Image, ImageDraw

DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
BG = (34, 28, 44)


def labelled(img, text):
    out = Image.new("RGB", (img.width, img.height + 16), BG)
    out.paste(img.convert("RGB"), (0, 16))
    ImageDraw.Draw(out).text((4, 2), text, fill=(235, 235, 235))
    return out


def hrow(imgs, gap=6):
    w = sum(i.width for i in imgs) + gap * (len(imgs) + 1)
    h = max(i.height for i in imgs) + 2 * gap
    out = Image.new("RGB", (w, h), BG)
    x = gap
    for i in imgs:
        out.paste(i, (x, gap)); x += i.width + gap
    return out


def vstack(imgs):
    w = max(i.width for i in imgs)
    out = Image.new("RGB", (w, sum(i.height for i in imgs)), BG)
    y = 0
    for i in imgs:
        out.paste(i, (0, y)); y += i.height
    return out


def main():
    src, tag = sys.argv[1], sys.argv[2]
    dst = sys.argv[3] if len(sys.argv) > 3 else src
    os.makedirs(dst, exist_ok=True)
    ld = lambda n: Image.open(os.path.join(src, f"{tag}_{n}.png")).convert("RGB")
    boards = {
        "turnaround": hrow([labelled(ld(v), f"{tag} {v}") for v in ("front", "q34", "side", "back")]),
        "faces": hrow([labelled(ld(v), f"{tag} {v}") for v in ("face_front", "face_q34", "face_side")]),
        "iso8": hrow([labelled(ld(f"iso_{d}"), d) for d in DIRS]),
        "px8_x6": hrow([labelled(ld(f"px_{d}").resize((32 * 6, 48 * 6), Image.NEAREST), d) for d in DIRS]),
    }
    for k, b in boards.items():
        b.save(os.path.join(dst, f"{tag}_{k}.png"))
    sheet = [boards["turnaround"], boards["faces"]]
    sheet += [b.resize((sheet[0].width, int(b.height * sheet[0].width / b.width))) for b in (boards["iso8"], boards["px8_x6"])]
    vstack(sheet).save(os.path.join(dst, f"{tag}_sheet.png"))
    print("boards ->", dst)


if __name__ == "__main__":
    main()
