# r15 AD review, round 3: S4_hd

**Verdict: FIXES (1, SW only)**

Per-pixel diff vs HEAD~1 rebuild, S/SE/SW/E/W, 6 clips:
- Fix 1 (S jump_sc f10 `<`): **done**. Closed-eye skin also lands well on S throw f1/f2/f4, SE throw f6, W jump_sc f11 and SW throw/jump_sc.
- Fix 2 (SE notch): **done** in all 6 frames, plus jump_sc f4. The outline K is kept.

**Regression (SW mirror):** the temple rule turns the dark **outline** into mid-hair, which cuts the hair contour 1-3 px short:
- walk f1/f5 (16,31-32), f2 (16,32-33)
- run f8 (15,31-32)
- throw f1 (14,37-38), f4 (16,31-33)
- jump_sc f2 (15,35), f9 (16,30-31)

Only convert skin, inside the outline, the same way as SE.
