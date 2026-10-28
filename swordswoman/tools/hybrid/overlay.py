import sys, numpy as np
from PIL import Image
D="hybrid/guide/measure/"
out=[]
for v in ("front","side","back"):
    a=np.array(Image.open(D+f"sil_proc_{v}.png"))[...,3]>128
    b=np.array(Image.open(D+f"sil_p3d_{v}.png"))[...,3]>128
    im=np.full(a.shape+(3,),255,np.uint8)
    im[a&~b]=(230,60,60); im[b&~a]=(60,90,230); im[a&b]=(120,120,120)
    out.append(im)
    print(v,"IoU",(a&b).sum()/(a|b).sum())
Image.fromarray(np.concatenate(out,1)).resize((1536,512)).save(D+"overlay_proc_vs_p3d.png")
