"""compare.py out.png Z: our heads (neutral/cheerful) next to real trainer heads, 1x and Zx"""
import sys; sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face2/tools'); import kit,pal
from PIL import Image, ImageDraw
out,Z=sys.argv[1],int(sys.argv[2]); B='/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/'
REF=[('lyra',B+'style/refs/battle/lyra.png',(31,12,51,32)),('dawn',B+'style/refs/battle/dawn.png',(28,15,48,35)),('rosa',B+'style/refs/battle/rosa-bw.png',(23,13,43,33)),
     ('lillie',B+'face2/refs/sd/lillie.png',(30,13,50,33)),('kris',B+'face2/refs/sd/kris.png',(28,15,48,35)),('serena',B+'face2/refs/sd/serena.png',(26,13,46,33))]
OURS=[(h,e) for h in sys.argv[3:] for e in ('neutral','cheerful')]
ims=[(f'{h} {e}',pal.to_img(kit.build(h,e))) for h,e in OURS]+[(n,Image.open(f).convert('RGBA').crop(b)) for n,f,b in REF]
cols=6; cw=20*Z+4; rh=20*Z+20+14; r=(len(ims)+cols-1)//cols
S=Image.new('RGB',(cols*cw,r*rh),(176,186,196)); d=ImageDraw.Draw(S)
for i,(n,im) in enumerate(ims):
    x,y=(i%cols)*cw,(i//cols)*rh; d.text((x+2,y),n,fill='black')
    big=im.resize((im.width*Z,im.height*Z),Image.NEAREST); S.paste(big,(x+2,y+12),big); S.paste(im,(x+2,y+14+20*Z),im)
S.save(out); print(S.size)
