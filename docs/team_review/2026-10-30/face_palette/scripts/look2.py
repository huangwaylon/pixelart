from common import *
from PIL import ImageDraw
tiles=[]
for act,v,i in [('idle','SE',0),('walk','SE',2),('run','E',3),('jump','S',4)]:
    im=final(act,v,i); m=skin_mask(act,v,i)
    d,_=info(act,v); c=d['frames'][i]['face']['_head']['centre_px']; x0=int(c[0])-20;y0=int(c[1])-20
    a=np.asarray(im).copy(); ov=a.copy(); ov[m>0.5]=(0,255,0,255)
    for arr in (a,ov):
        t=Image.fromarray(arr).crop((x0,y0,x0+40,y0+40)).resize((240,240),Image.NEAREST); tiles.append(t)
out=Image.new('RGBA',(250*len(tiles),240),(60,60,60,255))
for k,t in enumerate(tiles):out.alpha_composite(t,(k*250,0))
out.save('look_skin.png')
