import sys
from PIL import Image, ImageDraw
R='/Users/waylonhuang/Documents/other/pixelart/swordswoman/archive/v1/hybrid/S1_redraw/r1'
out=sys.argv[1]; names=sys.argv[2:]; Z=5; C=(14,30,114,118)
w=(C[2]-C[0])*Z; h=(C[3]-C[1])*Z
s=Image.new('RGBA',(w*len(names),h),(36,32,44,255)); d=ImageDraw.Draw(s)
for i,n in enumerate(names):
  bg=Image.new('RGBA',(w,h),(118,118,124,255) if i%2 else (96,104,80,255))
  im=Image.open(f'{R}/sprite/{n}.png').convert('RGBA').crop(C).resize((w,h),Image.NEAREST); bg.alpha_composite(im); s.paste(bg,(i*w,0))
  for y in range(0,h,Z*8): d.line([(i*w,y),(i*w+4,y)],fill='white')
  d.text((i*w+3,3),n,fill='white')
s.save(out)
