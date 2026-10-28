"""faces.py: FACE GRAMMAR stamps + builder. Eye stamps are 5x5 for the NEAR/LEFT eye with the OUTER corner on the LEFT:
row0 = brow band (row above the lash), rows1-4 = the 3x4 eye box, col0 = outer margin (lash wing), col4 = inner margin.
'.' keeps the base pixel. Front mouth stamps are 5 wide (centre col 2) x 3-4 rows (row0 cheek row, row1 mouth row, row2+ chin).
Profile (E) stamps: PROF eyes are 4 wide (col0 = wing x13 .. col3 = front skin col), MOUTH_P is 4 wide whose col3 = the
jaw-outline column at the anchor ('_' cuts the silhouette = lip notch / open jaw)."""
import sys, copy, json, re
sys.path.insert(0,'/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/face/tools'); import fc
EXPR=['neutral','determined','shout','effort','joy','smile','surprised','pain','blink_half','blink_closed','squash']
EYE={
 'neutral': [".....", "KKKK.", "KWiK.", ".iiI.", "..II."],
 'determined': ["K....", ".KKK.", "..KK.", ".WiI.", "..I.."],
 'shout': ["KK...", "..KK.", "K.KKK", ".WiI.", "....."],
 'effort': [".....", "KKK..", ".KKKK", ".WiI.", "....."],
 'joy': [".....", ".....", ".KK..", "K..K.", "....."],
 'smile': [".....", "KKKK.", "KWiK.", ".iiI.", "....."],
 'surprised': [".KKK.", "KKKK.", ".WKW.", "..i..", "....."],
 'pain': ["K....", ".KK..", "...K.", ".KK..", "K...."],
 'blink_half': [".....", ".....", "KKKK.", ".iII.", "....."],
 'blink_closed': [".....", ".....", ".....", "KKKK.", "....."],
 'squash': [".....", ".....", "KK...", ".KKKK", "....."],
}
MOUTH={
 'neutral': ["....r",".rrr.","....."],
 'determined': [".....",".rrr.","....."],
 'shout': [".....","rKKKr",".KeK."],
 'effort': [".rrr.","rWWWr",".rrr."],
 'joy':         [".....","rKKKr",".rer."],
 'smile': [".....","r...r",".rrr."],
 'surprised': [".rr..","rKKr.",".rr.."],
 'pain':        [".....",".r.r.","r.r.r"],
 'blink_half': [".....",".rrrr","....."],
 'blink_closed': [".....",".rrrr","....."],
 'squash':      [".....",".rrr.","r...r"],
}
MOUTH['blink_half']=MOUTH['blink_closed']=MOUTH['neutral']
MOUTH_SE={    # SE overrides (4 wide = front cols 1-4); default = front stamp minus its left column
 'neutral':     ["...r","rrr.","...."],
 'smile':       ["....","r..r",".rr."],
 'pain':        ["....","r.r.",".r.r"],
 'squash':      ["....",".rr.","r..r"],
}
MOUTH_SE['blink_half']=MOUTH_SE['blink_closed']=MOUTH_SE['neutral']
# ---- COMPACT set for the Level E FINAL head (~15w x 14h crown-chin at 48px: eyes 3 rows, face ~8px, mouth <=3px) ----
# Eye: 5x4 (band + 3 eye rows) = drop the bottom row (joy: drop row 1 so the arc stays centred). Used when eye_near h==3.
def eye3(ex, st): return [st[0]]+st[2:5] if ex=='joy' else st[:4]
EYE3={k:eye3(k,v) for k,v in EYE.items()}
EYE3['pain']=["K....",".KK..","..K..",".KK.."]          # 3-row chevron
EYE3['surprised']=[".KKK.","KWKW.","..i..","....."]      # lash up in the band, pupil, skin below
# S view with a narrow face (eye_near w==2): both eyes 2 wide = far() derivation (drop the middle column) on each side.
# Mouth: 3 wide x 2 rows (mouth row + 1 below; never touches the chin outline). centre col 1.
MOUTH3={
 'neutral':["..r","rr."], 'determined':["rrr","..."], 'shout':["KKK","KeK"], 'effort':["rWr","rrr"],
 'joy':["KKK",".e."], 'smile':["r.r",".r."], 'surprised':["rK.","rr."], 'pain':["r.r",".r."], 'squash':["rrr","r.r"],
}
MOUTH3['blink_half']=MOUTH3['blink_closed']=MOUTH3['neutral']
BLUSH={'joy','effort','shout','smile'}
# profile (E) eyes: 4 wide x 5 rows, col0 = back wing column, cols1-2 = eye box, col3 = front skin column
PROF=None  # filled below from EYE via prof()
# profile mouths: 4 wide x 3 rows (cheek, mouth, chin row); col2 = the notched lip outline (x16 on row 19), col3 = the
# upper/lower lip column (x17); '_' cuts the silhouette (open mouths)
MOUTH_P={
 'neutral':     ["..r.",".r..","...."],
 'determined':  ["....","rr..","...."],
 'shout':       ["....","KK__","eeK_"],
 'effort':      ["....","rKW.","...."],
 'joy':         ["r...",".K_.",".e.."],
 'smile':       ["r...",".rr.","...."],
 'surprised':   ["....",".K_.","...."],
 'pain':        ["....","r...",".r.."],
 'squash':      ["....","rrr.","...."],
}
MOUTH_P['blink_half']=MOUTH_P['blink_closed']=MOUTH_P['neutral']
def anchors(path):
    A={}
    for l in open(path):
        m=re.match(r';\s*(\w+)\s+(.*)',l)
        if m and re.fullmatch(r'[-\d ]+',m.group(2).strip()): A[m.group(1)]=[int(v) for v in m.group(2).split()]
    return A
