import sys, glob, os
sys.path.insert(0,os.path.dirname(__file__)); import prender
from PIL import Image, ImageDraw
D='/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face/portrait/'
O=['neutral','determined','shout','effort','joy','smile','surprised','pain','worried','inspired','teary','blink']
fs=[(o,D+f'P_{o}.txt') for o in O if os.path.exists(D+f'P_{o}.txt')]
sc=int(sys.argv[1]) if len(sys.argv)>1 else 5
cols=4; tw=40*sc+8; th=40*sc+60
B=Image.new('RGB',(tw*cols,th*((len(fs)+cols-1)//cols)),(128,128,128)); d=ImageDraw.Draw(B)
for k,(o,f) in enumerate(fs):
    x,y=(k%cols)*tw+4,(k//cols)*th
    d.text((x,y+1),o,fill=(255,255,255)); B.paste(prender.img(f,sc),(x,y+12)); B.paste(prender.img(f,1),(x,y+16+40*sc))
out=sys.argv[2] if len(sys.argv)>2 else D+'P_sheet.png'; B.save(out); print(out,B.size)
