import sys,numpy as np
from PIL import Image
im=Image.open(sys.argv[1]).convert('RGB');a=np.array(im).astype(int)
bg=a[2,2];print('bg',bg)
m=(np.abs(a-bg).sum(-1)>40)
ys,xs=np.where(m);print('bbox',xs.min(),ys.min(),xs.max(),ys.max())
H=int(sys.argv[2]);sc=(ys.max()-ys.min()+1)/H
im2=im.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1));W=round(im2.width/sc)
s=np.array(im2.resize((W,H),Image.BOX)).astype(int);mm=np.array(Image.fromarray(m[ys.min():ys.max()+1,xs.min():xs.max()+1].astype(np.uint8)*255).resize((W,H),Image.BOX))>100
print('    '+''.join(str(i%10) for i in range(W)))
for y in range(H):
  r=''
  for x in range(W):
    if not mm[y,x]: r+='.';continue
    R,G,B=s[y,x];L=R+G+B
    if L<150:r+='K'
    elif R>150 and G<90: r+='R'
    elif R>200 and G>150 and B>120 and R-B<90: r+='s'
    elif R>G+40 and B<120: r+='r' if L<400 else 'o'
    else: r+='x'
  print('%3d '%y+r)
