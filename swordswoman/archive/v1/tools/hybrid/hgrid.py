"""Draw normalised-height grid (sole=0, top=1) over figures for landmark reading."""
import sys, numpy as np
from PIL import Image, ImageDraw
def load(p, box=None):
    im=Image.open(p).convert("RGBA")
    if box: im=im.crop(box)
    a=np.array(im); 
    m=(a[...,3]>128)&(a[...,:3].min(-1)<225)
    bg=Image.new("RGBA",im.size,"white"); bg.alpha_composite(im); return bg, m
items=[("turn_v6",*load("concept/chibi_turnaround_v6.png",(40,150,400,900))),
       ("iso_v5",*load("concept/chibi_iso_v5.png",(250,100,700,1000))),
       ("p3d",*load("hybrid/guide/measure/tex_p3d_front.png",(250,0,800,1024))),
       ("r9",*load("renders/model_round_9/ortho_front.png",(250,0,800,1024)))]
outs=[]
for name,im,m in items:
    if name=="iso_v5":   # exclude sword and shadow: use rows of darker pixels; manual top/bottom
        top,bot=128-100,950-100
    else:
        rows=np.where(m[:, :int(m.shape[1]*0.75)].any(1))[0]; top,bot=rows[0],rows[-1]
    s=700/im.height; im=im.resize((int(im.width*s),700)); top*=s; bot*=s
    d=ImageDraw.Draw(im)
    for k in range(21):
        r=bot-(bot-top)*k/20
        d.line([(0,r),(im.width,r)],fill=(0,160,0) if k%2==0 else (150,220,150))
        if k%2==0: d.text((1,r-11),f"{k/20:.1f}",fill=(0,120,0))
    d.text((5,5),name,fill="black"); outs.append(im)
W=sum(o.width for o in outs); S=Image.new("RGB",(W,700),"white"); x=0
for o in outs: S.paste(o,(x,0)); x+=o.width
S.save(sys.argv[1]); print(S.size)
