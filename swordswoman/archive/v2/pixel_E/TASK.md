# PIXEL-E strand (side view): current task (from the lead)
Continue from the NOTES.md progress log. The step-1 E master r1 exists; its critiques failed and need a rerun.
1. Critique master/E_katana_r1.png with Opus (`claude-as be_system`) and Argon. Fix it with targeted Gemini edits plus Claude pixel edits until it scores ≥7. Also make the no-katana E master.
2. Using v2/anim/guides/<action>_E/ (anim-r6 frames.json when present), produce idle, walk, run, jump, dash and slash for E with the pixel strand's method:
   - head-stamp variants
   - procedural blade
   - smears and FX
   Copy any tool you change from v2/pixel/anim/ into v2/pixel_E/tools/.
3. Make per-action GIFs (4×, mid-grey, per-frame ms) plus sheets in v2/pixel_E/out/, and E_all.gif.
4. Run a critic panel after each action. Iterate until Opus gives ≥7 or you can name the blocker.
Work only in v2/pixel_E/.
