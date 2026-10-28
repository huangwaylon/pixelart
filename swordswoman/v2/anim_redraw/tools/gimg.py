#!/usr/bin/env python3
"""gemini-3-pro-image with imageConfig. gimg.py "prompt" out.png [--aspect 16:9] [--size 4K] [--maxside 2048] refs..."""
import base64, sys, os, tempfile, mimetypes
sys.path.insert(0, '/Users/waylonhuang/Documents/other/pixelart/swordswoman/tools')
import gemini as G
from PIL import Image

def part(p, ms):
    im = Image.open(p)
    if max(im.size) > ms:
        im.thumbnail((ms, ms), Image.NEAREST)
    t = tempfile.NamedTemporaryFile(suffix='.png', delete=False).name; im.save(t)
    return {"inlineData": {"mimeType": "image/png", "data": base64.b64encode(open(t, 'rb').read()).decode()}}

a = sys.argv[1:]
def opt(k, d):
    if k in a:
        i = a.index(k); v = a[i + 1]; del a[i:i + 2]; return v
    return d
asp = opt('--aspect', None); size = opt('--size', None); ms = int(opt('--maxside', '2048'))
prompt, out, refs = a[0], a[1], a[2:]
cfg = {"responseModalities": ["TEXT", "IMAGE"]}
ic = {}
if asp: ic['aspectRatio'] = asp
if size: ic['imageSize'] = size
if ic: cfg['imageConfig'] = ic
d = G.call(G.IMAGE_MODEL, [part(p, ms) for p in refs] + [{"text": prompt}], cfg)
n = 0
for p in d["candidates"][0]["content"]["parts"]:
    if "inlineData" in p and not p.get('thought'):
        path = out if n == 0 else out.replace('.png', f'_{n}.png')
        open(path, 'wb').write(base64.b64decode(p["inlineData"]["data"])); n += 1
        print('wrote', path, Image.open(path).size)
if n == 0:
    sys.exit('no image')
