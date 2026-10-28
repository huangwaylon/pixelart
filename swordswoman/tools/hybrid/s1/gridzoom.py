import sys
from PIL import Image, ImageDraw
R='/Users/waylonhuang/Documents/other/pixelart/swordswoman/hybrid/S1_redraw/r1'
out=sys.argv[1]; names=sys.argv[2:]; Z=6; C=(8,24,128,120)
w=(C[2]-C[0])*Z; h=(C[3]-C[1])*Z
s=Image.new('RGBA',(w*2,h*((len(names)+1)//2)),(36,32,44,255))
for i,n in enumerate(names):
  bg=Image.new('RGBA',(w,h),(120,120,126,255))
  im=Image.open(f'{R}/sprite/{n}.png').convert('RGBA').crop(C).resize((w,h),Image.NEAREST); bg.alpha_composite(im)
  d=ImageDraw.Draw(bg)
  for x in range(C[0],C[2],8): d.line([((x-C[0])*Z,0),((x-C[0])*Z,h)],fill=(0,255,255,90)); d.text(((x-C[0])*Z+1,1),str(x),fill='cyan')
  for y in range(C[1],C[3],8): d.line([(0,(y-C[1])*Z),(w,(y-C[1])*Z)],fill=(0,255,255,90)); d.text((1,(y-C[1])*Z+1),str(y),fill='cyan')
  d.text((w-150,h-14),n,fill='yellow')
  s.paste(bg,((i%2)*w,(i//2)*h))
s.save(out)
