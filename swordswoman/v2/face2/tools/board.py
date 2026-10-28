# board.py out.png Z cols file[:x0,y0,x1,y1] ... : nearest-upscaled labelled contact sheet
import sys
from PIL import Image, ImageDraw
out,Z,cols=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]); T=[]
for a in sys.argv[4:]:
    f,_,b=a.partition(':'); im=Image.open(f).convert('RGBA')
    if b: im=im.crop(tuple(map(int,b.split(','))))
    bg=Image.new('RGBA',im.size,(190,190,190,255)); bg.alpha_composite(im)
    T.append((f.split('/')[-1][:-4][:22],bg.resize((im.width*Z,im.height*Z),Image.NEAREST)))
w=max(t.width for _,t in T)+4; h=max(t.height for _,t in T)+12; r=(len(T)+cols-1)//cols
S=Image.new('RGB',(cols*w,r*h),'white'); d=ImageDraw.Draw(S)
for i,(n,t) in enumerate(T):
    x,y=(i%cols)*w,(i//cols)*h; S.paste(t,(x,y+11)); d.text((x+1,y),n,fill='black')
S.save(out); print(S.size)
