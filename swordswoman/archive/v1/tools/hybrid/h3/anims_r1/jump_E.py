# jump_E crouch / apex / land (ANIM_DIRECTION 5.4), built on cels/turn_E.cel.
# crouch -12 % (head sinks 2 into the collar), apex drawn 12 px up in the cell (hang, cloth floats up, smile),
# land -14 % with the skirt bell flaring out and dust puffs. Head/katana are rigid (never scaled).
FRAMES = {
 'jump_E_crouch': dict(
    base='turn_E.cel',
    off={'torso': (1, 5), 'skirt': (0, 5), 'sleeve': (-3, 5)},
    head=(2, 7), bow=(0, -1), expr='frown',
    replace={
      'legs': """@limb 66,95,2.6 71,97,2.4 67,100,1.8
@foot e 65,101
@limb 63,95,2.7 69,98,2.5 64,100,1.9
@foot en 61,101""",
      'ribbons': "@ribbon 60,82 58,85 56,89 55,93 55,97 side=-1",
      'katana': "@katana 61 93 165 22 hook=-1"},
    ops=["line 52,101 54,99 red_0", "line 51,102 53,100 K", "line 74,97 75,99 K"]),
 'jump_E_apex': dict(
    base='turn_E.cel',
    off={'torso': (0, -12), 'skirt': (0, -12), 'sleeve': (2, -16)},
    head=(0, -12), bow=(-1, -2), expr='smile',
    replace={
      'legs': """@limb 66,79,2.4 61,84,2.2 56,83,1.7
@foot etoe 53,81 flip=1
@limb 63,79,2.6 66,86,2.3 69,90,1.7
@foot point 68,90""",
      'ribbons': "@ribbon 59,64 55,61 51,60 47,61 44,63 side=1\n@ribbon 60,65 57,63 53,63 50,65 side=1",
      'katana': "@katana 68 73 150 24 hook=-1"},
    ops=["stamp 49,78 KK/KvK/.KvK", "stamp 72,77 .KK/KvK/KvK."]),
 'jump_E_land': dict(
    base='turn_E.cel',
    off={'torso': (1, 6), 'skirt': (0, 6), 'sleeve': (3, 6)},
    head=(1, 8), bow=(1, 1), expr='effort',
    replace={
      'legs': """@limb 62,96,2.7 58,98,2.5 57,101,1.9
@foot e 55,101
@limb 65,96,2.7 70,98,2.5 71,101,1.9
@foot e 69,101""",
      'ribbons': "@ribbon 60,82 59,86 59,90 60,93 side=-1",
      'katana': "@katana 62 96 165 22 hook=-1"},
    ops=["stamp 47,100 .KK/KvvK/KvvvK/.KKKK", "stamp 72,97 KK./KvK/KvvK/.KK.",
         "cluster 49,103 T XX./.XX", "cluster 45,101 t X../.X.", "cluster 84,103 T .XX/XX.", "cluster 88,101 t ..X/.X."]),
}
