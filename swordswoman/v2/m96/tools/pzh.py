"""pzh.py VIEW H SRC OUTSTEM: run pixelize pz.py EC0 at any figure height H into a 128 cell (soles row 124) -> OUTSTEM.{txt,png,json}"""
import sys, os, runpy, glob, shutil
T = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/pixelize/tools'; sys.path.insert(0, T)
import pzlib as Z
v, H, src, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
Z.CELL[H] = 128
tmp = out + '_pztmp'; os.makedirs(tmp, exist_ok=True)
sys.argv = ['pz.py', 'EC0', v, str(H), '--src', src, '--pal', Z.ROOT + 'v2/pixelize/palette.json', '--out', tmp]
try: runpy.run_path(T + '/pz.py', run_name='__main__')
except SystemExit: pass
for f in glob.glob(tmp + '/*'):
    ext = os.path.splitext(f)[1]; shutil.move(f, out + ext)
os.rmdir(tmp)
