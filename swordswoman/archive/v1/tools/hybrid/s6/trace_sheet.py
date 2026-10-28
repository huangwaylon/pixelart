import sys, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, __file__.rsplit('/',1)[0])
from common import *
cols = np.array([[0,0,0],[66,40,42],[116,72,58],[216,52,62],[253,227,210],[240,180,156],[146,32,63],[200,90,90],[74,46,32],
 [216,52,62],[74,22,64],[30,20,40],[245,112,90],[146,32,63],[240,180,156],[196,128,137],[253,227,210],[196,128,137],[240,180,156],[196,128,137],[80,68,98],[26,18,32],[248,181,200],[244,154,176],[238,240,245],[255,255,0]],np.uint8)
out = sys.argv[1]
tiles=[]
for n in NAMES:
    ids,clay = trace(GUIDES[n])
    np.save(f"hybrid/S6_claude_pixel/r1/guide/{n}_ids.npy", ids)
    if clay is not None: np.save(f"hybrid/S6_claude_pixel/r1/guide/{n}_clay.npy", clay)
    a = np.zeros((128,128,4),np.uint8); a[...,:3]=cols[ids]; a[...,3]=(ids>0)*255
    crop = a[30:110, 24:104]
    z = zoom(crop, 4, grid=True)
    im = Image.fromarray(z); ImageDraw.Draw(im).text((2,2), n, fill=(255,255,255))
    tiles.append(im)
W=6; h=len(tiles)//W+1
sheet=Image.new('RGB',(320*W,320*h),(20,20,20))
for i,t in enumerate(tiles): sheet.paste(t,((i%W)*320,(i//W)*320))
sheet.save(out)
