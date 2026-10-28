"""cmp.py V MASTER.txt OUT.png : illustration cell 4x | master 4x | master 1x (+2x) for visual comparison"""
import sys; sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/final/tools')
import ds, fid
from PIL import Image
v,mp,out=sys.argv[1:4]; g=fid.load(mp)
c=Image.new('RGB',(256*2+150,256),(150,150,160)); c.paste(Image.open(ds.F+f'work/ill_{v}.png'),(0,0))
a=ds.render(g,4); c.paste(a,(256,0),a); b=ds.render(g,1); c.paste(b,(520,10),b); b2=ds.render(g,2); c.paste(b2,(520,90),b2); c.save(out)
