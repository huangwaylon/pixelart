import sys
# spec lines: "y: x0 content [x0 content ...]" ; '.' inside content = transparent
src,out=sys.argv[1],sys.argv[2]; OFF=int(sys.argv[3]) if len(sys.argv)>3 else 0
g=[['.']*48 for _ in range(48)]
for line in open(src):
    line=line.split('#')[0].strip()
    if not line: continue
    y,rest=line.split(':'); y=int(y); t=rest.split()
    for i in range(0,len(t),2):
        x0=int(t[i])+OFF
        for j,c in enumerate(t[i+1]):
            if c!='.': g[y][x0+j]=c
open(out,'w').write('\n'.join(''.join(r) for r in g)+'\n')
