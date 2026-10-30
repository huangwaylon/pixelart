import sys
f,y0,y1,x0,x1=sys.argv[1],*map(int,sys.argv[2:6])
L=[l.rstrip('\n') for l in open(f)]
print('    '+''.join(str((x//10)%10) for x in range(x0,x1+1)))
print('    '+''.join(str(x%10) for x in range(x0,x1+1)))
for y in range(y0,y1+1): print(f'{y:3d} '+L[y][x0:x1+1])
