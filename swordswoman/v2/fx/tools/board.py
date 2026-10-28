"""board.py out.png s file1.txt ... : all frames of each map side by side, rows per file, bg #6e6e6e"""
import sys; sys.path.insert(0,__file__.rsplit('/',1)[0]); import fxlib as F
from PIL import Image, ImageDraw
out=sys.argv[1]; s=int(sys.argv[2]); rows=[]
for p in sys.argv[3:]:
    fr=F.read(p); rows.append([F.to_img(g,s,F.BG) for g,_ in fr])
W=max(sum(i.width+s*2 for i in r) for r in rows); H=sum(r[0].height+s*2 for r in rows)
B=Image.new('RGB',(W,H),(60,60,60)); y=0
for r in rows:
    x=0
    for im in r: B.paste(im,(x,y)); x+=im.width+s*2
    y+=r[0].height+s*2
B.save(out); print(B.size)
