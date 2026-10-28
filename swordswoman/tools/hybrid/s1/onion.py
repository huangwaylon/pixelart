"""motion review: onion.py OUT.png DIR seq1,seq2,... (each seq = comma list of names); row = frames at 3x + onion overlay"""
import sys
import numpy as np
from PIL import Image, ImageDraw
out, D = sys.argv[1], sys.argv[2]; seqs = [s.split(',') for s in sys.argv[3:]]
Z = 3; C = (20, 30, 124, 120); w, h = (C[2] - C[0]) * Z, (C[3] - C[1]) * Z
cols = max(len(s) for s in seqs) + 1
S = Image.new('RGB', (w * cols, h * len(seqs)), (30, 26, 36)); d = ImageDraw.Draw(S)
tints = [(255, 80, 80), (80, 200, 255), (120, 255, 120), (255, 220, 80)]
for j, seq in enumerate(seqs):
    on = np.zeros((C[3] - C[1], C[2] - C[0], 3), float); on[:] = (120, 120, 126)
    for i, n in enumerate(seq):
        im = Image.open(f'{D}/{n}.png').convert('RGBA').crop(C)
        bg = Image.new('RGBA', im.size, (120, 120, 126, 255)); bg.alpha_composite(im)
        dd = ImageDraw.Draw(bg); dd.line([(0, 104 - C[1]), (im.width, 104 - C[1])], fill=(90, 90, 100))
        S.paste(bg.convert('RGB').resize((w, h), Image.NEAREST), (i * w, j * h)); d.text((i * w + 3, j * h + 3), n, fill='yellow')
        a = np.array(im); m = a[..., 3] > 0
        on[m] = on[m] * 0.45 + np.array(tints[i % 4]) * 0.55
    S.paste(Image.fromarray(on.astype(np.uint8)).resize((w, h), Image.NEAREST), (len(seq) * w, j * h))
    d.text((len(seq) * w + 3, j * h + 3), 'onion (red,blue,green,yellow)', fill='white')
S.save(out)
