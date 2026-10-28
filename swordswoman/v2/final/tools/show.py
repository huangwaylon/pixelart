"""show.py FILE [r0 r1 c0 c1]: print char-map with row/col indices"""
import sys
rows=[l.rstrip('\n') for l in open(sys.argv[1]) if not l.startswith(';')]
r0,r1,c0,c1=(int(a) for a in sys.argv[2:6]) if len(sys.argv)>5 else (0,len(rows)-1,0,63)
print('   '+''.join(str(c//10) for c in range(c0,c1+1))); print('   '+''.join(str(c%10) for c in range(c0,c1+1)))
for r in range(r0,r1+1): print(f'{r:2d} '+rows[r][c0:c1+1])
