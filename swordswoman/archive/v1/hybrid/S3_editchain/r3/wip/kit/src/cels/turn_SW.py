# turn_SW (3/4 front, facing viewer-left-down). Hand-authored (NOT a mirror of SE): near side = her LEFT (viewer
# right) -> the katana hand is the NEAR hand, in front; the far arm (her right) is partly behind the body.
# Slit left of centre (front-left), back tail peeks on the viewer right. Lit from the top-left like every view.
HEAD = ('SW', 50, 43)
ORDER = ['tail', 'ribbonF', 'armF', 'legs', 'skirt', 'torso', 'armN', 'katana', 'collar', 'HEAD', 'collar_over',
         'ribbonN']
LAYERS = {
'tail': """
@skirt top=86 cx=64 tw=20 tips=48:99,81:101 slope=0.45 wedge=0
""",
'legs': """
@leg 59,93 59,97 59,100 foot=w fx=-1 shade=r
@leg 67,93 67,97 67,101 foot=w fx=-1 shade=r
""",
'skirt': """
@skirt top=82 cx=62.5 tw=14 tips=50:95,59:98,70:98,76:95 slit=61:88:2:2 shorts=93 slope=0.9 wedge=5
""",
'torso': """
74 70 ssK
75 70 sssK
76 56 KrRRRRRRRRRRrKssmK
77 56 KCRRRRRRRRRrrKssmK
78 55 KCRRRRRRRRRRrK
78 56 KKLLLLLLLLLLKK
79 57 KllllllllllK
80 57 KTTKllllllllK
81 57 KddlllllllllK
82 57 KTTKllllllllK
""",
'armF': """
@limb 56,75,1.5 55,79,1.3
@cuff 55,78 52,89 3 9 orn=-1
""",
'armN': """
@cuff 72.5,76 75.5,90 3 11
""",
'katana': """
@katana 75 89 45 20
""",
'collar': """
71 57 KCRRRRRRRRRRRrK
72 57 KCRRvvvvRRRRRrK
73 57 KCRRRRRRRRRRrK
74 58 KrRRRRRRRRrK
75 58 KvrrrrrrrrvK
""",
'collar_over': """
67 55 K
68 55 KCK
69 56 KCK
70 56 KCRK
66 73 K
67 72 KRK
68 71 KRrK
69 71 KRrK
70 70 KRRrK
""",
'ribbonF': """
@ribbonp 57,74 neutral -1
""",
'ribbonN': """
@ribbonp 69,75 neutral 1
75 69 PK
""",
}
SHIFT = (1, 0)
