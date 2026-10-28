from build import F
# r8 C part check: each new dash/slash part in context, one labelled frame per part
test = [
 F(300, 'dash8_legs_lunge', legs='dash8_legs_lunge', torso='dash6_torso_lean5', head='head_lean', hd=(3, 3), aN='armN_back', kat=(8, 1),
   fx=[('fx_dash8_streak1', -22, -31, -3, 'root'), ('fx_dash8_streak2', -26, -20, -3, 'root')]),
 F(300, 'ghostA+B', legs='dash8_legs_lunge', torso='dash6_torso_lean5', head='head_lean', hd=(3, 3), aN='armN_back', kat=(8, 1),
   fx=[('fx_dash8_ghostA', -7, 0, -1, 'root'), ('fx_dash8_ghostB', -14, 0, -2, 'root')]),
 F(300, 'ghostC', legs='dash8_legs_lunge', torso='dash6_torso_lean5', head='head_lean', hd=(3, 3), aN='armN_back', kat=(9, 1),
   fx=[('fx_dash8_ghostC', -6, 0, -1, 'root')]),
 F(300, 'slash8_lunge+torso', legs='slash8_legs_lunge', torso='slash8_torso_lunge', tor=(1, 1), hd=(2, 2), aN='armN_ext', aF='armF_back', kat=(14, 5)),
]
ACTIONS = {'test_r8C': (test, False)}
CELLS = {'test_r8C': dict(cell=(72, 64), ground=(40, 60))}
