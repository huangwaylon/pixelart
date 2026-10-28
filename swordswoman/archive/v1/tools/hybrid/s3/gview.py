import sys
from PIL import Image, ImageDraw
def grid(p, box, z=6):
    im=Image.open(p).convert('RGBA').crop(box)
    bg=Image.new('RGBA',im.size,(60,56,70,255)); bg.alpha_composite(im)
    big=bg.resize((im.width*z,im.height*z),Image.NEAREST); d=ImageDraw.Draw(big)
    for x in range(im.width):
        if (box[0]+x)%10==0: d.line([(x*z,0),(x*z,big.height)],fill=(0,0,0,110)); d.text((x*z+1,1),str(box[0]+x),fill=(255,255,0))
    for y in range(im.height):
        if (box[1]+y)%10==0: d.line([(0,y*z),(big.width,y*z)],fill=(0,0,0,110)); d.text((1,y*z+1),str(box[1]+y),fill=(255,255,0))
    return big
box=tuple(int(v) for v in sys.argv[1].split(','))
ims=[grid(p,box) for p in sys.argv[2:]]
W=Image.new('RGBA',(sum(i.width for i in ims)+4*len(ims),ims[0].height),(0,0,0,255)); x=0
for i in ims: W.paste(i,(x,0)); x+=i.width+4
W.save('/tmp/z.png'); print(W.size)
