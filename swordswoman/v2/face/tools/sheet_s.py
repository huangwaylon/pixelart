import sys; sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face/tools'); import faces, fc
from PIL import Image, ImageDraw
base=sys.argv[1]; out=sys.argv[2]; A=faces.anchors(base); sc=int(sys.argv[3]) if len(sys.argv)>3 else 6
box=[int(v) for v in sys.argv[4].split(',')] if len(sys.argv)>4 else None
tiles=[]
for ex in faces.EXPR:
    g=faces.build(base,'S',ex,A); s=[''.join(r) for r in g]
    if box: s=[r[box[0]:box[2]] for r in s[box[1]:box[3]]]
    tiles.append((ex,fc.pk.to_img(s,sc,bg=True),fc.pk.to_img(s,1,bg=True)))
tw=tiles[0][1].width+6; th=tiles[0][1].height+tiles[0][2].height+22
cols=6; B=Image.new('RGB',(tw*cols,th*((len(tiles)+cols-1)//cols)),(128,128,128)); d=ImageDraw.Draw(B)
for k,(n,a,b) in enumerate(tiles):
    x,y=(k%cols)*tw,(k//cols)*th; d.text((x+2,y+1),n,fill=(255,255,255)); B.paste(a,(x,y+12)); B.paste(b,(x+2,y+14+a.height))
B.save(out); print(out,B.size)
