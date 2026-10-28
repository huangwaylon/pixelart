"""patch.py in.txt out.txt 'r,c,STR' ... : overwrite STR at row r col c"""
import sys
g=[list(l.rstrip('\n').ljust(64,'.')) for l in open(sys.argv[1])][:64]
for p in sys.argv[3:]:
    r,c,s=p.split(',',2); r,c=int(r),int(c)
    for i,ch in enumerate(s): g[r][c+i]=ch
open(sys.argv[2],'w').write('\n'.join(''.join(r) for r in g)+'\n')
