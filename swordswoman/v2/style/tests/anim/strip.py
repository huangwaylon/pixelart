# review sheet: frames in a grid with ground-row (y45) and master-centre (x32) guides; usage: strip.py SCALE OUT [COLS] [--clean]
import sys,os
sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/style/tools')
from pk import read,to_img
from PIL import Image, ImageDraw
D=os.path.dirname(os.path.abspath(__file__)); a=[x for x in sys.argv[1:] if not x.startswith('--')]
s=int(a[0]) if a else 3; out_p=a[1] if len(a)>1 else 'strip.png'; cols=int(a[2]) if len(a)>2 else 6; clean='--clean' in sys.argv
fs=sorted(f for f in os.listdir(D) if f.startswith('A_slash_f') and f.endswith('.txt'))
ims=[to_img(read(os.path.join(D,f)),s,True) for f in fs]
w,h=ims[0].size; rows=(len(ims)+cols-1)//cols
out=Image.new('RGBA',(w*cols+2*(cols-1),h*rows+2*(rows-1)),(255,255,255,255))
d=ImageDraw.Draw(out)
for i,m in enumerate(ims):
    X,Y=(i%cols)*(w+2),(i//cols)*(h+2); out.alpha_composite(m,(X,Y))
    if not clean:
        d.line([(X,Y+46*s-1),(X+w-1,Y+46*s-1)],fill=(0,200,255,255)); d.line([(X+32*s,Y),(X+32*s,Y+h)],fill=(0,200,255,255))
out.convert('RGB').save(os.path.join(D,out_p) if not os.path.isabs(out_p) else out_p); print(out.size)
