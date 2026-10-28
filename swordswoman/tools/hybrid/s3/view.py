import sys
from PIL import Image
fs=sys.argv[2:]; H=int(sys.argv[1]) if sys.argv[1].isdigit() else 600
ims=[Image.open(f).convert('RGB') for f in fs]
ims=[i.resize((max(1,int(i.width*H/i.height)),H)) for i in ims]
W=Image.new('RGB',(sum(i.width for i in ims)+10*len(ims),H),(120,120,130));x=0
for i in ims: W.paste(i,(x,0)); x+=i.width+10
W.save('/tmp/view.png'); print(W.size,[Image.open(f).size for f in fs])
