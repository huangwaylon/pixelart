import sys, numpy as np
sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/docs/team_review/2026-10-30/line_art'); sys.path.insert(0,'.')
import lamet as LM, gates as GT, lock_chain as LC, json
from scipy import ndimage as nd
lab=np.load('out/walk_SE/labels.npz'); info=json.load(open('work/walk_SE/walk_SE.json'))
fr=[int(x) for x in sys.argv[1:]]
cols=[]
for i in fr:
    g=LM.load_txt(f'out/walk_SE/f{i:02d}.txt'); ink=lab[f'ink{i:02d}']; gl=g.copy(); gl[ink]='s'
    cols.append((f'f{i:02d}', gl))
    F=LC.load('work/walk_SE/walk_SE', i, info['align']); sub1=lab[f'sub1{i:02d}']
    t=gl.copy()
    for name, subs in GT.LIMBS.items():
        ids=[LC.SI[s] for s in subs]; L=(g!='.')&(g!='K')&np.isin(sub1,ids)
        core=nd.binary_opening(np.pad(L,1),np.ones((2,2)))[1:-1,1:-1]; th=L&~nd.binary_dilation(core,LC.CROSS)
        t[th]='W'
    cols.append((f'f{i:02d} THIN=W', t))
LM.board(cols,'tmp/dbg.png',s=5)