FAR={}  # SE far-eye overrides, already mirrored: 4 wide, col0 = inner margin, cols1-2 = box, col3 = outer wing
def far(st, ex=None):  # mirrored + foreshortened: drop the middle eye column
    if ex in FAR: return FAR[ex]
    return [r[::-1][:2]+r[::-1][3:] for r in st]
def prof(st): return [r[:3]+r[4:] for r in st]  # profile: drop the inner eye column (col0 wing, col3 front skin)
PROF={k:prof(v) for k,v in EYE.items()}
def build(base, view, ex, A, eye=None, mouth=None):
    g=fc.load(base); eye=eye or EYE; mouth=mouth or MOUTH
    compact=A.get('eye_near',[0,0,0,4])[3]==3
    if compact and eye is EYE: eye=EYE3
    if 'eye_near' in A:
        x,y,w,h=A['eye_near']; st=eye[ex] if w==3 else (PROF[ex] if view=='E' else [r[:2]+r[3:] for r in eye[ex]])
        if compact and view=='E': st=prof(eye[ex])
        fc.put(g, st, x-1, y-1)
    if 'eye_far' in A:
        x,y,w,h=A['eye_far']; st=[r[::-1] for r in eye[ex]] if w==3 else far(eye[ex],None if compact else ex)
        fc.put(g, st, x-1, y-1)
    fc.fill(g)
    if 'mouth' in A and ex in mouth:
        x,y=A['mouth'][:2]
        if compact and view!='E': fc.put(g, MOUTH3[ex], x-1, y)
        elif view=='E': fc.put(g, MOUTH_P[ex], x-3, y-1)
        elif view=='SE': fc.put(g, MOUTH_SE.get(ex,[r[1:] for r in mouth[ex]]), x-1, y-1)
        else: fc.put(g, mouth[ex], x-2, y-1)
    if ex in BLUSH:
        for k in ('blush','blush_far'):
            if k in A:
                x,y,w=A[k]
                for i in range(w):
                    if g[y][x+i] in 'sS': g[y][x+i]='e'
    return g

def build_view(base, view, ex):
    A=anchors(base)
    if view in ('NE','N'):
        g=fc.load(base); fc.fill(g)
        if 'cheek' in A and ex in BLUSH|{'pain'}:
            x,y=A['cheek'][:2]
            if g[y+1][x-1] in 'sS': g[y+1][x-1]='e'
    else:
        g=build(base, view, ex, A)
    if ex=='squash':  # head squash: drop one skull row (keeps width), pad 1 transparent row on top
        r=A.get('squash_row',[10])[0]; g=[['.']*len(g[0])]+g[:r]+g[r+1:]
    return g
