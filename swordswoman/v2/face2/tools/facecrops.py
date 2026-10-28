# facecrops.py out.png files... : crop face (skin bbox in upper part) of each ref, 6x, labelled grid; prints face boxes
import sys, colorsys
from PIL import Image, ImageDraw
def skin(p):
    r,g,b,a=p
    if a<128: return False
    h,l,s=colorsys.rgb_to_hls(r/255,g/255,b/255)
    return (h<0.11 or h>0.97) and 0.6<l<0.93 and s>0.25
out=sys.argv[1]; files=sys.argv[2:]; Z=6; C=22
tiles=[]
for f in files:
    f,_,yo=f.partition(":")
    im=Image.open(f).convert('RGBA'); W,H=im.size
    # topmost dense skin cluster
    rows=[sum(skin(im.getpixel((x,y))) for x in range(W)) for y in range(H)]
    y0=int(yo) if yo else next(y for y in range(H) if rows[y]>=3)
    xs=[x for y in range(y0,min(H,y0+10)) for x in range(W) if skin(im.getpixel((x,y)))]
    cx=(min(xs)+max(xs))//2
    box=(cx-C//2,y0-5,cx+C//2,y0-5+C)
    cr=im.crop(box); bg=Image.new('RGBA',cr.size,(200,200,200,255)); bg.alpha_composite(cr)
    tiles.append((f.split('/')[-1][:-4],bg.resize((C*Z,C*Z),Image.NEAREST),box))
    print(f, 'crop',box,'skin_top',y0)
n=len(tiles); cols=min(6,n); rws=(n+cols-1)//cols
S=Image.new('RGB',(cols*(C*Z+4),rws*(C*Z+14)),'white'); d=ImageDraw.Draw(S)
for i,(nm,t,b) in enumerate(tiles):
    x=(i%cols)*(C*Z+4); y=(i//cols)*(C*Z+14); S.paste(t,(x,y+12)); d.text((x+2,y),nm,fill='black')
S.save(out)
