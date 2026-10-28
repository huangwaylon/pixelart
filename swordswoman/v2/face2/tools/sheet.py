"""sheet.py out.png Z heads...: grid heads x EXPR at Z, 1x row under each"""
import sys; sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face2/tools'); import kit,pal
from PIL import Image, ImageDraw
out,Z,C=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]); heads=sys.argv[4:]; E=kit.EXPR; NR=(len(E)+C-1)//C
cw,ch=19,22; W=C*(cw*Z+2)+4; RH=ch*Z+ch+24
S=Image.new('RGB',(W,len(heads)*NR*RH+12),(170,180,190)); d=ImageDraw.Draw(S)
for i,h in enumerate(heads):
    for j,e in enumerate(E):
        y=12+(i*NR+j//C)*RH; d.text(((j%C)*(cw*Z+2)+2,y),h+' '+e[:10],fill='black')
        rows=kit.build(h,e); im=pal.to_img(rows,Z); x=(j%C)*(cw*Z+2)+2; S.paste(im,(x,y+10),im)
        im1=pal.to_img(rows,1); S.paste(im1,(x,y+12+ch*Z),im1)
S.save(out); print(S.size)
