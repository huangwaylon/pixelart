"""Hand-edit cells of a target grid file (see grid2px.py): gridedit.py GRID x,y,code [x,y,code ...]
Rewrites each touched row as 'y x0: codes' spanning its opaque extent."""
import sys
path=sys.argv[1]
rows={}; head=[]
for ln in open(path):
    ln=ln.rstrip('\n')
    if not ln.strip() or not ln[0].isdigit():
        head.append(ln); continue
    h,b=ln.split(':',1); y,x0=map(int,h.split())
    rows[y]={x0+i:c for i,c in enumerate(b.split())}
for op in sys.argv[2:]:
    x,y,c=op.split(','); x=int(x); y=int(y)
    rows.setdefault(y,{})[x]=c
out=list(head)
for y in sorted(rows):
    r={x:c for x,c in rows[y].items() if c!='.'}
    if not r: continue
    a,b=min(r),max(r)
    out.append(f"{y} {a}: "+' '.join(r.get(x,'.') for x in range(a,b+1)))
open(path,'w').write('\n'.join(out)+'\n')
