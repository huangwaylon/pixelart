"""paste.py BASE.txt BLOCK.txt OUT.txt : BLOCK first line '@ ROW COL', following lines pasted ('.'=transparent written, '_'=keep base)"""
import sys
base=[l.rstrip('\n').ljust(64,'.')[:64] for l in open(sys.argv[1]) if not l.startswith(';')][:64]
base=[list(r) for r in base]+[list('.'*64) for _ in range(64-len(base))]
L=[l.rstrip('\n') for l in open(sys.argv[2])]
r0,c0=map(int,L[0].split()[1:3])
for i,row in enumerate(L[1:]):
    for j,ch in enumerate(row):
        if ch!='_': base[r0+i][c0+j]=ch
open(sys.argv[3],'w').write('\n'.join(''.join(r) for r in base)+'\n')
