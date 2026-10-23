# r15 AD review, round 2: S4_hd far eye + bangs

**Verdict: FIXES (2 small, rule-level)**

**Verified per pixel** (S/SE/SW/E/W; idle, walk, run, carry_walk, throw, jump_sc):
- A1 lone bridge tips: gone in SE/SW.
- A2 bob strobe: the S/SE/SW run gap stays at 1 row.
- A3 slope and throw forehead: done.
- A4 arches keep 1 px of skin.
- A5 E/W pockets: 0.

**Request 1 (SE far eye): solved. Request 2 (sloped bangs): solved**, apart from the items below.

**Remaining lone pixels (frames 1-indexed)**
- S throw f1 (20,40) and f4 (27,34): **ACCEPT**. Side-lock contour meets the outer eye corner; reads as hair at 1x.
- S jump_sc f10 (27-28,37): **FIX**. Hair fills the notch of the right `<` squint eye. The `><` goes lopsided and the eye merges into the hair. Make both pixels skin, so closed eyes keep skin on their open side.

**Fix 2: far-temple notch.** The far-contour pixel on the row above the lash is skin in:
- SE walk f1/f5/f6
- SE run f4
- SE jump_sc f2
- SE throw f1

It blinks 1 px in the walk loop. Make it hair (the A2 rule should cover the contour column).

**Gemini:** both runs failed authentication (no OIDC/mTLS), so there is no external critique. Re-run once auth is restored. This does not block the fixes above.
