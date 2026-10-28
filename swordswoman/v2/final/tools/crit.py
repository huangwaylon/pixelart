"""crit.py suffix out.png : 5 views: row1 illustration crops, row2 masters at 8x, row3 masters at 1x and 2x"""
import sys; sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/final/tools'); import ds,fid
from PIL import Image, ImageDraw
suf,out=sys.argv[1:3]; V=['S','SE','E','NE','N']; c=Image.new('RGB',(1280,940),(150,150,160)); d=ImageDraw.Draw(c)
for i,v in enumerate(V):
    ill=Image.open(ds.F+f'work/ill_{v}.png').crop((16*4,12*4,48*4,62*4)).resize((256,400),Image.LANCZOS); c.paste(ill,(i*256,0))
    g=fid.load(ds.F+((suf.format(v=v) if '{v}' in suf else f'work/{v}_{suf}.txt') if suf!='-' else f'{v}.txt')); im=ds.render(g,8).crop((16*8,12*8,48*8,62*8)); c.paste(im,(i*256,410),im)
    a=ds.render(g,1); c.paste(a,(i*256+10,820),a); b=ds.render(g,2).crop((16*2,8*2,48*2,64*2)); c.paste(b,(i*256+100,816),b); d.text((i*256+4,4),v,fill='black')
c.save(out)
