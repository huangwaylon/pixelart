#!/bin/zsh
# facecrop.sh DIR OUT.png : illus|sprite 8x face crops of DIR/{S,SE,E}.txt (+ .json meta copied from masters), stacked
R=/Users/waylonhuang/Documents/other/pixelart/swordswoman; P=$R/.venv/bin/python; D=$1
for v in S SE E; do cp $R/v2/m96/masters/EC0_${v}_96.json $D/$v.json; done
$P $R/v2/m96/tools/m96.py crop $D/S 52 44 78 64 8 $D/_S.png >/dev/null
$P $R/v2/m96/tools/m96.py crop $D/SE 54 44 82 64 8 $D/_SE.png >/dev/null
$P $R/v2/m96/tools/m96.py crop $D/E 60 42 82 64 8 $D/_E.png >/dev/null
$P -c "
from PIL import Image
ims=[Image.open('$D/_%s.png'%v) for v in ['S','SE','E']]
o=Image.new('RGB',(max(i.width for i in ims),sum(i.height+4 for i in ims)),'white');y=0
for i in ims: o.paste(i,(0,y));y+=i.height+4
o.save('$2')"
