"""Run Gemini pixel-native repaint on the grid templates.
gen.py MODE(1x|2x) TAG [--model M] [names...]   -> gem/<name>_<MODE>_<TAG>.png (+ .txt prompt/log)"""
import sys, subprocess, os, time
from concurrent.futures import ThreadPoolExecutor
from common import *
PY = f"{ROOT}/.venv/bin/python"
ACTION = {
 "turn": "Neutral relaxed idle stance, mid-breath, katana held low in her LEFT hand (the hand on the sword side in image 1), blade angled down and out.",
 "walk_SE_k0": "Walk CONTACT key: front heel strikes the ground, rear foot on its toe, wide stride, free arm swings back, ribbons and skirt tails trail behind.",
 "walk_SE_k1": "Walk DOWN key: weight lands, stance knee bent, the whole body 2 px lower and slightly wider (squash), skirt flares, ribbons lift and lag behind.",
 "walk_SE_k2": "Walk PASSING key: swing foot lifted and passing the stance leg, body upright, ribbons and skirt tails lagging behind.",
 "walk_SE_k3": "Walk UP key: up on the ball of the stance foot, body stretched 1 px taller, skirt hem drops, ribbons float.",
 "slash_SE_k0": "Slash ANTICIPATION (coiled): torso twisted away, sword drawn back high over her shoulder with BOTH hands, weight on the back foot, knees bent, sleeves, ribbons and skirt tails pulled the opposite way. Determined frowning eyes.",
 "slash_SE_k1_nosmear": "Slash mid-swing at full speed, lunging forward, arms and sleeves stretched along the swing, ribbons and skirt tails whipping behind. Do NOT draw any smear, arc or effect: only the character and her sword.",
 "slash_SE_k1": "Slash SMEAR frame, mid-swing at full speed: the long pale PINK/WHITE CRESCENT in image 1 is the blade-arc SMEAR. Keep it: a solid hard-edged crescent, white core leading edge, pink body, thin pointed tail, no outline, no blur. Arms and sleeves stretched along the swing, lunging forward, ribbons and skirt whipping behind.",
 "slash_SE_k2": "Slash IMPACT (hit-stop): deep forward lunge, sword fully extended level at the end of the cut, front knee bent, body low and wide, a thin pink sliver of smear just behind the blade, ribbons and skirt flung forward by the stop. Fierce focused face.",
 "slash_SE_k3": "Slash FOLLOW-THROUGH: blade past the target and settling, body still lunged, ribbons, sleeves, bow and skirt tails overshooting forward and curling (secondary overlap), small pink wisp at the end of the arc.",
 "jump_E_crouch": "Jump CROUCH (anticipation squash): deep knee bend, body squashed short and wide, arms back, head sunk into the collar, skirt flared out to the sides.",
 "jump_E_apex": "Jump APEX (stretch / hang): body stretched tall, toes pointed down, arms up, skirt and ribbons floating upward, happy open face.",
 "jump_E_land": "Jump LANDING squash: knees deeply bent, body squashed short and wide, skirt bell flared out wide, ribbons and bow still dropping (lagging), a few small dust ticks at the feet.",
}
def prompt(name, mode):
    key = "turn" if name.startswith("turn_") else name
    n = 80 if mode == "1x" else 160
    pitch = "about 13 x 13" if mode == "1x" else "about 6 x 6"
    return (
f"Image 1 is a rough {n}x{n}-pixel game sprite shown enlarged, so every sprite pixel is one flat square block of {pitch} screen pixels. "
f"REPAINT IT AS FINISHED, POLISHED, HAND-MADE PIXEL ART ON EXACTLY THE SAME GRID: {n} by {n} square blocks of the same size, every block one single flat colour, perfectly hard edges, "
"no anti-aliasing, no gradients, no blur, no texture, no half blocks. Keep the character exactly where she is in image 1: same pose, same size, same feet position, same head position and silhouette. "
"The head, face, hair bun and red bow in image 1 are already final: keep them as they are. Redraw the BODY with care: "
"chibi anime swordswoman like image 2 (the target illustration) and image 3 (the target pixel style): tall flared red collar, bare shoulders, red dress with detached flared bell sleeves, "
"dark-brown buckled corset band, thin pink scarf ribbons in soft S-curves, black shorts, pale legs, small strappy dark heels, "
"one katana with a black and red wrapped handle, a small crescent hook guard and a straight silver blade 2 pixels wide. No sheath, nothing on her back or hip, only one sword. "
f"POSE: {ACTION[key]} "
"Style: clean 1-pixel dark outline (#1a1220), 2-3 tone cel shading per material, big flat colour clusters, key light from the upper left, no noise, no dithering. "
"Use only these colours: reds #4a1640 #92203f #d8343e #f5705a, hair #42282a #74483a #b07a62, skin #c48089 #f0b49c #fde3d2, corset #4a2e20 #a8744a, shorts #504462, steel #5f6678 #a8b0c0 #eef0f5, eyes #2c3f9e #5f8ee8, pink #f49ab0 #f8b5c8, outline #1a1220. "
"Background: one flat solid green (#00c000) everywhere outside the character, no shadow, no ground, no text, no grid lines, no border. Output the same framing as image 1.")
FACING = {
 "S": "She faces the viewer (front view, seen from slightly above).",
 "SE": "She faces down-right (3/4 front view toward the lower right).",
 "E": "She faces right (side profile toward the right).",
 "NE": "She faces AWAY from the viewer toward the upper right: we see her BACK and the back of her head and dress (3/4 back view). Her face is NOT visible, only a sliver of cheek.",
 "N": "She faces AWAY from the viewer (full back view): back of the head, bun, back of the dress.",
 "NW": "She faces AWAY from the viewer toward the upper left (3/4 back view). Her face is NOT visible.",
 "W": "She faces left (side profile toward the left). Exactly ONE character.",
 "SW": "She faces down-left (3/4 front view toward the lower left).",
}
SWORD_SIDE = {"S": "RIGHT", "SE": "RIGHT", "E": "RIGHT", "NE": "LEFT", "N": "LEFT", "NW": "LEFT", "W": "LEFT", "SW": "RIGHT"}
def prompt_edit(name, mode):
    key = "turn" if name.startswith("turn_") else name
    if name == "slash_SE_k1" and os.environ.get("S5_NOSMEAR"): key = "slash_SE_k1_nosmear"
    face = FACING[dir_of(name)] + (f" The katana stays on the {SWORD_SIDE[dir_of(name)]} side of the picture exactly where it is in image 1 (it is in her left hand)." if name.startswith("turn_") else "") + " There is exactly one character. The pose in image 1 is final: do not change the pose, the arm positions or the sword angle. "
    n = 80 if mode == "1x" else 160
    return (
f"EDIT image 1. Image 1 is a {n}x{n}-pixel game sprite of a chibi swordswoman, displayed enlarged so that each sprite pixel is a big flat square block. "
"Do NOT zoom, crop, move, re-pose or recompose: the output must be the SAME sprite at the SAME size in the SAME place, every block exactly where it is in image 1, with the same chunky block size. "
"Only clean up and finish the pixel art inside her silhouette: turn the rough noisy body into clean hand-made pixel clusters, like the finished heads in image 2: "
"1-pixel dark outline, 2-3 flat tones per material with light from the upper left, a tall flared red collar, red dress with flared detached sleeves, dark-brown corset band with buckles, "
"thin pink ribbons, black shorts, pale legs, small dark heels, one katana (black/red handle, small crescent guard, straight 2-pixel silver blade). "
+ face + f"Pose and action: {ACTION[key]} "
"Keep the head, hair, bow and face blocks unchanged. Keep the flat green background. Same palette as image 1. No anti-aliasing, no gradients, no blur, no grid lines, no text.")
def refs(name):
    d = dir_of(name)
    r = [f"{ROOT}/concept/chibi_iso_v5.png", f"{ROOT}/hybrid/lock/pixel/pixel_lock_sheet.png", f"{ROOT}/hybrid/lock/turn/turn_{d}.png"]
    if name.startswith("slash"): r.append(f"{ROOT}/refs/2.png")
    return r
