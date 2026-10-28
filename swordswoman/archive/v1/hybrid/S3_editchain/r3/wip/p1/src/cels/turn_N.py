# turn_N (back). Her LEFT hand (katana) is on the viewer's left. Split back tails, corset back lacing (present on N),
# collar seen from behind (tall funnel back + wing tips), ribbons trail outward behind the shoulders.
HEAD = ('N', 52, 43)
ORDER = ['ribbons', 'legs', 'skirt', 'tail', 'torso', 'armL', 'armR', 'katana', 'collar', 'HEAD', 'collar_over']
LAYERS = {
'legs': """
@leg 59,94 59,98 59,101 foot=n fx=0 shade=r
@leg 68,94 68,98 68,101 foot=n fx=0 shade=r
""",
'skirt': """
@skirt top=83 cx=63.5 tw=14 tips=51:95,57:96,70:96,76:95 slope=0.9 wedge=4
""",
'tail': """
@skirt top=85 cx=63.5 tw=10 tips=54:99,62:98,65:98,73:99 slit=63:91:1:2 shorts=0 slope=0.8 wedge=4
""",
'torso': """
74 53 KSsK
74 71 KssK
75 52 KSssKrRRRRRRRRRrKsssK
76 52 KSssKCRRRRRRRRRrKsssK
77 52 KSssKCRRRRRRRRRrKssmK
78 57 KCRRRRRRRRRrK
78 57 KKLLLLLLLLLKK
79 58 KlllllllllK
80 58 KllldKdllllK
81 58 KlllKdKlllK
82 58 KllldKdllllK
""",
'armL': """
@cuff 54.5,76 51.5,90 3 11
""",
'armR': """
@cuff 72.5,76 75.5,90 3 11
= 73 90
|KssK
|KsmK
|.KK.
""",
'katana': """
@katana 52 89 135 20 hook=-1
""",
'collar': """
71 55 KCRRRRRRRRRRRRrK
72 55 KCRRRRRRRRRRRrrK
73 56 KrRRRRRRRRRrrK
74 57 KvrrrrrrrrrvK
""",
'collar_over': """
66 54 K
67 54 KCK..............K
68 54 KCRK...........KrK
69 55 KCRRRRRRRRRRRRRrK
70 55 KCRRRRRRRRRRRRrrK
""",
'ribbons': """
@ribbonp 57,73 neutral -1
@ribbonp 70,73 neutral 1
""",
}
