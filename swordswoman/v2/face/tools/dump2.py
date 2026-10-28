import sys
from PIL import Image
im=Image.open(sys.argv[1]).convert('RGBA'); x0,y0,x1,y1=map(int,sys.argv[2:6])
leg={}; chars='abcdefghijmnopqrtuvwxyzABCDEFGHIJLMNOPQRTUVXYZ0123456789'
for y in range(y0,y1):
    row=''
    for x in range(x0,x1):
        p=im.getpixel((x,y))
        if p[3]<128: row+='.'; continue
        k=p[:3]
        if k==(0,0,0) or sum(k)<60: row+='K'; continue
        if min(k)>235: row+='W'; continue
        if k not in leg: leg[k]=chars[len(leg)]
        row+=leg[k]
    print(f'{y:3d} {row}')
print(' '.join(f'{v}=#{k[0]:02x}{k[1]:02x}{k[2]:02x}' for k,v in sorted(leg.items(),key=lambda t:t[1])))
