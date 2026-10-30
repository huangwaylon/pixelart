import sys; sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/docs/team_review/2026-10-30/line_art')
import lamet as L
for f in ['contact','passing']:
  g=L.load_txt(f'walk_SE_{f}.txt'); op=g!='.'
  z=L.run_defects(op)
  print(f,[(b[0],int(b[1][0]),int(b[1][1])) for b in z[4] if b[0]=='zig'], 'dbl', int(L.doubles(g).sum()))
