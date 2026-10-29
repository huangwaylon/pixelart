"""gen_jobs.py (F round 7): the Gemini expression-edit job list (view, expr, prompt) -> jobs.tsv; run with run_jobs.sh"""
BASE = ("Edit this anime girl head illustration. Change ONLY her facial expression: {d} Everything else identical: keep exactly the same art "
        "style, line weight, colours, shading, hair, bow, head size, position, angle and framing - pixel-for-pixel the same image except the "
        "eyes, eyebrows and mouth. Plain pure white background.")
EX = {
    'blink': "both eyes gently CLOSED (a relaxed blink: curved closed eyelid lines with lashes), calm mouth as before.",
    'smile': "a warm gentle smile with the mouth CLOSED (upturned corners), eyes open and soft, brows relaxed.",
    'joyful': "joyful laughing: both eyes closed in happy upward arcs (^ ^ shape), mouth OPEN in a big happy smile, light blush.",
    'determined': "determined and focused: eyebrows angled down toward the nose, eyes open and intense, mouth a firm straight line.",
    'surprised': "surprised: eyes wide open with small irises, eyebrows raised high, mouth a small open 'o'.",
    'squint': "squeezing both eyes tightly shut in a '> <' shape (bracing on landing), eyebrows pinched, mouth a tight short line.",
    'hurt': "in pain: both eyes squeezed shut in a '> <' shape, eyebrows tilted up toward the centre (worried), mouth a pained open grimace.",
    'effort': "straining with effort: eyes narrowed, eyebrows angled down hard, teeth gritted (mouth slightly open showing clenched teeth).",
}
VIEWS = ['S', 'SE', 'E']
with open('jobs.tsv', 'w') as f:
    for v in VIEWS:
        for e, d in EX.items():
            if v == 'S' and e == 'blink': continue   # done (test call)
            f.write(f"{v}\t{e}\t{BASE.format(d=d)}\n")
print(sum(1 for _ in open('jobs.tsv')), 'jobs')
