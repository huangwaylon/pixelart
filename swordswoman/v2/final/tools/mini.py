"""mini.py OUT.png V=file ... : grid of (illustration 3x | master 3x) pairs, 2 per row, <=800px wide"""
import sys; sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/final/tools'); import ds,fid
from PIL import Image
out=sys.argv[1]; pairs=[a.split('=',1) for a in sys.argv[2:]]
S=3; cw=64*S*2+8; n=len(pairs); cols=2; rows=(n+1)//2
c=Image.new('RGB',(cw*cols,64*S*rows),(150,150,160))
for i,(v,f) in enumerate(pairs):
    x=(i%cols)*cw; y=(i//cols)*64*S
    c.paste(Image.open(ds.F+f'work/ill_{v}.png').resize((64*S,64*S)),(x,y))
    a=ds.render(fid.load(f),S); c.paste(a,(x+64*S,y),a)
c.save(out)
