# quick preview: our 12 portraits at SCALE (6x2) + 1x strip
import sys, os; sys.path.insert(0,os.path.dirname(__file__)); import prender
from PIL import Image, ImageDraw
D='/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face/'
O=['neutral','determined','shout','effort','joy','smile','surprised','pain','worried','inspired','teary','blink']
sc=int(sys.argv[1]); ks=sys.argv[3:] or O; cols=min(6,len(ks)); tw=40*sc+4
rows=(len(ks)+cols-1)//cols
B=Image.new('RGB',(tw*cols,(tw+12)*rows+50),(128,128,128)); d=ImageDraw.Draw(B)
for k,o in enumerate(ks):
    x=(k%cols)*tw; y=(k//cols)*(tw+12)
    d.text((x,y),o,fill=(255,255,255)); B.paste(prender.img(D+f'portrait/P_{o}.txt',sc,(176,216,232)),(x,y+11))
    B.paste(prender.img(D+f'portrait/P_{o}.txt',1,(176,216,232)),(k*44,rows*(tw+12)+4))
B.save(sys.argv[2])
