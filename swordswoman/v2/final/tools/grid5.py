"""grid5.py suffix out.png : 5 views, row1 illustration crop, row2 master (5x, cols 16-48 rows 12-62)"""
import sys; sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/final/tools'); import ds,fid
from PIL import Image
suf,out=sys.argv[1:3]; V=['S','SE','E','NE','N']; c=Image.new('RGB',(800,500),(150,150,160))
for i,v in enumerate(V):
    ill=Image.open(ds.F+f'work/ill_{v}.png').crop((16*4,12*4,48*4,62*4)).resize((160,250)); c.paste(ill,(i*160,0))
    g=fid.load(ds.F+(f'work/{v}_{suf}.txt' if suf!='-' else f'{v}.txt')); im=ds.render(g,5).crop((16*5,12*5,48*5,62*5)); c.paste(im,(i*160,250),im)
c.save(out)
