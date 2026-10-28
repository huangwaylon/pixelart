"""eyes4/setspec.py : eye-fix round FINAL lid/lash construction (variant T) -> eye_spec.json.
Same 5-wide eye body (cols 0-4 of the 6x6 block, col 5 empty) + ONE wing px outside (dx -1); eye line, iris, catchlight unchanged.
ROUND ARCHED upper lash: 2-px K peak (cols 2-3 = over the iris centre) on the lash row, shoulders 1 row... ->
  lash row:   col 1 h (outer shoulder, dark AA)  cols 2-3 K (peak)  col 4 g (inner shoulder, mid AA)
  lash row+1: col 0 K (outer end) + col 1 K (thick outer corner, covers the iris top-left)   col 4 g (soft inner end)
  wing: ONE K px up-and-out at (-1, lash row), diagonally attached to the outer end; no lower-lash / second flick.
Thick outer half (K end + K corner + wing) tapering to a mid-tone inner end. Surprised = the same lid 1 row higher with the iris filling
the gap (no hollow); blink_half = lid 1 row lower; joy = the lid line without iris (n arc); blink_closed = U arc; effort/pain unchanged.
(Prototypes eyes4/try_s.py: A 6-wide inward -> S face_ssim .536; C dome .505; Cs2 .561; T .576 vs .574 before.)"""
import json, sys
V = sys.argv[1] if len(sys.argv) > 1 else 'D'   # FINAL = D (eye-fix round); docs in eye_spec were then edited by hand (front_left _doc, rules[0], lid _doc)
P = '/Users/waylonhuang/Documents/other/pixelart/swordswoman/v2/m96/eye_spec.json'; d = json.load(open(P))
def L(*r): return list(r)
FL = {'neutral': L("......", ".hKKg.", "KK@hg.", ".g@Kg.", ".gLLg.", "_....."),
      'cheerful': L("......", ".hKKg.", "KK@hg.", ".g@Kg.", "..LL..", "_....."),
      'surprised': L(".hKKg.", "KKhhg.", ".h@hh.", ".g@Kg.", ".gLLg.", "_....."),
      'blink_half': L("......", "......", ".hKKg.", "KK@Kg.", ".gLLg.", "_....."),
      'joy': L("......", "......", ".hKKg.", "KK..g.", "......", "_....."),
      'blink_closed': L("......", "......", "......", "K.....", ".KKKg.", "_.....")}
if V == 'G':   # variant G: mid-tone g outer contour (notch between wing and shoulder + col 0 below the K end) - face_ssim fit for SE
    FL = {'neutral': L("......", "ghKKg.", "KK@hg.", "gg@Kg.", "ggLLg.", "_....."),
          'cheerful': L("......", "ghKKg.", "KK@hg.", "gg@Kg.", "g.LL..", "_....."),
          'surprised': L("ghKKg.", "KKhhg.", "gh@hh.", "gg@Kg.", "ggLLg.", "_....."),
          'blink_half': L("......", "......", "ghKKg.", "KK@Kg.", "ggLLg.", "_....."),
          'joy': L("......", "......", ".KKK..", "K...K.", "......", "_....."),   # clean n arc (crit: the lid-line joy read as a flat dash)
          'blink_closed': L("......", "......", "......", "K.....", ".KKKg.", "_.....")}
if V == 'Z':   # variant Z (crit r1): mid-tone inner shoulder g (S = single-px orphan in qc) + dark outer shoulder h around the 2-px K peak, K ends both sides, outer eye contour h
    # (col 0 under the K end), iris bottom corners rounded to skin (oval iris); single wing; joy n arc
    FL = {'neutral': L("......", ".hKKg.", "KK@hK.", "hg@Kg.", "hsLLs.", "_....."),
          'surprised': L(".hKKg.", "KhhhK.", "hg@hg.", "hg@Kg.", "hsLLs.", "_....."),   # taller iris under the raised lid (crit: no heavy 2px block)
          'blink_half': L("......", "......", ".hKKg.", "KK@KK.", "hsLLs.", "_....."),
          'joy': L("......", "......", ".KKK..", "K...K.", "......", "_....."),
          'blink_closed': L("......", "......", "......", "K.....", ".KKKg.", "_.....")}
    FL['cheerful'] = FL['neutral']
