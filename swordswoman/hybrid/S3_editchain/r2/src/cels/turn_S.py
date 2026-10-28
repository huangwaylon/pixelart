# turn_S (front). Hand-typed cels + parametric petal skirt / bell cuffs / 3 px legs. Katana in her LEFT hand
# (viewer right). Head lock2 S at (52,43): chin row 72. Sole row 104.
HEAD = ('S', 52, 43)
ORDER = ['tail', 'ribbons', 'legs', 'skirt', 'torso', 'armL', 'armR', 'katana', 'collar', 'HEAD', 'collar_over', 'ribbon_root']
LAYERS = {
'tail': """
@skirt top=86 cx=63.5 tw=20 tips=47:101,80:101 slope=0.45 wedge=0
""",
'legs': """
@leg 59,94 59,98 59,101 foot=s fx=0 shade=r
@leg 68,94 68,98 68,101 foot=s fx=0 shade=r
""",
'skirt': """
@skirt top=83 cx=63.5 tw=14 tips=51:96,58:98,69:98,76:96 slit=63:89:2:2 shorts=94 slope=0.9 wedge=5
""",
'torso': """
75 53 KSss
75 71 ssmK
76 52 KSsssKrRRRRRRRRRRrKsssmK
77 52 KSsssKCRRRRRRRRRrrKsssmK
78 52 KSsssKCRRRRRRRRRrrKsssmK
78 57 KKLLLLLLLLLLKK
79 58 KllllllllllK
80 58 KlllllKTTKlK
81 58 KllllllddlKK
82 58 KlllllKTTKlK
83 58 KKKKKKKKKKKK
""",
'armL': """
@cuff 54.5,77 52.5,90 5 10
= 51 90
|KssK
|.KK.
""",
'armR': """
@cuff 72.5,77 74.5,90 5 10
""",
'katana': """
@katana 76 91 63.4 21
""",
'collar': """
72 55 KCRRRRRRRRRRRRrK
73 55 KCRRRRvvvvRRRRrK
74 56 KrRRRRRRRRRRrK
75 57 KvrrrrrrrrrvK
""",
'collar_over': """
67 53 K
68 53 KCK
69 53 KCRK
70 54 KCRK
71 54 KCRRK
67 74 K
68 72 KRK
69 71 KRrK
70 70 KRrK
71 69 KRRrK
""",
'ribbons': """
@ribbon 57,74 53,76 50,79 49,82 49,85 47,88 47,92 side=-1 over=0
@ribbon 70,74 74,76 77,79 78,82 78,85 80,88 80,91 side=1 over=0
""",
'ribbon_root': """
74 57 PK
75 56 pP
74 69 KP
75 70 Pp
""",
}
