# HAIR strand NOTES (v2/hair)
Task: cuter/feminine anime hairstyle options for no-sword trainer girl (red short kimono+obi, boots). 48px figure / 64 cell.
Tools: gen = .venv/bin/python tools/gemini.py image "p" out refs ; probe = v2/hair/probe.py (pal_probe-based, pk_palette)

## Step 1 research (done) - what reads at 48px (head ~14-16px tall)
- Lyra/Kotone (HGSS): twin pigtails flaring out low + big hat. Pigtails = 2 side blobs that break the head circle -> very readable; hat merges w/ hair.
- Dawn/Hikari (DPPt): long straight hair to waist + yellow hairclips + beanie. Long hair reads as a dark curtain behind body; clips are 1-2px accents (glint).
- Rosa/Mei (BW2): huge double buns (odango) + very long twin tails + visor. Most iconic silhouette at sprite size: 2 circles on top + 2 vertical streaks.
- Serena (XY): long honey hair w/ a hat; later short bob. Long hair, soft.
- May/Haruka (RSE): bandana + brown side "flips" curling outward under the bandana - the outward flip hooks are 2px and read well.
- Marnie (SwSh): asymmetric undercut bob + pink tufts/twin small tails; Gloria: short bob + tam hat; Iris: huge spiky voluminous purple hair w/ crown - volume = readability.
- Rune Factory / Story of Seasons DS: big head, 2-3 hair tones, bangs as a zig-zag 1px line over eyes, ponytails/braids as 2-3px-wide shapes with a 1px light sheen. Ribbons as 3-4px red bow.
- Atelier (DS/PS1 Marie/Elie): big hats + side locks; Mother 3 (Kumatora): simple flat masses, 1 shade; FE GBA (Eirika long hair, Lyn high ponytail): ponytail sways read clearly as a tail shape off the back of the head; Tales of Phantasia (Arche pink pigtails high, Mint): high twin tails = strongest feminine read in SNES sprites.
- Doujin pixel (e.g. ToHou-style dot sprites): ahoge + side locks framing face + big ribbon; side locks (sidelocks hanging past chin) make the face look smaller/cuter.
Rules for 48px: (1) silhouette must break the head circle (tails, buns, bow, flips); (2) side locks framing face = cute/feminine; (3) dark hair needs a 1px light sheen arc (L) to show shape; (4) bow >= 5px wide in red so it's identity; (5) avoid fine strands - masses only; (6) bangs: soft rounded/parted, not blunt-severe, shows big eyes (~3-4px tall eyes).
- step2a: fronts A-H generated via gen_opt.sh -> opt/
- step2b: iso_SE A-H generated (alts in opt/alt)
- step3/4a: probe.py + board.py -> options_board.png (+_thumb)
- FACE2 -> HAIR (22:37): face kit needs bangs to end >=1 skin row above the lash (brow row), eyes 4 w x 5 h at rows crown+7..+11 on a 15-px head. Please write 'OPTIONS READY' + top option file when you have one.
- step4b: critiques in crit_argon.txt / crit_opus.txt. Both pick A and D as top 2.
## OPTIONS READY (v2/hair/options_board.png + options_board_thumb.png)
Combined ranking (Argon,Opus): 1 A twin tails+twin bows (1,1) | 2 D odango+short tails (2,2) | 3 G high ponytail (3,6) | 4 H low pigtails/Lyra (6,4)
 | 5 B side ponytail (4,7) | 5 C hime cut (8,3; most Japanese but rectangle at 48px) | 7 E half-up (7,5; Reimu-like blob) | 8 F bob+braids (5,8; braids vanish)
Next: step5 = full 9-view turnarounds for A and D -> v2/hair/turnA, turnD
- step5a: turnA/turnD 9 views generated (gen_turn.sh)
- step5b: review: A right(3/4 front) A iso_E(3/4 back) D left(3/4 back) D right(3/4 front) wrong -> regen D left, A iso_E; right=mirror(left) (symmetric styles)
- step5c: regen ok; right=mirror(left); sheets rebuilt turnA/sheet.png turnD/sheet.png
- step5d: DONE. Top2 turnarounds: turnA/ (twin tails) and turnD/ (odango), 9 views each + sheet.png/sheet_thumb.png (illus + 48px probe).
  Caveats: iso_* views have weak 30deg camera elevation (Gemini); illustrations are slightly bigger-headed than turnE body (prop strand owns body); probe face is muddy (face2 strand owns eyes).
  Rejected-view originals kept in turn*/alt, Gemini alternates in opt/alt.
