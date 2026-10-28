# usage: refstats.py img [cellw cellh] -> colours (opaque), bbox height of first cell
import sys
from PIL import Image
import numpy as np
p=sys.argv[1]; im=Image.open(p)
if im.mode=='P' and 'transparency' not in im.info:
    # GBA style: index 0 = bg
    a=np.array(im); rgba=np.array(im.convert('RGBA')); rgba[a==0,3]=0
else: rgba=np.array(im.convert('RGBA'))
if len(sys.argv)>3:
    cw,ch=int(sys.argv[2]),int(sys.argv[3]); rgba=rgba[:ch,:cw]
op=rgba[...,3]>0
cols=np.unique(rgba[op][:,:3],axis=0)
ys,xs=np.where(op)
dark=[c for c in cols if c.sum()<150]
print(f"{p.split('/')[-1]:28s} cols={len(cols):3d} h={ys.max()-ys.min()+1:3d} w={xs.max()-xs.min()+1:3d} darkest={['#%02x%02x%02x'%tuple(c) for c in dark][:4]}")