if V == 'D':   # variant D (crit r2: 'move the centre lash px up 1'): 3-tier DOME - h cap (cols 2-3) in the gap row over a 3-K run (cols 1-3),
    # outer end K + thick outer corner K, inner shoulder/end g; oval iris (bottom corners skin); clean skin outer side (no contour)
    FL = {'neutral': L("..hh..", ".KKKg.", "KK@hg.", ".g@Kg.", ".sLLs.", "_....."),
          'surprised': L("..KK..", ".KhhK.", "Kg@hg.", ".g@Kg.", ".sLLs.", "_....."),
          'blink_half': L("......", "..hh..", ".KKKg.", "KK@Kg.", ".sLLs.", "_....."),
          'joy': L("......", "......", ".KKK..", "K...K.", "......", "_....."),
          'blink_closed': L("......", "......", "......", "K.....", ".KKKg.", "_.....")}
    FL['cheerful'] = FL['neutral']
for e, s in (('determined', 'neutral'), ('embarrassed', 'neutral'), ('shout', 'cheerful')): FL[e] = FL[s]
def right(t):   # mirror the lid (col c -> 5 - c); iris rows keep the iris layout (catchlight col 2): only the lid px K (cols 0/1) and the g inner end (col 4) swap sides
    out = []
    for row in t:
        if row.startswith('_'): out.append('....._'); continue
        if not any(c in '@L' for c in row) and not (row[1:5] == 'Khhg'): out.append(row[::-1]); continue
        m = list('.' + row[1:5] + '.')
        if row[0] in 'Kgh': m[5] = row[0]
        if row[1] == 'K': m[4] = 'K'; m[1] = 'g' if row[4] == 'g' else row[4]
        if row[1:5] == 'Khhg': m[2], m[3] = 'h', 'h'
        out.append(''.join(m))
    return out
FR = {e: right(t) for e, t in FL.items()}
d['front_left'].update(FL)
d['front_right_override'] = {'_doc': 'hand-mirrored right eyes (eye-fix round): lid mirrored (outer end col 5, thick outer corner col 4, inner soft end g col 1); iris cols 1-4 keep the catchlight at col 2', **FR}
W = {e: [[-1, 1]] for e in ('neutral', 'cheerful', 'embarrassed', 'determined', 'shout')}
d['wing'] = {'_doc': 'eye-fix round: ONE up-and-out wing K px per eye [dx, dy] relative to the front_left eye origin, diagonally attached to the outer lash end (open (-1,1); surprised (-1,0); blink_half/joy/blink_closed (-1,2); effort/pain none). front_right: dx -> 5 - dx; far (SE far eye): lands on the cheek outline. No lower-lash hint, no second flick.',
             **W, 'surprised': [[-1, 0]] if V != 'D' else [[-1, 1]], 'blink_half': [[-1, 2]], 'joy': [[-1, 2]], 'blink_closed': [[-1, 2]], 'effort': [], 'pain': []}
d['kind_override'] = {'_doc': 'eye-fix round: E profile = front_left; SE far = derived from front_right cols 1,2,3,5' + (' with the g outer contour dropped (the far outer side is the cheek outline)' if V == 'G' else '')}
if V == 'G':
    FAR = {e: [''.join(r[i] for i in (1, 2, 3, 5)) for r in right([row[:5] + '.' if not row.startswith('_') else row for row in [r_ if not r_.startswith('g') else '.' + r_[1:] for r_ in t]])] for e, t in FL.items()}
    d['kind_override']['far'] = FAR
if V == 'D':
    O = [".hh.", "gKK.", "h@hK", "h@K.", "gLL.", "..._"]
    FAR = {e: O for e in ('neutral', 'cheerful', 'determined', 'embarrassed', 'shout')}
    FAR.update(surprised=[".KK.", "KhhK", "g@hK", "h@K.", "gLL.", "..._"], blink_half=["....", ".hh.", "gKK.", "h@KK", "gLL.", "..._"])
    d['kind_override']['_doc'] += '; SE far = explicit (h cap, inner contour h, outer end K at the cheek outline)'
    d['kind_override']['far'] = FAR
if V == 'Z':   # SE far eye (foreshortened, outer side = cheek outline): inner shoulder g + 2-px K peak, inner contour h, outer end K
    O = ["....", "gKK.", "h@hK", "h@K.", "gLL.", "..._"]
    FAR = {e: O for e in ('neutral', 'cheerful', 'determined', 'embarrassed', 'shout')}
    FAR.update(surprised=["gKK.", "hhhK", "h@h.", "h@K.", "gLL.", "..._"], blink_half=["....", "....", "gKK.", "h@KK", "gLL.", "..._"])
    d['kind_override']['_doc'] += '; SE far = explicit (inner contour h, no outer contour: the cheek outline)'
    d['kind_override']['far'] = FAR
d['wing_override'] = {'_doc': 'eye-fix round: none (every kind uses the single wing)'}
d['lid']['run'] = [2, 3]; d['lid']['flicks_min'] = {e: (1 if d['wing'].get(e) else 0) for e in d['front_left'] if not e.startswith('_')}
json.dump(d, open(P, 'w'), indent=1); print('spec', V)
