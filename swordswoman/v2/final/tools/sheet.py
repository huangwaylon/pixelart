"""sheet.py [suffix]: final/sheet.png: per view column = illustration (cell, 4x) | master 4x | master 1x ; + palette swatch row. Also sheet_thumb.png (<=800w)"""
import sys; sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/final/tools')
import ds, fid
from PIL import Image, ImageDraw
V=['S','SE','E','NE','N']; suf=sys.argv[1] if len(sys.argv)>1 else None
cw=256*2+80; im=Image.new('RGB',(cw*3,256*2+110),(150,150,160)); d=ImageDraw.Draw(im)
for i,v in enumerate(V):
    x=(i%3)*cw; y=(i//3)*256
    g=fid.load(ds.F+((suf.format(v=v) if '{v}' in suf else f'work/{v}_{suf}.txt') if suf else f'{v}.txt'))
    im.paste(Image.open(ds.F+f'work/ill_{v}.png'),(x,y)); a=ds.render(g,4); im.paste(a,(x+256,y),a)
    b=ds.render(g,1); im.paste(b,(x+520,y+20),b); d.text((x+4,y+4),v,fill='black')
sw=Image.open(ds.F+'palette_swatch.png'); im.paste(sw,(cw+20,256+130+20)) if False else im.paste(sw,(cw*2+10,256+60))
OUT=sys.argv[2] if len(sys.argv)>2 else ds.F+'sheet.png'; im.save(OUT); im.resize((800,im.height*800//im.width)).save(OUT.replace('.png','_thumb.png')); print(im.size)
