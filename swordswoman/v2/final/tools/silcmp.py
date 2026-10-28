"""silcmp.py V MASTER.txt [r0 r1]: overlay silhouette master vs ds (illustration): '#'=both, '+'=illus only (missing), '-'=master only (extra)"""
import sys; sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/final/tools'); import fid
v,f=sys.argv[1:3]; r0,r1=(int(sys.argv[3]),int(sys.argv[4])) if len(sys.argv)>4 else (12,61)
m=fid.load(f); d=fid.load(fid.F+f'work/ds_{v}.txt')
print('   '+''.join(str(c//10) for c in range(14,50))); print('   '+''.join(str(c%10) for c in range(14,50)))
for r in range(r0,r1+1):
    s=''
    for c in range(14,50):
        a=m[r][c]!='.'; b=d[r][c]!='.'
        s+='#' if a and b else '+' if b else '-' if a else '.'
    print(f'{r:2d} '+s)
