"""kit.py: FACE2 face kit. Heads = char maps (placeholder neutral bob) with anchors; eyes/mouths/blush stamped per expression.
Eye stamp: 6 cols x 6 rows for the LEFT/near eye, OUTER corner at col0 (lash wing), cols1-4 = eye, col5 = inner margin;
row0 = brow row (skin row under the bangs), rows1-5 = 5-row eye box. '.' keeps base. Right eye = mirror.
Mouth stamp: 4 cols x 3 rows, row0 = cheek row (row under the eyes), row1 = mouth row, row2 = jaw row."""
import sys; sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face2/tools'); import pal
EXPR=['neutral','cheerful','determined','shout','effort','joy','surprised','pain','blink_half','blink_closed','embarrassed']
EYE={   # r3: 5 cols (c0 lash wing, c1-3 = 3-wide eye, c1 outer, c4 inner margin) x 6 rows (r0 brow row, r1-5 eye)
 'neutral':     [".....","KKKK.",".KWi.",".iWi.",".IIW.",".In.."],
 'cheerful':    [".....","KKKK.",".KWi.",".iWi.",".In..","....."],
 'determined':  [".....","KK...",".KKKK",".iWi.",".IIW.",".In.."],
 'shout':       ["hh...","..KK.","KKKK.",".KWi.",".In..","....."],
 'effort':      ["hh...",".....",".....","KK...","..KK.","....."],
 'joy':         [".....",".....",".KKK.","K...K",".....","....."],
 'surprised':   [".....","KKKK.",".WWW.",".WKi.",".iKi.","....."],
 'pain':        [".....","K....",".KK..","...K.",".KK..","K...."],
 'blink_half':  [".....",".....","KKKK.",".iii.",".In..","....."],
 'blink_closed':[".....",".....",".....",".....","K....",".KKK."],
 'embarrassed': ["...h.",".....","KKKK.",".KWi.",".iIW.","....."],
}
def far(st): return [r[:2]+r[3:] for r in st]          # 2-wide far eye (SE): drop stamp col 2
MOUTH={  # 4 cols x 3 rows: row0 cheek row, row1 mouth row, row2 jaw row (centre = cols 1-2)
 'neutral':     ["....",".rr.","...."],
 'cheerful':    ["....","rKKr",".ee."],
 'determined':  ["....","rrrr","...."],
 'shout':       ["rrrr","rKKr",".ee."],
 'effort':      ["....","rrrr","r..r"],
 'joy':         ["r..r","rKKr",".ee."],
 'surprised':   ["....",".KK.",".rr."],
 'pain':        ["....","rKKr","...."],
 'blink_half':  ["....",".rr.","...."],
 'blink_closed':["....",".rr.","...."],
 'embarrassed': ["....",".r.r","..r."],
}
BLUSH={'cheerful':2,'joy':2,'shout':1,'effort':1,'pain':1,'embarrassed':3}
HEADS={}
def stamp(g,st,x0,y0,mirror=False):
    for dy,r in enumerate(st):
        for dx,c in enumerate(r):
            if c=='.': continue
            if c=='_': c='.'
            x=x0-dx if mirror else x0+dx; y=y0+dy
            if 0<=y<len(g) and 0<=x<len(g[y]): g[y][x]=c
def build(head,expr,eye_tbl=None,mouth_tbl=None):
    H=HEADS[head]; g=[list(r) for r in H['rows']]
    for i,(x,y,m) in enumerate(H['eyes']):
        st=(H.get('eyetbl') or eye_tbl or EYE)[expr]
        if H.get('eyefn'): st=H['eyefn'](st)
        if H.get('far')==i: st=H.get('farfn',far)(st)
        stamp(g,st,x,y,m)
    mt=H.get('mouths',mouth_tbl or MOUTH)
    if H.get('mouth'): mx,my=H['mouth']; stamp(g,mt[expr],mx,my)
    if H.get('cue')=='NE':
        n=NE_LASH.get(expr,0)
        for k,(x,y) in enumerate(H.get('lash',[])):
            if k<n: g[y][x]='K'
    n=BLUSH.get(expr,0)
    for j,(bx,by) in enumerate(H.get('blush',[])):
        w=min(n,H.get('blushw',[3,3])[j])
        for k in range(w):
            x=bx+k if j==0 else bx+1-k
            if g[by][x] in 'sS': g[by][x]=H.get('blushc',{}).get(n,'kkk')[k] if n in H.get('blushc',{}) else 'k'
    return [''.join(r) for r in g]


import heads_e as HE
def prof_e(st):  # profile eye 4 wide: col0 = back corner + lash flick, cols1-3 iris toward the FRONT (right)
    return PROF_E.get(st_name(st), [r[:1]+r[2:5] for r in st])
PROF_E={
 'neutral':     ["K...",".KKK",".KWi","..ii","..In","...."],
 'cheerful':    ["K...",".KKK","..Wi","..In","....","...."],
 'determined':  ["..hh",".KKK","..KK","..Wi","..In","...."],
 'shout':       ["hh..","..hK","KKKK","..Wi","..n.","...."],
 'effort':      ["hh..","....","....","KK..","..KK","...."],
 'joy':         ["....","....","..KK",".K..","K...","...."],
 'surprised':   ["....",".KKK",".WWW","..WK","..iK","...."],
 'pain':        ["....","....","..K.","...K","..K.","...."],
 'blink_half':  ["....","....","KKKK","..ii","..In","...."],
 'blink_closed':["....","....","....","....","K...",".KKK"],
 'embarrassed': ["...h","....","KKKK",".KWi","..IW","...."],
}
MOUTH_E2={
 'neutral':     ["...",".r.","..."],
 'cheerful':    ["r..",".r.","..."],
 'determined':  ["...","rr.","..."],
 'shout':       ["...","rK_","reK"],
 'effort':      ["...","rr.","..."],
 'joy':         ["r..",".K_","..K"],
 'surprised':   ["...",".K_","..."],
 'pain':        ["...","rK_","..."],
 'blink_half':  ["...",".r.","..."],
 'blink_closed':["...",".r.","..."],
 'embarrassed': ["...","r.r","..."],
}
HEADS['S']=dict(rows=HE.S, eyes=[(3,9,False),(12,9,True)], mouth=(6,15), blush=[(3,15),(11,15)], blushc={3:'kek'})
MOUTH_SE=dict(MOUTH, neutral=['....','..r.','....'], blink_half=['....','..r.','....'], blink_closed=['....','..r.','....'])
HEADS['SE']=dict(rows=HE.SE, eyes=[(6,9,False),(13,9,True)], far=1, mouth=(9,15), mouths=MOUTH_SE, blush=[(7,15),(12,15)], blushw=[3,1])
HEADS['E']=dict(rows=HE.E, eyes=[(8,9,False)], eyetbl=PROF_E, mouth=(10,15), mouths=MOUTH_E2, blush=[(9,15)], blushw=[2])
NE_LASH={'neutral':1,'cheerful':1,'determined':1,'shout':1,'surprised':2,'embarrassed':1,'blink_half':1}
HEADS['NE']=dict(rows=HE.NE, eyes=[], mouth=None, blush=[(14,13)], blushw=[1], cue='NE', lash=[(16,11),(16,10)])
HEADS['N']=dict(rows=HE.N, eyes=[], mouth=None, blush=[], cue='N')
