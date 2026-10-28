# grid.py out.png scale cols file[:x0,y0,x1,y1] ...  -> labeled nearest-neighbour board on mid grey
import sys
from PIL import Image, ImageDraw
out, sc, cols = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
tiles=[]
for a in sys.argv[4:]:
    f, _, box = a.partition(':')
    im = Image.open(f).convert('RGBA')
    if box: im = im.crop(tuple(int(v) for v in box.split(',')))
    im = im.resize((im.width*sc, im.height*sc), Image.NEAREST)
    tiles.append((f.split('/')[-1][:22], im))
tw = max(t.width for _,t in tiles)+8; th = max(t.height for _,t in tiles)+18
rows=(len(tiles)+cols-1)//cols
B = Image.new('RGB',(tw*cols, th*rows),(128,128,128)); d=ImageDraw.Draw(B)
for k,(n,t) in enumerate(tiles):
    x,y=(k%cols)*tw+4,(k//cols)*th+14
    B.paste(t,(x,y),t); d.text((x,y-12),n,fill=(255,255,255))
B.save(out); print(out,B.size)
