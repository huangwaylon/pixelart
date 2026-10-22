# r12 HD model — consolidated fix list (AD + animation director + GD, all ADOPT-WITH-FIXES)
Sources: r12_hd_review_AD.md, r12_hd_review_anim.md, r12_hd_review_GD.md (read them for coordinates).

Blockers (must fix before adoption):
1. E/W face: flat-cut side lock covers eye + highlight (x29-32, y27-32). Pull side lock back in profile or draw eye over hair. [AD1]
2. Rust accent restored: 2-px hem band at sprite size (legacy y49-50); hem contrast vs legs at 1x. [AD2, GD5]
3. Bang rust highlight arc (S/SE/SW y22-24) restored. [AD3]
4. Mittens: teal must win over rust cuffs (throw S f2, jump_sc N f9, carry_walk S f2). [AD4]
5. Bow loops: no 1-px antennae in S, SE outline gap, N f9 symmetric/connected. [AD5]
6. idle NE f0/5/7 hair-brown waist line flicker (curtain tips vs belt depth); check NW. [Anim1]
7. idle S/N/NE crown + knot flicker ~2x legacy: damp idle chain jitter / hold crown highlight. [Anim2]
8. N/NE/NW raised arms: bow loops merge with teal mittens — keep 1-px dark separation. [Anim3]
9. throw N/NE f4 release: throwing arm visible over curtain/bow. [Anim4]
10. walk S1,S5,SE5,SW1 / carry_walk SE4,SW0: sole on row 59 — clamp to <= 58. [GD3]
11. run height E/W 33 vs N/NE 35 — even out to within 1 px. [GD4]
12. README: correct the prop-layer claim; HD body + JSON + prop strips ship as a set. [GD1]

Next pass (not blocking): back-view ponytail separation from curtain [Anim5], walk curtain-edge flicker [Anim6],
throw E release bow 3-colour mix, E/SE ponytail flat-cut tip, climb NW f0 strays, S idle lavender singles [AD minor].
On approval: cut releases/S4_hd_actions_v1 (leave v1 untouched). [GD2]
