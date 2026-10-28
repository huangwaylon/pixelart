# turn_S: front. Traced over hybrid/lock/turn/turn_S.png at the stamp's scale. Sword in her LEFT hand (viewer right).
SPEC = dict(
 head=('S', 51, 41),
 parts=[
  dict(n='skirtback', m='vio', p=[(58,88),(69,88),(71,95),(56,95)], z=0, sh=0, hl=0),
  dict(n='legL', m='skin', p=[(58,90),(62,90),(62,101),(59,101),(58,99)], z=1, sh=1),
  dict(n='legR', m='skin', p=[(65,90),(69,90),(69,99),(68,101),(65,101)], z=1, sh=2),
  dict(n='heelL', m='dark', p=[(58,101),(62,101),(62,104),(57,104)], z=2, sh=0, hl=0),
  dict(n='heelR', m='dark', p=[(65,101),(69,101),(70,104),(65,104)], z=2, sh=0, hl=0),
  dict(n='shorts', m='dark', p=[(59,86),(68,86),(69,91),(58,91)], z=3, sh=0, hl=0),
  dict(n='skirt', m='red', p=[(58,84),(69,84),(72,88),(76,95),(73,94),(71,96),(68,91),(66,87),(61,87),(59,91),(56,96),(54,94),(51,95),(55,88)],
       z=4, sh=3, sd=(1,0)),
  dict(n='shoulders', m='skin', p=[(56,76),(71,76),(73,78),(73,80),(54,80),(54,78)], z=5, sh=0),
  dict(n='torso', m='red', p=[(58,77),(69,77),(70,80),(69,84),(58,84),(57,80)], z=6, sh=2),
  dict(n='corset', m='lea', p=[(58,80),(69,80),(69,85),(58,85)], z=7, sh=0, hl=0),
  dict(n='armL', m='skin', p=[(54,78),(56,78),(56,90),(53,90)], z=8, sh=1),
  dict(n='armR', m='skin', p=[(71,78),(73,78),(74,90),(71,90)], z=8, sh=1),
  dict(n='sleeveL', m='red', p=[(53,81),(57,81),(57,87),(56,91),(51,92),(52,86)], z=9, sh=2),
  dict(n='sleeveR', m='red', p=[(70,81),(74,81),(75,86),(76,92),(71,91),(70,87)], z=9, sh=2),
  dict(n='collar', m='red', p=[(56,72),(58,74),(69,74),(71,72),(71,77),(69,78),(58,78),(56,77)], z=10, sh=2),
 ],
 ops=[
  # corset: lit top edge, two buckle straps, lace line
  "line 59,80 68,80 L", "line 59,82 68,82 K", "line 59,84 68,84 K", "stamp 60,82 T", "stamp 67,84 T",
  # collar: front opening shows the throat; flare tips stand out past the jaw
  "stamp 63,75 ss/.m", "stamp 55,71 K/R", "stamp 72,71 K/R",
  # hands
  "rect 52,91 55,92 s fill", "line 52,92 55,92 m", "rect 72,91 75,92 s fill", "line 72,92 75,92 m",
  # katana (left hand, viewer right): diamond-wrapped hilt up-left, crescent guard, blade down-right to the ground
  "line 71,87 74,91 K", "stamp 72,88 r", "stamp 73,90 r", "stamp 75,92 TT/T.",
  "line 76,93 82,104 w", "line 77,93 83,103 t",
  # ribbons from the collar back, hanging outside the sleeves, soft S-wave
  "curve 55,76 47,82 50,93 P", "curve 54,78 48,85 49,96 p",
  "curve 72,76 80,82 78,93 P", "curve 73,78 80,86 79,96 p",
  # heel straps (strappy heels): skin peeks between straps
  "stamp 59,102 s.s", "stamp 66,102 s.s",
 ])
