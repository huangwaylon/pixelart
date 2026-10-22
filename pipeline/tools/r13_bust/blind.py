"""Blind-test kit: shuffled, unlabeled 1x+2x images (mapping written separately, not shown to the tester)."""
import json, os, random, sys
from PIL import Image
from pipeline import pixgrid
NAMES = ["neutral", "smile", "laugh", "surprised", "sad", "angry", "embarrassed", "determined", "worried", "content"]
out = sys.argv[1]; seed = int(sys.argv[2])
os.makedirs(out, exist_ok=True)
order = NAMES[:]; random.Random(seed).shuffle(order)
mapping = {}
for k, n in enumerate(order):
    L = "ABCDEFGHIJ"[k]
    img, _ = pixgrid.load(f"art/hand/S4/bust/{NAMES.index(n) + 1:02d}_{n}.pix")
    a = pixgrid.to_image(img, 1, "#DFEAF6"); b = pixgrid.to_image(img, 2, "#DFEAF6")
    W = Image.new("RGBA", (96 + 192 + 30, 202), (36, 22, 40, 255))
    W.paste(a, (5, 5)); W.paste(b, (111, 5))
    W.save(os.path.join(out, f"{L}.png")); mapping[L] = n
json.dump(mapping, open(f"/tmp/bust/mapping_{seed}.json", "w"))
