"""Debug view: render a .pix region at big zoom with pixel grid + coordinate labels (for the artist's eyes only)."""
import sys
from PIL import Image, ImageDraw
from pipeline import pixgrid

def main(path, out, x0=0, y0=0, x1=None, y1=None, z=12, bg="#DFEAF6"):
    img, _ = pixgrid.load(path)
    H, W = img.shape[:2]
    x1 = W if x1 is None else x1; y1 = H if y1 is None else y1
    im = pixgrid.to_image(img[y0:y1, x0:x1], z, bg)
    pad = 22
    out_im = Image.new("RGBA", (im.width + pad, im.height + pad), (255, 255, 255, 255))
    out_im.paste(im, (pad, pad))
    d = ImageDraw.Draw(out_im)
    for i, x in enumerate(range(x0, x1)):
        X = pad + i * z
        d.line([(X, pad), (X, pad + im.height)], fill=(0, 0, 0, 60) if x % 5 else (255, 0, 0, 160))
        if x % 5 == 0: d.text((X + 1, 2), str(x), fill=(200, 0, 0, 255))
    for j, y in enumerate(range(y0, y1)):
        Y = pad + j * z
        d.line([(pad, Y), (pad + im.width, Y)], fill=(0, 0, 0, 60) if y % 5 else (255, 0, 0, 160))
        if y % 5 == 0: d.text((1, Y + 1), str(y), fill=(200, 0, 0, 255))
    out_im.save(out)

if __name__ == "__main__":
    a = sys.argv
    main(a[1], a[2], *[int(v) for v in a[3:]])
