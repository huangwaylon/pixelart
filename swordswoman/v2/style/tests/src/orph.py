import sys
g=[l.rstrip('\n') for l in open(sys.argv[1])]
for y in range(64):
  for x in range(64):
    c=g[y][x]
    if c in '.K': continue
    nb=[g[y+dy][x+dx] for dy in(-1,0,1) for dx in(-1,0,1) if (dy or dx) and 0<=y+dy<64 and 0<=x+dx<64]
    if c not in nb: print(y,x,c)
