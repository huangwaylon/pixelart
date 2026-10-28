"""p2_gifs.py ACT VIEW (P) -> render/out/p2/<act>/cmp_<act>_<view>_4x.gif : [round-1 chain | P2] side by side, 4x, mid-grey, per-frame ms
from the render json; plus <act>_<view>_strip1x.png (1x strip of P2 frames, transparent) for pxeval / critics."""
import sys, glob, json
from PIL import Image, ImageDraw
EXP = '/Users/waylonhuang/Documents/other/pixelart/REVIEW/exp/2026-10-28_sw_skinned/'
act, view = sys.argv[1:3]; S = 4; BG = (128, 128, 128); CR = (16, 8, 112, 128)
P2 = f'{EXP}render/out/p2/{act}/{act}_{view}'; R1 = f'{EXP}render/out/p2/r1/{act}/{act}_{view}'
info = json.load(open(P2 + '.json')); ms = [int(f['ms']) for f in info['frames']]
fr = lambda d: [Image.open(f).convert('RGBA') for f in sorted(glob.glob(d + '_px/f??.png'))]
A, B = fr(R1), fr(P2); w, h = (CR[2] - CR[0]) * S, (CR[3] - CR[1]) * S
out = []
for a, b in zip(A, B):
    im = Image.new('RGBA', (2 * w + 8, h + 16), (40, 40, 44, 255)); d = ImageDraw.Draw(im)
    for k, (x, lbl) in enumerate(((a, 'round-1 chain'), (b, 'P2'))):
        bg = Image.new('RGBA', x.size, BG + (255,)); bg.alpha_composite(x)
        im.paste(bg.crop(CR).resize((w, h), Image.NEAREST), (k * (w + 8), 16)); d.text((k * (w + 8) + 4, 2), lbl, fill=(230, 230, 120))
    out.append(im.convert('RGB').quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
out[0].save(f'{EXP}render/out/p2/{act}/cmp_{act}_{view}_4x.gif', save_all=True, append_images=out[1:], duration=ms, loop=0, disposal=1)
st = Image.new('RGBA', (128 * len(B), 128), (0, 0, 0, 0))
for i, b in enumerate(B): st.alpha_composite(b, (128 * i, 0))
st.save(f'{EXP}render/out/p2/{act}/{act}_{view}_strip1x.png'); print('gif', act, view, len(B))
