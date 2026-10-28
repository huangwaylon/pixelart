import sys;sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face/tools');import fc
from PIL import Image
D='/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face/heads/'
ims=[]
for v in ['S','SE','E','NE','N']:
    X=D+f'E_{v}_base'; g=fc.load(X+'.txt')
    L={len(r) for r in g}; print(v,len(g),L)
    fc.fill(g); fc.save(g,X+'_prev',(1,8)); ims.append(Image.open(X+'_prev_8x.png'))
W=sum(i.width for i in ims)+8*4; im=Image.new('RGB',(W,max(i.height for i in ims)),(90,90,90)); x=0
for i in ims: im.paste(i,(x,0)); x+=i.width+8
im.save('/Users/waylonhuang/Documents/other/pixelart/swordswoman/.scratch_heads/all.png')
