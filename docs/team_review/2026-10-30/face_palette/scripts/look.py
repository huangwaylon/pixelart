import json,sys
from PIL import Image,ImageDraw
from common import *
tiles=[]
for act,v,i in [('idle','SE',0),('idle','SE',7),('walk','SE',2),('run','E',3),('jump','S',4),('idle','S',0),('idle','E',0)]:
    d,_=info(act,v)
    fr=d['frames'][i]; im=final(act,v,i)
    c=fr['face']['_head']['centre_px']; x0=int(c[0])-20;y0=int(c[1])-20
    cr=im.crop((x0,y0,x0+40,y0+40)).resize((240,240),Image.NEAREST)
    bg=Image.new('RGBA',cr.size,(90,140,90,255));bg.alpha_composite(cr);dr=ImageDraw.Draw(bg)
    for k,a in fr['face'].items():
        if k.startswith('_'):continue
        x,y=a['px'];X=(x-x0)*6;Y=(y-y0)*6
        dr.ellipse((X-3,Y-3,X+3,Y+3),outline=(0,255,255) if a['visible'] else (255,0,0))
    print(act,v,i,fr['face_tex'],fr['proj_view'],fr['face']['_head'])
    tiles.append(bg)
out=Image.new('RGBA',(250*len(tiles),240),(0,0,0,255))
for k,t in enumerate(tiles):out.paste(t,(k*250,0))
out.save('look_anchors.png')
