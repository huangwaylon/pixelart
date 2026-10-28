"""build_all.py [tag]: compose every view x expression -> out/sprite/<V>_<expr>.txt + _1x/_8x png; sheet grids."""
import sys, os; sys.path.insert(0,os.path.dirname(__file__)); import faces, fc
from PIL import Image, ImageDraw
D='/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face/'
VIEWS=['S','SE','E','NE','N']
def grid(sc, exprs=faces.EXPR, views=VIEWS, label=True, base=lambda v: D+f'heads/E_{v}_base.txt', out=None):
    cells={}
    for v in views:
        for ex in exprs:
            g=faces.build_view(base(v),v,ex); cells[v,ex]=[''.join(r) for r in g]
    w=max(len(c[0]) for c in cells.values()); h=max(len(c) for c in cells.values())
    cw,ch=w*sc+4,h*sc+4; ox,oy=(28 if label else 2),(12 if label else 2)
    B=Image.new('RGB',(ox+cw*len(exprs),oy+ch*len(views)),(128,128,128)); d=ImageDraw.Draw(B)
    for j,ex in enumerate(exprs):
        if label: d.text((ox+j*cw+1,0),ex[:9],fill=(255,255,255))
    for i,v in enumerate(views):
        if label: d.text((2,oy+i*ch+ch//2-5),v,fill=(255,255,255))
        for j,ex in enumerate(exprs):
            c=cells[v,ex]; im=fc.pk.to_img(c,sc); B.paste(im,(ox+j*cw+2,oy+i*ch+2+(h-len(c))*sc),im)
    if out: B.save(out)
    return B, cells
if __name__=='__main__':
    B,cells=grid(1,label=False)
    for (v,ex),c in cells.items():
        p=D+f'out/sprite/{v}_{ex}'; fc.pk.write(p+'.txt',c); fc.pk.to_img(c,1).save(p+'_1x.png'); fc.pk.to_img(c,8,bg=True).save(p+'_8x.png')
    grid(4,out=D+'work/grid4.png'); print('ok',len(cells))