def run(args):
    name, mode, tag, model = args
    out = f"{OUT}/gem/{name}_{mode}_{tag}.png"
    if os.path.exists(out): return name, "cached"
    if tag.startswith("e"):
        p = prompt_edit(name, mode); rr = [f"{ROOT}/hybrid/lock/pixel/pixel_lock_sheet.png"]
        ref = os.environ.get("S5_REFSPRITE")
        if ref and not name.startswith("turn_"):
            d = dir_of(name); rp = f"{OUT}/work/ref_{d}_tpl.png"
            if os.path.exists(rp):
                rr = [rp] + rr
                p = p.replace("like the finished heads in image 2", "exactly like image 2, the FINISHED sprite of the same character standing on the same grid (same costume design, colours, proportions, outline and shading; only the pose differs), and the finished heads in image 3")
    else:
        p = prompt(name, mode); rr = refs(name)
    cmd = [PY, f"{ROOT}/tools/hybrid/s5/gem2.py", out, p, f"{OUT}/seed/{name}_tpl{mode}.png"] + rr
    if model: cmd += ["--model", model]
    open(out[:-4] + ".prompt.txt", "w").write(p + "\nREFS: " + " ".join(cmd[4:]))
    for a in range(3):
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        open(out[:-4] + ".log", "a").write(f"--- try {a}\nmodel={model}\n{r.stdout}\n{r.stderr}\n")
        if os.path.exists(out): return name, "ok"
        time.sleep(5)
    return name, "FAIL"
if __name__ == "__main__":
    a = sys.argv[1:]; mode, tag = a[0], a[1]; a = a[2:]; model = None
    if a and a[0] == "--model": model = a[1]; a = a[2:]
    names = a or NAMES
    with ThreadPoolExecutor(4) as ex:
        for r in ex.map(run, [(n, mode, tag, model) for n in names]): print(*r, flush=True)
