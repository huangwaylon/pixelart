# Landmark lines (y = line position: top edge of the row it names; chin/sole = last row + 1),
# read by eye from char-map dumps (prop/tools/dump_ref.py) of the alpha-cropped sprite, +-1 px.
# Widths in px: head = hair-mass width; neck = visible skin neck; shoulder = outer edge incl. sleeve caps;
# waist = narrowest torso (body only, arms excluded where a gap exists, else the silhouette);
# hip = widest at hip/skirt/shorts (body only); thigh/calf = one leg incl. outline; foot = one shoe length as seen.
ROWS = ['crown', 'eye', 'chin', 'shoulder', 'armpit', 'waist', 'hip', 'crotch', 'hem', 'knee', 'ankle', 'sole']
WIDS = ['head', 'neck', 'shoulder', 'waist', 'hip', 'thigh', 'calf', 'foot']
# path, crop (x,y offset of alpha bbox), rows, widths
REFS = {
 'Hilda BW':   ('style/refs/battle/hilda-bw.png', dict(crown=7, eye=20, chin=26, shoulder=28, armpit=31, waist=38, hip=43, crotch=45, hem=46, knee=54, ankle=62, sole=74),
                dict(head=18, neck=5, shoulder=14, waist=11, hip=18, thigh=7, calf=6, foot=8)),
 'Rosa B2W2':  ('style/refs/battle/rosa-bw.png', dict(crown=3, eye=16, chin=23, shoulder=24, armpit=28, waist=33, hip=38, crotch=40, hem=40, knee=50, ankle=55, sole=67),
                dict(head=22, neck=4, shoulder=16, waist=11, hip=15, thigh=6, calf=5, foot=8)),
 'Lyra HGSS':  ('style/refs/battle/lyra.png', dict(crown=3, eye=14.5, chin=20, shoulder=23, armpit=27, waist=30, hip=34, crotch=37, hem=37, knee=46, ankle=57, sole=65),
                dict(head=18, neck=3, shoulder=14, waist=8, hip=13, thigh=5, calf=5, foot=6)),
 'Dawn DPPt':  ('style/refs/battle/dawn.png', dict(crown=3, eye=14, chin=21, shoulder=22, armpit=26, waist=28, hip=36, crotch=40, hem=40, knee=48, ankle=58, sole=65),
                dict(head=20, neck=4, shoulder=13, waist=9, hip=17, thigh=6, calf=6, foot=7)),
}
# ours: masters in 64-cell coords (not cropped); 'sil' = silhouette widths (sleeves merge with body, no gap)
OURS = {
 'S':  ('masters/S.png',  dict(crown=15, eye=22.5, chin=30, shoulder=31, armpit=34, waist=37, hip=42, crotch=44, hem=44, knee=50, ankle=57, sole=62),
        dict(head=17, neck=0, shoulder=17, waist=19, hip=25, thigh=5, calf=4, foot=6)),
 'SE': ('masters/SE.png', dict(crown=15, eye=22.5, chin=30, shoulder=31, armpit=34, waist=37.5, hip=41, crotch=43, hem=43, knee=50, ankle=57, sole=62),
        dict(head=18, neck=0, shoulder=14, waist=20, hip=25, thigh=5, calf=4, foot=6)),
 'E':  ('masters/E.png',  dict(crown=17, eye=23.5, chin=31, shoulder=32, armpit=35, waist=38, hip=42, crotch=44, hem=44, knee=50, ankle=57, sole=62),
        dict(head=18, neck=0, shoulder=10, waist=11, hip=14, thigh=6, calf=6, foot=9)),
 'NE': ('masters/NE.png', dict(crown=16, eye=None, chin=30, shoulder=30, armpit=34, waist=37.5, hip=42, crotch=43, hem=43, knee=50, ankle=57, sole=62),
        dict(head=19, neck=0, shoulder=17, waist=21, hip=25, thigh=5, calf=4, foot=6)),
 'N':  ('masters/N.png',  dict(crown=17, eye=None, chin=30, shoulder=31, armpit=34, waist=37.5, hip=43, crotch=44, hem=44, knee=51, ankle=57, sole=62),
        dict(head=18, neck=0, shoulder=16, waist=22, hip=27, thigh=5, calf=4, foot=6)),
 # Level E design sheet, measured on a 70-row downsample of the figure bbox (bun top = row 0)
 'designE front': ('design/turnE/front.png', dict(crown=7, eye=17, chin=25, shoulder=28, armpit=32, waist=35, hip=41, crotch=45, hem=45, knee=53, ankle=62, sole=70),
        dict(head=19, neck=3, shoulder=15, waist=21, hip=31, thigh=5, calf=4, foot=5)),
 'designE isoSE': ('design/turnE/iso_SE.png', dict(crown=7, eye=17, chin=26, shoulder=28, armpit=32, waist=35, hip=41, crotch=45, hem=45, knee=53, ankle=61, sole=70),
        dict(head=21, neck=3, shoulder=14, waist=21, hip=20, thigh=5, calf=4, foot=6)),
}
# design body-only (obi / skirt without the hanging sleeves): front waist 11 hip 15; isoSE waist 10 hip 19
def fr(rows, wids):
    c, s = rows['crown'], rows['sole']; H = s - c
    r = {k: (None if rows[k] is None else round((rows[k] - c) / H, 3)) for k in ROWS}
    w = {k: round(wids[k] / H, 3) for k in WIDS}
    return H, r, w
