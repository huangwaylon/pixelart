import sys,numpy as np
from PIL import Image
im=Image.open(sys.argv[1]).convert('RGBA');a=np.array(im)
m=a[...,3]>0;ys,xs=np.where(m);a=a[ys.min():ys.max()+1,xs.min():xs.max()+1]
cols={};ch='abcdefghijklmnopqrstuvwxyzABCDEFGHIJLMNOPQRSTUVWXYZ0123456789'
print('crop off',xs.min(),ys.min(),'size',a.shape[1],a.shape[0])
print('    '+''.join(str(i//10) for i in range(a.shape[1])));print('    '+''.join(str(i%10) for i in range(a.shape[1])))
for y,row in enumerate(a):
  s=''
  for p in row:
    if p[3]==0: s+='.';continue
    k=tuple(p[:3]);l=sum(k)
    if l<120: s+='K';continue
    if k not in cols: cols[k]=ch[len(cols)%len(ch)]
    s+=cols[k]
  print('%3d '%y+s)
print(' '.join('%s=%02x%02x%02x'%(v,*k) for k,v in cols.items()))