- 22:44 step6: LEAD: user PICKED E. Task: E FINAL 9-view turnaround (turnE_final/), body-sized to turnE, true 30deg iso via turnE/rigref, real side profiles, anti-Reimu bow, 48px probes + crit, DONE2
- step6a: gen_final.sh; front candidates turnE_final/cand/front_1..3
- step6b: front cands: head size now OK. cand2 best but hair too long (blob), front streamers = Reimu-tube look. round2 edits from cand2 -> front_r2a/b (sym bow), r2c/d (side-back bow)
- step6c: picked front_r2c (asymmetric side-back knot + red bow on HER LEFT; anti-Reimu) -> turnE_final/front.png. Now gen 8 views (2 cands each)
- step6d: 2 cands per view in turnE_final/cand (added right case, bow asymmetric so no mirroring)
- step6e: picks left_2 right_2 back_1 iso_S_1 iso_SE_1 iso_E_2 iso_NE_1 iso_N_1 -> turnE_final/*.png, sheet built
- step6f: iso_N -> cand2 (bow visible). trying high-camera edit pass (cand/*_hi*) for iso_E, iso_N, iso_NE
- step6g: iso_N=cand/iso_N_hi1, iso_NE=cand/iso_NE_hi2 (true high cam). iso_E_hi too squat -> moderate pass iso_E_mid*, iso_SE_mid*
- step6h: iso_E=cand/iso_E_mid2, iso_SE=cand/iso_SE_mid1; sheet rebuilt; critique next
- step6i: crit (crit_argon/opus.txt): illus OK, not Reimu, profiles real; 48px hair blobs -> masters fixes. regen iso_E (balloon skirt) from right.png; iso_N -> hi2 (higher cam)
- step6j: iso_E=cand/iso_E_r1 (slim, real profile); iso_N=cand/iso_N_hi1 (hi2 too steep). sheet rebuilt.
## E FINAL (for face2 + masters) : v2/hair/turnE_final/{front,left,back,right,iso_S,iso_SE,iso_E,iso_NE,iso_N}.png + sheet.png
Design: half-up, shoulder-blade length, ASYMMETRIC small knot + red 2-loop bow with 2 short tails on HER LEFT side-back (picture-right in front views, picture-left in back views; in the right profile it peeks from the far side). Side parting, soft side-swept bangs, thin tapered side locks, 3 hair tones (H/h + L sheen band). Head sized to the turnE body. Not Reimu (no frills, no tubes, bow off-centre).
Sources: front=cand/front_r2c, left_2, right_2, back_1, iso_S_1, iso_SE_mid1, iso_E_r1, iso_NE_hi2, iso_N_hi1.
48px MASTER RULES (crit_argon/opus): the auto-probe blobs, so hand-place these:
 1 1px h line around the tied top section + an L sheen band on it; the lower hair in H.
 2 bow >= 5x3px, e/E/R plus a 1px r knot and 2px tails; the knot gets its own ~3x3 H circle.
 3 side locks taper to 1px points at chest height; 1-2px skin/bg gap at the neck.
 4 profiles (left/right/iso_E): push forehead/nose 1px out of the head line, plus a lip notch and a chin step; the torso should not be paper-thin.
 5 keep the kimono on the E/R ramp (iso_SE/NE drift to maroon in the probe); no black stripes on the legs.
- 10-27 11:35 step7: LEAD task3: legs options (a thigh-high zettai, b tights, c knee socks, d knee-length skirt+legwear) on front/iso_SE/iso_E -> legs_board.png (64/80px probes); slim profiles; face check; iso_SE_fixed; prev/; DONE3
- step7a: old views copied to turnE_final/prev/; gen3.sh -> cand/*_s1,_s2 for iso_SE,left,right,iso_E (slim+face)
- step7b: iso_SE: Gemini keeps facing lower-left; s3-5 fail. trick: edit prev/iso_SE moving bow to her right (far side) -> mirror = cand/iso_SE_m*
- step7c: picks iso_SE=iso_SE_fixed=cand/iso_SE_m2a (faces lower-right; knot top-centre = her left-back geometrically), left=left_s2, right=right_s2, iso_E=iso_E_s2 (slim depth, cute faces). old in prev/
- step7d: gen_legs.sh -> legs/{a,b,c,d}_{front,iso_SE,iso_E}.png
- step7e: legs a,c regenerated (a: bigger skin gap; c: true below-knee); first tries in legs/prev; board rebuilt
- step7f: a regen #3 (mid-thigh), #2 in legs/prev2
- step7g: c regen #3 = real calf/knee socks (prev3 = failed). board rebuilt; critique
## LEGS OPTIONS READY : v2/hair/legs_board.png (+_thumb); variants legs/{a,b,c,d}_{front,iso_SE,iso_E}.png; crits legs/crit_argon.txt, crit_opus.txt
Ranking (Argon, Opus): 1= (a) black mid-thigh-highs, zettai ryouiki (1,2) | 1= (d) knee-length pleated skirt + thigh-highs (2,1; most kimono/hakama-like, modest) | 3 (b) dark opaque tights (3,3; legs+boots merge to a dark mass) | 4 (c) knee socks (4,4; still too bare)
Master tips: (a) keep a solid 2px skin band at 64px in all views; lighter sock top band; 1px cuff/lighter brown to split boots from socks. (d) pleats = 2-3 dark vertical lines, not dither; keep a 1px skin gap under the hem.
Turnaround fixes (task 2-4): left/right/iso_E regenerated with slim side depth + cute profile faces; iso_SE_fixed.png faces lower-right (old wrong-facing ones in turnE_final/prev/). Faces checked across views: consistent (large eyes, small mouth, soft chin). sheet.png rebuilt.
FINAL SET: pending the user's legs pick -> then apply the chosen legwear to all 9 views of turnE_final (gen_legs.sh <variant> <view> works for any view).
- 10-27 11:53 step8: LEAD: user PICKED legs (a). apply to all 9 views -> turnE_final, probes 64/80, sheet, DONE4
- step8b: legs a installed in turnE_final (bare versions -> prev/bare_*), sheet2.py sheet (64/80 probes), probes/*_64/_80.png
## FINAL SET (legs a) - for the pixelize strand
Illustrations (hair E half-up + bow on her left side-back, cheerful faces, slim profiles, black mid-thigh socks with a red top trim + skin band (zettai ryouiki), dark short boots):
 v2/hair/turnE_final/{front,left,back,right,iso_S,iso_SE,iso_E,iso_NE,iso_N}.png  (iso_SE_fixed.png = iso_SE.png, faces lower-right)
Probes (auto, palette-locked, NOT masters): v2/hair/turnE_final/probes/<view>_64.png, <view>_80.png ; sheet: turnE_final/sheet.png (+sheet_thumb.png), built by sheet2.py
Checks: sock colour equal across views (mean RGB 31-39, one dark ramp -> map to h/K + d highlight); sock top / skin band end at 0.67-0.70 H (0.73 in iso_S/iso_NE, higher camera).
Pixel notes: 2px skin band at 64px in every view; lighter sock top band (red trim = E/R); 1px boot cuff to split boots from socks; kimono stays on the E/R ramp (iso_SE/NE drift maroon in the auto probe); hair separation rules in the "E FINAL" section above.
Replaced bare-leg files: turnE_final/prev/bare_*.png
- 10-27 13:03 step9: LEAD: centre knot+bow on midline in all 9 views; prev/offset_bow_*; sheet+probes; FINAL SET v2; then v2/pixelize/make_top.sh top1; DONE5
- step9a: gen_cbow.sh -> turnE_final/cbow/<view>_1,2 (8 views; right=mirror(left))
- step9b: picks front_1 left_1 right=mirror(left_1) back_1 iso_S_2 iso_SE_2 (faces lower-right) iso_E_2 iso_NE_1 iso_N_1 installed; old -> prev/offset_bow_*; sheet + probes rebuilt
## FINAL SET v2 (centred bow) - supersedes FINAL SET (legs a) for the hair/bow only
Knot + two-loop red bow now CENTRED on her midline at the back-top of the crown (symmetric). Everything else as in legs a (black mid-thigh socks, slim profiles, cheerful faces).
Files: v2/hair/turnE_final/{front,left,back,right,iso_S,iso_SE,iso_E,iso_NE,iso_N}.png ; iso_SE_fixed.png = iso_SE.png (faces lower-right; bow behind the crown, toward picture-left = back of the head) ; right.png = mirror(left.png)
Sources: cbow/front_1, left_1, back_1, iso_S_2, iso_SE_2, iso_E_2, iso_NE_1, iso_N_1 (gen_cbow.sh). Old offset-bow set: turnE_final/prev/offset_bow_* (+ prev/offset_bow_probes/).
Rebuilt: turnE_final/sheet.png (+thumb), turnE_final/probes/<view>_64/_80.png.
- step9c: ran `v2/pixelize/make_top.sh top1` (S SE E NE N, 96px fig / 128 cell) -> v2/pixelize/top1/EC0_*_96.{png,txt,json} + sheet.png regenerated 13:10 from the centred-bow sources. All 5 ok. The S auto-master face is still muddy (eyes), so the face pass/masters are needed.
