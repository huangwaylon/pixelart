# turn_NE (3/4 back, facing up-right). Near side = her LEFT (viewer left) -> the katana is in the NEAR hand at the
# viewer's left. Back tails visible on the viewer-left/bottom, corset lacing on the back.
HEAD = ('NE', 52, 43)
ORDER = ['ribbonF', 'armR', 'legs', 'skirt', 'tail', 'torso', 'armL', 'katana', 'collar', 'HEAD', 'collar_over', 'ribbonN']
LAYERS = {
'legs': """
@leg 60,94 60,98 60,101 foot=ne fx=0 shade=r
@leg 68,93 68,97 68,100 foot=ne fx=0 shade=r
""",
'skirt': """
@skirt top=83 cx=64 tw=14 tips=51:95,58:96,70:96,77:94 slope=0.9 wedge=4
""",
'tail': """
@skirt top=85 cx=62 tw=10 tips=52:100,59:98,62:98,70:99 slit=60:91:1:2 shorts=0 slope=0.8 wedge=4
""",
'torso': """
74 53 KSsK
75 52 KSssKrRRRRRRRRRRrK
76 52 KSssKCRRRRRRRRRRrK
77 52 KSssKCRRRRRRRRRrrK
78 57 KCRRRRRRRRRrrK
78 57 KKLLLLLLLLLLKK
79 58 KllllllllllK
80 58 KldKdllllllK
81 58 KlKdKlllllKK
82 58 KldKdllllllK
""",
'armL': """
@cuff 54.5,76 52.5,90 5 10
""",
'armR': """
@limb 71,75,1.5 72,79,1.3
@cuff 72,77 74,89 4 8
""",
'katana': """
@katana 53 91 116.6 21 hook=-1
""",
'collar': """
71 55 KCRRRRRRRRRRRRrK
72 55 KCRRRRRRRRRRRrrK
73 56 KrRRRRRRRRRrrK
74 57 KvrrrrrrrrrvK
""",
'collar_over': """
66 54 K
67 54 KCK
68 54 KCRK
69 55 KCRRRRRRRRRRRK
70 55 KCRRRRRRRRRRrrK
""",
'ribbonF': """
@ribbon 70,73 74,75 77,78 78,82 78,86 80,89 side=1 over=0
""",
'ribbonN': """
@ribbon 57,73 53,75 50,78 48,82 48,86 46,89 side=-1 over=0
""",
}
