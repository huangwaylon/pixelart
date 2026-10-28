import sys
g=[l.rstrip('\n') for l in open(sys.argv[1])]; y0,y1,x0,x1=map(int,sys.argv[2:6])
print('    '+''.join(str((x//10)%10) for x in range(x0,x1+1))); print('    '+''.join(str(x%10) for x in range(x0,x1+1)))
for y in range(y0,y1+1): print(f'{y:3d} '+g[y][x0:x1+1])
