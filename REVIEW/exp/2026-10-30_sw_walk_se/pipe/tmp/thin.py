import sys, numpy as np, json
sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/docs/team_review/2026-10-30/line_art'); sys.path.insert(0,'.')
import lamet as LM, gates as GT, lock_chain as LC
from scipy import ndimage as nd
lab=np.load('out/walk_SE/labels.npz')
r=json.load(open('out/walk_SE/gates.json'))
for i in range(8):
    g=LM.load_txt(f'out/walk_SE/f{i:02d}.txt'); sub1=lab[f'sub1{i:02d}']
    for name, flags in ((k,v['flags']) for k,v in r['limbs'][i].items() if v['flags']):
        ids=[LC.SI[s] for s in GT.LIMBS[name]]; L=(g!='.')&(g!='K')&np.isin(sub1,ids)
        core=nd.binary_opening(np.pad(L,1),np.ones((2,2)))[1:-1,1:-1]; th=L&~nd.binary_dilation(core,LC.CROSS)
        ys,xs=np.nonzero(th if th.any() else L)
        y0,x0=ys.min()-2,xs.min()-3
        print(i,name,flags,'thin px',int(th.sum()), 'at', list(zip(ys.tolist(),xs.tolist()))[:6])
        sub=np.array([[ '.' if v<0 else 'abcdefghijk'[v] for v in row] for row in sub1])
        for yy in range(y0, min(ys.max()+3,128)): print('   ', ''.join(g[yy,x0:x0+10]), ' ', ''.join(sub[yy,x0:x0+10]), ' ', ''.join('#' if th[yy,x] else '.' for x in range(x0,x0+10)))
