"""pair.py OUT.png TAG MODE names... : template | gemini output, 400px each"""
import sys
from PIL import Image
from common import *
out, tag, mode = sys.argv[1:4]; names = sys.argv[4:]
S = 400
sh = Image.new("RGB", (2*S*len(names), S), (30, 30, 30))
for i, n in enumerate(names):
    sh.paste(Image.open(f"{OUT}/seed/{n}_tpl{mode}.png").convert("RGB").resize((S, S)), (2*S*i, 0))
    try: sh.paste(Image.open(f"{OUT}/gem/{n}_{mode}_{tag}.png").convert("RGB").resize((S, S)), (2*S*i+S, 0))
    except Exception as e: print(e)
sh.save(out)
