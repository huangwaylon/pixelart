"""context.py OUT.png [scale] [frame]: every effect at its anchors cell_offset on the 96 px SE master (pixelize/top1/EC0_SE_96.png, 128 cell),
one 128x128 panel per effect (layer behind/over respected), 5 columns, bg #6e6e6e. Also writes OUT_thumb.png at 1x."""
import sys, json, os
sys.path.insert(0,__file__.rsplit('/',1)[0]); import fxlib as F; import build_order
from PIL import Image, ImageDraw
S=int(sys.argv[2]) if len(sys.argv)>2 else 2; FR=sys.argv[3] if len(sys.argv)>3 else 'peak'
fig=Image.open(F.D+'../pixelize/top1/EC0_SE_96.png').convert('RGBA')
panels=[]
for n in build_order.order:
    p=F.D+f'maps/{n}.txt'
    if not os.path.exists(p): continue
    a=json.load(open(F.D+f'maps/{n}.anchors.json')); fr=F.read(p)
    i=(min(1,len(fr)-1) if FR=='peak' else min(int(FR),len(fr)-1)); e=F.to_img(fr[i][0])
    co=a.get('cell_offset',[64,124])
    if isinstance(co,dict): co=list(co.values())[0]
    P=Image.new('RGBA',(128,128),F.BG+(255,)); pos=(co[0]-a['pivot'][0],co[1]-a['pivot'][1])
    if a.get('layer','over').startswith('behind'): P.alpha_composite(e,pos) if pos[0]>=0 and pos[1]>=0 else P.paste(e,pos,e); P.alpha_composite(fig)
    else: P.alpha_composite(fig); P.paste(e,pos,e)
    ImageDraw.Draw(P).text((2,2),n,fill=(230,230,230)); panels.append(P)
cols=5; rows=(len(panels)+cols-1)//cols
for s,out in [(S,sys.argv[1]),(1,sys.argv[1][:-4]+'_thumb.png')]:
    B=Image.new('RGB',(cols*(128*s+s),rows*(128*s+s)),(40,40,40))
    for i,P in enumerate(panels): B.paste(P.convert('RGB').resize((128*s,128*s),Image.NEAREST),((i%cols)*(128*s+s),(i//cols)*(128*s+s)))
    B.save(out); print(out,B.size)
