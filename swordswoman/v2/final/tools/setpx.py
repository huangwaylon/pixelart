"""setpx.py FILE r,c,ch [r,c,ch ...] | setpx.py FILE row:col0:string  -> edit in place"""
import sys
p=sys.argv[1]; G=[list(l.rstrip('\n').ljust(64,'.')[:64]) for l in open(p) if not l.startswith(';')][:64]
for a in sys.argv[2:]:
    if a.count(':')==2:
        r,c,s=a.split(':'); r,c=int(r),int(c)
        for i,ch in enumerate(s): G[r][c+i]=ch
    else:
        r,c,ch=a.split(','); G[int(r)][int(c)]=ch
open(p,'w').write('\n'.join(''.join(r) for r in G)+'\n')
