# turn_W (profile, facing viewer left). Hand-authored (NOT a mirror): near side = her LEFT, so the katana hand is
# the NEAR hand in front of the skirt; the slit opens at the front (viewer left); back tail long on the right.
HEAD = ('W', 56, 43)
ORDER = ['tail', 'legF', 'legs', 'skirt', 'torso', 'collar', 'ribbon', 'armN', 'katana', 'HEAD', 'collar_over']
LAYERS = {
'tail': """
@skirt top=84 cx=67 tw=12 tips=66:97,80:101 slope=0.5 wedge=0
""",
'legF': """
@leg 64,93 63,97 63,100 foot=w fx=-2 shade=r
""",
'legs': """
@leg 68,93 68,97 68,101 foot=w fx=-2 shade=r
""",
'skirt': """
@skirt top=82 cx=65.5 tw=11 tips=57:95,63:98,71:98,77:96 slit=59:88:3:1 shorts=93 slope=0.9 wedge=5
""",
'torso': """
75 66 KsssK
76 63 KCRRRRRRrK
77 62 KCRRRRRRRrK
78 62 KCRRRRRRRrK
78 62 KKLLLLLLLKK
79 63 KlllLLllK
80 63 KTTllLLlK
81 62 KdlllTLLllK
82 63 KTTllLLlK
""",
'collar': """
70 72 K
71 62 K.......KCK
72 62 KCRRRRRRRrK
73 62 KCRRRRRRRrK
74 63 KCRRRRRRrK
75 64 KvrrrrrvK
""",
'armN': """
@limb 66,75,1.6 66,80,1.4
@cuff 66,78 68,90 3 12
""",
'katana': """
@katana 65 90 135 18 hook=-1
""",
'collar_over': """
66 73 K
67 72 KK
68 72 KCK
69 71 KCrK
70 71 KCrK
""",
'ribbon': """
@ribbonp 69,74 neutral 1
""",
}
SHIFT = (-1, 0)
