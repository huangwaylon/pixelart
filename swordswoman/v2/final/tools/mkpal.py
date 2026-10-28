import json, numpy as np
from PIL import Image, ImageDraw
P={ 'K':('#160c0d','outline (all materials), pupil, lash line'),
 'h':('#342126','hair shadow / inner hair lines / tie line; iris top; boot shadow'),
 'H':('#433833','hair base; boot base'),
 'g':('#5e4a45','hair light (tied-top + crown); iris mid; boot light'),
 'L':('#85706a','hair sheen band; iris lower light; boot toe glint'),
 's':('#eaa991','skin base'),
 'S':('#c98a7c','skin shadow (under bangs, neck, inner legs)'),
 'm':('#a5706b','mouth, nose dot, inner skin lines, brow'),
 'k':('#e58f84','blush (expressions only)'),
 'e':('#962723','red light (bow top, shoulder, sleeve top edge)'),
 'E':('#7d1918','red base (dress, sleeves, bow)'),
 'R':('#5f1220','red shadow (folds, under obi, sleeve inside, bow knot)'),
 'Q':('#c6c4c4','obi light edge / highlight'),
 'O':('#857a90','obi base (grey-lavender)'),
 'o':('#63576a','obi shadow'),
 'W':('#f6eeea','eye highlight, eye white'),
}
json.dump({'name':'final_turnE','note':'Locked palette extracted from v2/hair/turnE_final (k-means per material over all 9 views). Boots share the hair ramp (illustration boots are the same dark brown, within 8 levels). Iris uses h/g/L (grey-brown) + K pupil + W glint.','colors':{k:[v[0],v[1]] for k,v in P.items()}},open('palette.json','w'),indent=1)
im=Image.new('RGB',(16*40,70),'white'); d=ImageDraw.Draw(im)
for i,(k,(c,_)) in enumerate(P.items()):
    d.rectangle([i*40+2,2,i*40+37,47],fill=c,outline='black'); d.text((i*40+15,52),k,fill='black')
im.save('palette_swatch.png')
