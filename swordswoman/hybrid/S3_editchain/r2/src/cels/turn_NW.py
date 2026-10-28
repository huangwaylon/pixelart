# turn_NW (3/4 back, facing up-left). Hand-authored (NOT a mirror of NE): near side = her RIGHT (viewer right);
# the katana (her LEFT hand) is the FAR hand at the viewer's left, blade angled down-left behind the skirt edge.
# Back tails peek on the viewer right, corset back lacing.
HEAD = ('NW', 52, 43)
ORDER = ['ribbonF', 'armF', 'katana', 'legs', 'skirt', 'tail', 'torso', 'armN', 'collar', 'HEAD', 'collar_over',
         'ribbonN']
LAYERS = {
'legs': """
@leg 59,93 59,97 59,100 foot=n fx=0 shade=r
@leg 67,94 67,98 67,101 foot=n fx=0 shade=r
""",
'skirt': """
@skirt top=83 cx=63 tw=14 tips=50:94,57:96,69:96,76:95 slope=0.9 wedge=4
""",
'tail': """
@skirt top=85 cx=65 tw=10 tips=57:99,65:98,68:98,75:100 slit=67:91:1:2 shorts=0 slope=0.8 wedge=4
""",
'torso': """
74 71 KsSK
75 57 KrRRRRRRRRRRrKssK
76 57 KCRRRRRRRRRRrKssK
77 57 KCRRRRRRRRRrrKsmK
78 57 KCRRRRRRRRRrrK
78 57 KKLLLLLLLLLLKK
79 58 KllllllllllK
80 58 KlllllldKdlK
81 58 KlllllldKdKK
82 58 KllllllldKdK
""",
'armF': """
@limb 57,75,1.5 56,79,1.3
@cuff 56,77 54,89 4 8
""",
'armN': """
@cuff 72.5,76 74.5,90 5 10
= 73 90
|KssK
|.KK.
""",
'katana': """
@katana 54 90 116.6 18 hook=-1
""",
'collar': """
71 56 KCRRRRRRRRRRRRrK
72 56 KCRRRRRRRRRRRrrK
73 57 KrRRRRRRRRRrrK
74 58 KvrrrrrrrrrvK
""",
'collar_over': """
66 73 K
67 72 KrK
68 71 KRrK
69 57 KCRRRRRRRRRRRrK
70 56 KCRRRRRRRRRRRrrK
""",
'ribbonF': """
@ribbon 57,73 53,75 50,78 48,82 48,86 46,89 side=-1 over=0
""",
'ribbonN': """
@ribbon 70,73 74,75 77,78 79,82 79,86 81,89 side=1 over=0
""",
}
SHIFT = (1, 0)
