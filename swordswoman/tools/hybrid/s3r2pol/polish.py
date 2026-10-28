"""S3 r2 POLISH (Claude hand pixel pass): r2/std + r2/sprite bonus -> r2/polished. Every edit is logged with a reason
in r2/polwork/edits.json. Run from the project root: .venv/bin/python tools/hybrid/s3r2pol/polish.py"""
import sys, os, shutil, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pk, bows, bowlag, sleeve
import crouch_try, k1_try, apex_try, orph
from collections import Counter
R = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/hybrid/S3_editchain/r2'
DST = R + '/polished'
LOG = []
def note(n, what, why): LOG.append(dict(sprite=n, edit=what, reason=why))

def turn_NE(a, n):
    bows.ne(a); note(n, 'added far bow loop x49-54 y45-51 tucked behind the bun (behind-mode)', 'bow read as ONE small loop; S/N/SE/E show two loops (identity drift)')
def turn_NW(a, n):
    bows.nw(a); note(n, 'added far bow loop x74-79 y45-51 tucked behind the bun', 'same two-loop bow as N/NE')
def turn_SW(a, n):
    bows.sw(a); note(n, 'bow red_3 moved from loop right edges to upper-left', 'mirrored cel flipped the light; light is upper-left in every direction')
def turn_W(a, n):
    bows.w(a); note(n, 'bow red_3 moved from loop right edges to upper-left', 'mirrored cel flipped the light')
LAG = {0: -1, 1: -1, 2: 0, 3: 1}
def walk(a, n):
    k = int(n[-1]); dy = LAG[k]
    if dy:
        bowlag.shift_bow(a, (57, 38, 72, 53), dy); bowlag.fill_holes(a, (57, 40, 72, 53))
        note(n, 'bow shifted %+d px vs head' % dy, 'overlap: the bow trails the head bob by one key (up while falling, down on the rise)')
def slash_k1(a, n):
    k1_try.fix(a); note(n, 'blade-arc rows 91-93 x53-74 repainted as skirt + hem, arc keeps its 3-row lead band', 'arc buried hips and hem; silhouette unreadable at 1x')
def slash_k23(a, n):
    seed = (55, 91) if n.endswith('k2') else (55, 90)
    sleeve.separate(a, seed, (44, 82, 64, 99))
    note(n, 'near bell sleeve: red_1 cast shadow 1 px right of its seam + red_0 lining in the opening', 'sleeve and lit skirt were the same red_3: red-on-red at 1x')
def crouch(a, n):
    crouch_try.fix(a); note(n, 'repainted skirt bell y88-98 (wider squash, lit upper-left, petal hem) + knees/shins', 'skirt vanished behind the knees; squash must widen the volume')
def apex(a, n):
    apex_try.fix(a); note(n, '5 tapered take-off speed lines (pink_1 near body -> pink_0, broken tails)', 'motion lines were 2 short dashes; the take-off read static')

FIX = {'turn_NE': turn_NE, 'turn_NW': turn_NW, 'turn_SW': turn_SW, 'turn_W': turn_W,
       'walk_SE_k0': walk, 'walk_SE_k1': walk, 'walk_SE_k3': walk,
       'slash_SE_k1': slash_k1, 'slash_SE_k2': slash_k23, 'slash_SE_k3': slash_k23,
       'jump_E_crouch': crouch, 'jump_E_apex': apex}

def run():
    if os.path.exists(DST): shutil.rmtree(DST)
    os.makedirs(DST)
    for f in os.listdir(R + '/std'):
        if f.endswith('.png'): shutil.copy(R + '/std/' + f, DST + '/' + f)
    shutil.copytree(R + '/std/guide', DST + '/guide')
    for n, fn in FIX.items():
        p = '%s/%s.png' % (DST, n); a = pk.load(p); fn(a, n); pk.save(a, p)
        before = {(x, y) for x, y, _ in orph.orphans('%s/std/%s.png' % (R, n))}
        for x, y, d in orph.orphans(p):
            if (x, y) in before: continue
            nb = Counter(pk.ch(a, x + i, y + j) for i in (-1, 0, 1) for j in (-1, 0, 1) if (i or j) and pk.ch(a, x + i, y + j) != '.')
            c = nb.most_common(1)[0][0]; pk.put(a, x, y, c)
            note(n, 'orphan %s at (%d,%d) -> %s' % (d, x, y, c), 'cleanup R13: single pixel left by the edit above')
        pk.save(a, p)
    os.makedirs(DST + '/bonus', exist_ok=True)
    for f in ('run_SE_f1.png', 'dash_SE_f1.png'): shutil.copy(R + '/sprite/' + f, DST + '/bonus/' + f)
    os.makedirs(R + '/polwork', exist_ok=True)
    json.dump(LOG, open(R + '/polwork/edits.json', 'w'), indent=1)
    print(len(LOG), 'edits')
if __name__ == '__main__': run()
